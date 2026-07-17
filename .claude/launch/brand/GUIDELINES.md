# Purvia brand guidelines

Complete enough that a stranger can produce a new on-brand asset from this file alone.
Copy the tokens from `tokens.css` / `tokens.json`; use the marks in `marks/`.
Every factual claim in the canonical copy blocks carries an ID from `../evidence/claims.md`; do not write new factual claims without adding them to that ledger first.
Decided 2026-07-16 via the published tournament (`TOURNAMENT.md`, five blind pitches, three judges); the winning thesis is "The Receipts Are the Product" (61.7/65), with grafts from the runners-up noted inline.

## 1. Name

**Purvia**, coined from *purview*: the scope of what one is authorized to see and know.
The name is the differentiator: the product's core mechanic is enforcing each viewer's purview inside the retrieval predicate (graft from tournament pitch P2).
Decided in ADR-0011 (accepted 2026-07-14, merged 2026-07-15); the technical namespace deliberately stays `agentic-rag` (I1).

Wordmark casing: **purvia**, lowercase, monospace (see §5). Prose casing: **Purvia**.
Pronunciation: PUR-vee-ah.

Status disclosures that travel with the name (a receipts brand states its own risks):
- `purvia.ai` was available at registry level on 2026-07-16; `purvia.com` is parked by a third party since 2012, so typo/email traffic leaks until acquired (I2). Checked, not purchased.
- USPTO Class 9+42 clearance is pending. Known collisions: a same-name consumer AI face-swap app (highest risk, software), PURVIA WATER (beverage, negligible cross-class risk), a withdrawn 2008 sweetener application (I3). No branding spend before clearance.

## 2. Positioning statement

For production-minded engineers adding RAG to a real multi-user product, who can build a retrieval loop in a weekend but cannot cheaply prove it does not leak across users or auto-resolve what it should have escalated, Purvia is the MIT-licensed RAG kit that publishes its receipts: 38 nightly eval snapshots including seven weeks of its own dead retrieval leg, a zero-leak table scoped to its gold labels, a 30-plus-assertion API attack suite, and a buyer-set false-resolve ceiling, all rerunnable from a documented three-step path.
Unlike the LangChain and LlamaIndex per-user-filter tutorials, which ship a DIY pattern the developer must re-apply on every query, fail-open by construction, with no eval proving it holds.
(Claims: A9, A1, A3, B6, B11, C2, A13, E1, E2, E10.)

**Tagline:** The RAG kit that shows its work.

One-sentence version: Purvia is a permissions-aware RAG kit whose access-correctness and answer-safety claims are checked by evals wired into CI, not asserted in a README.

Name-to-thesis bridge (use wherever the name needs to earn its keep next to the receipts tagline, per red team BR-5): Purvia, from purview: the receipts prove each viewer's purview held.

## 3. Messaging hierarchy

Use in this priority order; each message carries its claim IDs and its mandatory caveat.

1. **Verification is the product, not a feature.** Every claim terminates in a committed artifact: 38 published nightly snapshots (say "38 snapshots," never "every night," J7), rerunnable in under ten minutes (A13, A9).
2. **The centerpiece receipt is a failure.** The lexical leg shipped dead; 33 straight published snapshots showed the leg dead (0.110 at the series start; 0.140 after the golden set was extended on 07-06, an instrument change, not a drift) before a competitor comparison prompted the first real read. Publication is not detection, and the copy says so (A1, A3, J4); the series also has an 18-night June outage the copy discloses first (A9). The fix: 0.140 to 0.917 keyword recall@5 on the extended 60-question set, verified in the same public series (A5, A7), plus the instrumentation: a lexical golden-set category measured on every run, and a one-sided alarm that only fires on real drops (D10). Never claim the lesson is fully operational; the broken scale benchmark (J2) is the standing counterexample the copy owns out loud. The zero-leak table stayed 1.000 throughout, with the A8 keyword-row asterisk attached (A8).
3. **Isolation is enforced in the predicate and attacked in CI.** Chunk-level ACLs inside the retrieval SQL under the viewer's JWT (B2, B3); the no-access table reads 1.000 in every cell, exactly as complete as the gold labels, which is why under-labeling is treated as a security defect (B6, J15); the assert has no tolerance knob and no config off-switch (B7, B8); AU4 throws forged JWTs and cross-tenant ACL holders at the API edge and fails the required CI check on any leak (B11, J14 wording).
4. **Answer safety is a number, not a vibe.** Deterministic escalate-vs-answer control flow, no model escalate() tool (C1); one buyer-set false-resolve ceiling, default 5%, enforced by the eval gate, never the request path (C2, C3, C4). Caveats first: threshold knobs are documented placeholders (J12); published LLM-judged history is thin (J6).
5. **No orchestration framework in the product** (D1, J8 wording). The pitch to the raw-SDK buyer: you will build the loop yourself, and you should; what you will not cheaply build is the proof (F2 confronted, per THESIS).

