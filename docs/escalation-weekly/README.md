# E7 weekly escalation snapshots

`<DATE>.md` and `<DATE>.json` in this directory are **generated** by `.github/workflows/escalation-eval-weekly.yml` (Sundays 06:00 UTC + `workflow_dispatch`) from `evals.retrieval.e7_runner --include-p1b --include-p2 --include-p3 --include-parity --sweep`.
They are the run's verbatim record, so they are never hand-edited, not even to correct a claim a later change proved wrong.
Corrections go here instead, as dated errata.
The full treatment of what the snapshots contain and which numbers are pinned lives in `docs/evals.md` § 6.

## Errata

### 2026-09-20 to 2026-10-11 - the `false-resolve 18-27%` breaches measured the offline judge, not the pipeline (issue #163)

The `2026-09-20`, `2026-09-27`, `2026-10-04` and `2026-10-11` snapshots read false-resolve 27% (3/11), 18% (2/11), 18% (2/11) and 27% (3/11), the ceiling gate reads BREACH, and the parity leg reads DISAGREE.
The rows that auto-resolved are `e7-p3-01`, `e7-p3-05` and `e7-p3-09` (two of the three in the middle two weeks).
Their drafts were a bare "I don't have that information." (jewelry warranty, Diamond tier) and "quoted on a per-case basis" (over-20-lbs return fee).
The runtime gate rejected every one of them in the same snapshots.
On those three rows the OFFLINE Claude answer judge was the outlier, and it was deterministic: replaying the captured inputs, 5 of 5 identical calls said `answers=true` on each of them.
Those are 3 of the 4 parity mismatches on 2026-09-20 and every mismatch in the three weeks after; the fourth went the other way (see the open product risk below).

What started it: PR #156 (merged 2026-09-15) began showing that judge the retrieved context.
Before it the same drafts were scored `answers=false` in every weekly from 2026-08-09 to 2026-09-13.
With the context in view, a forced single-boolean tool call graded the draft's truth against the context and counted an accurate deferral as an answer.
What exposed it: only the next weekly, because the LLM-judged legs are not per-PR and the live rubric layer used one-section hand-written contexts that never looked like ground truth.
What a buyer saw: nothing wrong from these three rows.
The shipped pipeline, run end to end with only the runtime gates in a 2026-10-15 sweep of 5 runs per question, escalated every P3 question in every run (0 false-resolves in 55 runs) and answered every P2 question (0 false-escalates in 20).

The offline judge is fixed forward from the next weekly run onward (these snapshots are kept as the record): `runner.judge_answering` now has the judge name the asked value and the stated value before it decides, and the verdict requires a non-empty stated value.
See `docs/evals.md` § 6.

**OPEN PRODUCT RISK, not fixed by this change: the runtime gate passes the `e7-p3-10` adjacent-fact draft.**
The fourth 2026-09-20 parity mismatch, `e7-p3-10`, was the RUNTIME gate (gpt-4o-mini, temperature 0) passing a draft the offline judge rejected.
The question was "What is the return shipping fee for an international return?" and the draft was "For international returns, the return shipping is at the customer's expense, unless the return is for a wrong-item-shipped or damaged-in-transit case."
That is the adjacent-fact non-answer the rubric names: it says who pays, and the customer asked how much.
The weekly scored it as an escalation because the P3 leg's verdict is the offline judge's; the shipped send path uses the runtime gate, which would have auto-sent it.
Across the 2026-10-15 end-to-end pipeline runs on that one question, a larger set than the 5 it got in the 55-run sweep above, it escalated 35 of 35 times, so those runs did not leak.
But replaying that verbatim (question, context, draft) triple through the runtime `answer_gate` 10 times on 2026-10-15 (gpt-4o-mini, temperature 0, default cutoff) let it through 5 of 10 and escalated 5 of 10, with no judge failure.
The drafter writes that shape regularly: 7 of the 18 distinct `e7-p3-10` drafts across the committed weekly snapshots and replays carry no disclaimer and state only who pays.
The runtime rubric, prompt and model are unchanged here.
While this risk is open the weekly can still go red on it.
A week whose drafter writes that no-disclaimer shape for `e7-p3-10` gets an offline escalate and, about half the time, a runtime pass, so the parity leg reads DISAGREE on that row (offline `answers=false`, runtime `answers=true`), the runner exits 1, and the gate-finding issue fires again.
That red is this open risk surfacing, not a regression of the offline-judge fix, and it does not move the false-resolve rate, which the offline judge scores.
`backend/test_answer_gate_rubric.py` carries the triple as a real-context live row: the offline half asserts it must escalate, and the runtime half prints its verdicts as KNOWN OPEN RISK without failing.
That exemption never retires on its own: it is removed by hand, in the change that fixes the runtime gate, and the row is asserted only after that.

### 2026-07-31 - the main leg's `false-resolve 100% (3/3)` was an eval artifact, not a live pipeline breach (issue #96)

