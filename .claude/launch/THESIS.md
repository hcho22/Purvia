# THESIS

The bet behind marketing Purvia, in falsifiable form, with the signals that would kill it.
Every load-bearing claim here carries an ID from `launch/evidence/claims.md`; anything without an ID is labeled as inference or assumption.
Written 2026-07-16; revision 2 after the Phase-1 skeptic pass (dispositions in `launch/BUILD_LOG.md`).

## The asset

Purvia is a permissions-aware RAG kit where the two claims that matter are checked by evals wired into CI, not asserted in a README.
Access-correctness: chunk-level ACLs materialized at ingestion (B1), checked inside the retrieval SQL predicate under the viewer's JWT (B2, B3), with zero-leak evals (B6, B9) and API-layer attack tests (B11) failing their required CI checks on any breach (B10, B15, J14 wording).
The security asserts have no tolerance knob and no config off-switch for the verdict; downgrading a leak finding requires a code-visible PR diff, while a run that cannot execute at all is flagged loudly but does not block (B7, B8 scope limit, weakness 10).
Answer-trustworthiness: a deterministic escalation gate with a buyer-set false-resolve ceiling that fails the eval workflow when breached (C1, C2, C4).
The retrieval stack is measured by a 60-question golden set with 38 published nightly snapshots, including seven weeks of snapshots showing its own lexical leg dead, published rather than deleted (A1, A9).
MIT core, raw OpenAI SDK + Pydantic, no orchestration framework in the product (D1, D6, J8 phrasing).

## The centerpiece story, told the only honest way (J4)

The lexical leg of hybrid retrieval shipped dead.
The nightly harness put that on the public record from its first snapshot (keyword recall@5 0.110 on 2026-05-19) through 33 consecutive snapshots (A1, A3).
Nobody read the tables for seven weeks, partly because the only automated alarm was a two-sided baseline check stuck flagging improvements as failures (D10).
A comparison against another project on 2026-07-10 prompted the first real read; the fix was scoped the same day from the harness's own numbers, landed by 07-13 (A6), and the same public series now shows the first healthy lexical-leg numbers (A7).
The fix itself was deliberately boring, a standard OR-fallback (A4); what the pass actually bought was instrumentation: a lexical golden-set category measured on every run, and a one-sided alarm that only fires on real drops (D10).
Instrumentation is not the same as the discipline of reading it: the June nightly outage (weakness 9) and the still-red scale benchmark (weakness 3) are the standing counterexamples, and the copy owns both first.
That story sells honesty and instrumentation, not heroics, and every sentence of it is checkable in committed artifacts.

## The buyer

A production-minded engineer (or 2-5 person team) adding RAG to a real multi-user product: a SaaS app, an internal tool with real permissions, a customer support surface.
They have been burned by framework churn (F1, F3) or have read enough to fear it (F2).
They have users whose documents must not leak to other users (F4, F5, G5).
Confronting F2 head-on: this buyer's creed is "you don't need a framework," so the pitch is never "adopt my abstraction."
It is: you will build the retrieval loop yourself anyway, in a few hundred lines on the raw SDK, and you should; what you will not cheaply build is the proof: the golden set, the zero-leak evals, the attack suite, the escalation gate with a measurable safety ceiling.
Take the kit whole if you want, or treat it as the reference implementation plus the test harness for the one you build.
Whether this framing converts is exactly what kill criterion 1 measures.
Explicitly not the buyer: no-code builders, agencies, B2B SMB automation buyers (brief §0; the skeptic pass found no evidence against the exclusions).

## What they do today instead

1. Assemble LangChain or LlamaIndex plus a vector DB, following the vendors' own per-user-filter tutorials (E1, E2): a DIY pattern the developer must re-apply on every query, fail-open by construction, with no eval proving it holds.
2. Follow a vendor tutorial (Supabase RLS guide, AWS reference blog) and build the rest themselves over weeks (G6): the tutorials validate the architecture but ship no eval harness, no attack tests, no escalation gate.
3. Buy enterprise (Glean, Credal, $100K-class Vectara) if they are big enough, which the ICP is not (E8, G1, G2).
4. Ship without permission enforcement and hope, which is the failure mode Copilot made famous at enterprise scale (G5, F6).

