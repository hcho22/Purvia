# X standalone posts (10)

Status: DRAFT ONLY - nothing posted (guardrail §3.2).
Each post is reply-guy-proof: the source is a repo path or a fetched URL already in `launch/evidence/`.
Claim IDs in brackets (strip before posting). Posting order and dates: `../content-calendar.md`.

---

**X-01 - the post-filter math**
Post-filtering RAG permissions fails quietly. A viewer who sees 5% of the corpus, top-10 retrieval: expected visible chunks = 10 x 0.05 = 0.5. Half a chunk. Multi-hop needs two.
The fix is the ACL inside the SQL predicate. Math: docs/permissions-aware-rag.md
[B13]

**X-02 - fail-open vs fail-closed**
Vectara's own docs: "A query without a metadata_filter returns all documents the API key can read."
That is per-query, developer-remembered access control. Forget once, leak once.
In Purvia the ACL is inside match_chunks, resolved from the JWT. There is nothing to remember per query.
[E8, B2, B4]

**X-03 - the un-downgradable verdict**
My favorite line of code in my repo this year is an error message: "security gates are pinned fail and cannot be downgraded; delete the eval to remove it."
A zero-leak verdict has no tolerance knob and no config off-switch. Burying one takes a code-visible PR diff. evals/gate/declaration.py
[B7, B8]

**X-04 - the E6 design**
To eval tenant isolation, seed a SECOND workspace with an identical copy of the corpus. Grant the viewer ACLs on both. Membership in only one.
Assert recall@10 == 0.0 across the boundary, with a positive control so a vacuous pass fails too. evals/retrieval/e6.py
[B9]

**X-05 - escalation without disclosure**
When my support bot escalates because the asker lacks access, the escalation constructor's output is asserted byte-for-byte identical to the ordinary "let me get a human" deferral, across every escalation reason.
Escalating must never disclose that restricted content exists. evals/retrieval/e7_runner.py
[C6, SE-11 scope]

**X-06 - deflection is derived, not stored**
No resolved_by_bot column. A conversation resolved with escalated_at IS NULL means the bot handled it alone, and escalated_at is stamped by a Postgres trigger callers cannot fake.
If your KPI can be written by the thing it measures, it is not a KPI. supabase/migrations/20260623130000
[C9]

**X-07 - the reranker decision**
Measured on my golden set: LLM reranking wins adversarial MRR by +0.052. It also costs ~1.2s median per query.
Default stays RERANKER=none, and the bake-off doc says why, with the source JSONs committed next to it. docs/reranker-bakeoff.md
[A11]

**X-08 - determinism decides CI placement**
Rule in my eval harness: only deterministic gates may fail a PR check. LLM-judged gates run weekly.
Declaring an LLM-judged gate as per-PR fail-on-red is a structural load error, not a lint warning. evals/gate/placement.py
A judge wobble should never red-bar an innocent merge.
[C11]

**X-09 - the broken one (required weakness post)**
Currently broken in my repo, in public: the 10k-chunk permissions scale benchmark has published 0.000 in every cell since June 19. Likely cause: a migration orphaned the benchmark's synthetic viewers.
The alarm fired into a void for weeks. I found it while writing launch copy. docs/permissions-scale-nightly/
[J2]

**X-10 - the cross-family judge**
OpenAI writes the answers. A Claude model grades them. The grader should not share the writer's blind spots, and the Anthropic key is never read by the live backend: it exists only for evals.
evals/retrieval/runner.py
[D4]
