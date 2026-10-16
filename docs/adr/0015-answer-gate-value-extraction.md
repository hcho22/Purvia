# ADR 0015: the answer gate extracts the asked and stated value; gpt-5-mini measured worse and is not adopted

- **Status:** Accepted
- **Date:** 2026-10-16
- **On:** ADR-0003 (deterministic escalate-vs-answer control flow), ADR-0006 (model-role separation), ADR-0012 (judges unchanged), ADR-0013 (gpt-5-mini runtime judge)
- **Relation to ADR-0013:** supersedes its **model decision** (gpt-5-mini is NOT adopted); its `JUDGE_REASONING_EFFORT` knob and boot warnings stay.

## Context

The runtime answer gate (`escalation.answer_gate`) decides whether a drafted reply is sent to a customer or handed to a person.
It runs `gpt-4o-mini` at temperature 0 by default.
The captain's ask on 2026-10-15 was "harden the live gate".

The open product risk behind it is recorded in the issue-#163 erratum in `docs/escalation-weekly/README.md`.
The verbatim `e7-p3-10` triple ("What is the return shipping fee for an international return?", answered with who pays, not how much) passed the gate 5 of 10 times on a replay, while the same question escalated 35 of 35 times end to end because the drafter usually adds a disclaimer.
7 of 18 distinct drafts seen had no disclaimer, so a buyer could receive a confident non-answer instead of a hand-off, and the weekly escalation eval could go red on that row.

ADR-0013 (accepted 2026-08-21) had chosen `gpt-5-mini` for this judge on a benchmark that showed it roughly halving false-resolves.
It shipped the code knob only; the `JUDGE_MODEL` flip was left as an operator step and was never taken.
The hosted deployment was paused when this was measured, so "what production runs" is the code default: `gpt-4o-mini`, temperature 0, no `reasoning_effort`.
The repository sets no Actions variables, so the weekly eval runs those defaults too.

## What was measured (2026-10-15)

Every number below drives the real `faithfulness_gate` and `answer_gate` functions through a metering proxy, on GitHub Actions with the repository's own OpenAI key, from a throwaway branch that has since been deleted.
It used 1,269 OpenAI calls (about $0.61 at list price) and no Anthropic calls.
The inputs were:

- the verbatim `e7-p3-10` triple;
- the real-context and hand-written rows of `backend/test_answer_gate_rubric.py`;
- 85 distinct (question, retrieved context, draft) triples for the gold questions, 60 of them real drafts and contexts from the committed weekly snapshots of 2026-09-20 to 2026-10-11 and the rest fresh drafts from the current drafter.
  66 are should-escalate (P3) and 19 are should-answer (P2).

### The status quo is a thin argmax, not a safe margin

- The verbatim `e7-p3-10` triple passed 0 of 40 runs at temperature 0 (two runs, model `gpt-4o-mini-2024-07-18`, judge score 0.0 every time). The erratum's 5 of 10 did not reproduce, and the SDK version is not the cause (the request schema hashes identically on openai 1.70.0, 1.109.1 and 3.31.0).
- But the logprob of the `answers` boolean on that triple read P(true) = 0.22, 0.27 and 0.44 across three identical calls, so the logit gap moved by about a nat between identical requests, as much as the margin itself.
- Sampling the same request at temperature 1 passed it 10 of 20.
- The one real leak in the replay (1 of 66 should-escalate drafts) was `e7-p3-07` (below).

### Candidates

- **Status quo:** gpt-4o-mini, temperature 0, current rubric.
- **A:** gpt-4o-mini, temperature 0, the current rubric plus the offline judge's mechanism: the judge commits to `asked_value`, `stated_value` and `same_kind` before it decides, and the verdict is `answers AND stated_value AND same_kind`.
- **B:** gpt-5-mini per ADR-0013 (`JUDGE_TEMPERATURE=none`, `JUDGE_REASONING_EFFORT=minimal`), current rubric.
- **C:** gpt-5-mini minimal plus the A rubric.

| Candidate | Should-escalate drafts sent (66) | Fixture should-not-answer trials sent (30) | Should-answer withheld (19 drafts, 8 trials) | `e7-p3-10` verbatim passes, T=0 | Same, T=1 | Latency per reply (p50 faithfulness + answer) | Cost per reply |
|---|---|---|---|---|---|---|---|
| Status quo | 1 | 0 | 0, 0 | 0 of 40 | 10 of 20 | 1.26 s | $0.00071 |
| A | 1 | 0 | 0, 0 | 0 of 20 | 0 of 20 | 1.40 s | $0.00076 |
| B | 15 | 18 | 0, 0 | 40 of 40 | not run | 1.64 s | $0.00126 |
| C | 4 | 1 | 0, 0 | 3 of 20 | not run | 2.02 s | $0.00139 |

