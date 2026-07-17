# RAG-in-production pain - fetched sources

All sources below were fetched with WebFetch on 2026-07-16 (UTC times per section).
Quotes are short verbatim spans.

## https://news.ycombinator.com/item?id=40739982

Fetched: 2026-07-16 14:09:30 UTC

HN discussion of the Octomind "Why we no longer use LangChain" post.

> "the second you need to something a little original you have to go through 5 layers of abstraction just to change a minute detail" (commenter sc077y)

> "LangChain is _the_ definition of death by abstraction" (commenter SCUSKU)

> "Most LLM applications require nothing more than string handling, API calls, loops, and maybe a vector DB if you're doing RAG. You don't need several layers of abstraction" (commenter w4)

> "my god, LangChain isn't usable beyond demos. It feels like even proper logging is pushing it beyond it's capabilities" (commenter tkellogg)

Why it matters: engineers in their own words on framework abstraction churn; the raw-SDK exodus sentiment Purvia's "no framework tax" positioning targets.

## https://minimaxir.com/2023/07/langchain-problem/

Fetched: 2026-07-16 14:10:10 UTC

Max Woolf (minimaxir), "The Problem With LangChain".

> "The problem with LangChain is that it makes simple things relatively complex, and with that unnecessary complexity creates a tribalism which hurts the up-and-coming AI ecosystem as a whole."

> "LangChain is one of the few pieces of software that increases overhead in most of its popular use cases."

Why it matters: a widely-cited practitioner post naming the framework-overhead pain directly.

## https://www.yellowduck.be/posts/why-we-no-longer-use-langchain-for-building-our-ai-agents

Fetched: 2026-07-16 14:10:40 UTC

Mirror/summary of the Octomind post (the original octomind.dev domain no longer resolves as of this fetch).

> "replacing its rigid high-level abstractions with modular building blocks simplified our code base"

Why it matters: the canonical "we ripped LangChain out after 12 months in production" story; quote captures the rigid-abstraction complaint.

## https://hn.algolia.com/api/v1/items/48273068

Fetched: 2026-07-16 14:12:50 UTC

HN comment by hennell (canonical page https://news.ycombinator.com/item?id=48273068, verified via Algolia items API after HN rate-limited).

> "the rag setup would often ignore file access and permissions, so queries like 'List the highest paid members of x team sorted by salary' would just work"

> "The combo of rushing with a technology that isn't very easy to control, understand or securely limit is just mad to me."

Why it matters: a practitioner recounting the Microsoft 365 Copilot permissions-ignoring failure mode in plain words; exactly the leak Purvia's ACL-in-retrieval design prevents.

## https://hn.algolia.com/api/v1/search?query=%22RAG%22%20%22permissions%22&tags=comment&hitsPerPage=10

Fetched: 2026-07-16 14:12:00 UTC

HN Algolia comment search for RAG + permissions.

> "And RAG has many, many issues with document permissions that make the current approaches bad for enterprises" (commenter foobiekr, item 41698981)

Why it matters: blunt enterprise-practitioner framing of the permissions gap in current RAG approaches.

## https://www.pinecone.io/learn/rag-access-control/

Fetched: 2026-07-16 14:10:30 UTC

Pinecone (vector DB vendor), "RAG with Access Control".

> "If different users have different levels of access to data, as they do in most real-world systems, your RAG pipeline must enforce those access boundaries."

> "This capability introduces a serious risk: information leakage."

> "In RAG pipelines, where content retrieval directly influences model output, fine-grained authorization must be enforced at every layer."

Why it matters: a major vendor conceding the access-control problem is real and must be enforced at every layer.

## https://arxiv.org/abs/2408.04870

Fetched: 2026-07-16 14:12:10 UTC

ConfusedPilot paper (RAG security vulnerabilities in Microsoft Copilot).

> "we introduce ConfusedPilot, a class of security vulnerabilities of RAG systems that confuse Copilot and cause integrity and confidentiality violations in its responses"

> "we demonstrate a vulnerability that leaks secret data, which leverages the caching mechanism during retrieval"

Why it matters: documented research showing production RAG (Copilot) leaking data across trust boundaries.

## https://arxiv.org/abs/2509.14608

Fetched: 2026-07-16 14:12:20 UTC

"Enterprise AI Must Enforce Participant-Aware Access Control" (arXiv position paper).

> "We demonstrate data exfiltration attacks on AI assistants where adversaries can exploit current fine-tuning and RAG architectures to leak sensitive information by leveraging the lack of access control enforcement."

> "only a deterministic and rigorous enforcement of fine-grained access control during both fine-tuning and RAG-based inference can reliably prevent the leakage of sensitive data to unauthorized recipients"

Why it matters: independent support for deterministic, DB-enforced access control (Purvia's RLS + chunk_acl approach) over soft filtering.

## https://hamel.dev/blog/posts/evals/

Fetched: 2026-07-16 14:11:30 UTC

Hamel Husain, "Your AI Product Needs Evals".

> "Unsuccessful products almost always share a common root cause: a failure to create robust evaluation systems."

> "Evaluation systems create a flywheel that allows you to iterate very quickly. It's almost always where people get stuck when building AI products."

Why it matters: the canonical practitioner statement of "evals or it didn't happen".

## https://qaskills.sh/blog/rag-regression-testing-guide

Fetched: 2026-07-16 14:12:15 UTC

RAG regression testing guide (June 2026).

> "A retrieval-augmented generation system is never finished. You upgrade the embedding model, re-chunk the corpus, tweak a prompt, swap the LLM, add ten thousand new documents, and every one of those changes can silently degrade answer quality."

> "On every pull request that touches prompts, retrievers, models or the corpus, CI runs the eval and fails the build if any metric falls below its floor."

Why it matters: articulates silent quality drift and the CI eval-gate pattern Purvia ships (Phase-2 eval gates).

## https://www.cbsnews.com/news/aircanada-chatbot-discount-customer/

Fetched: 2026-07-16 14:12:05 UTC

CBS News on the Air Canada chatbot tribunal ruling (Feb 2024).

> "While a chatbot has an interactive component, it is still just a part of Air Canada's website." (tribunal member Christopher Rivers)

> "It makes no difference whether the information comes from a static page or a chatbot." (tribunal member Christopher Rivers)

Why it matters: the canonical legal precedent that a company owns what its support bot says; motivates escalate-over-hallucinate design.

## https://cloudsecurityalliance.org/blog/2024/06/05/the-risks-of-relying-on-ai-lessons-from-air-canada-s-chatbot-debacle

Fetched: 2026-07-16 14:12:45 UTC

Cloud Security Alliance analysis of the Air Canada case.

> "Companies cannot absolve themselves of responsibility for AI-generated interactions."

Why it matters: security-industry framing of the trust/liability pain around confident-but-wrong support bots.