## Why this beats those, stated so a skeptic can check it

- Against DIY-on-framework: the differentiator is verification, not code volume. The eval harness kept a timestamped public record of its own dead leg and of the fix (the section above); an evaluating engineer does not have to trust me, they can rerun the runner (A13) and read the snapshots (A9). No comparable open kit we found advertises chunk-level ACLs enforced in the retrieval predicate with leak evals that fail the required CI check (E10; all three qualifiers, always, per J13).
- Against tutorials: the tutorials agree with the architecture (G6) but stop at the predicate. Purvia ships the predicate plus the proof: E6 cross-workspace zero-leak (B9, B10), AU4 API-edge attacks (B11), a binary security assert whose verdict has no config off-switch (B7, B8).
- Against enterprise platforms: they sell an adjacent thing, permission inheritance synced from enterprise sources, to large orgs (G1 scope note). Purvia ships native chunk-level ACLs plus the eval proof for teams whose own app owns its permission model, at a free-to-$249 license against $100K-class platform contracts; the buyer trades vendor operations for owning the stack (J16 wording).
- Against the closest OSS competitor: Onyx's docs state differentiated document access is Enterprise-only (E5). What Onyx EE centrally sells is permission syncing from external sources, which Purvia does not ship; the honest contrast is that the enforcement primitive and its leak evals are in Purvia's MIT core.

## The falsifiable bet

Production-minded engineers will adopt a RAG kit whose access-correctness and answer-safety are proven by evals they can rerun in CI, because for this buyer the cost of verifying a RAG stack exceeds the cost of building one.

The falsifiable core: **receipts change adoption behavior.**
If eval receipts do not measurably out-convert feature lists for this ICP, the thesis is wrong, however good the engineering is.

Directional proof looks like: inbound that cites the eval artifacts unprompted; golden sets authored by strangers on their own corpora; the deflection/security framing repeated back in others' words.
What it does not claim: best-in-class retrieval quality (J1), production track record (J9), any market-size number.
No market-size figure appears in this thesis because I have no sourced one; any TAM number would be fan-fiction (said out loud per brief §1).

## Commercial shape (challenged twice, revised once, logged)

Open core, free MIT core, paid pro tier at $149-$249 one-time.

What the evidence actually establishes: the $149-$249 band is a familiar price for developer assets (H1, H2, H3), and the market splits one-time for code-you-own vs subscription where the vendor hosts or maintains a dependency (H4, H5).
The price band is familiar; the category fit is untested (H5 caveat): no comparable sells "production hardening" one-time, and displayed prices are asks, not verified sales.

The skeptic pass killed the original pro-gate list, and the correction stands:
everything currently in the repo, including the deflection widget, the escalation gate, and the eval tooling, is MIT-licensed and already distributed; that grant is irrevocable, those modules are load-bearing for the marketing claims, and none of them can ever be paywalled without repeating the Onyx move this thesis attacks (E5).
So the pro tier can only ever gate things that do not exist in the repo today: future hardening modules built after a paid-tier decision, priority support, a maintained update stream (Pegasus-style "1 year of updates" structure per H3), possibly hosted eval dashboards.
Stated plainly: as of today the pro tier's content is a hypothesis with an empty backlog, not a withheld feature set.
If pro gates updates and support, the Sidekiq subscription logic (H4) applies and one-time pricing is a deliberate concession for launch simplicity, revisited if maintenance load materializes.
Nothing in this launch package presells any of it; the first 20 buyer conversations exist to find what, if anything, clears the willingness-to-pay bar.

