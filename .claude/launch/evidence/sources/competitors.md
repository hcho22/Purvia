# Competitor landscape evidence: permission-aware, eval-gated RAG kits

Method note: every section below is a page actually fetched with WebFetch on 2026-07-16 (UTC times per section).
Quotes are the verbatim spans reported from the fetched page content.
Failed fetches are listed at the bottom.

## https://github.com/langchain-ai/langchain

Fetched: 2026-07-16 ~14:09 UTC

> LangChain is a framework for building agents and LLM-powered applications.

> Agent evals, observability, and debugging for LLM apps

(The second quote is from the LangSmith upsell block, a separate commercial product.)
Star count shown: 142k.
Why it matters: the biggest OSS framework's README makes no mention of permissions, access control, ACLs, or retrieval security, and no mention of evals or CI gates in LangChain itself.

## https://docs.langchain.com/oss/python/security-policy

Fetched: 2026-07-16 ~14:14 UTC

> Scope permissions specifically to the application's need. Granting broad or excessive permissions can introduce significant security vulnerabilities.

> Always assume that any system access or credentials may be used in any way allowed by the permissions they are assigned.

> It's best to combine multiple layered security approaches rather than relying on any single layer of defense.

Why it matters: LangChain's own security policy frames permissioning as the developer's job (scoping credentials, sandboxing).
Per-user document access control in retrieval and retrieval-predicate ACL enforcement are not mentioned anywhere on the page.

## https://github.com/run-llama/llama_index

Fetched: 2026-07-16 ~14:09 UTC

> LlamaIndex OSS (by LlamaIndex) is an open-source framework to build agentic applications.

> LlamaIndex is a "data framework" to help you build LLM apps.

Star count shown: 50.9k.
Why it matters: no mention of permissions, access control, or ACLs, and no mention of evals or CI gates in the README.

## https://github.com/deepset-ai/haystack

Fetched: 2026-07-16 ~14:09 UTC

> Open-source AI orchestration framework for building production-ready LLM applications in Python.

> Use built-in components for retrieval, indexing, tool calling, memory, and evaluation

Star count shown: 25.9k.
Why it matters: Haystack lists evaluation as a component but the README says nothing about permissions, access control, or CI gating.

## https://docs.haystack.deepset.ai/docs/evaluation

Fetched: 2026-07-16 ~14:13 UTC

> Judge how well your system is performing on a given domain, Compare the performance of different models, Identify underperforming components in your pipeline.

Evaluators listed: AnswerExactMatchEvaluator, ContextRelevanceEvaluator, DocumentMRR/MAP/RecallEvaluator, FaithfulnessEvaluator, LLMEvaluator, SASEvaluator, plus RagasEvaluator and DeepEvalEvaluator integrations.
Why it matters: the fetched evaluation docs contain no reference to CI pipelines, blocking gates, or security/permission evals.
Evaluation is framed as offline quality measurement, not a release gate.

## https://github.com/infiniflow/ragflow

Fetched: 2026-07-16 ~14:09 UTC

> RAGFlow is a leading open-source Retrieval-Augmented Generation (RAG) engine that fuses cutting-edge RAG with Agent capabilities to create a superior context layer for LLMs.

> Grounded citations with reduced hallucinations

Star count shown: 85.2k.
Why it matters: the highest-starred dedicated RAG engine's README mentions no permissions, ACLs, row-level security, multi-tenancy, evals, or CI gates.

## https://github.com/onyx-dot-app/onyx

Fetched: 2026-07-16 ~14:10 UTC

> Onyx is the application layer for LLMs - bringing a feature-rich interface that can be easily hosted by anyone.

> Role Based Access Control: RBAC for sensitive resources like access to agents, actions, etc.

> Onyx Enterprise Edition (EE) includes extra features that are primarily useful for larger organizations.

Star count shown: 30.9k.
Why it matters: Onyx is the closest OSS competitor on permissions, but RBAC and SSO are listed under the Enterprise (paid) section, and the README has no mention of evals or CI gates.

## https://docs.onyx.app/security/architecture/access_controls

Fetched: 2026-07-16 ~14:12 UTC

> Different access to documents is only available in the Enterprise Edition of Onyx.

Why it matters: document-level access control, the headline permission feature, is explicitly paywalled behind Onyx EE.
The fetched page does not describe how or where enforcement happens (e.g. at retrieval time in a query predicate).

## https://github.com/weaviate/Verba

Fetched: 2026-07-16 ~14:10 UTC

> Project Discontinued - Repository Archived

> Verba is designed and optimized for single user usage only. There are no plans on supporting multiple users or role based access in the near future.

RAG Evaluation is listed as "planned" in the feature table.
Star count shown: 7.7k.
Why it matters: Verba is archived, explicitly single-user with no access control, and its RAG evaluation feature never shipped.

## https://github.com/SciPhi-AI/R2R

Fetched: 2026-07-16 ~14:10 UTC

> R2R is an advanced AI retrieval system supporting Retrieval-Augmented Generation (RAG) with production-ready features.

> User & Access Management: Complete authentication & collection system

Star count shown: 7.9k.
Why it matters: R2R is the strongest OSS claim on access management among the kits checked, but it is framed as auth plus collections (container-level grouping), with no chunk-level ACL claim and no mention of evals or CI gates in the README.

## https://github.com/morphik-org/morphik-core

