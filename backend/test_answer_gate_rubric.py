"""Issue #104: the answer-completeness gate's RUBRIC, as opposed to its plumbing.

`test_answer_gate.py` drives `answer_gate` through a fake judge that returns a
canned verdict. That pins the plumbing — exactly-one-call, fail-closed, clamping,
cutoff — and it is deliberately blind to what the rubric actually DISCRIMINATES,
because the fake never reads the prompt. Until this file there was no layer below
the weekly E7 sweep where a rubric change could be pinned at all, which is why the
issue-#104 gap survived from the gate's authoring (PR #99) to the 2026-08-03 sweep.

THE GAP THIS FILE PINS
----------------------
The original rubric caught the shape that ANNOUNCES itself — a draft saying it
lacks the information. It missed the shape where the CORPUS's own answer is a
deferral. `db_seed/corpus/returns-process.md:33` says return shipping over 20 lbs
is "quoted per-case"; `db_seed/corpus/warranty-terms.md:29` says a book warranty
claim past 30 days is "at the discretion of customer service". A draft restating
either is faithful, fluent, and lands exactly on the slot the question asked
about, so the gate read the slot as filled and auto-sent. The customer still has
no fee and no warranty period. `e7-p3-05` and `e7-p3-11` false-resolved that way.

Those two shapes are ORTHOGONAL, and both must be pinned:
  * whether the draft ADMITS ignorance is a fact about the drafter;
  * whether the customer ends up HOLDING the requested value is a fact about the
    answer.
Keying on the first alone made the send/escalate verdict ride on whether
`gpt-4o-mini` happened to append "Therefore, I don't have that information" — an
observed coin flip across runs of the same row.

THE RESIDUAL THIS FILE PINS (issue #104-residual / the retrieved-context fix)
-----------------------------------------------------------------------------
The two deferral shapes above are both announced by the DRAFT's own wording. The
third shape needs the RETRIEVED CONTEXT: a draft that states a fact ADJACENT to
the question — who pays, when it is paid, that no fee is published — when the
ASKED value itself is absent from the context. The draft is faithful and fluent,
stays exactly on the asked subject, and volunteers no disclaimer, so the old
rubric read the slot as filled. Both rubrics now receive the retrieved context
and state the rule: when the value asked for is absent from the RETRIEVED
CONTEXT, no draft that merely restates what the CONTEXT does contain can be that
value. The `_CASES` rows below carry the corpus slice each draft was written
from, and the live layer threads it into both implementations.

THE FIX THIS FILE NOW PINS (ADR-0015, 2026-10-16)
-------------------------------------------------
The residual above was closed in the prompt but not in the verdict: a single
boolean on the adjacent-fact draft was a thin argmax. On the verbatim `e7-p3-10`
triple the `answers` token's P(true) read 0.22 to 0.44 across identical calls and
sampling at temperature 1 passed it 10 of 20, so the temperature-0 verdict could
flip with serving noise (the erratum recorded 5 of 10 passing; a 40-run
measurement on 2026-10-15 recorded 0, which is what a thin argmax looks like from
the lucky side). The runtime gate now has the judge commit to `asked_value`,
`stated_value` and `same_kind` BEFORE it decides, and the verdict requires a stated
value of the asked kind. The unit layer pins the mechanism with no model (verdict
cells, field order, the lockstep rules, the offline mirror carrying the same
fields); the live layer pins what it CONCLUDES, on both implementations:
`_CASES` (hand-written and real-context rows, three reps, unanimous) and
`answer_gate_measured_trade.json` (the measured trade: 19 should-answer drafts that
must still send, the 24 distinct `e7-p3-10` drafts that must not, a constructed
who-pays answer to a who-pays question that must send next to a constructed range
for an exact-amount question that must not, and the one KNOWN REMAINING GAP below).

THE KNOWN REMAINING GAP, asserted as such
-----------------------------------------
`e7-p3-07` asks for the goodwill refund cap ONCE A CASE IS ESCALATED to a
supervisor. A draft that states the UN-escalated cap ("50% of the order total")
names a real, specific value of the asked kind, for the wrong branch. Every rubric
measured on 2026-10-15 sent it: the old gate (in the replay, and 4 of 10 at
temperature 1), this one (8 of 8 at temperature 0) and a variant with a same-case
field (8 of 8). The measured-trade fixture holds that draft as `known_gap_answers`
and the live layer asserts the gate STILL sends it. That is deliberate: a gap that
is only printed can close or widen unnoticed; one asserted as it is today turns red
the day it changes, and the failure message says to update ADR-0015 and the row.
Only the runtime half is asserted (the offline judge was not measured on it).

A KNOWN LIMITATION of the issue-#104 clause
-------------------------------------------
The clause is stated UNCONDITIONALLY: a reply that only reports the answer is
quoted case-by-case / at someone's discretion / decided by staff / unpublished
"does NOT answer the question". It never conditions on WHAT was asked. That is
right for the two E7 rows it was built from, which both ask for a value the
corpus defers. It is wrong for a question whose correct answer genuinely IS the
policy or the disposition — "Who decides a book warranty claim after 30 days?"
is fully answered by "customer service, at their discretion", yet the clause,
read literally, calls that draft a deferral, and both judges escalated it when
the clause was written.

The `_CASES` row labelled "FORMER KNOWN LIMITATION: the disposition IS the
requested information" pins that shape. It was pinned at escalate (answers=False)
when the clause was written, measured 5/5 stable then. A live run on 2026-10-15
found BOTH judges answering it (3/3 each, and the pre-fix offline judge too), with
neither rubric nor `backend/escalation.py` changed since: the models moved under
the pin. That is the outcome invariant 8's own test calls correct (the customer
asked WHO decides and the draft says who), so the row now expects it. The clause
is still unconditional on paper, so this is observed behaviour, not a guarantee:
re-check the row whenever either judge model or rubric changes.

LIVE CALLS vs RECORDED FIXTURES — the deliberate choice
-------------------------------------------------------
This file makes LIVE model calls in its integration layer, and records nothing.

Recorded fixtures were considered and rejected for the discrimination cases. A
recorded judge response is a canned verdict replayed from disk, which is exactly
what the `_FakeJudge` already does: it would re-pin the plumbing under a new name
while still never exercising the rubric. A fixture can only tell you that the
model said X on the day you recorded it, so the one failure mode this layer exists
to catch — a rubric edit that changes what the model concludes — is precisely the
one it would be blind to.

What that costs, stated plainly:
  * money and latency: `len(_CASES) * _REPS` calls per implementation, on the two
    cheap judge models, so a full run with both keys set is
    `len(_CASES) * _REPS * 2`. Read it off the table rather than trusting a
    hand-count here - `_cost_note()` prints the current number at run time, and a
    row added to `_CASES` moves it without this paragraph needing an edit;
  * a dependency on network + API keys, so it CANNOT be part of the always-run
    unit layer;
  * mild non-determinism. Mitigated, not hand-waved: both judges are now pinned
    to temperature 0 (issue #104's other half) - the live layer neutralizes the
    ambient `JUDGE_MODEL` / `JUDGE_TEMPERATURE` exactly as the unit layer does, so
    a developer shell cannot un-pin the run the failure message describes as
    pinned - each case is asserted UNANIMOUS over `_REPS` calls. The hand-written
    rows were measured stable at 5/5 when they were added, except the FORMER
    KNOWN LIMITATION row, whose current expectation was measured 3/3 on
    2026-10-15. Of the real-context rows, the runtime gate rejected `e7-p3-01`,
    `e7-p3-05-disclaimer` and `e7-p3-09` 5/5 on 2026-10-15; the bare-draft
    `e7-p3-05` row was taken from the 2026-10-11 snapshot without a live run, so
    its first live run is its measurement. Every row is now asserted on every
    implementation it runs on: the exemption that used to cover the RUNTIME half of
    the real-context `e7-p3-10` row was removed in the change that made the gate
    extract the asked and stated value (ADR-0015), as its own text required. The
    offline half of this layer has not been run on that change: the Claude judge's
    `same_kind` was measured only on the measured trade's should-answer rows (20 of
    20 answered, ADR-0015), so the first hand run with both keys is this layer's
    first offline measurement. The pin removes the
    SAMPLER, which is best-effort rather than a guarantee — no `seed` is passed —
    so a split can still come from the provider rather than from the rubric. It
    fails the test either way, because both causes need looking at and neither
    should be retried away.

The offline half stays fixture-free in a different sense: recording fake clients
invoke both judge entry points and assert that the final emitted prompts and tool
schemas carry the same rules. That needs no model at all, so it runs in the
always-on layer and catches both rubric drift and an unwired prompt literal.

Layers (the project convention — see CLAUDE.md "How to test"):
  * unit layer, ALWAYS runs, no network/keys/DB: rubric lockstep + rule presence,
    the offline verdict's stated-value rule, malformed-payload raise and tool
    field order, executable structured judge-failure behavior, plus the boot
    warning's call-site wiring in `main.py`.
  * integration layer, SKIPS CLEANLY without keys: live discrimination on both
    implementations.

Run:
    python -m backend.test_answer_gate_rubric
"""

