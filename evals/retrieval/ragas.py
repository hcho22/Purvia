"""US-001: RAGAS scoring module — a parallel eval signal alongside the custom Claude judge.

RAGAS (Retrieval Augmented Generation Assessment) computes the four canonical
RAG metrics — Faithfulness, Answer Relevancy, Context Precision, Context
Recall — over the retrieval eval's 60-question golden set. Those standardized
metric names appear in nearly every reference RAG paper and competitor doc, so
shipping them lets a reader recognize the methodology without reading runner
source.

Same-family bias trade-off
--------------------------
The RAGAS judge LLM is ``gpt-4o-mini`` — the *same vendor family* (OpenAI) as
the eval's answer generator (``runner.py``'s ``generate_answer``, US-036, whose
model is selected by ``GENERATION_MODEL`` and is not necessarily ``gpt-4o-mini``).
A judge that shares a family with the generator can be systematically lenient: it
tends to favour outputs that "reason like it does". We accept this deliberately:

  * Cost. ``gpt-4o-mini`` is cheap enough to run all four metrics weekly.
  * Independence is preserved elsewhere. The existing custom Claude judge
    (``runner.py::judge_answer``) is a genuine *cross-family* observation —
    different vendor, different model, different prompting technique — and it
    remains the load-bearing headline signal. RAGAS ships *alongside* it for
    standardized-vocabulary parity, not as a replacement.

So RAGAS trades judge independence for recognizable vocabulary; the Claude
judge keeps the independence. The two judges measure overlapping ground from
independent angles.

Lazy import
-----------
``ragas`` pulls in instructor, langchain-core, datasets and pandas — heavy deps
the PR-CI install (``requirements-ci.txt``) deliberately omits. All RAGAS
imports therefore happen inside ``_load_ragas_runtime``, called only by
``score_with_ragas``. Importing this module — or ``runner.py`` — never costs the
RAGAS install; only an actual ``--include-ragas`` run does.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import math
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any, Callable

log = logging.getLogger("agentic_rag.evals.retrieval.ragas")

# The four canonical RAGAS metrics, in display order.
RAGAS_METRICS: tuple[str, ...] = (
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
)

# FR-7: a NaN score carries a reason from this fixed enum — never free text —
# so downstream gate logic (US-005+) can branch on it programmatically. A
# score that succeeded stores `None`. An out-of-enum string is coerced to
# `unknown` by `_normalize_nan_reason` rather than stored verbatim.
NAN_REASONS: frozenset[str] = frozenset(
    {
        "judge_refused",
        "parse_error",
        "empty_contexts",
        "metric_error",
        "timeout",
        "unknown",
    }
)

# FR-4: the RAGAS judge LLM is gpt-4o-mini, hardcoded in v1 — deliberately not
# exposed on the CLI so an eval run can't be accidentally misconfigured onto a
# different judge. It shares a model family with the answer generator; see the
# same-family bias note in the module docstring.
RAGAS_JUDGE_MODEL = "gpt-4o-mini"

# RAGAS 0.4's Answer Relevancy metric is the only canonical metric here that
# needs embeddings. Keep the model explicit so a dependency default cannot
# silently change the meaning of the weekly time series.
RAGAS_EMBEDDING_MODEL = "text-embedding-3-small"

# Bound provider concurrency independently of the 60-question × two-cell input
# size. Each row runs its four metrics sequentially so judge-call accounting is
# exact; rows run concurrently so the weekly remains comfortably bounded.
RAGAS_MAX_CONCURRENCY = 8

# FR-3: RAGAS scores hybrid retrieval only. Cross-mode comparison already lives
# in the recall@k tables, so running RAGAS on vector / keyword adds no new
# comparative signal — just cost.
RAGAS_MODE = "hybrid"

# FR-3: of the six (viewer × filter) cells the runner sweeps, RAGAS scores only
# these two. full_access×post_filter is degenerate (full_access sees
# everything, so post-filtering drops nothing); the no_access cells are covered
# by the security table; partial_access×post_filter is covered by the recall
# trade-off table. Only the two pre_filter cells carry new RAGAS signal.
RAGAS_CELLS: frozenset[tuple[str, str]] = frozenset(
    {("full_access", "pre_filter"), ("partial_access", "pre_filter")}
)

# The same two cells as ordered `viewer:filter` id strings — the keys used in
# RagasRow.cell and aggregates.by_cell, and the row order of the summary.md
# RAGAS comparison table. Ordered (frozensets are not) so output is stable.
RAGAS_CELL_IDS: tuple[str, ...] = (
    "full_access:pre_filter",
    "partial_access:pre_filter",
)


def ragas_cell_enabled(mode: str, viewer: str, filter_strategy: str) -> bool:
    """True when RAGAS should score this (mode × viewer × filter) cell.

    The gate is the conjunction of FR-3's two conditions: hybrid mode AND one
    of the two pre_filter cells in ``RAGAS_CELLS``. Every other combination is
    skipped so the weekly cost stays bounded.
    """
    return mode == RAGAS_MODE and (viewer, filter_strategy) in RAGAS_CELLS


@dataclass
class RagasRow:
    """One question's RAGAS scores for a single (cell × mode).

    ``scores`` and ``nan_reasons`` are keyed by the names in ``RAGAS_METRICS``.
    A ``None`` score carries a matching ``nan_reasons`` entry drawn from the
    fixed failure-reason enum (``judge_refused``, ``parse_error``,
    ``empty_contexts``, ``metric_error``, ``timeout``, ``unknown``); a
    successful score stores ``None`` as its reason.

    ``judge_calls`` counts row-local calls from a RAGAS metric into the
    evaluator wrapper. Provider-internal retries inside one wrapper call are
    intentionally not represented as additional logical judge calls.
    """

    question_id: str
    cell: str
    mode: str
    scores: dict[str, float | None] = field(default_factory=dict)
    nan_reasons: dict[str, str | None] = field(default_factory=dict)
    api_errors: int = 0
    judge_calls: int = 0


class RagasScoringError(RuntimeError):
    """The requested RAGAS run could not produce a meaningful measurement."""


@dataclass(frozen=True)
class _RagasRuntime:
    """Lazy-loaded RAGAS/OpenAI surface, replaceable by offline test doubles."""

    evaluation_dataset: Any
    async_openai: Callable[..., Any]
    llm_factory: Callable[..., Any]
    embeddings: Callable[..., Any]
    faithfulness: Callable[..., Any]
    answer_relevancy: Callable[..., Any]
    context_precision: Callable[..., Any]
    context_recall: Callable[..., Any]
    api_error_types: tuple[type[BaseException], ...]
    timeout_error_types: tuple[type[BaseException], ...]
    parse_error_types: tuple[type[BaseException], ...]


def _load_ragas_runtime() -> _RagasRuntime:
    """Import the pinned RAGAS 0.4 collections API only on the paid path."""
    try:
        from instructor.core.exceptions import (  # type: ignore[import-untyped]
            AsyncValidationError,
            IncompleteOutputException,
            InstructorRetryException,
        )
        from openai import APIError, APITimeoutError, AsyncOpenAI
        from ragas import EvaluationDataset
        from ragas.embeddings import OpenAIEmbeddings
        from ragas.llms import llm_factory
        from ragas.metrics.collections import (
            AnswerRelevancy,
            ContextPrecisionWithReference,
            ContextRecall,
            Faithfulness,
        )
    except ImportError as e:  # pragma: no cover - exercised in the slim CI env
        raise RuntimeError(
            "--include-ragas requires the pinned `ragas` package. "
            "Run `pip install -r evals/retrieval/requirements.txt`."
        ) from e

    return _RagasRuntime(
        evaluation_dataset=EvaluationDataset,
        async_openai=AsyncOpenAI,
        llm_factory=llm_factory,
        embeddings=OpenAIEmbeddings,
        faithfulness=Faithfulness,
        answer_relevancy=AnswerRelevancy,
        context_precision=ContextPrecisionWithReference,
        context_recall=ContextRecall,
        api_error_types=(APIError,),
        timeout_error_types=(APITimeoutError, asyncio.TimeoutError),
        parse_error_types=(
            AsyncValidationError,
            IncompleteOutputException,
            InstructorRetryException,
        ),
    )


def _required_text(row: dict[str, Any], key: str, index: int) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RagasScoringError(
            f"RAGAS input row {index} has no non-empty `{key}`; refusing an "
            "unscoreable run"
        )
    return value


def _build_evaluation_dataset(
    rows: list[dict[str, Any]], runtime: _RagasRuntime
) -> tuple[Any, list[tuple[str, str, str]]]:
    """Validate identities and map collector rows to RAGAS's supported schema."""
    dataset_rows: list[dict[str, Any]] = []
    identities: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    for index, row in enumerate(rows):
        question_id = _required_text(row, "question_id", index)
        cell = _required_text(row, "cell", index)
        mode = _required_text(row, "mode", index)
        identity = (question_id, cell, mode)
        if identity in seen:
            raise RagasScoringError(
                "duplicate RAGAS input identity "
                f"question={question_id} cell={cell} mode={mode}"
            )
        seen.add(identity)

        contexts = row.get("contexts")
        if not isinstance(contexts, list) or any(
            not isinstance(context, str) for context in contexts
        ):
            raise RagasScoringError(
                f"RAGAS input row {index} has invalid `contexts`; expected list[str]"
            )

        # An empty context list is a measured retrieval failure, not a missing
        # row. It stays in the dataset/denominator and becomes `empty_contexts`
        # for all four metrics below. `answer` may consequently be empty because
        # the generator is deliberately not called without grounding context.
        answer = row.get("answer")
        if not isinstance(answer, str):
            raise RagasScoringError(
                f"RAGAS input row {index} has invalid `answer`; expected str"
            )
        if contexts and not answer.strip():
            raise RagasScoringError(
                f"RAGAS input row {index} has contexts but an empty `answer`; "
                "refusing to score a failed generation as a real response"
            )

        dataset_rows.append(
            {
                "user_input": _required_text(row, "question", index),
                "retrieved_contexts": contexts,
                "response": answer,
                "reference": _required_text(row, "reference", index),
            }
        )
        identities.append(identity)

    dataset = runtime.evaluation_dataset.from_list(dataset_rows)
    samples = getattr(dataset, "samples", None)
    if not isinstance(samples, list) or len(samples) != len(rows):
        raise RagasScoringError(
            "RAGAS EvaluationDataset changed row cardinality; refusing to map "
            "scores onto the wrong question identities"
        )
    return dataset, identities