Fetched: 2026-07-16 ~14:11 UTC

> Morphik Core is a AI-native toolset for visually rich documents and multimodal data

Star count shown: 3.6k.
Why it matters: a representative newer (2025-era) entrant; its README mentions no permissions, access control, multi-tenancy, evals, or CI gates.

## https://www.vectara.com/pricing

Fetched: 2026-07-16 ~14:11 UTC

> Starting at $100K/ year

(SaaS tier; VPC is "Starting at $250K/ year", on-prem "Starting at $500K/ year".)
Why it matters: the flagship RAG-as-a-service platform prices at enterprise level, and its pricing page does not mention access control, RBAC, or entitlements at all.
This leaves a wide-open price gap under $100K/year.

## https://docs.vectara.com/docs/security/authorization/attribute-based-access-control

Fetched: 2026-07-16 ~14:12 UTC

> ABAC enables you to attach metadata to documents and apply filters at query time.

> A query without a `metadata_filter` returns all documents the API key can read.

> Filters are enforced per query, not at platform level

> Always construct the filter expression server-side from verified identity attributes. Never derive it from user-supplied input.

Why it matters: even the paid RAG platform's access control is opt-in metadata filtering that the customer's backend must construct correctly on every query; forgetting the filter returns everything.
This is fail-open by construction, the opposite of an ACL enforced inside the retrieval predicate.

## https://www.ragie.ai/pricing

Fetched: 2026-07-16 ~14:11 UTC

> $100 / month

(Starter tier; Pro is "$500 / month", Developer free, Enterprise custom.)

> Organize your documents into groups for more secure, faster, and precise retrieval. Perfect for multi-tenant SaaS apps and isolated knowledge bases.

Why it matters: Ragie's isolation story is "Partitions" (document grouping for tenants), not per-user or per-chunk ACLs, and its paid tiers are recurring $100-$500/month, versus a one-time $149-$249 kit.

## https://docs.langchain.com/langsmith/pytest

Fetched: 2026-07-16 ~14:14 UTC

> The LangSmith pytest plugin lets Python developers define their datasets and evaluations as pytest test cases.

> Track assertions in LangSmith and raise assertion errors locally (e.g. in CI pipelines).

Why it matters: the closest competitor claim to eval gating in CI comes from LangSmith, a commercial SaaS add-on, not an open kit, and the fetched page mentions no security, permission, or leak evals.

## Failed fetches

- https://docs.onyx.app/admins/connectors/permissioning/overview returned HTTP 404 (replaced by the access_controls page above).
- https://docs.langchain.com/oss/python/security returned HTTP 404 (replaced by the security-policy page above).

## Absence-of-evidence checklist (for the differentiation claim)

Pages checked for (a) chunk-level ACLs enforced in the retrieval SQL predicate, (b) zero-leak security evals as blocking CI gates, (c) a false-resolve ceiling:
LangChain README, LangChain security-policy docs, LlamaIndex README, Haystack README, Haystack evaluation docs, RAGFlow README, Onyx README, Onyx access-controls docs, Verba README, R2R README, Morphik Core README, Vectara pricing, Vectara ABAC docs, Ragie pricing, LangSmith pytest docs.
None of these pages claims (a), (b), or (c).
Caveat: this is absence on the pages fetched, not an exhaustive audit of every docs page of every project.

---

## Skeptic-pass addenda (fetched 2026-07-16, Phase-1 verification workflow)

These pages were fetched by the market skeptic specifically to try to falsify the absence claims (E10). None falsified the narrow triple (chunk-level ACLs in the retrieval SQL predicate + CI-blocking zero-leak evals); both framework pages document DIY per-query filter patterns, which sharpens the fail-open contrast.

### https://python.langchain.com/v0.2/docs/how_to/qa_per_user/
Fetched: 2026-07-16 (skeptic:market agent)
LangChain's official "per-user retrieval" how-to. Documents restricting retrieval per user via retriever-level metadata filters that the developer must apply on every query. This falsifies any claim that "LangChain has no permissions story" and is now cited in claims E1 as the DIY/fail-open pattern.

### https://developers.llamaindex.ai/python/examples/multi_tenancy/multi_tenancy_rag/
Fetched: 2026-07-16 (skeptic:market agent)
LlamaIndex's official Multi-Tenancy RAG example using `ExactMatchFilter(key="user")` per query, with a demonstrated cross-user denial. DIY, developer-applied, unenforced, no eval proof. Cited in claims E2.

### https://docs.onyx.app/admins/permissions/whats_changing
Fetched: 2026-07-16 (skeptic:market agent)
> "Document-level access is still controlled by connector access types (Public, Private, Synced) and group-to-resource associations, which remain the same."
Partially conflicts with the harsher access_controls page; Community Edition keeps connector-level Public/Private scoping. Cited as counter-source in claims E5.

### R2R full docs (r2r-docs.sciphi.ai/documentation/collections)
Attempted 2026-07-16: 404/moved. DeepWiki mirror describes owner/member collection permissions with document inheritance (collection granularity, not chunk). Recorded as unfetchable; claims E7 scoped accordingly.

### Not checked (recorded as a scope limit, claims E11)
AI support vendors (Intercom Fin, Decagon, Ada) publish resolution-rate metrics and containment controls and were NOT swept; false-resolve-ceiling uniqueness claims are scoped to RAG kits checked.
