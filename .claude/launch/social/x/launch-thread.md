# X launch thread

Status: DRAFT ONLY - nothing posted (guardrail §3.2).
10 tweets. Every claim resolves to a repo path a "source?" reply can open.
Claim IDs from `launch/evidence/claims.md` in brackets after each tweet (strip before posting).

---

**1/**
I shipped the lexical leg of my hybrid retrieval dead.

My own nightly eval published keyword recall@5 = 0.110 on May 19. It stayed on the public record for seven weeks. I never read it.

This thread is the story of Purvia, the RAG kit that shows its work.

[A1, A3]

**2/**
Purvia is an MIT-licensed, permissions-aware RAG kit. Chunk-level ACLs enforced inside the retrieval SQL predicate, zero-leak evals in CI, and a support bot with a false-resolve ceiling you set.

Raw OpenAI SDK + Pydantic. No orchestration framework in the product.

github.com/hcho22/Purvia

[D1, D6, B2, C2]

**3/**
The receipt: docs/nightly/2026-07-09.md.

keyword recall@5: 0.140
keyword paraphrase: 0.000
hybrid MRR 0.786 vs vector 0.796

The dead keyword leg was dragging hybrid below its own vector leg. Hybrid should never lose to its best single leg.

[A1, A2]

**4/**
Nobody noticed for seven weeks, for two reasons, both mine. Nobody is paged on a nightly report, so nobody read it. And my non-regression alarm was two-sided: it flagged improvements as failures, so it was red for reasons nobody needed to act on. An alarm that always fires is no alarm.

[A3, D10]

**5/**
What finally made me look: comparing my repo against someone else's project on July 10.

Same day: root cause named (websearch_to_tsquery ANDs every term; one missing word zeroes the match), fix PRD filed, SQL fix merged. The fix is deliberately boring: AND first, OR fallback. docs/adr/0009.

[A3, A4, A6]

**6/**
The next nightly, 2026-07-11: keyword recall@5 = 0.917.

By 07-15: hybrid 0.950 vs vector 0.875 on recall@5, at or above vector in every category.

Caveat I owe you: hybrid MRR still trails vector on paraphrase, 0.767 vs 1.000. That cell is not done.

[A5, A7, J3]

**7/**
The fix that matters is not the SQL. It is the instrumentation:

- a lexical golden-set category, so this leg is measured on every run
- a one-sided alarm that only fires on real drops (US-118)

The bug cost one migration. The alarm that failed to catch it cost a redesign.

[A4, D10]

**8/**
Meanwhile, the thing that never broke: the zero-leak table.

Every no-access run, every mode: 1.000 (scope: labeled gold chunks; under-labeling is a security defect by contract). One asterisk I owe you: a keyword leg retrieving at 0.11 barely stresses the ACL, so that row proves less during the dead period. Vector and hybrid carried real pressure throughout.

[A8, B6, J15]

**9/**
The other receipts, all in the repo:

- ACL check inside match_chunks, under the viewer's JWT
- E6: second workspace, identical corpus, ACL granted, membership withheld: recall 0.0 across the boundary
- AU4: 30+ exact assertions of forged JWTs and cross-tenant attacks
- a 5% false-resolve ceiling on the support bot, enforced by the eval gate

[B2, B9, B11, C2]

**10/**
What it does not do yet:

- the 10k-chunk scale benchmark is currently broken (red since 06-19; the red badge is on the site)
- the nightly itself was down 18 nights in June and I missed that too
- 8-doc demo corpus; the harness is the product, not the metric values
- zero users. You would be early.

Receipts: github.com/hcho22/Purvia

[J2, A9, A12, J9]
