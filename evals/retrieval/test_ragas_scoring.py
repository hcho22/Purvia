"""Offline regression guard for the weekly RAGAS scoring surface.

The paid provider path is replaced with deterministic doubles, but the test
drives the real repository adapter end to end: collector-shaped rows become a
RAGAS EvaluationDataset, four metric results map back onto the unchanged
question/cell identities, failures remain in the denominator, and an empty
surface cannot pass a gate.

Run:
    python -m evals.retrieval.test_ragas_scoring
"""

from __future__ import annotations

import asyncio
import importlib.util
import math
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

try:
    from packaging.requirements import Requirement
    from packaging.specifiers import SpecifierSet
    from packaging.utils import canonicalize_name
except ImportError:  # pragma: no cover - depends on the ambient slim environment
    from pip._vendor.packaging.requirements import Requirement  # type: ignore
    from pip._vendor.packaging.specifiers import SpecifierSet  # type: ignore
    from pip._vendor.packaging.utils import canonicalize_name  # type: ignore

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import evals.retrieval.ragas as ragas_mod  # noqa: E402
from evals.retrieval.ragas import (  # noqa: E402
    RAGAS_EMBEDDING_MODEL,
    RAGAS_JUDGE_MODEL,
    RAGAS_METRICS,
    RagasRow,
    RagasScoringError,
    _RagasRuntime,
    build_ragas_section,
    score_with_ragas,
)
from evals.retrieval.ragas_gates import (  # noqa: E402
    TAG_API_ERROR_DRIFT,
    TAG_COVERAGE_DRIFT,
    TAG_COVERAGE_OPERATIONAL,
    TAG_COVERAGE_PIPELINE,
    TAG_SINGLE_JUDGE_RED,
    check_diagnostic_gates,
    check_operational_gates,
    check_score_regressions,
)
from evals.retrieval.validate_ragas_snapshot import (  # noqa: E402
    InvalidRagasSnapshot,
    validate_ragas_payload,
)

REQUIREMENTS = ROOT / "evals" / "retrieval" / "requirements-ragas.txt"
PINNED_RAGAS_STACK = {
    "ragas": "0.4.3",
    "langchain": "0.3.25",
    "langchain-core": "0.3.63",
    "langchain-community": "0.3.24",
    "langchain-openai": "0.3.19",
    "langchain-text-splitters": "0.3.8",
    "langsmith": "0.2.10",
    "pydantic": "2.10.4",
}


class _FakeAPIError(Exception):
    pass


class _FakeTimeout(Exception):
    pass


class _FakeParseError(Exception):
    pass


class _FakeClient:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


class _FakeLLM:
    configs: list[tuple[str, dict[str, Any]]] = []

    async def agenerate(self, *_args: Any, **_kwargs: Any) -> object:
        return object()


class _FakeEvaluationDataset:
    last_rows: list[dict[str, Any]] = []

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.samples = [SimpleNamespace(**row) for row in rows]

    @classmethod
    def from_list(cls, rows: list[dict[str, Any]]) -> "_FakeEvaluationDataset":
        cls.last_rows = rows
        return cls(rows)


class _FakeEmbeddings:
    last_model: str | None = None

    def __init__(self, *, client: Any, model: str) -> None:
        assert isinstance(client, _FakeClient)
        type(self).last_model = model


class _FakeMetric:
    def __init__(
        self,
        name: str,
        outcomes: dict[tuple[str, str], float | BaseException],
        *,
        llm: Any,
        embeddings: Any | None = None,
    ) -> None:
        self.name = name
        self.outcomes = outcomes
        self.llm = llm
        if name == "answer_relevancy":
            assert isinstance(embeddings, _FakeEmbeddings)

    async def ascore(self, **kwargs: Any) -> SimpleNamespace:
        # The real metrics make one or more calls. One deterministic call here
        # proves the repository counter attributes calls to the correct row.
        await self.llm.agenerate("prompt", object)
        outcome = self.outcomes[(self.name, kwargs["user_input"])]
        if isinstance(outcome, BaseException):
            raise outcome
        return SimpleNamespace(value=outcome)


def _runtime(
    outcomes: dict[tuple[str, str], float | BaseException], client: _FakeClient
) -> _RagasRuntime:
    def metric(name: str):
        return lambda **kwargs: _FakeMetric(name, outcomes, **kwargs)

    def llm_factory(model: str, **kwargs: Any) -> _FakeLLM:
        _FakeLLM.configs.append((model, kwargs))
        return _FakeLLM()

    return _RagasRuntime(
        evaluation_dataset=_FakeEvaluationDataset,
        async_openai=lambda: client,
        llm_factory=llm_factory,
        embeddings=_FakeEmbeddings,
        faithfulness=metric("faithfulness"),
        answer_relevancy=metric("answer_relevancy"),
        context_precision=metric("context_precision"),
        context_recall=metric("context_recall"),
        api_error_types=(_FakeAPIError,),
        timeout_error_types=(_FakeTimeout,),
        parse_error_types=(_FakeParseError,),
    )