@dataclass
class _JudgeCallCounter:
    calls: int = 0


def _count_judge_calls(llm: Any) -> _JudgeCallCounter:
    """Count row-local calls from RAGAS metrics into the evaluator wrapper."""
    counter = _JudgeCallCounter()
    original = llm.agenerate

    async def counted(*args: Any, **kwargs: Any) -> Any:
        counter.calls += 1
        return await original(*args, **kwargs)

    llm.agenerate = counted
    return counter


def _exception_contains(
    exc: BaseException, error_types: tuple[type[BaseException], ...]
) -> bool:
    """Inspect provider errors wrapped by instructor retry/validation errors."""
    pending: list[BaseException] = [exc]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if isinstance(current, error_types):
            return True
        for candidate in (
            current.__cause__,
            current.__context__,
            getattr(current, "last_exception", None),
        ):
            if isinstance(candidate, BaseException):
                pending.append(candidate)
    return False


def _metric_failure_reason(exc: BaseException, runtime: _RagasRuntime) -> str:
    if _exception_contains(exc, runtime.timeout_error_types):
        return "timeout"
    if _exception_contains(exc, runtime.api_error_types):
        return "metric_error"
    if _exception_contains(exc, runtime.parse_error_types):
        return "parse_error"
    return "metric_error"


