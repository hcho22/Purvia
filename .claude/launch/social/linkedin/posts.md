# LinkedIn posts (5)

Status: DRAFT ONLY - nothing posted (guardrail §3.2).
Audience: the engineer/hiring-manager overlap; the job search outranks the product.
Written as prose paragraphs. No one-line-paragraph stacking, no rhetorical-question openers, no engagement bait.
Claim IDs in brackets at the end of each post (strip before posting).

---

## L-01: A postmortem on my own alarm fatigue

I spent ten years in hardware validation before moving to AI systems, and last week my side project handed me the most hardware-shaped failure I have seen in software.

The lexical leg of my RAG kit's hybrid retrieval shipped dead. Not degraded: dead. Keyword recall@5 was 0.110 in the first nightly eval snapshot my CI ever published, on May 19. Thirty-three published snapshots repeated the same story for seven weeks. I did not read them. What finally made me look was comparing my repo against someone else's project in July.

The uncomfortable part is that I had an alarm. It was a two-sided non-regression check, and it flagged improvements as failures, so it was red on every snapshot it published, for a reason nobody needed to act on. In hardware validation we had a name for this: an alarm that always fires is no alarm. I knew the rule and I still shipped the alarm.

The fix took a day because the eval harness had already localized the problem precisely (the keyword query ANDed every term; one missing word zeroed the match). The part I actually care about took three more days: a new golden-set category so this leg is measurable forever, and a rewritten one-sided alarm that only fires on real drops. The bug cost one migration. The lesson cost a redesign of the alarm that failed to catch it.

Everything above is in the repo, including all seven weeks of bad snapshots: github.com/hcho22/Purvia, docs/nightly. I left them in because a validation record you can edit is not a record.

[A1, A3, A4, A5, D10, A9]

---

## L-02: Permissions in RAG are a retrieval problem, not a filter problem

Most RAG permission bugs are not bugs in the permission system. They are bugs in where the permission system runs.

The common pattern is post-filtering: retrieve top-k by similarity, then drop what the viewer cannot see. The math kills it quietly. At 5% visibility and top-10, the expected number of visible chunks in the result is 10 times 0.05, which is half a chunk. The viewer usually sees nothing relevant, and a multi-hop question that needs two chunks is unanswerable. Fetching more candidates does not rescue it, because similarity is no longer ranking the visible set against itself.

Microsoft's Copilot deployment guidance names "remediating oversharing" as its first pillar, and the trade press has settled on the right framing: the AI did not bypass security, it reflected the permissions it was given. The failure lives at retrieval time.

In my kit, the ACL check is inside the retrieval SQL itself, under the viewer's JWT, alongside a workspace-membership clause the backend cannot override, because the function never accepts a tenant id from the backend at all. A forgotten filter can only narrow, never widen. And because a design claim is not a property until something attacks it, CI runs a second-workspace eval that grants a viewer ACLs on another tenant's documents while withholding membership, and asserts recall@10 of 0.0 against the other workspace's labeled gold chunks, with a positive control so a vacuous pass fails too, plus an API-edge suite that replays forged and expired tokens. The zero-leak table reads 1.000 in every cell of every published snapshot, scoped to the labeled gold chunks, and the authoring guide treats an unlabeled relevant chunk as a security defect for exactly that reason. The snapshots are the same deterministic assertions rerun nightly, an audit trail rather than independent trials, which is what a change-detector should be.

Repo, with the SQL and both eval suites: github.com/hcho22/Purvia

[B13, G5, B2, B3, B4, B9, B11, B6, J15]

---

## L-03: A support bot's risk tolerance should be a number

The Air Canada ruling settled the accountability question: the tribunal wrote that it makes no difference whether the information comes from a static page or a chatbot. The company owns what the bot says.

If you own what the bot says, the number you need to control is how often it confidently resolves a question it should have handed to a human. In my kit that number has a name, a default, and an enforcement mechanism. The false-resolve ceiling defaults to 5%. A weekly eval replays a population of questions that must escalate (strong retrieval, but no faithful answer available), and if the measured false-resolve rate exceeds the ceiling, the workflow fails and files an issue. It is never downgraded to a comment.