from __future__ import annotations

import ast
import asyncio
import contextlib
import json
import os
import re
import sys
import types
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from escalation import (  # noqa: E402
    _non_answer,
    AnswerJudgment,
    DEFAULT_ANSWER_CUTOFF,
    answer_gate,
    get_judge_model,
    get_judge_temperature,
)
from evals.retrieval.runner import judge_answering  # noqa: E402

# How many times each live case is judged. Every case must come back UNANIMOUS.
_REPS = 3

# The app's own source, read the same way again for the boot-warning CALL-SITE
# check below. Read, never imported: `main` pulls the ML stack and the whole
# service surface, neither of which this offline guard job installs.
_MAIN_SRC = ROOT / "backend" / "main.py"

# The env var that decides whether the support-widget surface exists at all
# (AGENTS.md invariant 10), and therefore whether the two runtime gates can ever
# run. The boot warning must be wired to it.
_WIDGET_SURFACE_ENV = "SUPABASE_SERVICE_ROLE_KEY"


def _check(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _calls_to(path: Path, func_name: str) -> list[ast.Call]:
    """Every `func_name(...)` call node in `path`'s source.

    Matches a BARE-NAME call, which is how both call sites checked below are
    written (each module imports the callee by name). A qualified call
    (`escalation.func(...)`) is deliberately not matched — that errs toward the
    safe direction, because each caller below asserts on the calls it finds and
    fails loudly when it finds none, rather than passing on an empty set.
    """
    calls: list[ast.Call] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == func_name:
                calls.append(node)
    return calls


def _names_in(node: ast.AST) -> set[str]:
    """Every identifier and string literal appearing anywhere under `node`.

    Used to ask whether an argument expression MENTIONS a given name. It reads
    textual reference only: it says nothing about what the expression computes,
    so a caller must not read a hit as the expression being correct.
    """
    found: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            found.add(child.id)
        elif isinstance(child, ast.Attribute):
            found.add(child.attr)
        elif isinstance(child, ast.Constant) and isinstance(child.value, str):
            found.add(child.value)
    return found


# The rules BOTH implementations must state. Phrased as the substrings they share,
# so the check survives the small wording differences between the two prompts
# while still failing loudly if one of them loses a rule the other keeps.
_SHARED_RULES = {
    "non-answer verdict": "does NOT answer the question",
    "admits it lacks the information": "have the information",
    "cannot help": "cannot help",
    "defers to a human": "the customer to a human",
    "answers a different question": "DIFFERENT question",
    "judges answering only, not grounding": "not grounding, tone, or politeness",
    # --- the issue-#104 addition ---
    "corpus's answer is 'quoted case-by-case'": "quoted case-by-case",
    "corpus's answer is 'someone's discretion'": "someone's discretion",
    "corpus's answer is unpublished": "otherwise not published",
    "accuracy of the deferral is irrelevant": (
        "however accurately or confidently the reply states that policy"
    ),
    "an adjacent fact is not the asked value": (
        "a fact ADJACENT to the question rather than the value asked for"
    ),
    "an absent context value cannot be supplied by restatement": (
        "when the value asked for is absent from the RETRIEVED CONTEXT"
    ),
    "context restatement cannot invent the absent value": (
        "merely restates what the CONTEXT does contain can be that value"
    ),
    # --- the ADR-0015 addition ---
    "commits asked and stated value before deciding": "commit to two fields",
    "no stated value means no answer": (
        "`stated_value` is null and the ANSWER does not answer the QUESTION"
    ),
    "the stated value must be the same kind": "the SAME KIND of thing",
    "a range or estimate is not an exact amount": (
        "a range, an estimate, 'varies', or a fact about who pays"
    ),
}

_PROMPT_QUESTION = "How much is international return shipping?"
_PROMPT_CONTEXT = "International returns are at the customer's expense."
_PROMPT_DRAFT = "The customer pays for international return shipping."


class _RecordingRuntimeCompletions:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def parse(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        message = types.SimpleNamespace(
            parsed=AnswerJudgment(
                asked_value="the fee amount",
                stated_value="the customer pays",
                same_kind=True,
                answers=True,
                score=1.0,
            ),
            refusal=None,
        )
        return types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=message)]
        )


class _RecordingAnthropicMessages:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        block = types.SimpleNamespace(
            type="tool_use",
            name="submit_answering",
            input={
                "asked_value": "the fee amount",
                "stated_value": "the customer pays",
                "same_kind": True,
                "answers": True,
            },
        )
        return types.SimpleNamespace(content=[block])


def _capture_runtime_call() -> dict[str, Any]:
    completions = _RecordingRuntimeCompletions()
    client = types.SimpleNamespace(
        chat=types.SimpleNamespace(completions=completions)
    )
    decision = asyncio.run(
        answer_gate(
            client,
            _PROMPT_QUESTION,
            _PROMPT_DRAFT,
            DEFAULT_ANSWER_CUTOFF,
            context=_PROMPT_CONTEXT,
        )
    )
    _check(decision.answers, f"recording runtime judge did not pass: {decision!r}")
    _check(len(completions.calls) == 1, "runtime rubric capture must make one call")
    return completions.calls[0]


def _capture_offline_call() -> dict[str, Any]:
    messages = _RecordingAnthropicMessages()
    client = types.SimpleNamespace(messages=messages)
    verdict = asyncio.run(
        judge_answering(
            client,
            _PROMPT_QUESTION,
            _PROMPT_CONTEXT,
            _PROMPT_DRAFT,
        )
    )
    _check(verdict is True, f"recording offline judge returned {verdict!r}")
    _check(len(messages.calls) == 1, "offline rubric capture must make one call")
    return messages.calls[0]


# --- unit layer (always runs) ---------------------------------------------


