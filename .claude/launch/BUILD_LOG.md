# BUILD_LOG

Decisions, self-answered questions, cuts, and costs for the Purvia go-to-market build.
Mission brief: `gtm/marketing-build-prompt_071626.md`.
Build started 2026-07-16.

## Session setup

- Global instructions reference `~/OPINIONS.md` and `~/VOICE.md`; neither file exists on this machine.
  Logged, proceeding with the voice rules in the brief (§4) as the sole voice authority.
- API keys available in `.env` (names only): OPENAI_API_KEY, ANTHROPIC_API_KEY, SUPABASE_*.
  No new services will be used (§3.1).
  External calls made are logged in the "External calls" section at the bottom.
- All new artifacts go under `launch/`. Nothing outside it is modified.

## Self-answered questions

### Q1: The brief's §2 weakness list says the lexical leg is broken and the fix is "specced but not shipped." The repo says otherwise. Which wins?

**Answer:** The repo wins, per the brief's own ground-truth rule (§1: every claim must be cashable in a repo artifact).

**Reasoning:** The brief was evidently drafted before the retrieval-quality pass landed. Repo state as of 2026-07-16:

- `docs/nightly/2026-07-09.md` shows the broken state the brief describes: keyword recall@5 0.140 (paraphrase 0.000), hybrid MRR 0.786 vs vector 0.796, adversarial 0.453 vs 0.503.
- `.claude/agent/tasks/prd-retrieval-quality-pass.md` line 3: "Status: complete. US-113 ... US-118 all landed."
- Merged PRs #77 (PRD, 2026-07-10), #79/#80 (2026-07-10), #81/#82 (2026-07-11), #84/#86 (2026-07-13).
- `docs/nightly/2026-07-15.md` shows the recovered state: keyword recall@5 0.917, hybrid 0.950 >= vector 0.875, hybrid MRR 0.858 >= vector 0.813, adversarial hybrid MRR 0.623 > 0.503.

**Consequence for marketing:** We do NOT claim the leg is still broken, and we do NOT hide that it was. The story gets stronger and stays true: the nightly eval caught the regression on 2026-07-09, the fix was specced as a PRD on 2026-07-10, shipped by 2026-07-13, and the 2026-07-15 nightly proves the recovery. Six days, every step in a committed artifact. "The eval harness that caught the regression is the product" survives intact - now with a completed arc instead of an open wound. The still-true weaknesses (small corpus, zero users/revenue/testimonials, no public deploy) stay disclosed everywhere the brief requires.

### Q2: The brief's §0 names six naming candidates and says "beat them or pick one." The repo already committed a name.

**Answer:** Purvia is the incumbent and enters the Phase-2 naming tournament as a contender that the others must beat.

**Reasoning:** ADR-0011 (accepted 2026-07-14) names the product Purvia, coined from "purview," with Deflio rejected as mis-scoped and the technical namespace deliberately left as `agentic-rag`. PRs #87-#91 (2026-07-15) completed the display-layer rebrand. The brief predates this. Overturning a committed, ADR-documented rename days after it merged would need evidence the name fails on the brief's own axes (searchability, trademark risk, fit to differentiator); the tournament will test exactly that against the six candidates rather than pretend the decision was never made. Guardrail note: ADR-0011 itself flags that USPTO trademark clearance is pending and a consumer "Purvia" face-swap app exists in a different class - that disclosure carries into the brand guidelines.

### Q3: `evidence/` at repo root (§1) or `launch/evidence/` (§8)?

**Answer:** `launch/evidence/`, per the §8 directory layout and guardrail §3.4 (all new artifacts under `launch/`).

### Q6: Was adding `.gitignore` entries within the guardrails?

**Answer:** Yes, judged in-scope and done (entries for `gtm/` and `launch/`).