def _score_value(result: Any) -> tuple[float | None, str | None]:
    """Normalize a RAGAS MetricResult without allowing NaN/invalid ranges."""
    value = getattr(result, "value", result)
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None, "parse_error"
    if not math.isfinite(score):
        return None, "parse_error"
    if not 0.0 <= score <= 1.0:
        return None, "metric_error"
    return score, None


async def _score_sample(
    sample: Any,
    identity: tuple[str, str, str],
    judge_model: str,
    client: Any,
    embeddings: Any,
    runtime: _RagasRuntime,
    semaphore: asyncio.Semaphore,
) -> RagasRow:
    question_id, cell, mode = identity
    contexts = sample.retrieved_contexts or []
    if not contexts:
        return RagasRow(
            question_id=question_id,
            cell=cell,
            mode=mode,
            scores={metric: None for metric in RAGAS_METRICS},
            nan_reasons={metric: "empty_contexts" for metric in RAGAS_METRICS},
        )

    async with semaphore:
        try:
            # One row-local wrapper lets us attribute the exact number of RAGAS
            # judge calls despite running several rows concurrently.
            llm = runtime.llm_factory(judge_model, client=client, temperature=0)
            counter = _count_judge_calls(llm)
        except Exception as exc:
            raise RagasScoringError(
                "failed to configure RAGAS evaluator for "
                f"question={question_id} cell={cell} mode={mode}: "
                f"{type(exc).__name__}"
            ) from exc

        specs: tuple[tuple[str, Callable[[], Any], dict[str, Any]], ...] = (
            (
                "faithfulness",
                lambda: runtime.faithfulness(llm=llm),
                {
                    "user_input": sample.user_input,
                    "response": sample.response,
                    "retrieved_contexts": contexts,
                },
            ),
            (
                "answer_relevancy",
                lambda: runtime.answer_relevancy(llm=llm, embeddings=embeddings),
                {"user_input": sample.user_input, "response": sample.response},
            ),
            (
                "context_precision",
                lambda: runtime.context_precision(llm=llm),
                {
                    "user_input": sample.user_input,
                    "reference": sample.reference,
                    "retrieved_contexts": contexts,
                },
            ),
            (
                "context_recall",
                lambda: runtime.context_recall(llm=llm),
                {
                    "user_input": sample.user_input,
                    "retrieved_contexts": contexts,
                    "reference": sample.reference,
                },
            ),
        )

        scores: dict[str, float | None] = {}
        nan_reasons: dict[str, str | None] = {}
        api_errors = 0
        for metric, build_metric, kwargs in specs:
            try:
                result = await build_metric().ascore(**kwargs)
                score, reason = _score_value(result)
            except Exception as exc:
                score = None
                reason = _metric_failure_reason(exc, runtime)
                if _exception_contains(
                    exc, runtime.api_error_types + runtime.timeout_error_types
                ):
                    api_errors += 1
                # Do not print provider response bodies: they can echo prompt
                # content. Identity + exception class is enough to triage.
                log.warning(
                    "RAGAS %s failed for question=%s cell=%s mode=%s (%s)",
                    metric,
                    question_id,
                    cell,
                    mode,
                    type(exc).__name__,
                )
            scores[metric] = score
            nan_reasons[metric] = reason

        return RagasRow(
            question_id=question_id,
            cell=cell,
            mode=mode,
            scores=scores,
            nan_reasons=nan_reasons,
            api_errors=api_errors,
            judge_calls=counter.calls,
        )