Third challenge logged (red team CAR-4/BR-8, 2026-07-16): a priced tier with admitted-empty contents damages both the buyer read ("a price tag on an empty box") and the hiring read ("commercial intent without commercial competence").
Resolution: the launch surfaces no longer display a price. The site's pro panel and the datasheet's future-parts row now say unpriced, planned, gating only what does not exist yet, with the $149-$249 band named only as the hypothesis under test in the 20 buyer conversations.
The brief's commercial shape (open core, $149-$249 pro) survives as this thesis's tested hypothesis rather than a displayed offer; that is the evidence-backed amendment the brief permits, and this paragraph is the log of it.

## Launch preconditions (currently RED, must be green before any public launch)

These are present-tense facts, not future kill signals; launching over them would ship a receipts story with broken receipts.
**The content calendar is hard-gated on this list** (its header says so): no post gets a real date until every item below is green.
Every item is an owner action (this build cannot touch files outside `launch/`, guardrail §3.4); each has a named action and a "done when."

1. **The permissions-scale nightly is red and has been since 2026-06-19** (0.000 in every cell, J2). Action: fix the benchmark's workspace membership, or commit a dated breakage annotation. Done when: a green nightly publishes, or the annotation is on main. The red team rated launching without this a kill (SE-1, BUY-5).
2. **The README contradicts the repo's own nightly directory** (BUY-6): it presents the all-1.000 scale table undated with a present-tense "fails loudly" claim while the benchmark publishes 0.000. Action: date the table in the README and mark the benchmark broken since 2026-06-19 with a link to the red directory. Done when: the README edit is on main. The repo must be at least as honest as the landing page about the repo.
3. **Branch protection is not configured on main** (J14). Action: enable a ruleset requiring the E6/AU4/E7 checks. Done when: the GitHub API returns the ruleset. Until then all copy says "fails the required CI check."
4. **USPTO Class 9+42 clearance for "Purvia" is pending** (I3); the same-name consumer AI face-swap app is the highest-risk collision. Action per the brand critic (BR-5): finish clearance AND run a 10-person cold SERP/pronunciation test with ICP engineers. Done when: both return without a disqualifier.
5. **The founder biography is ledgered as owner-supplied, unverified** (claims section K; SE-5/CAR-1). Action: verify years, titles, and the employer reference against the resume; round down if in doubt. Done when: section K rows flip to verified.
6. **Security disclosure channel** (SE-6): the repo has no SECURITY.md and the old site footer routed vulnerability finds to public issues (now fixed in the footer). Action: enable GitHub private vulnerability reporting and commit a SECURITY.md. Done when: both exist.
7. **Repo hygiene** (SE-9/CAR-6): `gtm/` and `launch/` are untracked in the public repo's working tree; one reflexive commit publishes the build prompt and the platform-strategy files. Action taken by this build: both are now in `.gitignore` (see BUILD_LOG Q6). Remaining owner decision: whether to deliberately publish selected artifacts (the claims ledger and datasheet would strengthen the brand; the platform-strategy files never will). Also: decide the uncommitted `frontend/widget-host-example.html` edit and clean `supabase/snippets/`.
8. **Pre-launch career read**: solicit reads from five named staff-engineer/hiring-manager contacts; three or more independent "inflated/fluffy" verdicts sends the package back for de-hyping before anything publishes.

## Kill criteria (post-launch, each actionable within a week of observing it)

Thresholds below are chosen judgment numbers, labeled as assumptions per the ground-truth rule; none is a sourced benchmark.

