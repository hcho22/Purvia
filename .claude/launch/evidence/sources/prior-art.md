# Prior art: permission-aware retrieval

Evidence log for the claim set "who else says permissions belong in the retrieval predicate".
All quotes are verbatim spans from pages actually fetched with WebFetch on 2026-07-16.

## https://www.glean.com/blog/secure-generative-ai-for-the-enterprise-requires-the-right-permissions-structure

Fetched: 2026-07-16 14:09 UTC

> "The information being input into the model strictly follows the permissioning rules set for each and every document."

> "Glean's AI assistant is fully permissions-aware and personalized, only sourcing information the user has explicit access to."

> "Without that guarantee, workers have no idea if confidential documents will stay confidential."

Why it matters: the market leader in enterprise search names and validates the category ("fully permissions-aware").
Segment signal: the article is framed around enterprise organizations (survey of 1000+ employee orgs); no public pricing on the page - Glean sells top-down enterprise, leaving the developer-kit segment open.

## https://www.credal.ai/products/enterprise-developer-rag-platform

Fetched: 2026-07-16 14:10 UTC

> "Every agent automatically inherits source permissions, so users only ever see data they are already authorized to access."

> "Permissions mirror source systems in real time with no extra configuration"

> "Credal is designed to meet the security, compliance, and governance standards large organizations require"

Why it matters: a second credible vendor whose core pitch is permission-inheriting RAG; explicitly positioned as "the governed registry for enterprise AI agents" for "large organizations" - again enterprise-segment, not an open developer kit.
(Note: https://www.credal.ai/enterprise-developer-rag-platform returned 404; the /products/ path is the live page.)

## https://www.osohq.com/post/right-approach-to-authorization-in-rag

Fetched: 2026-07-16 14:10 UTC

> "You ask for the top 10 results, filter out 8 that the user shouldn't see, keep 2, then ask for results 11-20"

> "Each iteration requires vector similarity search, 2 network hops, and a cycle through your for loop, turning what should be a fast operation into something that's slow and inefficient."

Also (paraphrase-adjacent verbatim spans from the same page): authorization should be "a first-class concern that can participate directly in query planning and execution", treated as "query logic, not post-processing".

Why it matters: Oso (an authz infra vendor) makes the explicit math/mechanics argument that post-filtering breaks top-k retrieval - the closest published articulation of "permissions belong in the retrieval predicate".

## https://www.pinecone.io/learn/rag-access-control/

Fetched: 2026-07-16 14:10 UTC

> "If different users have different levels of access to data, as they do in most real-world systems, your RAG pipeline must enforce those access boundaries."

> "In RAG pipelines, where content retrieval directly influences model output, fine-grained authorization must be enforced at every layer."

> "This capability introduces a serious risk: information leakage."

Why it matters: the leading vector-DB vendor teaches access-controlled RAG as a first-class pattern and names the leakage risk; notes post-filtering degrades with "a low positive hit-rate".

## https://authzed.com/blog/fine-grained-authorization-using-spicedb-for-retrieval-augmented-generation-rag

Fetched: 2026-07-16 14:10 UTC

> "users can only augment prompts with data they're authorized to access"

> "pre-filter vector database queries with a list of authorized object IDs, improving both efficiency and security"

Why it matters: AuthZed/SpiceDB (Zanzibar-style authz infra) prescribes pre-filtering the vector query - i.e., permissions inside the retrieval step, not after it.
They ship an open-source authz library for RAG (langchain-spicedb), but it is an authorization component, not a full retrieval kit with eval proof.

## https://learn.microsoft.com/en-us/microsoft-365/copilot/secure-govern-copilot-foundational-deployment-guidance

Fetched: 2026-07-16 14:10 UTC (served as the content of the Copilot oversharing-blueprint URL; canonical URL cited)

> "This deployment blueprint outlines the essential steps for establishing a secure and governed foundation for Copilot by remediating oversharing, implementing reliable guardrails, and fulfilling AI-related regulatory obligations"

> "grounding responses in the data users already have permission to access"

> "A practical framework to reduce Copilot exposure quickly, then harden your environment with enforceable defaults"

Why it matters: Microsoft itself publishes an official deployment blueprint whose first pillar is "Remediate oversharing" - first-party confirmation that AI-surfaced over-permissioned content is a real, named enterprise problem.

## https://petri.com/copilot-didnt-overshare-your-data-your-permissions-did/

Fetched: 2026-07-16 14:11 UTC

> "Permission sprawl that accumulated over years is now discoverable in seconds through plain-language prompts."

> "Copilot does not bypass security; it reflects it. The problem where Copilot is surfacing confidential data isn't a bug; it's a data management failure and we are all guilty of it."

Why it matters: reputable IT-pro press articulating the canonical horror story - AI assistants make latent permission sprawl instantly discoverable - which motivates permission-aware retrieval as a category.

## https://supabase.com/docs/guides/ai/rag-with-permissions

Fetched: 2026-07-16 14:11 UTC

> "you can restrict which documents are returned during a vector similarity search to users that have access to them"

> every "select" query on document_sections "will implicitly filter the returned sections based on whether or not the current user has access to them"

Why it matters: Supabase's official docs teach exactly the RLS-in-the-retrieval-query pattern (Postgres RLS + pgvector) - independent validation of the architecture, but as a tutorial, not a shipped product with eval proof.

## https://aws.amazon.com/blogs/security/authorizing-access-to-data-with-rag-implementations/

Fetched: 2026-07-16 14:11 UTC

> "RAG implementations return vector database results directly from the LLM, bypassing permission checks at the original data source."

> "LLMs should be considered untrusted entities because they do not implement authorization as part of a response."

> "Assume that any data passed to an LLM as part of a prompt could be returned to the principal."

Why it matters: AWS Security Blog reference architecture states the threat model in the sharpest terms - anything retrieved can leak, so authorization must gate what is retrieved; hyperscaler-grade validation of the category.

## Negative-space observation (not a fetched fact)

Across all nine sources: the enterprise vendors (Glean, Credal) sell closed platforms to large organizations; the infra vendors (Oso, AuthZed, Pinecone, Supabase, AWS) publish patterns, tutorials, and authz components.
None of the fetched pages shows an open developer kit that ships permission-aware retrieval end-to-end WITH published eval-gate proof of tenant isolation.
This is an inference from absence, not a verified fact - treat it as "inferred" in copy and phrase it carefully ("we haven't found...", not "nobody has...").