async def score_with_ragas(
    rows: list[dict[str, Any]], judge_model: str
) -> list[RagasRow]:
    """Score ``rows`` with the four canonical RAGAS metrics.

    ``rows`` is the per-question generation detail produced by the runner
    (question, retrieved contexts, generated answer, reference). ``judge_model``
    is the RAGAS judge LLM — ``gpt-4o-mini`` in v1 (see FR-4).

    Uses RAGAS 0.4's supported ``EvaluationDataset`` schema and collections
    metrics. The returned list is positionally identical to ``rows``: identity
    stays in repository-owned metadata while the RAGAS dataset carries only its
    canonical fields (``user_input``, ``retrieved_contexts``, ``response``,
    ``reference``).

    Metric failures are isolated to one metric/question and surfaced as a
    ``None`` score plus a fixed ``nan_reason``. A completely empty input is a
    harness defect and raises: publishing zero rows would make every downstream
    coverage/regression gate vacuously green.
    """
    if not rows:
        raise RagasScoringError(
            "RAGAS scoring received 0 rows; refusing a vacuous green run. "
            "Check --mode/--viewers, generation gold, and retrieval collection."
        )

    runtime = _load_ragas_runtime()
    dataset, identities = _build_evaluation_dataset(rows, runtime)
    client = runtime.async_openai()
    try:
        embeddings = runtime.embeddings(client=client, model=RAGAS_EMBEDDING_MODEL)
        semaphore = asyncio.Semaphore(RAGAS_MAX_CONCURRENCY)
        scored = await asyncio.gather(
            *(
                _score_sample(
                    sample,
                    identity,
                    judge_model,
                    client,
                    embeddings,
                    runtime,
                    semaphore,
                )
                for sample, identity in zip(dataset.samples, identities)
            )
        )
    finally:
        close = getattr(client, "close", None)
        if close is not None:
            closed = close()
            if inspect.isawaitable(closed):
                await closed

    if len(scored) != len(rows):  # defensive: gather should make this impossible
        raise RagasScoringError(
            f"RAGAS scored {len(scored)} of {len(rows)} rows; refusing partial "
            "identity mapping"
        )
    return list(scored)