- gpt-5-mini at its default reasoning effort, instead of minimal, passed the `e7-p3-10` draft 16 of 20 times, sent 16 of 30 fixture should-not-answer trials, and took 3.05 s p50 and 5.5 s p95 for the answer gate call alone.
- Latency is from a GitHub-hosted runner at concurrency 4, so it is indicative only. Cost is at list prices: gpt-5-mini $0.25 and $2.00 per 1M input and output tokens, gpt-4o-mini $0.15 and $0.60.
- 0 withheld of 27 should-answer trials cannot rule out a false-escalate rate up to about 12%.

### Two variants that were not taken

- **A1 (extraction fields only, no `same_kind`):** the same as A on the table above, but it counts a range as a stated value. On a constructed bare draft "10% to 80% of the order total" for the exact-amount question it passed 3 of 8 at temperature 0 and 7 of 8 at temperature 1, against 0 of 8 and 0 of 8 for the status quo. This is the regression the repo notes had warned about.
- **A3 (A plus a same-case field):** no gain on anything measured, and it still passed the `e7-p3-07` draft 8 of 8 and 10 of 10.

A passes the range draft 0 of 8 at temperature 0 and 2 of 8 at temperature 1, so it narrows that regression without removing it.

## Final-head re-measure (2026-10-16)

The same measurement was repeated on the committed implementation, using the repository's real `answer_gate` and `faithfulness_gate` and the committed live tests.
It ran twice, each time through a copy of the weekly workflow with its publish, issue and commit steps removed, from a throwaway branch that has since been deleted.
The first run used 299 OpenAI calls.
Review then found that the `same_kind` field description excluded a range, an estimate, 'varies' and a who-pays, when or where fact for every question, while the kind rule in the prompt excludes them only where an exact amount is asked.
Read literally, that description would escalate a faithful who-pays answer to a who-pays question.
Both descriptions, runtime and offline, now state the rule's condition, and a constructed who-pays answer to a who-pays question was added to the measured trade as a row that must send.
The second run measured that final head with 298 OpenAI calls and no Anthropic calls, and every call was valid (no failed judge call).

| Measure on the committed gate | Second run (final head) | First run | Phase-1 candidate A |
|---|---|---|---|
| `e7-p3-10` verbatim triple, temperature 0 | 0 of 20 passed | 0 of 20 | 0 of 20 |
| same triple, temperature 1 (margin proxy) | 0 of 20 passed | 0 of 20 | 0 of 20 (old gate: 10 of 20) |
| 85 stored triples: should-escalate drafts sent | 1 of 66 (the `e7-p3-07` known gap) | 1 of 66 | 1 of 66 |
| 85 stored triples: should-answer drafts withheld | 0 of 19 | 0 of 19 | 0 of 19 |
| live rubric layer, runtime half (16 cases, 3 reps, unanimous) | all pass | all pass | not run |
| live measured-trade test, runtime half | 50 rows: false-escalate 0 of 20 (the who-pays row sent), false-resolve 0 of 29, known gap still sends | 49 rows: 0 of 19, 0 of 29, still sends | not run |
| judge latency per reply (p50 faithfulness + answer) | 1.44 s | 1.33 s | 1.40 s |
| judge cost per reply | $0.00078 | $0.00078 | $0.00076 |

All 85 stored triples had the same outcome in both runs.
In the second run the unchanged faithfulness gate stopped two should-escalate drafts that the answer gate had stopped in the first, so it made 160 replay calls instead of 162.
The latency difference is runner noise: the mean tokens per call differ by under 5 input and 1 output.
Against the old gate's $0.00071 and 1.26 s, the committed gate costs about $0.00007 and 0.07 to 0.18 s more per reply that reaches the answer gate.

### The offline (Claude) half, on the should-answer rows

The second run also measured the offline judge (`claude-haiku-4-5`) on the final head, for the should-answer rows only, with 28 Anthropic calls.

- One weekly-path run of the P2 leg with the parity leg (`e7_runner --include-p2 --include-parity`, 8 Anthropic calls): the offline judge auto-resolved all 4 P2 rows, and the parity leg passed 4 of 4, with no mismatch and nothing unmeasured, `e7-p2-02` ("3-5 business days") included.
- The 20 should-answer rows of the measured trade through the real `judge_answering` (20 Anthropic calls): 20 of 20 answered, each with `same_kind` true. That includes the 7 `e7-p2-02` range drafts and the who-pays row, and matches the runtime gate, which sends all 20.
- The should-escalate side of the offline judge and the offline half of the live rubric layer were not run.

## Decision

1. **Keep `gpt-4o-mini` at temperature 0 as the runtime judge. Do not adopt gpt-5-mini.**
   Both gpt-5-mini candidates lose the number the gate exists for (B sent 15 of 66 should-escalate drafts against 1 of 66).
   That contradicts the benchmark in ADR-0013 (24% to 8%); the likely reasons are different items and an older rubric, but that is not verified.
   ADR-0013's model decision is not adopted; its `JUDGE_REASONING_EFFORT` knob and boot warnings remain correct for any reasoning judge an operator chooses to run.
