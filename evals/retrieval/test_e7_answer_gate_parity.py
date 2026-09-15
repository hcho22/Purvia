"""Offline/runtime answer-gate parity guards for the weekly E7 evaluation.

No network calls: the runtime gate is injected. Run with:

    python -m evals.retrieval.test_e7_answer_gate_parity
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Awaitable, Callable

from .e7_runner import (
    E7P2Result,
    E7ParityResult,
    P2Decision,
    ParityCheck,
    e7_pinned_invariants_failed,
    render_e7_parity_section,
    run_e7_parity,
)


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _decision(
    *,
    question_id: str = "e7-p2-01",
    answered: bool | None = True,
    question: str = "How long is the electronics warranty?",
    draft: str | None = "Electronics carry a 12-month warranty.",
    context: str | None = "[1] Electronics carry a 12-month warranty.",
) -> P2Decision:
    auto = answered is True
    return P2Decision(
        question_id=question_id,
        question=question,
        decision="auto_resolve" if auto else "escalate",
        expected="auto_resolve",
        correct=auto,
        false_escalate=not auto,
        escalate_leg=None if auto else ("answer" if answered is False else "faithfulness"),
        gate_strong=True,
        top1_cosine=0.7,
        n_cleared=2,
        gate_reason="strong",
        faithfulness_score=5 if answered is not None else 3,
        helpfulness_score=5,
        faithfulness_judge_min=4,
        faithful=answered is not None,
        answered=answered,
        n_results=2,
        draft=draft,
        draft_calls=1,
        judge_calls=1,
        answer_judge_calls=1 if answered is not None else 0,
        context=context,
    )


def _result(*decisions: P2Decision) -> E7P2Result:
    return E7P2Result(
        population="P2",
        label="answerable_faithful",
        tau_sim=0.4,
        n_min=2,
        match_threshold=0.3,
        faithfulness_judge_min=4,
        judge_model="offline-test",
        n_questions=len(decisions),
        decisions=list(decisions),
    )


async def _run(
    scored: E7P2Result,
    gate: Callable[[str, str, str], Awaitable[tuple[bool, bool]]],
) -> E7ParityResult:
    return await run_e7_parity(
        results=[scored],
        runtime_answer_gate=gate,
        offline_judge_model="offline-test",
        runtime_judge_model="runtime-test",
    )


def test_matching_verdict_replays_exact_inputs_once() -> None:
    decision = _decision()
    seen: list[tuple[str, str, str]] = []

    async def gate(question: str, context: str, draft: str) -> tuple[bool, bool]:
        seen.append((question, context, draft))
        return True, False

    parity = asyncio.run(_run(_result(decision), gate))
    _check(parity.status == "pass" and parity.passed, f"expected pass, got {parity!r}")
    _check(
        seen == [(decision.question, decision.context, decision.draft)],
        f"parity must replay the exact existing inputs once, got {seen!r}",
    )
    _check(parity.to_dict()["checks"][0]["matches"] is True, "JSON must record match")
    print("ok: parity replays exact question/context/draft once and passes on agreement")


def test_mismatch_fails_and_surfaces_both_verdicts() -> None:
    async def gate(_question: str, _context: str, _draft: str) -> tuple[bool, bool]:
        return False, False

    parity = asyncio.run(_run(_result(_decision()), gate))
    rendered = "\n".join(render_e7_parity_section(parity))
    payload = parity.to_dict()
    _check(parity.status == "fail" and not parity.passed, "mismatch must fail")
    _check(payload["mismatch_ids"] == ["e7-p2-01"], f"bad mismatch ids: {payload!r}")
    for fragment in ("e7-p2-01", "True", "False", "MISMATCH"):
        _check(fragment in rendered, f"rendered parity must include {fragment!r}")
    print("ok: mismatch fails and reports row id plus offline/runtime verdicts")


def test_runtime_failure_is_unmeasured_not_agreement() -> None:
    async def gate(_question: str, _context: str, _draft: str) -> tuple[bool, bool]:
        return False, True

    parity = asyncio.run(_run(_result(_decision(answered=False)), gate))
    check = parity.checks[0]
    _check(parity.status == "unmeasured", "judge failure must be UNMEASURED")
    _check(check.matches is None, "fail-closed False must never compare as agreement")
    _check(check.runtime_judge_failed, "structured runtime failure must be retained")
    print("ok: runtime judge failure is UNMEASURED, never false agreement")


def test_missing_context_is_unmeasured_without_runtime_call() -> None:
    calls = 0

    async def gate(_question: str, _context: str, _draft: str) -> tuple[bool, bool]:
        nonlocal calls
        calls += 1
        return True, False

    parity = asyncio.run(_run(_result(_decision(context="")), gate))
    _check(parity.status == "unmeasured", "missing context must be UNMEASURED")
    _check(calls == 0, f"missing-context row must not call runtime, got {calls}")
    _check(parity.checks[0].error == "missing_context", "missing context reason lost")
    print("ok: missing context fails parity closed without a runtime call")


def test_zero_eligible_rows_is_unmeasured() -> None:
    async def gate(_question: str, _context: str, _draft: str) -> tuple[bool, bool]:
        raise AssertionError("an ineligible row must not reach runtime")

    parity = asyncio.run(_run(_result(_decision(answered=None)), gate))
    _check(parity.n_eligible == 0, f"expected zero eligible, got {parity.n_eligible}")
    _check(parity.status == "unmeasured" and not parity.passed, "zero rows cannot pass")
    print("ok: zero eligible rows is structurally UNMEASURED")


def test_parity_is_an_additive_pinned_invariant() -> None:
    base = dict(
        p1a_result=SimpleNamespace(passed=True, cleared_gate=[]),
        p1b_result=None,
        non_disclosure=None,
        p3_result=None,
        ceiling_verdict=SimpleNamespace(breached=False),
    )
    passed = E7ParityResult(
        n_questions=1,
        checks=[
            ParityCheck("P2", "ok", True, True, False, True),
        ],
    )
    failed = E7ParityResult(
        n_questions=1,
        checks=[
            ParityCheck("P2", "bad", True, False, False, False),
        ],
    )
    _check(not e7_pinned_invariants_failed(**base, parity_result=passed), "pass must be inert")
    _check(e7_pinned_invariants_failed(**base, parity_result=failed), "mismatch must pin fail")
    _check(not e7_pinned_invariants_failed(**base, parity_result=None), "omitted parity is inert")
    print("ok: parity is additive to the existing pinned-invariant decision")


def main() -> int:
    tests = [
        test_matching_verdict_replays_exact_inputs_once,
        test_mismatch_fails_and_surfaces_both_verdicts,
        test_runtime_failure_is_unmeasured_not_agreement,
        test_missing_context_is_unmeasured_without_runtime_call,
        test_zero_eligible_rows_is_unmeasured,
        test_parity_is_an_additive_pinned_invariant,
    ]
    for test in tests:
        test()
    print(f"\nPASS: {len(tests)} E7 answer-gate parity test groups")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