def _row(
    question_id: str,
    question: str,
    *,
    contexts: list[str] | None = None,
    answer: str = "answer",
) -> dict[str, Any]:
    return {
        "question_id": question_id,
        "cell": "full_access:pre_filter",
        "mode": "hybrid",
        "question": question,
        "contexts": ["grounding"] if contexts is None else contexts,
        "answer": answer,
        "reference": "reference",
    }


async def _mapping_partial_and_error_check() -> None:
    provider_wrapper = _FakeParseError("provider wrapper")
    provider_wrapper.__cause__ = _FakeAPIError("provider failed")
    timeout_wrapper = _FakeParseError("timeout wrapper")
    timeout_wrapper.__cause__ = _FakeTimeout("provider timed out")
    rows = [
        _row("q1", "healthy"),
        _row("q2", "partial"),
        _row("q3", "empty retrieval", contexts=[], answer=""),
    ]
    outcomes: dict[tuple[str, str], float | BaseException] = {
        ("faithfulness", "healthy"): 0.9,
        ("answer_relevancy", "healthy"): -0.2,
        ("context_precision", "healthy"): 0.7,
        ("context_recall", "healthy"): 0.6,
        ("faithfulness", "partial"): provider_wrapper,
        ("answer_relevancy", "partial"): math.nan,
        ("context_precision", "partial"): 0.5,
        ("context_recall", "partial"): timeout_wrapper,
    }
    client = _FakeClient()
    _FakeLLM.configs = []
    fake_runtime = _runtime(outcomes, client)
    original = ragas_mod._load_ragas_runtime
    ragas_mod._load_ragas_runtime = lambda: fake_runtime
    try:
        scored = await score_with_ragas(rows, RAGAS_JUDGE_MODEL)
    finally:
        ragas_mod._load_ragas_runtime = original

    assert [row.question_id for row in scored] == ["q1", "q2", "q3"]
    assert [row.cell for row in scored] == [
        "full_access:pre_filter",
        "full_access:pre_filter",
        "full_access:pre_filter",
    ]
    assert all(row.mode == "hybrid" for row in scored)

    assert scored[0].scores == {
        "faithfulness": 0.9,
        "answer_relevancy": -0.2,
        "context_precision": 0.7,
        "context_recall": 0.6,
    }
    assert scored[0].judge_calls == 4
    assert scored[0].api_errors == 0

    assert scored[1].scores == {
        "faithfulness": None,
        "answer_relevancy": None,
        "context_precision": 0.5,
        "context_recall": None,
    }
    assert scored[1].nan_reasons == {
        "faithfulness": "metric_error",
        "answer_relevancy": "parse_error",
        "context_precision": None,
        "context_recall": "timeout",
    }
    assert scored[1].judge_calls == 4
    assert scored[1].api_errors == 2

    assert scored[2].scores == {metric: None for metric in RAGAS_METRICS}
    assert scored[2].nan_reasons == {
        metric: "empty_contexts" for metric in RAGAS_METRICS
    }
    assert scored[2].judge_calls == 0
    assert scored[2].api_errors == 0

    # This is the actual supported RAGAS dataset vocabulary. Repository-owned
    # identity remains parallel and therefore cannot be renamed by RAGAS.
    assert _FakeEvaluationDataset.last_rows == [
        {
            "user_input": row["question"],
            "retrieved_contexts": row["contexts"],
            "response": row["answer"],
            "reference": row["reference"],
        }
        for row in rows
    ]
    assert _FakeEmbeddings.last_model == RAGAS_EMBEDDING_MODEL
    assert len(_FakeLLM.configs) == 2  # empty-context row makes no judge
    assert all(model == RAGAS_JUDGE_MODEL for model, _ in _FakeLLM.configs)
    assert all(kwargs["client"] is client for _, kwargs in _FakeLLM.configs)
    assert all(kwargs["temperature"] == 0 for _, kwargs in _FakeLLM.configs)
    assert client.closed, "the row scorer must close its private OpenAI client"

    section = build_ragas_section(scored, RAGAS_JUDGE_MODEL)
    block = section["aggregates"]["by_cell"]["full_access:pre_filter"]
    assert block["faithfulness"] == {
        "mean_strict": 0.3,
        "mean_available": 0.9,
        "coverage": 0.3333,
        "api_errors": 2,
    }
    assert block["context_precision"] == {
        "mean_strict": 0.4,
        "mean_available": 0.6,
        "coverage": 0.6667,
        "api_errors": 2,
    }
    assert block["answer_relevancy"] == {
        "mean_strict": -0.0667,
        "mean_available": -0.2,
        "coverage": 0.3333,
        "api_errors": 2,
    }
    findings = check_operational_gates(section["aggregates"])
    assert findings, "partial scoring must not pass operational gates"
    assert all(f.severity == "red" for f in findings)
    print(
        "  mapping: identities stable; success/partial/error/empty rows stay measured"
    )