The bot itself never decides to escalate. There is no escalate() tool for the model to call or forget to call. Escalate-versus-answer is deterministic control flow: retrieve once, gate on raw cosine scores, draft, gate on faithfulness, then answer or defer. Every failure mode fails closed. A judge timeout escalates. A missing service key turns the widget surface off entirely rather than running it open. Escalating for permission reasons produces a message asserted byte-identical to the ordinary deferral, so escalation never reveals that restricted content exists.

I have not proven the thresholds are optimal; they are documented placeholders until the parameter sweep promotes better ones, and the published weekly history is still thin. What I can show today is the mechanism, in code and in CI: github.com/hcho22/Purvia, backend/escalation.py.

[F8, C2, C4, C1, C7, C8, C6, J12, J6]

---

## L-04: What ten years of hardware validation taught me about shipping AI

At Zebra I validated hardware, where "it works" is not a sentence you get to say without a test log. Two years into applied AI work, I keep meeting the same gap: teams ship retrieval systems whose central properties (does it leak, does it bluff, did quality regress) are asserted in READMEs instead of checked by anything.

I built my RAG kit as an argument that the validation toolkit transfers. Golden sets instead of vibes: 60 questions, five categories, including adversarial and exact-token lexical questions, with content anchors quoted verbatim from the corpus so swapping in your own corpus fails loudly instead of silently passing. Non-regression baselines with one-sided tolerance, because a check that flags improvements trains people to ignore it. Cross-family judging, because a grader from the same model family shares the writer's blind spots. And a placement rule I think more AI teams should steal: only deterministic checks may fail a PR; LLM-judged checks run on a schedule, and declaring one as a merge gate is a structural load error in the config parser, not a convention.

The part I am least proud of is the strongest evidence for the approach. My own nightly evals published a dead retrieval leg for seven weeks before I read them, and my scale benchmark is red in public right now for a different reason. The instrumentation was sound; the operational discipline lagged it. Hardware taught me that too: the test rack is only half the system. The other half is somebody actually reading the log.

One more disclosure, because the git log makes it anyway: 49 of the 152 human-authored commits on main carry a Co-authored-by: Claude trailer. The workflow is PRD-driven agent development, with stories scoped in committed task specs, seams shipped inert before call-sites go live, and the deterministic eval gates acting as the reviewer of record precisely because the commits are co-authored by a model. Hardware validation taught me to trust instruments over assurances; this is the same bet, applied to my own development loop.

The whole thing is MIT and public, failures included: github.com/hcho22/Purvia

[A12, D11, D10, D4, C11, A3, J2, D6, K4]

---

## L-05: How a solo repo earns a second reviewer

A solo repository has a structural problem: nobody reviews the merge. I built my RAG kit's process around that constraint instead of pretending it away, and the result is the part of the project I would most want to talk about in a design review.

Decisions live in committed ADRs, six of them, covering things like why tenant membership is enforced inside the retrieval function rather than by a backend filter, and why the document parser sits behind a one-module seam with its own boundary test. Work arrives as PRDs decomposed into stories with acceptance criteria and validation steps, checked into the repo alongside the code they produced. New infrastructure ships as an inert, unit-tested seam first, and gets wired to its live call-site in a separate change; the adaptive-fusion seam landed with a test proving retrieval output was byte-identical before the follow-up story flipped it on.

The reviewer of record is the eval CI. Deterministic security gates run on every relevant PR: a cross-workspace leak eval, an API-edge attack suite with over 30 exact assertions, and an escalation tripwire, all of which fail their required check on any breach. A placement rule in the gate config makes it a structural load error to put an LLM-judged eval on the per-PR path, so the only checks that can stop a merge are the ones that cannot flake. Behind that sit 42 backend test modules, about 14,000 lines of test code against 27,000 lines of backend Python.

The honest limit: a test suite is not a colleague. It cannot tell me a design is wrong, only that a property broke, and the two operational lapses in this repo's public record, a dead retrieval leg unread for seven weeks and a scale benchmark red for a month, are exactly the failures a second human might have caught sooner. That is the trade I am working inside, and the repo shows both sides of it: github.com/hcho22/Purvia

[D8, D9, D12, B9, B10, B11, C11, A3, J2, K4]