Reserved for LinkedIn and About pages (graft from pitch P3): the founder's framing, first person: ten years of hardware validation applied to AI systems: golden sets, non-regression baselines, one-sided alarms, fail-closed defaults.

## 4. Voice

Write like an engineer explaining a system to a peer who will check the work.

Rules (from the mission brief, §4, all hard):
- Short declarative sentences. Specific nouns. Real numbers with units and caveats.
- State a claim, then immediately state how the reader can verify it (a path, a command, a snapshot date).
- First person singular where the founder speaks. I built this. I found this. I have not proven this yet.
- Name the limitation before the reader finds it.
- Concrete over abstract: "a cross-workspace viewer with an ACL on the other tenant's document retrieves zero rows, asserted in CI" beats "enterprise-grade security."

Banned outright (the voice linter greps for these): revolutionize, unlock(s/ed/ing), supercharge, seamless, effortless, game-changing, cutting-edge, robust, powerful, blazing-fast, next-generation, "agentic" as a value claim, exclamation marks, emoji in body copy, em dashes (use plain hyphens), rhetorical-question openers, "Here's the thing", "Let that sink in", stacked one-line paragraphs for drama, ALL-CAPS emphasis. <!-- voice-lint:allow -->

House phrasings (use these exact formulations; they encode the anti-claims):
- "fails the required CI check" (never "blocks the merge," J14)
- "no comparable open kit we found ships chunk-level ACLs in the retrieval predicate with leak evals that fail the required CI check" (all three qualifiers, always, and the third uses the J14 wording, J13/E10)
- "the guarantee is as complete as the gold labels" (whenever the 1.000 table appears, J15)
- "38 published nightly snapshots" (never "every night," J7; the June gap is an 18-night outage, disclosed, A9)
- "the leg stayed dead throughout; the figure moved 0.110 to 0.140 when the golden set was extended on 07-06" (never "drifted"; the instrument changed, not the leg)
- "180 no-access runs per nightly run" (never "a night" as a streak; A14)
- "the vector and hybrid rows carried real attack pressure throughout; the keyword row proves less during the dead period" (whenever A8 is used)
- "a free-to-paid license against $100K-class platform contracts" (never "orders of magnitude cheaper," J16)

## 5. Canonical copy blocks

Hero (founder voice; the judge-corrected version):

> I shipped the lexical leg of hybrid retrieval dead.
> The first nightly snapshot, 2026-05-19, put keyword recall@5 at 0.110, and 33 straight published snapshots showed the leg dead - 0.110 at the series start, 0.140 after the golden set was extended on July 6 - before a comparison against another project made me actually read them.
> The fix landed the same day, and the next nightly snapshot, 2026-07-11, shows keyword recall@5 at 0.917 on the extended 60-question set (A5, A6).
> Every bad snapshot is still in the repo.
> That is the kit: you do not have to trust me, you rerun the harness.

Boilerplate (short): Purvia is an MIT-licensed, permissions-aware RAG kit. Chunk-level ACLs are enforced inside the retrieval SQL predicate and proven by zero-leak evals in CI; a deterministic escalation gate keeps the support bot under a buyer-set false-resolve ceiling. Raw OpenAI SDK + Pydantic; no orchestration framework in the product.

## 6. Logo and mark

Files: `marks/mark.svg` (light), `marks/mark-dark.svg`, `marks/lockup.svg`, `marks/lockup-dark.svg`, `marks/favicon.svg`.

The mark is a 3x3 grid of chunks with a rounded boundary enclosing the 2x2 subset the viewer is authorized to see.
Semantics, so new assets stay coherent: green chunks = within the viewer's purview (owner or ACL-granted); gray chunks = exist in the corpus, outside the purview; the boundary = the predicate, always drawn closed.
Never draw a green chunk outside the boundary; that is the leak the product exists to prevent.