1. **Receipts don't convert.** Within 30 days of public launch: fewer than 5 of the first 20 inbound contacts reference the eval artifacts/receipts unprompted (primary, tests the actual bet), OR fewer than 150 new GitHub stars AND fewer than 10 ICP-fit inbound conversations (secondary reach floor; 150/10/5/20 all assumed). Either trigger fires the review. Action: stop growth investment; keep the repo as a portfolio artifact; the job search keeps the technical story.
2. **Nobody pays.** Within 90 days of launch or 20 substantive ICP conversations, whichever comes first: zero buyers exhibit real willingness-to-pay signals (describes a budgeted current alternative, asks about invoicing/procurement, or has previously paid for a comparable developer asset). Hypothetical "yes I'd pay" answers do not count in either direction (Mom-Test discipline). Action: kill the pro tier within a week; redirect to consulting or employment leads from the same artifact.
3. **The moat closes** (pivot trigger, with a second-order kill). A comparable open kit ships chunk-level ACL enforcement in the retrieval predicate plus blocking leak evals, free (watch: Onyx CE per E5, AuthZed's ecosystem per G7). Action: within a week, re-anchor differentiation on the escalation gate + eval-harness authoring story or fold into "the validation layer for any RAG stack." Second-order kill: if the re-anchored positioning also fails criterion 1's metrics in its own 30-day window, stop.
4. **The receipts rot post-launch.** The nightly series stops publishing, or a security gate goes red without a same-week fix or public annotation, while strangers are reading the artifacts. Action: fix or annotate within the week; a receipts brand with stale receipts is worse than no brand.

## Known weaknesses, updated against the repo (supersedes brief §2 where stale)

Marketing that contradicts any of these is a lie we would be caught in:

1. The brief lists the lexical leg as broken with the fix unshipped; the repo shows the fix landed and verified (A5, A6, A7). What stays true is narrower and told in full above: the harness published the failure for seven weeks before anything read it (A3, J4). Publication is not detection, and US-118 exists because of that lesson (D10).
2. Hybrid MRR still trails vector on paraphrase (J3); the retrieval-quality PRD's own goal is not fully met on that cell.
3. The permissions-scale benchmark is currently broken and has been red since 2026-06-19 (J2). Discovered during this build; disclosed, not papered over; launch precondition 1.
4. The eval corpus is deliberately small (8 docs, 16 chunks); metric values are not interpretable at scale, and docs/evals.md says so itself (A12, J1). The security guarantee is scoped by the gold labels (J15).
5. Zero users, zero revenue, zero testimonials (J9). Not deployed to a public URL (J10). No branch protection on main (J14).
6. Published LLM-judged history is thin: one RAGAS weekly snapshot, no escalation-weekly reports yet (J6).
7. Purvia trademark clearance is directional only; USPTO Class 9+42 clearance pending, face-swap app unclassified (I3).
8. Solo repo: PRs are self-merged with no second reviewer (A6); the CI gates are the only independent check, which is both the honest weakness and the reason the gates are the product.
9. The retrieval nightly itself had an 18-night outage: GitHub Actions shows it ran and failed at the "Seed corpus + run eval" step every night 2026-06-01 through 06-18, and nobody noticed that either (A9; red team SE-2). The harness was down and the operator did not see it, which is the same lesson as the dead leg, twice.
10. The E6 security gate fails open on infrastructure failure by design: a run that cannot execute after retries is surfaced loudly but does not fail the check (B8 scope limit; SE-3). The verdict cannot be downgraded; the not-run case can slip through on a flaky day. Owner decision pending on making repeated execution failure fail-closed.
11. The receipts do not transfer to the buyer's corpus: swapping in your own corpus and authoring your own golden set are the same step by design, so day one on your data starts at zero receipts plus a labeling contract where under-labeling is a security defect (BUY-2). The site states this cost plainly; a semi-automated golden-set bootstrapper is the roadmap answer, not shipped.
12. Adoption assumptions now stated instead of implied (L1, L2): Supabase is the identity/RLS substrate (bringing your own auth means porting the predicate, RLS, JWT minting, and eval seeds), and the default install pulls docling/torch (an optional-extra split behind the existing PARSER seam is a roadmap item).
13. Bus factor is one, and this document's own kill criteria route failure into the job search (BUY-7). The succession answer, stated publicly on the site: MIT license plus the eval harness is what makes a hard fork survivable; there is no other answer at zero users.