**Reasoning:** Guardrail §3.4 forbids modifying "application source, migrations, evals, or CI"; a `.gitignore` entry is none of those and changes no behavior. The red team (SE-9, CAR-6) showed the alternative risk is worse: the untracked war room was one reflexive `git add -A && git push` away from publishing the build prompt and platform-strategy files into the public repo, which would violate the stricter guardrail §3.2 (publish nothing). The ignore rule structurally enforces §3.2. Moving `launch/` out of the repo entirely was rejected because §3.4 requires artifacts to live in `./launch/`. The owner can still deliberately publish selected artifacts by force-adding them (THESIS precondition 7 records that decision as theirs).

## Cost/time budget

- No user-set token target. Self-imposed shape: one research workflow per phase where fan-out pays (Phase 1 research, Phase 2 tournament, Phase 5 red team), inline work elsewhere. Tournament capped at 5 pitchers + 3 judges; red team capped at 4 personas + verify passes. Rationale: the brief warns that orchestration that burns the window before Phase 5 is a failure.

## External calls

All external network calls made during this build (per §9 checklist). Each is a read-only fetch; nothing was published, posted, or purchased.

- 2026-07-16: DNS lookups (`dig`) for 16 candidate domains; registry `whois` for purvia.ai (nic.ai), purvia.com, purvia.dev (nic.google). Read-only availability checks; nothing registered.
- 2026-07-16: Web search for "Purvia" trademark collisions; WebFetch of CIPO trademark record 1403254 (success), uspto.report + trademarks.justia.com (both 403, recorded as unfetchable in evidence).
- 2026-07-16: Phase-1 research workflow agents fetch competitor/pain/prior-art/pricing pages via WebFetch/WebSearch; every fetched URL is recorded in launch/evidence/sources/*.md with timestamp and quoted span.

## Phase log

### Phase 1 - started 2026-07-16

- Grounding reads done inline: CONTEXT.md, README.md, ADR-0011, prd-retrieval-quality-pass.md, nightly 2026-07-09 + 2026-07-15, workflow list, git log.
- Research fan-out launched: 4 repo-evidence extractors + 4 web researchers (competitors, RAG-in-production pain, permission-aware prior art, pricing comparables).
- Fan-out completed: 8/8 agents, 190 tool calls, ~381k subagent tokens, 9.4 min wall clock. Evidence files written: competitors.md, production-pain.md, prior-art.md, pricing.md, naming-domains.md (orchestrator).
- **Material discovery (Q4): the permissions-scale nightly benchmark is broken.** Every report since 2026-06-19 (through 2026-07-15) publishes 0.000 in every viewer x ef_search cell with n_returned=0; last good day 2026-06-18. This contradicts the README's all-1.000 scale table. Likely cause (inference): the 2026-06-17/18 workspace-membership migrations added an AND-ed membership clause and the benchmark's synthetic viewers were never backfilled into workspace_membership. Decision: marketing never cites the README scale table as current (claims.md J2); the breakage goes on the disclosed-weakness list (THESIS.md weakness 3) and becomes a launch precondition (kill criterion 4). Guardrail §3.4 forbids fixing application code in this build.
- Honesty caveats banked into claims.md section J (anti-claims): staged Δ-0.510 demo framing, hybrid-MRR-paraphrase gap, uncommitted ADR-0003/4/5/6/8, thin weekly-eval history, "50-question" stale comment, squash-merge PR counts, LangSmith SDK in runtime deps.
- Wrote launch/evidence/claims.md and launch/THESIS.md (falsifiable bet, kill criteria, updated weakness list superseding brief §2). Revision 1 counts corrected per critic: the rev-1 ledger had 85 claim rows + 13 anti-claims; rev-2 (post-skeptic) has 73 claim rows + 16 anti-claims.
- Verification pass: 3 skeptics (market/receipts/thesis) + completeness critic with veto. 4/4 agents, 66 tool calls, ~219k subagent tokens, 7.6 min.

#### Skeptic dispositions (all applied in claims.md rev-2 + THESIS.md rev-2)

Fatal objections, both FIXED:
1. "The harness caught the regression" was false. The leg was dead from the first nightly (2026-05-19, keyword 0.110), 33 consecutive snapshots, 7 weeks unread; the two-sided alarm sat in permanent false-alarm state; the 2026-07-10 aimee comparison prompted the first real read. Fixed: claims section A rewritten around the honest arc (new A1/A3/A6/A7 wording, J4 replaced, "regression/recovered/caught" banned); THESIS gained a "centerpiece story, told the only honest way" section. The honest version is a better story: publish-don't-delete + "an alarm that always fires is no alarm" (US-118).
2. The open-core pro-gate list was incoherent: every named module is already MIT-shipped and irrevocable. Fixed: THESIS commercial-shape section rewritten; pro can only gate not-yet-built modules, support, and an update stream; stated plainly that today's pro tier is a hypothesis with an empty backlog.

Material objections, all FIXED: E1 (LangChain qa_per_user how-to exists; reworded to DIY/fail-open framing + URL added), E2/E4 (README-scope caveats + LlamaIndex multi-tenancy URL), E5 (Onyx whats_changing counter-source; EE-sells-permission-syncing conflation fixed), E10 (sample honesty: 15 mostly-README pages + 4 docs pages; skeptic fetched the 4 likeliest falsifiers, none falsified the narrow triple), G1/G2 (adjacent-category reframe), "three orders of magnitude" (J16: license cost vs TCO), E8 (corpus-boundary scope note), B10/B11 + THESIS (no branch protection on main; "blocks the merge" -> "fails the required CI check"; new J14; enabling a ruleset flagged to owner as launch precondition 2), B6/B7/B8 glosses (gold-label scope J15; "no config off-switch, silencing is code-visible in a PR diff"), A5 (mixed-denominator caveat: ~0.90 on original 50 questions), A6 (self-merged solo-repo disclosure, now also weakness 8), kill criteria redesigned (receipt-citation primary trigger, calendar bounds, Mom-Test signals, pivot trigger with second-order kill, preconditions split out as currently-RED), I3 (face-swap app IS software and is the highest-risk collision; purvia.com squatter leverage disclosed).

Minor objections FIXED in wording (A1 33rd-snapshot context, A4 deliberately-boring-fix note, E3/G7 scoping). One flagged to owner, not fixable in this build (guardrail §3.4): the `--viewers full` escape-hatch comment in retrieval-eval.yml would be quoted back by a skeptical reader; recommend removing it pre-launch.

#### Completeness critic: PASS

Verdict PASS, three non-blocking gaps, all addressed: (1) BUILD_LOG claim count corrected above; (2) kill-criteria thresholds now labeled as assumed judgment numbers in THESIS; (3) quickstart claim added as A13 for the landing page's "run it yourself" section.

**Phase 1 sign-off: complete, 2026-07-16.**

### Phase 2 - Brand

- Tournament: 5 blind pitches x 3 judges, rubric published first in launch/brand/TOURNAMENT.md; 8 agents, ~361k subagent tokens, 9.2 min. Winner: "The Receipts Are the Product" (61.7/65, unanimous). Full scorecards including all four losers appended to TOURNAMENT.md. Grafts adopted: P2's name-earns-its-keep line, P3's validation-engineer framing (reserved for LinkedIn/About), two judge precision fixes (0.110-to-0.140 drift wording; E10 rescope).
- Deliverables: GUIDELINES.md (self-sufficiency-tested), tokens.css/tokens.json (every text-role ratio computed, both themes), 5 SVG marks + preview screenshot (viewed at 64/24/16px, both themes), voice linter at launch/tools/voice-lint.sh (run recorded: GUIDELINES/THESIS/TOURNAMENT all pass; "agentic" hits are report-only namespace references).
- Q5: wordmark uses SVG text with the system mono stack rather than outlined paths (no font-outlining tool available without new installs); documented in GUIDELINES §6 with the platform fallback rule.
- Completeness critic: VETO on first pass - caught a real date error in the hero copy ("fix landed four days after that read"; the fix merged the SAME day, first 0.917 nightly is 07-11) plus a missing dark-warn contrast ratio. Both fixed (hero rewritten, A5 ledger row updated with docs/nightly/2026-07-11.md:8, 11.22:1 added in three files); re-review PASS with all six A6 commit hashes independently resolved.

**Phase 2 sign-off: complete, 2026-07-16.**

### Phase 3 - Landing page

- launch/site/index.html: single self-contained file, zero build step (tokens inlined, data-URI favicon, system fonts, no JS); README documents `open` and an http.server one-liner. Live CI badges point at the three real workflow files and rendered green in the screenshots.
- Screenshot pass 1 found real horizontal overflow at 390px (grid min-width:auto); fixed with `.grid2>*{min-width:0}` and re-verified programmatically (scrollWidth == clientWidth, zero uncontained offenders). Final screenshots at 390px and 1440px viewed and archived in launch/site/screenshots/.
- Voice linter: index.html initially flagged `<!DOCTYPE` (false positive); linter now excludes HTML declarations/comments. Final run: OK.
- Completeness critic: PASS. Full number audit (every figure on the page vs its artifact: zero mismatches), all 21 repo links resolve, snippets diff clean against source, J anti-claims all honored. Five should-fix gaps, all applied: (1) "(inline comments mine)" on the predicate snippet, (2) gold-label scope at the arc's 1.000 mention, (3) ship-green scoped to "every eval-surface push to main", (4) "straight published snapshots" wording with the gaps note, (5) "per-PR fail-on-red" wording. Screenshots re-taken after the edits; linter re-run OK.
- Critic also flagged repo-internal rot outside this build's scope (ship-green.yml header says "7-doc/14-chunk" vs actual 8/16): logged for the owner alongside the retrieval-eval.yml `--viewers full` escape-hatch comment (Phase-1 flag) and branch protection (launch precondition 2).

**Phase 3 sign-off: complete, 2026-07-16.**

### Phase 4 - Social package

- Delivered: X launch thread (10 tweets) + 10 standalone posts (incl. required build-in-public weakness post X-09); 4 LinkedIn essays; Instagram "Receipts" feed concept + 8 finished 1080x1350 cards rendered via headless Chromium and visually reviewed (contact sheet committed); 4 TikTok scripts with exact commands per shot; two-week content calendar with all 19 entries pointing at existing asset files; per-platform voice-and-format notes.
- Dataviz discipline: card ig-06 plots keyword recall@5 verbatim from all 38 nightly JSONs (extracted, not illustrated), single series, selective labels, gap shown.
- Card overflow QA: programmatic scrollWidth/scrollHeight check on all 8 fixed-frame cards; 4 overflows found and fixed before rendering.
- Voice linter: all 11 social .md files exit 0 (output captured; one linter improvement: ban-list allow-marker used once in linkedin/voice-and-format.md).
- Completeness critic: VETO round 1 - caught a real J7 violation ("every night" over a gapped series) in IG-01 (card + caption) and T-01, plus 5 minor gaps (T-04 missing "likely" hedge, "red every night" family, an overclaimed no-shared-sentences assertion, cadence mismatch, ls count nit). All six fixed; ig-01/ig-07 re-rendered and re-viewed; PASS on re-review with the ig-07 deltas independently verified against both nightly files.

**Phase 4 sign-off: complete, 2026-07-16.**

### Phase 5 - Red team

- Crew: 4 fresh adversaries (skeptical staff engineer, buyer, brand critic, career auditor), explicitly barred from reading BUILD_LOG/tournament reasoning; 149 tool calls, ~418k subagent tokens, 11.4 min. They independently reran numbers, hit the GitHub API (branch protection, Actions history, repo metadata), measured post lengths, and viewed the rendered assets.
- Yield: 40 verbatim objections (3 kill, 26 major, 11 minor), all in launch/RED_TEAM.md with dispositions. Highlights this build had missed: the curated badge row (the one red workflow was the one omitted), the IG-06 chart drawing seven weeks of failure in pass-green, the unledgered founder bio on a page that dares readers to find an unreceipted claim, the E6 fail-open-on-infra-failure path, the 18-night June nightly outage (diagnosed via the Actions API: ran and failed at the seed step nightly, 06-01..06-18), the launch/ dir being one push away from publishing the war room, and 49 Co-authored-by: Claude trailers that the radical-honesty copy never mentioned.
- Fix pass: 31 fixed in-package (copy across site/THESIS/claims/GUIDELINES/social, ig-01/04/06/07/08 cards re-rendered with semantic chart colors, X banner re-rendered with the J15 scope, favicon sub-24px variant, new L-05 LinkedIn post, new claims sections K/L, new datasheet errata PV-E8/PV-E9, calendar hard-gated with a confession budget); 6 accepted as publicly-stated limits; 3 partial judgment calls logged in the dispositions (aphorism ration, no-rename, unpriced-not-deleted pricing). THESIS launch preconditions grew from 4 to 8, each with an action and done-when.
- External calls this phase: GitHub API reads (workflows list, run history for retrieval-eval-nightly and permissions-scale-eval, run jobs for one June failure, branch-protection and repo metadata via gh api by red-team agents). All read-only.
- Site re-screenshotted at 390/1440 after the fixes (overflow re-checked programmatically: clean); all card overflows re-checked; full-package voice lint: 18 files, zero failures.

**Phase 5 sign-off: complete, 2026-07-16.** (The red team is the §7 pass; its completeness function is the disposition table itself - nothing left TBD.)

### Phase 6 - Package

- URL liveness re-check (definition-of-done item 2): 54 unique fetched URLs re-curled (HEAD then GET fallback, browser UA); 51 return 200; the 3 non-200s were already documented as dead/blocked at original fetch time inside the evidence files. Record: launch/evidence/url-check-2026-07-16.txt.
- Placeholder sweep: repo-wide grep for lorem/TODO/FIXME/placeholder over launch/ finds only legitimate references to the eval knobs' documented placeholder status. No stubs.
- launch/recap.html written: five-minute business summary, links to every deliverable, the graded §9 table (13/13 PASS with evidence per row), external-calls disclosure, and a "what a skeptic should read first" section that leads with the red team's harshest verdicts.
- Link-check proof: `tools/link-check.sh recap.html site/index.html extras/datasheet.html social/instagram/cards.html extras/profile-assets/banners.html brand/marks/_preview.html` output: "ALL LINKS RESOLVE". Claims-ledger repo paths all resolve (docs/escalation-weekly/ allowlisted as cited-because-absent).
- Final voice-lint runs: 18 deliverable files + recap.html, zero failures (tools/voice-lint-final-run.txt).
- Recap screenshot taken and viewed (launch/recap-screenshot.png).

**Phase 6 sign-off: complete, 2026-07-16. Build complete.**

## Final cost/time accounting

- Orchestrated workflows: Phase-1 research (8 agents, ~381k subagent tokens), Phase-1 verify (4 agents, ~219k), Phase-2 tournament (8 agents, ~361k), Phase-5 red team (4 agents, ~418k); plus 3 synchronous completeness critics (~239k combined) and 1 re-review. Total subagent spend ~1.6M tokens across 28 agents, wall-clock ~45 minutes of agent runtime inside a single-day build.
- Phases 3, 4, and 6 were built inline by the orchestrator (voice-critical copy, browser render/verify loops).
- The §5 budget rule held: every fan-out was a single workflow, tournament capped at 5+3, red team at 4, and the context window survived to Phase 6.