async def _empty_and_malformed_checks() -> None:
    try:
        await score_with_ragas([], RAGAS_JUDGE_MODEL)
    except RagasScoringError as exc:
        assert "0 rows" in str(exc) and "vacuous green" in str(exc)
    else:
        raise AssertionError("empty scoring input returned successfully")

    try:
        build_ragas_section([], RAGAS_JUDGE_MODEL)
    except RagasScoringError as exc:
        assert "0 per-question rows" in str(exc)
    else:
        raise AssertionError("empty RAGAS section was publishable")

    duplicate = [_row("q1", "one"), _row("q1", "two")]
    client = _FakeClient()
    fake_runtime = _runtime({}, client)
    original = ragas_mod._load_ragas_runtime
    ragas_mod._load_ragas_runtime = lambda: fake_runtime
    try:
        try:
            await score_with_ragas(duplicate, RAGAS_JUDGE_MODEL)
        except RagasScoringError as exc:
            assert "duplicate" in str(exc) and "question=q1" in str(exc)
        else:
            raise AssertionError("duplicate question/cell identity was accepted")
    finally:
        ragas_mod._load_ragas_runtime = original
    print("  empty/malformed: zero rows and duplicate identities fail loudly")


def _gate_non_vacuity_check() -> None:
    findings = check_operational_gates({"by_cell": {}})
    assert len(findings) == 2 * len(RAGAS_METRICS), findings
    assert all(f.severity == "red" for f in findings)
    assert all(f.tag == TAG_COVERAGE_PIPELINE for f in findings)

    partial = {
        "by_cell": {
            "full_access:pre_filter": {
                "faithfulness": {
                    "coverage": 1.0,
                    "mean_strict": 1.0,
                    "mean_available": 1.0,
                    "api_errors": 0,
                }
            }
        }
    }
    findings = check_operational_gates(partial)
    missing = {(f.cell, f.metric) for f in findings}
    assert ("full_access:pre_filter", "answer_relevancy") in missing
    assert ("partial_access:pre_filter", "faithfulness") in missing

    complete = {
        "by_cell": {
            cell: {
                metric: {
                    "coverage": 1.0,
                    "mean_strict": 0.75,
                    "mean_available": 0.75,
                    "api_errors": 0,
                }
                for metric in RAGAS_METRICS
            }
            for cell in ("full_access:pre_filter", "partial_access:pre_filter")
        }
    }
    assert check_operational_gates(complete) == []

    one_provider_failure = {
        "by_cell": {
            cell: {
                metric: {**block, "api_errors": int(cell == "full_access:pre_filter")}
                for metric, block in metrics.items()
            }
            for cell, metrics in complete["by_cell"].items()
        }
    }
    one_provider_failure["by_cell"]["full_access:pre_filter"]["faithfulness"][
        "coverage"
    ] = 59 / 60
    findings = check_operational_gates(one_provider_failure)
    assert any(
        finding.tag == TAG_COVERAGE_PIPELINE
        and finding.metric == "faithfulness"
        for finding in findings
    )
    assert sum(f.tag == TAG_COVERAGE_OPERATIONAL for f in findings) == 1

    one_metric_failure = {
        "by_cell": {
            cell: {metric: dict(block) for metric, block in metrics.items()}
            for cell, metrics in complete["by_cell"].items()
        }
    }
    one_metric_failure["by_cell"]["full_access:pre_filter"]["context_precision"][
        "coverage"
    ] = 59 / 60
    findings = check_operational_gates(one_metric_failure)
    assert len(findings) == 1
    assert findings[0].tag == TAG_COVERAGE_PIPELINE
    assert findings[0].metric == "context_precision"
    print("  gates: missing structure or one failed metric/provider call is red")