def test_both_rubrics_state_every_shared_rule() -> None:
    """The runtime gate and its offline E7 mirror must state the SAME rules.

    They are two separate strings in two packages, kept in step by hand (the
    cross-family independence is deliberate; see the block comment above
    `ANSWER_JUDGE_PROMPT_TEMPLATE`). Drift between them silently turns the weekly
    E7 false-resolve number into a measurement of something the buyer does not
    ship, which is how the two were found disagreeing on 5 of 17 probes.
    """
    runtime_call = _capture_runtime_call()
    offline_call = _capture_offline_call()
    runtime = "\n".join(message["content"] for message in runtime_call["messages"])
    offline = "\n".join(message["content"] for message in offline_call["messages"])
    for label, value in (
        ("question", _PROMPT_QUESTION),
        ("context", _PROMPT_CONTEXT),
        ("draft", _PROMPT_DRAFT),
    ):
        _check(value in runtime, f"runtime emitted prompt lost the {label}")
        _check(value in offline, f"offline emitted prompt lost the {label}")
    for label, fragment in _SHARED_RULES.items():
        _check(
            fragment in runtime,
            f"the RUNTIME rubric (escalation._ANSWER_JUDGE_SYSTEM_PROMPT) no longer "
            f"states the rule {label!r} (missing {fragment!r})",
        )
        _check(
            fragment in offline,
            f"the OFFLINE mirror (runner.ANSWER_JUDGE_PROMPT_TEMPLATE) no longer "
            f"states the rule {label!r} (missing {fragment!r}) — the two rubrics "
            "have drifted apart",
        )
    print(f"ok: both rubrics state all {len(_SHARED_RULES)} shared rules")


def test_both_tool_schemas_describe_the_disposition_case() -> None:
    """The structured-output description the model reads must agree with the
    rubric, in both implementations — a schema that still says a deferral counts
    as an answer would pull against the prompt."""
    runtime_call = _capture_runtime_call()
    offline_call = _capture_offline_call()
    runtime_schema = runtime_call["response_format"]
    offline_tool = offline_call["tools"][0]
    _check(
        offline_call["tool_choice"] == {"type": "tool", "name": "submit_answering"},
        f"offline judge must force submit_answering, got {offline_call['tool_choice']!r}",
    )
    for what, description in (
        (
            "runtime AnswerJudgment.answers",
            runtime_schema.model_fields["answers"].description or "",
        ),
        (
            "offline submit_answering.answers",
            offline_tool["input_schema"]["properties"]["answers"]["description"],
        ),
    ):
        for fragment in (
            "case-by-case",
            "discretionary",
            "unpublished",
            "fact adjacent to the question rather than the value asked for",
            "RETRIEVED CONTEXT that does not contain the requested value",
        ):
            _check(
                fragment in description,
                f"{what} must describe the issue-#104 disposition case "
                f"(missing {fragment!r}): {description!r}",
            )
    print("ok: both tool schemas describe the disposition case")


# The two halves of the ADR-0015 kind condition, as the rule states them.
_KIND_PAIRS = "(an amount for an amount, a duration for a duration, a yes/no for a yes/no)"
_NOT_AN_EXACT_AMOUNT = (
    "a range, an estimate, 'varies', or a fact about who pays, when, or where"
)


def _sentence_stating(text: str, fragment: str) -> str:
    sentences = [s for s in re.split(r"(?<=[.?!])\s+", text) if fragment in s]
    _check(
        len(sentences) == 1,
        f"want exactly one sentence stating {fragment!r}, got {sentences!r}",
    )
    return sentences[0]


def test_same_kind_field_and_kind_rule_state_the_same_condition() -> None:
    """The `same_kind` field description and the kind rule state ONE condition.

    The judge reads both in the same call: the rule in the prompt, the description
    in the schema it fills. The condition is that the stated value is the same kind
    as the one asked, and only where an EXACT AMOUNT is asked must it also be a
    specific amount rather than a range, an estimate, 'varies', or a fact about who
    pays, when, or where. A description that drops the exact-amount scope tells the
    judge that a who-pays answer is never the same kind, so a faithful "the customer
    pays" for "who pays?" escalates and latches the conversation. Checked on the
    emitted prompt and schema of both implementations, so a reworded literal on
    either side fails here.
    """
    runtime_call = _capture_runtime_call()
    offline_call = _capture_offline_call()
    texts = (
        (
            "runtime kind rule (emitted system prompt)",
            "\n".join(message["content"] for message in runtime_call["messages"]),
        ),
        (
            "runtime AnswerJudgment.same_kind (emitted schema)",
            runtime_call["response_format"].model_json_schema()["properties"][
                "same_kind"
            ]["description"],
        ),
        (
            "offline kind rule (emitted prompt)",
            "\n".join(message["content"] for message in offline_call["messages"]),
        ),
        (
            "offline submit_answering.same_kind (emitted tool schema)",
            offline_call["tools"][0]["input_schema"]["properties"]["same_kind"][
                "description"
            ],
        ),
    )
    for what, text in texts:
        _check(
            _KIND_PAIRS in text,
            f"{what} must state the same-kind pairs {_KIND_PAIRS!r}: {text!r}",
        )
        exclusion = _sentence_stating(text, _NOT_AN_EXACT_AMOUNT)
        _check(
            "exact amount" in exclusion,
            f"{what} states the range/who-pays exclusion without scoping it to an "
            f"exact amount, which is not the condition the kind rule states: "
            f"{exclusion!r}",
        )
    print("ok: the same_kind field and the kind rule state the same condition on both sides")


