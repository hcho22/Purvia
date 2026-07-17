# TikTok scripts (4)

Status: DRAFT ONLY - script and storyboard only, no rendered video (per brief §Phase 4).
Terminal-screen-recording energy. Every shot names the exact repo command or artifact filmed.
Voice rules apply to on-screen text and voiceover: no hype words, no exclamation marks, no em dashes.
Claim IDs in brackets (strip from production notes before filming).

---

## T-01: "Seven weeks" (45-60s)

Hook (0-3s):
- SHOT: Terminal, dark theme, large font. Type: `cat docs/nightly/2026-05-19.md | grep keyword`
- ON-SCREEN TEXT: "this number sat in my repo for 7 weeks"
- VO: "This number sat in my public repo for seven weeks and I never read it."

Body (3-40s):
- SHOT: Output shows `| keyword | 0.110 |`. Scroll pause. [A1]
- VO: "Keyword recall at five: zero point one one. The lexical leg of my hybrid retrieval shipped dead, and my own nightly eval published that fact in thirty-three straight snapshots."
- SHOT: `ls docs/nightly/*.md` scrolling 38 files. [A9]
- VO: "Thirty-eight snapshots, committed to the repo. Thirty-three of them show the dead leg. Nobody deleted anything."
- SHOT: `git log --oneline --since 2026-07-10 --until 2026-07-14` showing PRs #77-#86. [A6]
- VO: "When I finally read the numbers, the fix took a day. It was a boring SQL fallback. The interesting part is what I had to admit: publication is not detection."
- SHOT: `cat docs/nightly/2026-07-11.md | grep keyword` shows `0.917`. [A5]
- VO: "Zero point nine one seven the next night."

Close (40-50s):
- ON-SCREEN TEXT: "publication is not detection"
- VO: "The kit is called Purvia. Every claim it makes ends in a file path. Link in bio."

Artifacts filmed: docs/nightly/2026-05-19.md, docs/nightly/ listing, git log, docs/nightly/2026-07-11.md.

---

## T-02: "Watch a stranger retrieve nothing" (30-45s)

Hook (0-3s):
- SHOT: Terminal. Type: `python -m evals.retrieval.runner --viewers all`
- ON-SCREEN TEXT: "180 runs as a user who should see nothing"
- VO: "On every nightly run, my eval exercises my retrieval stack as a user who is allowed to see nothing relevant."

Body (3-30s):
- SHOT: Runner output scrolls; cut to the security table rendering 1.000 across all cells. [B6]
- VO: "The table has to read one point zero zero zero in every cell: zero labeled chunks returned, in vector mode, keyword mode, and hybrid. If a single cell drops, the run exits non-zero."
- SHOT: Open evals/gate/security.py at the binary assert. [B7]
- VO: "There is no threshold to tune. The check is equals one point zero, and the loader rejects any config that tries to soften a security gate. Deleting the eval is the only off switch, and that shows up in a diff."
- SHOT: Open docs/golden-set-authoring.md header. [J15]
- VO: "One honest caveat: the guarantee is as complete as the gold labels, which is why under-labeling is treated as a security bug."

Close:
- ON-SCREEN TEXT: "the zero-leak table, rerun on every nightly"
- Artifacts filmed: evals/retrieval/runner.py run, evals/gate/security.py, docs/golden-set-authoring.md.

---

## T-03: "The bot that refuses to bluff" (30-45s)

Hook (0-3s):
- SHOT: Split terminal. Left: widget chat UI (local). Right: backend logs.
- ON-SCREEN TEXT: "my support bot has no escalate button. on purpose."
- VO: "My support bot cannot decide to escalate, because I never gave the model that tool."

Body (3-35s):
- SHOT: Open backend/escalation.py to the control-flow docstring. [C1]
- VO: "Escalate versus answer is plain control flow. Weak retrieval escalates before a single token is drafted. A strong draft still has to pass a faithfulness judge, and if the judge times out, that counts as unfaithful. Everything fails closed."
- SHOT: Run `python -m evals.retrieval.e7_runner --include-p1b`; highlight the byte-equality assertion output. [C6]
- VO: "This eval asserts the escalation message a no-access customer sees is byte for byte identical to the normal deferral. Escalating never reveals that hidden content exists."
- SHOT: grep ESCALATION_FALSE_RESOLVE_CEILING backend/escalation.py showing 0.05. [C2]
- VO: "And the risk tolerance is a number. Five percent false-resolve ceiling, enforced by a weekly eval that fails and files an issue."

Close:
- ON-SCREEN TEXT: "weak retrieval escalates before a single token is drafted"
- Artifacts filmed: backend/escalation.py, e7_runner run, the ceiling default.

---

## T-04: "Red in public" (20-30s)

Hook (0-3s):
- SHOT: Terminal: `ls docs/permissions-scale-nightly/ | tail -5` then `grep -A3 recall docs/permissions-scale-nightly/2026-07-15.md`
- ON-SCREEN TEXT: "this benchmark of mine is broken right now"
- VO: "This is the part of my repo that is broken right now, in public."

Body (3-22s):
- SHOT: The 0.000 cells on screen. [J2]
- VO: "My ten-thousand-chunk scale benchmark has published zeros since June nineteenth. The likely cause is a migration that orphaned the benchmark's test users, and the alarm fired into a void for weeks."
- VO: "I found it while writing launch copy for the same repo. It stays red, in public, until it is fixed."

Close:
- ON-SCREEN TEXT: "the red cells stay public until fixed"
- VO: "If the receipts are the product, the red ones count too."
- Artifacts filmed: docs/permissions-scale-nightly/2026-07-15.md.