def _history_baseline_eligibility_check() -> None:
    cell_id = "full_access:pre_filter"

    def cell(
        context_precision: float,
        *,
        coverage: float = 1.0,
        api_errors: int = 0,
    ) -> dict[str, dict[str, float | int]]:
        return {
            metric: {
                "mean_strict": context_precision
                if metric == "context_precision"
                else 0.9,
                "coverage": coverage,
                "api_errors": api_errors,
            }
            for metric in RAGAS_METRICS
        }

    current = {
        "ragas": {"aggregates": {"by_cell": {cell_id: cell(0.8)}}},
        "aggregates": {},
    }
    eligible = {"by_cell": {cell_id: cell(0.9)}}
    partial_low = {"by_cell": {cell_id: cell(0.4, coverage=0.5)}}
    findings = check_score_regressions(
        current,
        [eligible for _ in range(4)] + [partial_low for _ in range(4)],
        [],
    )
    assert any(
        finding.tag == TAG_SINGLE_JUDGE_RED
        and finding.metric == "context_precision"
        for finding in findings
    ), "partial low scores must not depress an eligible regression baseline"

    insufficient = [eligible for _ in range(3)] + [partial_low]
    assert check_score_regressions(current, insufficient, []) == []

    provider_error = {"by_cell": {cell_id: cell(0.9, api_errors=1)}}
    assert check_score_regressions(
        current, [provider_error for _ in range(4)], []
    ) == []

    diagnostic_current = {
        "by_cell": {cell_id: cell(0.8, coverage=0.8, api_errors=1)}
    }
    missing: dict[str, Any] = {"by_cell": {}}
    assert check_diagnostic_gates(
        diagnostic_current, [eligible, missing, missing, missing]
    ) == []

    diagnostic_findings = check_diagnostic_gates(
        diagnostic_current, [eligible, eligible, eligible, missing]
    )
    assert any(f.tag == TAG_COVERAGE_DRIFT for f in diagnostic_findings)
    assert any(f.tag == TAG_API_ERROR_DRIFT for f in diagnostic_findings)
    print("  history: only enough complete zero-error runs form a baseline")


def _snapshot_publishability_check() -> None:
    rows = [
        RagasRow(
            question_id="q1",
            cell=cell,
            mode="hybrid",
            scores={metric: 0.75 for metric in RAGAS_METRICS},
            nan_reasons={metric: None for metric in RAGAS_METRICS},
            judge_calls=4,
        )
        for cell in ("full_access:pre_filter", "partial_access:pre_filter")
    ]
    section = build_ragas_section(rows, RAGAS_JUDGE_MODEL)
    validate_ragas_payload({"ragas": section})

    for invalid in (
        {"ragas": {"per_question": [], "aggregates": {"by_cell": {}}}},
        {
            "ragas": {
                **section,
                "aggregates": {"by_cell": {"full_access:pre_filter": {}}},
            }
        },
    ):
        try:
            validate_ragas_payload(invalid)
        except InvalidRagasSnapshot:
            pass
        else:
            raise AssertionError("empty/partial RAGAS snapshot was publishable")
    print("  snapshot: only non-empty rows + both complete cells are publishable")


def _dependency_contract_check() -> None:
    requirements: dict[str, list[Requirement]] = {}
    for raw in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line and not line.startswith("-"):
            requirement = Requirement(line)
            canonical_name = canonicalize_name(requirement.name)
            requirements.setdefault(canonical_name, []).append(requirement)

    for package_name, pinned_version in PINNED_RAGAS_STACK.items():
        declared = requirements.get(package_name, [])
        assert len(declared) == 1, (
            "evals/retrieval/requirements-ragas.txt must declare the RAGAS "
            f"compatibility dependency {package_name} exactly once; got {declared!r}"
        )
        requirement = declared[0]
        assert (
            requirement.specifier == SpecifierSet(f"=={pinned_version}")
            and not requirement.extras
            and requirement.marker is None
            and requirement.url is None
        ), (
            "evals/retrieval/requirements-ragas.txt must exactly pin the verified "
            f"RAGAS compatibility dependency {package_name} to {pinned_version}; "
            f"got {requirement!r}"
        )

    if importlib.util.find_spec("ragas") is not None:
        from importlib.metadata import version

        for package_name, pinned_version in PINNED_RAGAS_STACK.items():
            assert version(package_name) == pinned_version, (
                f"installed {package_name} must match the verified RAGAS compatibility "
                f"version {pinned_version}; got {version(package_name)}"
            )
        runtime = ragas_mod._load_ragas_runtime()
        assert callable(runtime.evaluation_dataset.from_list)
        assert all(
            callable(component)
            for component in (
                runtime.llm_factory,
                runtime.embeddings,
                runtime.faithfulness,
                runtime.answer_relevancy,
                runtime.context_precision,
                runtime.context_recall,
            )
        )
        print("  dependency: installed compatibility set exposes all four metrics")
    elif os.environ.get("RAGAS_RUNTIME_REQUIRED") == "1":
        raise AssertionError(
            "RAGAS_RUNTIME_REQUIRED=1 but the pinned RAGAS runtime is not installed"
        )
    else:
        print("  dependency: exact compatibility set declared (import skipped)")


async def amain() -> int:
    print("RAGAS scoring regression guard (offline deterministic doubles):")
    await _mapping_partial_and_error_check()
    await _empty_and_malformed_checks()
    _gate_non_vacuity_check()
    _history_baseline_eligibility_check()
    _snapshot_publishability_check()
    _dependency_contract_check()
    print("\nPASS: RAGAS scoring emits real-shaped rows and cannot pass empty")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(amain()))