class _ScriptedAnthropicMessages:
    """Returns one scripted `submit_answering` payload, whatever it is asked."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    async def create(self, **kwargs: Any) -> Any:
        block = types.SimpleNamespace(
            type="tool_use", name="submit_answering", input=self.payload
        )
        return types.SimpleNamespace(content=[block])


def _offline_verdict(payload: dict[str, Any]) -> bool:
    client = types.SimpleNamespace(messages=_ScriptedAnthropicMessages(payload))
    return asyncio.run(
        judge_answering(client, _PROMPT_QUESTION, _PROMPT_CONTEXT, _PROMPT_DRAFT)
    )


def test_offline_verdict_requires_a_stated_value() -> None:
    """The offline verdict is `answers AND the judge named the value it gave AND the
    value is of the asked kind`.

    This is the 2026-09-20 .. 2026-10-11 weekly breach, pinned WITHOUT a model: a
    bare-boolean judge shown the retrieved context graded the draft's truth instead
    of whether it answers, and returned `answers=true` for an accurate "I don't have
    that information". The judge must now commit to `stated_value` first, and a
    verdict of "answers" with no stated value is self-contradictory, so it resolves
    toward ESCALATION. `same_kind` (ADR-0015) is the runtime gate's own extra field,
    mirrored here so the weekly measures the verdict the buyer ships. Every cell is a
    verdict the weekly P3 leg turns into a false-resolve if it comes back True.
    """
    asked = "the return shipping fee for a return over 20 lbs"

    def payload(stated: Any, answers: bool = True, same_kind: bool = True) -> dict[str, Any]:
        return {
            "asked_value": asked,
            "stated_value": stated,
            "same_kind": same_kind,
            "answers": answers,
        }

    cases = [
        # (payload, expected verdict, why)
        (payload("$14.95"), True, "a real value was stated and the judge says it answers"),
        (
            payload(None),
            False,
            "THE BREACH: the judge said it answers but named no value the customer holds",
        ),
        (payload(""), False, "an empty stated value is no value"),
        (payload("   "), False, "a whitespace-only stated value is no value"),
        (payload("null"), False, "the word null instead of JSON null is no value"),
        (payload(" NULL "), False, "the word null, padded, in any case, is no value"),
        (payload("$14.95", answers=False), False, "a stated value never overrides an explicit non-answer verdict"),
        (payload(None, answers=False), False, "a plain deferral stays a non-answer"),
        (
            payload("customer's expense", same_kind=False),
            False,
            "ADR-0015: a value of the wrong kind (who pays, for a fee amount) is no answer",
        ),
        (
            payload("10% to 80%", same_kind=False),
            False,
            "ADR-0015: a range is not an exact amount",
        ),
        (
            payload("$14.95", answers=False, same_kind=False),
            False,
            "every flag against the draft stays a non-answer",
        ),
    ]
    for p, expected, why in cases:
        got = _offline_verdict(p)
        _check(
            got is expected,
            f"offline verdict for {p!r} was {got!r}, want {expected!r} - {why}",
        )
    print(f"ok: the offline verdict requires a stated value of the asked kind ({len(cases)} cells)")


def test_offline_judge_raises_on_a_malformed_payload() -> None:
    """A payload with no boolean `answers`, no string-or-null `stated_value` or no
    boolean `same_kind` is no verdict at all, so it RAISES. `asked_value` is not
    validated.

    Scoring it False would read as the answer leg correctly escalating a P3 row,
    and if the runtime gate also said False the parity leg would record agreement:
    a malformed judge reply published as a passing measurement on the pinned
    safety metric (invariant 12). Raising kills the run, which the weekly reports
    as UNMEASURED. A null or blank `stated_value` is NOT malformed - it is the
    judge's legitimate "no value" and stays a False verdict above.
    """
    asked = "the return shipping fee for a return over 20 lbs"
    cases = [
        (
            {"asked_value": asked, "answers": True},
            "the payload omits stated_value",
        ),
        (
            {"asked_value": asked, "stated_value": 14.95, "answers": True},
            "stated_value is neither a string nor null",
        ),
        (
            {"asked_value": asked, "stated_value": "$14.95"},
            "the payload omits answers",
        ),
        (
            {"asked_value": asked, "stated_value": "$14.95", "answers": "false"},
            "answers is not a boolean (bool('false') would read as True)",
        ),
        (
            {"asked_value": asked, "stated_value": "$14.95", "answers": True},
            "the payload omits same_kind (ADR-0015)",
        ),
        (
            {
                "asked_value": asked,
                "stated_value": "$14.95",
                "same_kind": "true",
                "answers": True,
            },
            "same_kind is not a boolean (a truthy string would pass it)",
        ),
        (
            {
                "asked_value": asked,
                "stated_value": "$14.95",
                "same_kind": None,
                "answers": True,
            },
            "same_kind is null (null is not 'the same kind')",
        ),
    ]
    for payload, why in cases:
        try:
            got = _offline_verdict(payload)
        except RuntimeError:
            continue
        raise AssertionError(
            f"offline judge returned {got!r} for {payload!r} instead of raising - "
            f"{why}, so the reply broke the tool schema and must fail the run"
        )
    print(f"ok: the offline judge raises on a malformed payload ({len(cases)} cells)")


def test_offline_tool_schema_commits_the_values_before_the_verdict() -> None:
    """The extraction fields exist, are required, and come BEFORE `answers`.

    The model fills a tool payload in property order, so `asked_value` and
    `stated_value` being committed first is the mechanism, not decoration; moving
    `answers` up (or dropping a field from `required`) silently reverts the judge
    to the bare boolean that read an accurate deferral as an answer.
    """
    schema = _capture_offline_call()["tools"][0]["input_schema"]
    order = list(schema["properties"])
    _check(
        order == ["asked_value", "stated_value", "same_kind", "answers"],
        f"offline tool properties must be ordered asked_value, stated_value, "
        f"same_kind, answers (verdict LAST), got {order!r}",
    )
    _check(
        set(schema["required"])
        == {"asked_value", "stated_value", "same_kind", "answers"},
        f"offline tool must REQUIRE all three fields, got {schema['required']!r}",
    )
    stated = schema["properties"]["stated_value"]
    _check(
        stated["type"] == ["string", "null"],
        f"stated_value must be nullable (null is how the judge says 'none'), "
        f"got {stated['type']!r}",
    )
    for fragment in (
        "unavailable",
        "not provided",
        "quoted per case",
        "someone's discretion",
        "adjacent fact",
    ):
        _check(
            fragment in stated["description"],
            f"stated_value must say when to return null (missing {fragment!r}): "
            f"{stated['description']!r}",
        )
    print("ok: the offline tool commits asked_value, stated_value and same_kind before the verdict")


def test_runtime_and_offline_commit_the_same_fields_in_the_same_order() -> None:
    """Invariant 8, structurally: the runtime `AnswerJudgment` and the offline
    `submit_answering` tool must ask the judge for the SAME extraction fields in the
    SAME order, with the verdict after them. The runtime adds only `score` (its
    cutoff input), which the offline verdict does not use.

    Prompt wording is checked by `test_both_rubrics_state_every_shared_rule`; this
    is the schema half, so a field added to one side and not the other fails here
    instead of turning the weekly into a measurement of a different verdict.
    """
    runtime = [f for f in AnswerJudgment.model_fields if f != "score"]
    offline = list(_capture_offline_call()["tools"][0]["input_schema"]["properties"])
    _check(
        runtime == offline,
        f"runtime fields {runtime!r} and offline fields {offline!r} must match "
        "one to one, verdict last",
    )
    print(f"ok: runtime and offline judges commit the same {len(runtime)} fields in the same order")


def test_non_answer_failures_are_structured_independently_of_reason() -> None:
    """Every diagnostic tag yields the same executable fail-closed signal."""
    for tag in (
        "judge_error",
        "judge_no_choices",
        "judge_refusal",
        "judge_no_payload",
        "future_failure_tag",
    ):
        decision = _non_answer(tag)
        _check(
            decision.answers is False
            and decision.addressed is False
            and decision.judge_failed is True,
            f"{tag}: must be a structured fail-closed judge failure, got {decision!r}",
        )
        _check(
            decision.reason == f"non_answer: {tag}",
            f"{tag}: diagnostic reason changed unexpectedly to {decision.reason!r}",
        )
    print("ok: answer judge failures use the structured signal for every reason")


def test_boot_warning_call_site_is_wired_to_the_widget_surface() -> None:
    """`main.py` must CALL the boot warning, passing an argument that mentions
    `SUPABASE_SERVICE_ROLE_KEY`.

    WHAT THIS PROVES, exactly: a source-level structural property of the call
    site — the call exists in `backend/main.py`, and the value it passes is
    derived from the widget-surface env var rather than hard-coded or dropped.
    That is the regression it is here for: `warn_if_judge_rejects_temperature`'s
    scoping to the support surface (AGENTS.md invariant 10) lives entirely in
    `main.py`, where an edit that hoists the call out of that predicate, passes a
    constant, or deletes the call altogether otherwise leaves the whole suite
    green.

    WHAT IT DOES NOT PROVE — do not read it as more than the above:
      * NOT that the warning is correctly scoped at RUNTIME. It never boots the
        app, never imports `main`, and observes no log record.
      * NOT that `SUPABASE_SERVICE_ROLE_KEY` is the RIGHT condition. It only
        checks that the argument mentions that name.
      * NOT that the predicate has the right SENSE. `support_configured=not
        SUPABASE_SERVICE_ROLE_KEY` — the exact inversion of the intended
        scoping — satisfies this check.
    `test_boot_warning_for_known_temperature_refusing_models` in
    `backend/test_faithfulness_gate.py` covers the other half: what the function
    DOES given each value of that parameter. Together they cover wiring plus
    behaviour; neither, alone or together, is an end-to-end runtime check.

    SOURCE, not runtime, deliberately. The call site only executes inside
    FastAPI's startup hook, and every test module that imports `main` does so
    behind a skip-on-failure guard (missing Supabase env, or the ML import stack
    the offline guard job does not install), so a runtime version of this check
    would go quiet in exactly the CI job that is supposed to enforce it. A guard
    that can silently skip is how this project published zero recall for 42
    nights; keep this one unconditional rather than "upgrading" it to a skipping
    integration test.
    """
    calls = _calls_to(_MAIN_SRC, "warn_if_judge_rejects_temperature")
    _check(
        bool(calls),
        f"{_MAIN_SRC.name} must call warn_if_judge_rejects_temperature at boot - "
        "issue #104's judge pin is a new request parameter, and the warning is the "
        "only thing that tells a mid-upgrade operator about it",
    )
    for call in calls:
        args = [kw.value for kw in call.keywords if kw.arg] + list(call.args)
        _check(
            bool(args),
            f"{_MAIN_SRC.name}:{call.lineno}: warn_if_judge_rejects_temperature "
            "must be passed the widget-surface predicate, not called bare",
        )
        mentioned = set().union(*(_names_in(a) for a in args))
        _check(
            _WIDGET_SURFACE_ENV in mentioned,
            f"{_MAIN_SRC.name}:{call.lineno}: the argument to "
            f"warn_if_judge_rejects_temperature must derive from "
            f"{_WIDGET_SURFACE_ENV} (got {sorted(mentioned)}). The gates run only "
            "on the support path, so per AGENTS.md invariant 10 a "
            "knowledge-assistant-only deploy must never see this warning - it "
            "would describe conversations latching in a deploy that has none.",
        )
    print(f"ok: the boot warning is called in {_MAIN_SRC.name}, wired to the widget surface")


# --- integration layer (skips cleanly without keys) ------------------------

# question, draft, context, must_answer, why. The drafts are the ones actually
# observed in the 2026-08-03 sweep and its local re-runs, not invented
# paraphrases. `context` is the RETRIEVED CONTEXT the draft would have been
# written from (the corpus text a grounded drafter sees) — the adjacent-fact
# residual (issue #104) only discriminates when the judge can see that the asked
# value is absent from it, so each row carries the corpus slice its draft
# restates.
_CASES: list[tuple[str, str, str, str, bool, str]] = [
    (
        "p3-05 quoted-per-case",
        "What is the return shipping fee for a return over 20 lbs?",
        "The return shipping fee for returns over 20 lbs is quoted on a per-case basis.",
        "US domestic returns use USPS or UPS Ground depending on package weight. "
        "The deduction is $7.95 for standard returns under 5 lbs; $14.95 for returns "
        "5-20 lbs; quoted per-case for returns over 20 lbs.",
        False,
        "the corpus's own answer is a deferral; the customer still has no fee",
    ),
    (
        "p3-05 quoted-per-case, verbose",
        "What is the return shipping fee for a return over 20 lbs?",
        "The return shipping fee for returns over 20 lbs is quoted per-case, meaning "
        "the specific amount is not fixed and will vary based on the situation.",
        "The deduction is $7.95 for standard returns under 5 lbs; $14.95 for returns "
        "5-20 lbs; quoted per-case for returns over 20 lbs.",
        False,
        "same shape, restated at length; length must not buy a pass",
    ),
    (
        "p3-11 at-someone's-discretion",
        "What is the warranty period for a book with a printing defect after 30 days?",
        "Books carry a 30-day warranty against printing defects (missing pages, "
        "blurred ink, binding failure). Beyond 30 days, book warranty claims are at "
        "the discretion of customer service. Therefore, the warranty period for a "
        "book with a printing defect after 30 days is not specified and is subject "
        "to customer service judgment.",
        "Books carry a 30-day warranty against printing defects (missing pages, "
        "blurred ink, binding failure). Beyond 30 days, book warranty claims are at "
        "the discretion of customer service.",
        False,
        "the second flavour: the document names a human decision-maker",
    ),
    (
        "p3-11 at-someone's-discretion, NO self-disclaimer",
        "What is the warranty period for a book with a printing defect after 30 days?",
        "Books carry a 30-day warranty against printing defects. Beyond 30 days, "
        "book warranty claims are at the discretion of customer service.",
        "Books carry a 30-day warranty against printing defects (missing pages, "
        "blurred ink, binding failure). Beyond 30 days, book warranty claims are at "
        "the discretion of customer service.",
        False,
        "THE REGRESSION GUARD: identical substance, no volunteered disclaimer. If "
        "this one passes, the gate is back to keying on the drafter's phrasing",
    ),
    (
        "p3-10 adjacent fact: who pays is not the fee amount",
        "What is the return shipping fee for an international return?",
        "International returns are at the customer's expense.",
        "The RMA includes a pre-paid shipping label for US domestic returns; "
        "international returns are at the customer's expense unless the return is "
        "for a wrong-item-shipped or damaged-in-transit case. The domestic "
        "deduction is $7.95 under 5 lbs and $14.95 for 5-20 lbs.",
        False,
        "the draft faithfully states who pays, but the customer asked how much",
    ),
    (
        "p3-04 adjacent fact: general warranty is not refurbished warranty",
        "How long is the warranty on a refurbished electronics item?",
        "Electronics carry a 12-month limited warranty against manufacturing defects.",
        "Electronics carry a 12-month limited warranty against manufacturing defects. "
        "Coverage excludes physical damage and unauthorized modifications; the "
        "document does not mention refurbished items.",
        False,
        "the general electronics period is adjacent to, not an answer for, the "
        "missing refurbished-item condition",
    ),
    (
        "announced ignorance (the original issue-#97 shape)",
        "What is the warranty period for jewelry?",
        "I don't have that information.",
        "Electronics carry a 12-month limited warranty against manufacturing "
        "defects. The warranty starts on the order's shipped_at date.",
        False,
        "the shape the gate was built for; must stay caught",
    ),
    (
        "answerable: a published fee",
        "What is the return shipping fee for an item between 5 and 20 pounds that I "
        "changed my mind about?",
        "The return shipping fee for an item between 5 and 20 pounds that you "
        "changed your mind about is $14.95.",
        "The deduction is $7.95 for standard returns under 5 lbs; $14.95 for returns "
        "5-20 lbs; quoted per-case for returns over 20 lbs.",
        True,
        "OPPOSITE DIRECTION: a real published figure must still auto-resolve, so "
        "an over-tightened rubric fails here instead of quietly killing deflection",
    ),
    (
        "answerable: a published warranty period",
        "How long is the electronics warranty?",
        "The electronics warranty is 12 months against manufacturing defects, "
        "starting on the order's shipped_at date.",
        "Electronics carry a 12-month limited warranty against manufacturing "
        "defects. The warranty starts on the order's shipped_at date, not the "
        "paid_at date.",
        True,
        "opposite direction, second instance",
    ),
    (
        "answerable: a published window",
        "Within how many days of the shipped_at date can I request a refund?",
        "You may request a refund within 30 days of the order's shipped_at date.",
        "Customers may request a refund within 30 days of the order's shipped_at "
        "date. Orders that have not shipped follow the cancellation policy instead.",
        True,
        "opposite direction, third instance",
    ),
    # FORMER KNOWN LIMITATION, now pinned at the OBSERVED (and desired) behaviour.
    #
    # Here the disposition IS the requested information: the customer asked WHO
    # decides, and the draft tells them who. By invariant 8's own test - does the
    # customer end up holding what they asked for - this should auto-send. It was
    # pinned at escalate because the issue-#104 clause is stated unconditionally and
    # the judges then read it as a deferral. On 2026-10-15 both judges answered it
    # 3/3 (and the pre-fix offline judge did too), with no rubric or backend change,
    # so the pin was stale and the live layer was red on a shape that is correct.
    #
    # It is still here so a future rubric or model change that flips this shape says
    # so out loud instead of moving live send/escalate behaviour unobserved. The
    # clause remains unconditional, so treat True as observed, not guaranteed.
    (
        "FORMER KNOWN LIMITATION: the disposition IS the requested information",
        "Who decides a book warranty claim after 30 days?",
        "Beyond 30 days, book warranty claims are decided by customer service, at "
        "their discretion.",
        "Books carry a 30-day warranty against printing defects (missing pages, "
        "blurred ink, binding failure). Beyond 30 days, book warranty claims are at "
        "the discretion of customer service.",
        True,
        "the customer asked WHO decides and the draft says who, so invariant 8's "
        "test says auto-send. Both judges answered it 3/3 on 2026-10-15; if this "
        "row starts failing, a judge model or rubric moved and the issue-#104 "
        "clause is reading it as a deferral again - see the module docstring",
    ),
]


# The four questions where the weekly parity leg saw the two judges disagree, plus
# one drafter variant. They carry the REAL retrieved context (8-10 KB, every
# warranty category / the whole returns section / the whole tier list) verbatim:
# the hand-written slices above are short enough that a judge never saw a context
# it could mistake for ground truth, which is why this layer passed through PR #156
# and the failure surfaced only in the next weekly. e7-p3-01, e7-p3-05 and
# e7-p3-09 are the OFFLINE judge's misses (auto-resolved in the 2026-09-20 ..
# 2026-10-11 weeklies while the runtime gate rejected them). e7-p3-05 carries the
# no-disclaimer draft that breached, copied from the 2026-10-11 snapshot;
# e7-p3-05-disclaimer is the same question and context with the draft an
# unmodified-main run produced on 2026-10-15, which adds that the amount is not
# provided. e7-p3-10 is the RUNTIME gate's miss on 2026-09-20, copied from that
# snapshot: who pays, not how much. All five must NOT answer.
_REAL_CONTEXT_FIXTURE = (
    ROOT / "backend" / "test-fixtures" / "e7_offline_answer_judge_rows.json"
)
_REAL_CONTEXT_WHY = {
    "e7-p3-01": "an accurate 'I don't have that information' is still a non-answer; "
    "the real warranty context lists every category but jewelry",
    "e7-p3-05": "the corpus's own answer is a deferral ('quoted per-case'); "
    "reporting it accurately leaves the customer with no fee. THE REGRESSION "
    "GUARD: this is the draft that breached, with no volunteered disclaimer; if "
    "it passes while e7-p3-05-disclaimer escalates, the judge is keying on the "
    "drafter's phrasing",
    "e7-p3-05-disclaimer": "the same deferral with the drafter's 'not provided "
    "in the context' disclaimer added; still no fee for the customer",
    "e7-p3-09": "an accurate 'I don't have that information' is still a non-answer; "
    "the real context lists four tiers and no Diamond",
    "e7-p3-10": "the draft faithfully states who pays, but the customer asked how "
    "much, and the real returns context publishes no international fee",
}


def _real_context_label(row_id: str) -> str:
    return f"{row_id} REAL retrieved context"


def _real_context_cases() -> list[tuple[str, str, str, str, bool, str]]:
    _check(
        _REAL_CONTEXT_FIXTURE.is_file(),
        f"missing fixture {_REAL_CONTEXT_FIXTURE}: the live layer's real-context "
        "rows (the issue-#163 parity mismatches) are read from it",
    )
    rows = json.loads(_REAL_CONTEXT_FIXTURE.read_text(encoding="utf-8"))["rows"]
    ids = [row["id"] for row in rows]
    _check(
        sorted(ids) == sorted(_REAL_CONTEXT_WHY),
        f"{_REAL_CONTEXT_FIXTURE.name} rows {ids} must match _REAL_CONTEXT_WHY "
        f"{sorted(_REAL_CONTEXT_WHY)} one to one: every fixture row needs its label "
        "and every labelled row must still be in the fixture",
    )
    return [
        (
            _real_context_label(row["id"]),
            row["question"],
            row["draft"],
            row["context"],
            False,
            _REAL_CONTEXT_WHY[row["id"]],
        )
        for row in rows
    ]


_CASES.extend(_real_context_cases())


def _cost_note(n_impls: int) -> str:
    """The live layer's call count, DERIVED from the table rather than restated.

    The module docstring argues that the live-call cost is a deliberate, quantified
    tradeoff, so the quantity has to track `_CASES` instead of drifting away from a
    hand-count the next row invalidates.
    """
    return (
        f"{len(_CASES)} cases x {_REPS} reps x {n_impls} implementation(s) = "
        f"{len(_CASES) * _REPS * n_impls} live judge calls"
    )


class _Skipped(Exception):
    """A test group that MEASURED NOTHING, raised so `main` can see it.

    Invariant 12 applies to this module's own summary line: a skipped live layer
    must not be reportable as a passing group. A printed `SKIP` line is not enough
    - `main` would have to parse stdout to notice - so the skip is structural.
    """


def _skip(reason: str) -> None:
    print(f"SKIP (live rubric layer): {reason}")
    raise _Skipped(reason)


# --- shared live-layer plumbing ---------------------------------------------

Judge = Callable[[str, str, str], Awaitable[tuple[bool, bool]]]


@contextlib.contextmanager
def _neutral_judge_env() -> Iterator[None]:
    """Neutralize the ambient judge environment for the duration of a live run.

    The runtime half calls the real `answer_gate`, which resolves its knobs from the
    ambient environment - and the developer most likely to run this file is the one
    debugging the pin, whose shell may well export `JUDGE_TEMPERATURE=none` (the
    documented escape hatch), a bring-your-own `JUDGE_MODEL` the plain OpenAI client
    built below cannot serve, or the ADR-0013 `JUDGE_REASONING_EFFORT` that a
    non-reasoning model 400s on. Any of them silently changes the run whose
    unanimity assertion and SPLIT message both state "gpt-4o-mini at temperature 0",
    so a run whose stated mitigation was never in effect would be reportable as a
    clean measurement - invariant 12, in the module that argues it hardest. This bug
    class was fixed once already in the unit-layer gate tests and came back here
    because the fix was applied only where the finding pointed.
    """
    names = ("JUDGE_MODEL", "JUDGE_TEMPERATURE", "JUDGE_REASONING_EFFORT")
    saved = {k: os.environ.get(k) for k in names}
    for key in names:
        os.environ.pop(key, None)
    try:
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _live_impls() -> list[tuple[str, Judge]]:
    """The judge implementations a live run can exercise with the keys at hand."""
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    impls: list[tuple[str, Judge]] = []
    if openai_key:
        from openai import AsyncOpenAI

        oc = AsyncOpenAI(api_key=openai_key)

        async def runtime(question: str, context: str, draft: str) -> tuple[bool, bool]:
            # `answer_gate` fails CLOSED, so an expired key, a rate limit, a
            # timeout or a network blip all return answers=False - the same value a
            # correct non-answer verdict returns. Reading only `.answers` would
            # print `ok` for every must_answer=False case while zero rubric
            # evaluation happened, which is exactly the invariant-12 shape the
            # project forbids. The structured failure signal separates the two,
            # independently of diagnostic wording.
            decision = await answer_gate(
                oc, question, draft, DEFAULT_ANSWER_CUTOFF, context=context
            )
            return decision.answers, decision.judge_failed

        impls.append(("runtime", runtime))
    if anthropic_key:
        try:
            import anthropic
        except ImportError as exc:
            print(
                "note: ANTHROPIC_API_KEY is set but the OFFLINE mirror's "
                f"dependencies are not installed ({exc.name or exc}); skipping "
                "the OFFLINE mirror half"
            )
        else:
            ac = anthropic.AsyncAnthropic(api_key=anthropic_key)

            # The offline mirror RAISES on a failed call or a payload with no
            # boolean `answers`, no string-or-null `stated_value` or no boolean
            # `same_kind` rather than failing closed, so it cannot silently report
            # a dead judge as a verdict and never needs a failure tag.
            async def offline(question: str, context: str, draft: str) -> tuple[bool, bool]:
                return await judge_answering(ac, question, context, draft), False

            impls.append(("offline", offline))
    return impls


def _require_live_keys() -> None:
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        _skip("neither OPENAI_API_KEY nor ANTHROPIC_API_KEY is set")


# --- the measured-trade fixture (ADR-0015) ---------------------------------

_TRADE_FIXTURE = ROOT / "backend" / "test-fixtures" / "answer_gate_measured_trade.json"
_TRADE_EXPECTATIONS = ("answers", "escalates", "known_gap_answers")
# The counts the ADR-0015 numbers are quoted from. A change here is a change to the
# measured trade, so it is made on purpose, with the ADR and the PR text.
_TRADE_N_ANSWERS = 19
_TRADE_N_P310_DRAFTS = 24
_TRADE_GAP_ID = "e7-p3-07 wrong-branch"


def _trade_rows() -> list[dict[str, Any]]:
    _check(
        _TRADE_FIXTURE.is_file(),
        f"missing fixture {_TRADE_FIXTURE}: the measured-trade rows are read from it",
    )
    data = json.loads(_TRADE_FIXTURE.read_text(encoding="utf-8"))
    contexts = data["contexts"]
    rows = []
    for row in data["rows"]:
        _check(
            row["expect"] in _TRADE_EXPECTATIONS,
            f"{row['id']}: expect must be one of {_TRADE_EXPECTATIONS}, got {row['expect']!r}",
        )
        _check(
            row["qid"] in contexts and contexts[row["qid"]].strip(),
            f"{row['id']}: no retrieved context stored for {row['qid']!r}",
        )
        rows.append({**row, "context": contexts[row["qid"]]})
    return rows


def test_measured_trade_fixture_is_well_formed() -> None:
    """The fixture the live trade test reads must measure what the ADR quotes.

    Always runs, no keys: a fixture that quietly lost its should-answer rows would
    let the live test pass a gate that escalates everything (invariant 12: measured
    nothing is not a measurement), so the populations are counted here, not just
    iterated there.
    """
    rows = _trade_rows()
    ids = [r["id"] for r in rows]
    _check(len(ids) == len(set(ids)), "measured-trade row ids must be unique")
    for r in rows:
        _check(r["question"].strip() and r["draft"].strip(), f"{r['id']}: empty question or draft")
    answers = [r for r in rows if r["expect"] == "answers" and not r.get("constructed")]
    gap = [r for r in rows if r["expect"] == "known_gap_answers"]
    p310 = [r for r in rows if r["qid"] == "e7-p3-10" and not r.get("constructed")]
    _check(
        len(answers) == _TRADE_N_ANSWERS,
        f"want {_TRADE_N_ANSWERS} real should-answer rows (the 'no loss' side of the "
        f"trade), got {len(answers)}",
    )
    _check(
        {r["qid"] for r in answers} == {f"e7-p2-0{i}" for i in range(1, 5)},
        "the should-answer rows must cover all four gold P2 questions",
    )
    _check(
        len(p310) == _TRADE_N_P310_DRAFTS and all(r["expect"] == "escalates" for r in p310),
        f"want {_TRADE_N_P310_DRAFTS} e7-p3-10 drafts, all expected to escalate, got "
        f"{len(p310)}",
    )
    _check(
        [r["id"] for r in gap] == [_TRADE_GAP_ID],
        f"exactly one known-gap row ({_TRADE_GAP_ID!r}) is expected, got {[r['id'] for r in gap]}",
    )
    _check(
        "50%" in gap[0]["draft"] and "escalated" in gap[0]["question"],
        "the known gap is the un-escalated cap stated for an after-escalation question",
    )
    real = {c[0]: c for c in _CASES}[_real_context_label("e7-p3-10")]
    _check(
        any(r["draft"] == real[2] and r["context"] == real[3] for r in p310),
        "the verbatim e7-p3-10 triple of the real-context fixture must be among the "
        "measured-trade rows, with the same context",
    )
    _check(
        any(r["population"] == "range" and r["expect"] == "escalates" for r in rows),
        "the constructed range draft (the shape the stated-value mechanism alone "
        "mishandles) must be in the trade",
    )
    _check(
        any(
            r["population"] == "who_pays" and r["expect"] == "answers" and r.get("constructed")
            for r in rows
        ),
        "the constructed who-pays answer to a who-pays question (the case the "
        "exact-amount scope of `same_kind` exists for) must be in the trade, "
        "expected to send",
    )
    print(
        f"ok: the measured-trade fixture holds {len(answers)} should-answer, "
        f"{len(p310)} e7-p3-10, 1 known-gap, the range and the who-pays rows"
    )


def test_live_rubric_discrimination() -> None:
    """Exercise the REAL rubric, on both implementations, against labelled cases.

    Skips cleanly when a key or package is absent so the unit layer above still
    runs anywhere. Requires unanimity over `_REPS` calls per case: both judges are
    pinned to temperature 0, so a split verdict is a finding, not a flake. That
    claim only holds if the pin the failure message asserts is the pin that
    actually ran, so the ambient judge environment is neutralized for the duration
    of this layer - see `_neutral_judge_env`.

    A judge that was CALLED AND FAILED is a third outcome, distinct from both a
    clean skip and a verdict: it is reported as UNMEASURED and fails the test. The
    runtime gate fails closed, so a dead judge answers False on every case and
    would otherwise print `ok` for every `must_answer=False` row while exercising
    no rubric at all - invariant 12's "measured nothing must never be reportable as
    a measurement", in the one layer whose entire job is to measure the rubric.
    """
    _require_live_keys()
    failures: list[str] = []

    async def run() -> None:
        impls = _live_impls()
        if not impls:
            _skip("no usable judge implementation")
        # Record WHICH judge answered and at what temperature: the determinism the
        # SPLIT message argues from is a property of that pair, not of the rubric
        # alone, so the verdicts below are only interpretable alongside it.
        print(
            f"  live rubric layer: {_cost_note(len(impls))}; runtime judge "
            f"{get_judge_model()!r} at temperature {get_judge_temperature()!r}"
        )

        for label, question, draft, context, must_answer, why in _CASES:
            for impl_name, judge in impls:
                results = await asyncio.gather(
                    *[judge(question, context, draft) for _ in range(_REPS)]
                )

                # A judge that was called and failed measured NOTHING, so this case
                # is UNMEASURED - never a legitimate non-answer verdict, and never
                # an `ok`.
                if any(judge_failed for _, judge_failed in results):
                    print(
                        f"  UNMEASURED [{impl_name:>7}] {label}: the judge was "
                        "called and failed"
                    )
                    failures.append(
                        f"[{impl_name}] {label}: HARNESS FAILURE - the judge was "
                        "called and failed, so this "
                        "case exercised no rubric at all. The gate fails closed, so "
                        "a dead judge reports answers=False and would otherwise read "
                        "as the rubric correctly rejecting a non-answer. Fix the "
                        "judge credentials/connectivity and re-run."
                    )
                    continue

                verdicts = [answers for answers, _ in results]
                unanimous = len(set(verdicts)) == 1
                got = verdicts[0] if unanimous else verdicts
                ok = unanimous and verdicts[0] is must_answer
                print(
                    f"  {'ok ' if ok else 'FAIL'} [{impl_name:>7}] {label}: "
                    f"answers={got} (want {must_answer})"
                )
                if not unanimous:
                    failures.append(
                        f"[{impl_name}] {label}: SPLIT verdict {verdicts} over "
                        f"{_REPS} calls at temperature 0 — INVESTIGATE, do not "
                        "retry away. Two causes produce this observation and they "
                        "need different fixes: (a) the rubric no longer "
                        "discriminates this case cleanly, which is a real "
                        "regression in the shipped send/escalate behaviour; or (b) "
                        "provider-side nondeterminism, since temperature 0 is "
                        "best-effort and no `seed` is passed. Re-run to tell them "
                        "apart — (a) reproduces, (b) usually does not."
                    )
                elif verdicts[0] is not must_answer:
                    failures.append(
                        f"[{impl_name}] {label}: answers={verdicts[0]}, want "
                        f"{must_answer} — {why}"
                    )

    with _neutral_judge_env():
        asyncio.run(run())

    _check(not failures, "live rubric discrimination failed:\n  - " + "\n  - ".join(failures))
    print("ok: the live rubric separates deferral-shaped non-answers from real answers")


def test_live_measured_trade() -> None:
    """The measured trade of ADR-0015, held on the live judges (one pass, T=0).

    * every `answers` row (19 real should-answer drafts from the gold P2 questions,
      and a constructed who-pays answer to a who-pays question) must still SEND:
      the mechanism may not cost a deflection it did not cost on 2026-10-15 (0 of
      19, and 0 of 8 on the hand-written answerable rows);
    * every `escalates` row (the 24 distinct `e7-p3-10` drafts, the disclaimed
      `e7-p3-07` drafts and a constructed bare range draft for an exact-amount
      question) must NOT send;
    * the `known_gap_answers` row is the `e7-p3-07` wrong-branch draft: the gate
      sends it TODAY and this test asserts that it still does, so the gap cannot
      close or widen unnoticed (see the module docstring). Runtime half only.

    One pass rather than `_REPS`: this is a population check, not a unanimity check.
    The same judge-failed -> UNMEASURED rule as the discrimination test applies.
    """
    _require_live_keys()
    rows = _trade_rows()
    failures: list[str] = []
    summary: list[str] = []

    async def run() -> None:
        impls = _live_impls()
        if not impls:
            _skip("no usable judge implementation")
        print(
            f"  live measured trade: {len(rows)} rows x {len(impls)} implementation(s) "
            f"= {len(rows) * len(impls)} live judge calls"
        )
        sem = asyncio.Semaphore(6)

        async def one(judge: Judge, row: dict[str, Any]) -> tuple[bool, bool]:
            async with sem:
                return await judge(row["question"], row["context"], row["draft"])

        for impl_name, judge in impls:
            results = await asyncio.gather(*[one(judge, row) for row in rows])
            if any(failed for _, failed in results):
                n = sum(1 for _, failed in results if failed)
                print(f"  UNMEASURED [{impl_name:>7}] {n} of {len(rows)} calls failed")
                failures.append(
                    f"[{impl_name}] HARNESS FAILURE - {n} judge call(s) failed, so the "
                    "trade was not measured on this implementation. Fix credentials or "
                    "connectivity and re-run."
                )
                continue
            false_escalate = 0
            false_resolve = 0
            gap_sent: bool | None = None
            for row, (answers, _) in zip(rows, results):
                if row["expect"] == "answers" and not answers:
                    false_escalate += 1
                    failures.append(
                        f"[{impl_name}] {row['id']}: a should-answer draft was withheld "
                        "- the stricter verdict cost a deflection (ADR-0015 measured none withheld)"
                    )
                elif row["expect"] == "escalates" and answers:
                    false_resolve += 1
                    failures.append(
                        f"[{impl_name}] {row['id']}: a must-escalate draft SENT - "
                        f"{row['population']} shape ({row['draft'][:90]!r})"
                    )
                elif row["expect"] == "known_gap_answers":
                    gap_sent = answers
            n_answers = sum(1 for r in rows if r["expect"] == "answers")
            n_escal = sum(1 for r in rows if r["expect"] == "escalates")
            summary.append(
                f"[{impl_name}] false-escalate {false_escalate}/{n_answers}, "
                f"false-resolve {false_resolve}/{n_escal}, known gap "
                f"{'still sends' if gap_sent else 'no longer sends'} ({_TRADE_GAP_ID})"
            )
            if impl_name == "runtime" and gap_sent is not True:
                failures.append(
                    f"[runtime] {_TRADE_GAP_ID}: the KNOWN REMAINING GAP changed - the "
                    "runtime gate no longer sends the wrong-branch draft. If that is an "
                    "improvement, set the row to expect='escalates', and update "
                    "ADR-0015's known-gap paragraph and the banner above "
                    "`_ANSWER_EXTRACTION_RULE` in backend/escalation.py. If it is a "
                    "one-off split from the provider, re-run before touching anything."
                )

    with _neutral_judge_env():
        asyncio.run(run())

    for line in summary:
        print(f"  {line}")
    _check(not failures, "live measured trade failed:\n  - " + "\n  - ".join(failures))
    print("ok: the live gate holds the measured trade (no loss on should-answer, known gap as recorded)")


def main() -> int:
    tests = [
        test_both_rubrics_state_every_shared_rule,
        test_both_tool_schemas_describe_the_disposition_case,
        test_same_kind_field_and_kind_rule_state_the_same_condition,
        test_offline_verdict_requires_a_stated_value,
        test_offline_judge_raises_on_a_malformed_payload,
        test_offline_tool_schema_commits_the_values_before_the_verdict,
        test_runtime_and_offline_commit_the_same_fields_in_the_same_order,
        test_non_answer_failures_are_structured_independently_of_reason,
        test_boot_warning_call_site_is_wired_to_the_widget_surface,
        test_measured_trade_fixture_is_well_formed,
        test_live_rubric_discrimination,
        test_live_measured_trade,
    ]
    # A skipped group measured NOTHING and must never be counted into the passing
    # total (invariant 12, in the module that argues it hardest). In CI the guard
    # job sets no API keys, so the live layer skipping is the NORMAL case:
    # reporting len(tests) groups passing where len(tests) - len(skipped) ran would
    # be exactly the shape this file exists to forbid, printed by the file itself.
    # Both numbers are computed below rather than written out - a hand-maintained
    # count drifting from the list above is the same defect in miniature.
    passed: list[str] = []
    skipped: list[str] = []
    for t in tests:
        try:
            t()
        except _Skipped:
            skipped.append(t.__name__)
        else:
            passed.append(t.__name__)
    summary = f"\nPASS: {len(passed)} answer-gate RUBRIC (issue #104) test groups"
    if skipped:
        summary += (
            f", {len(skipped)} SKIPPED and therefore UNMEASURED "
            f"({', '.join(skipped)})"
        )
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
