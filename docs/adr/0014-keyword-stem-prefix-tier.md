# ADR 0014: Keyword search stem-prefix tier (a third fallback tier)

- **Status:** Accepted
- **Date:** 2026-10-15
- **On:** ADR-0009 (keyword AND to OR fallback), ADR-0002 (workspace tenant isolation)

## Context

The weekly RAGAS gate went red on 2026-10-04 (issue #172): one of 60 questions in
one cell had no context, so coverage was 0.9833 against the fixed floor of 1.0.
The row is q40, "How quickly do you respond to my messages?", for the partial-access
viewer. That viewer's visible set holds the gold chunk (`customer-service-sop:0`,
"First response within 60 seconds") and retrieval returned nothing:

- Vector leg: the gold chunk scores cosine 0.2265 and the best chunk 0.276, both under
  the 0.3 `SEARCH_SIMILARITY_THRESHOLD`.
- Keyword leg: the english dictionary stems `respond` to `respond` but `response` to
  `respons`, so neither the AND query nor the exact-lexeme OR fallback of ADR-0009
  connects them.

The miss is not new (q40 x partial_access was empty in every snapshot since
2026-08-03). It surfaced because #157 made RAGAS scoring real and the coverage floor
refuses to let an unscorable row vanish.

## Decision

`keyword_search` gains a **third match tier** inside the SQL function:

- For each normalized query lexeme of 6 or more letters (`^[a-z]{6,}$`), drop the last
  character and prefix-match it (`respon:*`), OR-ed together, in the `simple` config so
  the truncated stem is compared to the chunk's stemmed lexemes as-is.
- Tier 1 (AND) and tier 2 (exact-lexeme OR) are unchanged and always rank above tier 3.
  Tier 3 only fills slots the first two tiers left empty, so the old rows are always an
  exact prefix of the new rows (same chunk, similarity and order). This is pinned across
  the whole golden set by `backend/test_keyword_stem_tolerance.py`.
- Short lexemes, digits and whole identifiers carrying digits or hyphens (`err-4102`,
  `acme-widget`) are never widened, so exact-token lookups stay exact.
  Letter-only parts of 6 or more letters inside a compound identifier do get the prefix tier: `WEBHOOK_RETRY_MAX` splits into `webhook`, `retri` and `max`, so `webhoo:*` is added, and `ACME-WIDGETS` adds `widge:*`.
  Those rows still rank below every tier 1 and tier 2 match.
- The visibility predicate and granting-principal projection are copied verbatim, so
  this is a recall change only. No `role` / `is_bot` (core invariant 1).

The vector similarity threshold is deliberately **not** changed: it is also the
escalation retrieval gate's per-row floor, so lowering it would move the deflection
safety gate.

Reversible: `supabase/rollbacks/20261015120000_keyword_search_stem_prefix_tier.down.sql`
restores the ADR-0009 definition verbatim. It lives outside `supabase/migrations/` so
the CLI never applies it as a forward migration.

## Consequences

- The tier changes the support-widget deflection path, not only the eval and the assistant.
  `run_deflection_pipeline` (`backend/escalation.py`) retrieves through `hybrid_search`, which calls this `keyword_search`.
  A tier-3 row can therefore enter the context that the deflection drafter and both content gates (faithfulness and answer completeness) consume, and so reach an auto-sent answer.
  The deterministic legs are unchanged: visibility is identical, and a keyword-only hit carries no cosine, so the escalation retrieval gate still reads such a turn as weak retrieval and defers exactly as before.
- The similarity scale in the keyword leg gains a third tier; consumers use it only for
  order and RRF rank, which is order-only.

## Evidence

Deterministic, against Postgres in a rolled-back transaction:

- `backend/test_keyword_stem_tolerance.py` pins q40 x partial viewer (zero rows before, the gold chunk after), the old rows as an exact prefix of the new rows across the 60-question golden set, and unchanged visibility.
- All 18 E7 escalation questions (`evals/retrieval/escalation_gold.yaml`) return identical keyword rows before and after the migration.
  This holds at match_count 5, 10, 20 and 50 over the seeded corpus as `chunk_text` splits it (16 chunks), which covers the deflection path's hybrid keyword pool (top_k 5 x 4 = 20).
  The tier fills no slot for any E7 question, so the retrieved context E7 scores on the seeded corpus is unchanged.

Open evidence gaps, both live and both paid:

1. The weekly RAGAS run has not been measured on this change; the branch's diagnostic run (38826620138) measured retrieval only, without importing RAGAS.
2. The live E7 P2/P3 measurement has not been made on this branch; that diagnostic run's E7 output was empty.

Both run once, together with the full weekly RAGAS run, when the Anthropic API limit is raised.

## Alternatives considered and rejected

- **Lower `SEARCH_SIMILARITY_THRESHOLD`.** Product-wide and moves the escalation gate.
- **Reword q40 or skip empty-retrieval rows in the eval.** Hides a real miss and loosens
  the coverage gate.
- **Trigram similarity.** Needs a new extension and index; the prefix tier reuses the
  existing GIN index.