def _normalize_nan_reason(reason: str | None) -> str | None:
    """Coerce a NaN reason onto the fixed `NAN_REASONS` enum (FR-7).

    `None` (the score succeeded) passes through unchanged. An out-of-enum
    string is recorded as `unknown` with a warning rather than stored verbatim
    — an arbitrary reason string would defeat programmatic gate evaluation.
    """
    if reason is None or reason in NAN_REASONS:
        return reason
    log.warning(
        "RAGAS nan_reason %r is not in the fixed enum; recording as 'unknown'",
        reason,
    )
    return "unknown"


def _aggregate_by_cell(rows: list[RagasRow]) -> dict[str, dict[str, Any]]:
    """Per (cell × metric): mean_strict, mean_available, coverage, api_errors.

    `mean_strict` averages over every question in the cell with NaN counted as
    0 — the headline number, so a degraded run can't hide behind a shrinking
    denominator (FR-6: never `nanmean` for a headline). `mean_available`
    averages over non-NaN scores only, and is `None` when a metric scored NaN
    everywhere. `coverage` is the non-NaN fraction. `api_errors` is the cell
    total — RagasRow counts errors per question, not per metric, so the same
    cell total appears in each of the four metric blocks.
    """
    cells: dict[str, list[RagasRow]] = defaultdict(list)
    for row in rows:
        cells[row.cell].append(row)

    by_cell: dict[str, dict[str, Any]] = {}
    for cell, cell_rows in cells.items():
        total = len(cell_rows)
        api_errors = sum(row.api_errors for row in cell_rows)
        metrics: dict[str, Any] = {}
        for metric in RAGAS_METRICS:
            available: list[float] = []
            for row in cell_rows:
                value = row.scores.get(metric)
                if value is not None:
                    available.append(value)
            n_available = len(available)
            metrics[metric] = {
                "mean_strict": round(sum(available) / total, 4),
                "mean_available": (
                    round(sum(available) / n_available, 4) if n_available else None
                ),
                "coverage": round(n_available / total, 4),
                "api_errors": api_errors,
            }
        by_cell[cell] = metrics
    return by_cell


def build_ragas_section(rows: list[RagasRow], judge_model: str) -> dict[str, Any]:
    """Assemble the `ragas` top-level results-JSON section (US-003).

    Shape: `judge_model`, `per_question` (one normalized RagasRow dict per
    scored question), and `aggregates.by_cell`. RAGAS lives under its own
    top-level key so existing consumers of the results JSON — which never look
    for `ragas` — stay byte-stable (FR-5).
    """
    if not rows:
        raise RagasScoringError(
            "RAGAS produced 0 per-question rows; refusing to publish an empty "
            "comparison or evaluate gates without a denominator"
        )

    identities = [(row.question_id, row.cell, row.mode) for row in rows]
    if len(set(identities)) != len(identities):
        raise RagasScoringError(
            "RAGAS produced duplicate question/cell/mode rows; refusing an "
            "ambiguous aggregate"
        )
    question_ids_by_cell: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        question_ids_by_cell[row.cell].add(row.question_id)
    present_expected = [
        question_ids_by_cell[cell]
        for cell in RAGAS_CELL_IDS
        if cell in question_ids_by_cell
    ]
    if len(present_expected) > 1 and any(
        ids != present_expected[0] for ids in present_expected[1:]
    ):
        counts = ", ".join(
            f"{cell}={len(question_ids_by_cell[cell])}"
            for cell in RAGAS_CELL_IDS
            if cell in question_ids_by_cell
        )
        raise RagasScoringError(
            "RAGAS comparison cells cover different question identities "
            f"({counts}); refusing a biased comparison"
        )

    per_question: list[dict[str, Any]] = []
    for row in rows:
        record = asdict(row)
        record["nan_reasons"] = {
            metric: _normalize_nan_reason(reason)
            for metric, reason in row.nan_reasons.items()
        }
        per_question.append(record)

    return {
        "judge_model": judge_model,
        "per_question": per_question,
        "aggregates": {"by_cell": _aggregate_by_cell(rows)},
    }