The `2026-07-31.md` main leg (τ_sim=0.4) reads **false-resolve 100% (3/3)** and the ceiling gate reads **BREACH**, and the erratum immediately below calls that breach "manifestly measured."
It *was* measured - but it measured the **eval**, not the pipeline. The E7 P2/P3 legs modeled only the runtime **faithfulness** gate; they did not model the runtime **answer-completeness** gate (issue #97), even though the live deflection pipeline had gated the send path on BOTH since that change.

Every one of the three P3 rows is a "topic on-corpus, specific fact absent" question (jewelry warranty, Hawaii shipping, exact delay refund), and the drafter (`escalation.draft_support_answer`) is *instructed* to say it does not have the information rather than guess.
So each draft is a **grounded deferral**: faithful (the offline judge scored all three 5/5, zero unsupported claims) yet answering nothing.
The runtime pipeline escalates every one of those at the answer gate; the E7 leg, seeing only the faithfulness verdict, scored each as an **auto-resolve** and therefore a false-resolve.
The 100% was three correct escalations mislabeled - the pipeline was never auto-sending answers to unanswerable questions.

Fixed forward from the **next** weekly run onward (this snapshot predates it and is kept as the historical record): `_run_judged_leg` now runs a second OFFLINE cross-family judge, `runner.judge_answering`, on the would-be-answered path (after a draft clears faithfulness), mirroring `escalation.run_deflection_pipeline`.
A P3 grounded deferral now escalates at the new `answer` leg and is scored a **correct** content-gate escalation, not a false-resolve; only a draft that is faithful **and** answers auto-resolves.
The P3 result JSON gains `answered` / `answer_judge_calls` / `total_answer_judge_calls` and renames `n_escalated_at_faithfulness` → `n_escalated_at_content_gate`.
See `docs/evals.md` § 6 and the `_run_judged_leg` docstring in `evals/retrieval/e7_runner.py`.

### 2026-07-31 - the recommended knee's `false-resolve 0%` measured nothing

The sweep table in `2026-07-31.md` selects a knee at τ_sim=0.5 / N_min=1 / faithfulness≥4/5 reading **false-resolve 0%**, and prints it as **"Recommended US-050 defaults: `ESCALATION_TAU_SIM=0.5`, `ESCALATION_N_MIN=1`"**.
That 0% is vacuous: it is not evidence the faithfulness gate held at that operating point, because the faithfulness gate never ran there.

The P3 population at the time of that run was three rows, and the same snapshot records each one's top-1 cosine: `e7-p3-01` 0.4607, `e7-p3-02` 0.4214, `e7-p3-03` 0.4298.
All three sit below 0.5, so at the recommended τ_sim every one of them escalates at the **retrieval** gate, where it is scored `mislabeled` and can never be tallied a false-resolve.
Zero P3 rows reached the faithfulness gate at the recommended knee.
The same run's main leg, scored at the default τ_sim=0.4 where all three rows do clear retrieval, measured false-resolve **100% (3/3)** and the ceiling gate correctly read **BREACH**.
The sweep was therefore recommending a knob change that would have hidden a live ceiling breach rather than fixed it - an operating point the runner's own pinned P3 positive control exits non-zero on.

**Do not promote `ESCALATION_TAU_SIM=0.5` / `ESCALATION_N_MIN=1` off this snapshot.**
Read its deflection (75%) and false-escalate (25%) columns as measured; read its false-resolve column at τ_sim=0.5 as unmeasured.
The τ_sim=0.3 and τ_sim=0.4 rows at N_min=1 and N_min=2 read false-resolve 100%, which is manifestly measured.
The N_min=3 rows read 67%, and the snapshot does not record whether the missing row escalated at the retrieval gate (mislabeled, so unmeasured) or at the faithfulness gate (measured) - that ambiguity is exactly what the new column removes.

Fixed forward in two places, both of which land from the **next** weekly run onward - this snapshot predates both and is kept as the historical record:

- Each sweep point now carries `p3_n_questions` / `p3_n_exercised` / `p3_n_mislabeled` / `p3_mislabel_ratio` and a derived `p3_vacuous`, rendered as a **`P3 exercised`** column in the markdown and serialized on every sweep point in the JSON, with `p3_n_exercised` + `p3_vacuous` additionally riding on `curve_points` and on `recommended_defaults` so a script promoting the knee off the JSON alone still sees the warning, plus an explicit callout above the recommendation when the selected knee is vacuous or majority-mislabeled. This is reporting, not enforcement: `feasible` and `_select_knee` are unchanged, so the same knee is still selected - it is now labelled.
- The P3 golden set was widened to 9 rows deliberately spanning the swept grid, four of which clear 0.5 (`e7-p3-04` 0.5339, `e7-p3-05` 0.5800, `e7-p3-10` 0.5288, `e7-p3-11` 0.5605), so raising τ_sim to the top of the grid can no longer silence the whole population. See the `P3 COSINE COVERAGE` block in `evals/retrieval/escalation_gold.yaml` and the authoring rule in `docs/golden-set-authoring.md`.
- The current set has 11 rows: `e7-p3-12` and `e7-p3-13` add rephrased adjacent-fact traps for international-return fees and refurbished-electronics warranty periods. They are intentionally marked UNMEASURED until the first scheduled run records their own top-1 cosine; no value is borrowed from the earlier row they vary.