2. **Adopt candidate A in the runtime gate.**
   `AnswerJudgment` gains `asked_value`, `stated_value` and `same_kind`, in that order, ahead of `answers` and `score`.
   The system prompt gains the two paragraphs measured here, word for word, appended to the existing rubric.
   The `same_kind` field description states the kind rule's own condition: the stated value is the same kind as the one asked, and only where an exact amount is asked must it also be a specific amount rather than a range, an estimate, 'varies', or a fact about who pays, when, or where.
   `test_same_kind_field_and_kind_rule_state_the_same_condition` holds the emitted rule and both emitted field descriptions to that condition.
   The verdict is `answers AND a stated value AND same_kind AND score >= cutoff`.
   A judge that says "answers" but names no value, or a value of the wrong kind, is self-contradictory and escalates.
   The literal string `null` counts as no value (a model writing the word instead of the JSON token), which can only move a verdict toward escalation.
   Control flow is unchanged: one call, no retry, every failure fails closed, and a judge failure still defers the turn without latching.
3. **Mirror it offline, in lockstep (invariant 8).**
   `runner.judge_answering` already named the asked and stated value (PR #184).
   It gains the `same_kind` field, the same two prompt paragraphs, and a verdict that requires it; a payload without a boolean `same_kind` raises (UNMEASURED).
   `test_runtime_and_offline_commit_the_same_fields_in_the_same_order` pins the field list and order on both sides.

## Consequences

- **Cost and latency:** about $0.00005 to $0.00007 and 0.07 to 0.18 s more per reply that reaches the answer gate (more input and about 26 more output tokens per call; the latency spread across phase 1 and the two final-head runs is runner noise at the same token counts).
- **A thinner margin removed, not a certainty:** the temperature-1 sample on the `e7-p3-10` triple went from 10 of 20 passing to 0 of 20. That is a proxy for how little serving noise it takes to flip the verdict, not a production rate.
- **A is weaker than the status quo on one shape:** the bare range draft at temperature 1 (2 of 8 against 0 of 8, measured in phase 1 before the field-description fix; the final head's temperature-0 trade run still withholds it). Accepted, because the `e7-p3-10` shape has been seen failing in practice and the range shape has not.
- **Known remaining gap, asserted as such:** a value of the right kind stated for the wrong branch. `e7-p3-07` asks for the goodwill refund cap once a case is escalated to a supervisor, and a draft stating the un-escalated 50% names a real, specific, same-kind value. Every rubric measured passed it (the status quo in the replay and 4 of 10 at temperature 1, A 8 of 8 at temperature 0, A3 8 of 8). `backend/test_answer_gate_rubric.py` holds that draft as `known_gap_answers` and asserts the runtime gate still sends it, so the gap turns the live layer red the day it changes and must then be re-recorded here.
- **The offline half is measured on the should-answer rows only.**
  `same_kind` can only move the offline verdict toward escalation.
  The weekly's parity leg is a pinned gate: any offline/runtime disagreement fails the run and files the gate-finding issue.
  So a Claude reading of `same_kind` that withheld a should-answer draft would turn the weekly red, not just raise an advisory false-escalate rate.
  On the final head it did not: parity 4 of 4 on the P2 leg and 20 of 20 stored should-answer drafts answered (above).
  On the should-escalate rows `same_kind` can only lower the offline false-resolve rate, but a row the runtime gate sends and the offline judge now escalates would still be a parity mismatch.
  That side was not run on Claude, so the first weekly after the merge, or a hand run of the live layer with both keys, is its first measurement.
- **The temperature-0 pin stays.** Nothing here un-pins invariant 8's sampler pin; the ADR-0013 trade that would have relaxed it is not taken.
- **Deploy:** buyers get this only through a backend deploy. There is no new environment variable, model change or migration, and nothing to do to existing `JUDGE_*` configuration. Rollback is reverting the change and redeploying.

## Alternatives considered

- **gpt-5-mini minimal (B), or with the A rubric (C):** rejected on the numbers above. C closes most of the gap but is still worse than the status quo and doubles per-reply latency.
- **gpt-5-mini at default reasoning effort:** no better on the safety number (16 of 30 fixture trials sent) and about 3 s per call, which is not viable on the reply path.
- **A1 (extraction without `same_kind`):** regresses on ranges, as the notes had warned.
- **A3 (same-case field):** no measurable gain, more tokens.
- **Leave the gate unchanged and only pin `e7-p3-10` and `e7-p3-07` in tests:** the fallback put to the captain. Rejected by the captain's choice of A. It would have left the thin margin in place.
- **A deterministic slot guard** (require a currency or number token when the question asks "how much"): not measured and brittle on percentages, durations and "free"; left as a possible later layer, not part of this decision.