Usage: minimum size 16px (favicon variant below 24px); clear space equal to one chunk (10/64 of mark width) on all sides; do not rotate, recolor outside the token palette, add gradients or shadows, or open the boundary stroke.
The lockup sets the wordmark in the mono stack at weight 600, lowercase; if a platform re-renders SVG text unreliably, use the mark alone plus "purvia" typed in the platform's own text layer in a monospace font.

## 7. Color

Copy `tokens.css` (it includes the dark theme and a `prefers-color-scheme` fallback). Ratios are computed WCAG 2.1.

| Token | Light | Ratio on paper | Dark | Ratio on dark paper | Role |
|---|---|---|---|---|---|
| paper | #FAFAF7 | - | #0B1220 | - | page background |
| surface | #FFFFFF | - | #111A2E | - | cards, tables |
| ink | #0B1220 | 17.9:1 | #E7EAF0 | 15.54:1 | body text |
| muted | #475569 | 7.25:1 | #CBD5E1 | 12.61:1 | secondary text |
| faint | #64748B | 4.55:1 | #94A3B8 | 7.3:1 | captions, 14px minimum |
| pass | #15803D | 4.8:1 | #4ADE80 | 10.74:1 | the accent: CI-green, verified, granted |
| fail | #B91C1C | 6.19:1 | #F87171 | 6.77:1 | failed checks, disclosed breakage |
| warn | #92400E | 6.78:1 | #FBBF24 | 11.22:1 | caveats, pending items |
| link | #1D4ED8 | 6.41:1 | #93C5FD | 10.38:1 | links |
| chunk | #94A3B8 | graphic only | #475569 | graphic only | out-of-purview grid chunks |

Rules: `pass` green is the only accent and it means something (a passing check, a granted chunk); never use it decoratively on non-verified content.
Buttons and chrome are not verdicts: CTAs, borders, and navigation use ink/link/border tokens, never `pass` (red team BR-4).
In charts, a series segment is green only where the underlying check or metric was healthy; failure periods render in `fail` or `chunk` gray.
`fail` red appears wherever we disclose our own breakage (the brand shows red cells; hiding them is off-brand).
One accent per surface; no gradients; no purple (the default AI-launch palette is the thing we are distinguishable from).

## 8. Type

Body: the system stack (`--pv-font-body`). Mono: the `ui-monospace` stack (`--pv-font-mono`).
No webfonts: zero external requests is on-brand (the product's pitch includes owning your stack, D1) and keeps every asset self-contained.

Mono is mandatory for: all metric numbers (0.917, 1.000, 5%), file paths, commands, dates-as-receipts, table cells, the wordmark.
Body size 16px, line-height 1.6; small text floor 14px (and then only `faint` or stronger).
Headings: body stack, weight 700, tight leading (1.15), no letter-spacing tricks.
Numbers always carry units and caveats in the surrounding sentence; a bare big number is off-voice.

## 9. Graphic language: receipts

The house visual is the **receipt**: a bordered `surface` panel, `--pv-radius` corners, containing a mono-set table or metric with (a) the artifact path it came from and (b) its caveat, both visible in the panel, set in `faint`.
Examples: the E4 1.000 table with "as complete as the gold labels" in the caption; the 0.140 to 0.917 pair with "extended 60-question set" attached.
A check glyph (pass green) may mark verified rows; a cross (fail red) marks disclosed breakage, and it is used honestly (the permissions-scale panel renders red until the benchmark is fixed, J2).
Grid-of-chunks motifs may decorate section dividers, always obeying §6 semantics.
No stock illustration, no 3D blobs, no glow, no mascots, no screenshots-of-dashboards-that-do-not-exist.

## 10. Applying the brand (worked example)

To make a new asset (card, slide, banner):
1. Paper background, ink text, one receipt panel as the focal point.
2. The receipt quotes a real artifact (path + number + caveat) from `../evidence/claims.md`; if the claim is not in the ledger, add it there first or do not ship the asset.
3. Mark in a corner at >= 24px with clear space; wordmark lowercase mono.
4. Run the voice linter (`../tools/voice-lint.sh`) over the asset's text.
5. Check contrast if you deviate from the token pairs (do not deviate).

## 11. What the brand never does

No invented users, logos, or testimonials (J9); no deployed-product screenshots (J10); no superlatives the ledger cannot cash (J1); no hiding of red cells (J2); no "agentic" as a selling word; no purple gradients; no urgency mechanics.
