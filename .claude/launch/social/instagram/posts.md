# Instagram posts (8)

Status: DRAFT ONLY - nothing posted (guardrail §3.2).
Each post = one rendered card in `cards/` + caption + alt text + hashtags.
Hashtags go in the first comment, not the caption (cleaner caption, same reach).
Claim IDs in brackets (strip before posting).

---

## IG-01 - `cards/ig-01.png`

**Caption:** My own nightly eval published this failure in 33 straight snapshots across seven weeks, and I did not read one of them. Keyword recall@5 was 0.110 at the series start and 0.140 after the golden set was extended on July 6; the leg stayed dead throughout, and it dragged hybrid retrieval below its own vector leg. The fix took one day once I finally looked. The record of me not looking is still in the repo, all 38 snapshots of it. Link in bio. [A1, A3, A5, A9]

**Alt text:** Card titled "My eval published my failure in 33 straight snapshots." A table shows keyword recall at five drifting from 0.110 to 0.140 while hybrid MRR trailed vector, then jumping to 0.917 after the fix on July 11, with hybrid MRR 0.858 above vector 0.813. Source: the nightly eval files in the Purvia repo.

**First comment hashtags:** #rag #retrievalaugmentedgeneration #llm #evals #mlops

## IG-02 - `cards/ig-02.png`

**Caption:** The quietest way to break RAG permissions is to bolt them on after retrieval. Retrieve top-10, drop what the viewer cannot see, and at 5% visibility the expected visible result is half a chunk. Multi-hop questions need two. The fix is structural: put the ACL inside the SQL predicate, so the planner only ever ranks what the viewer is allowed to see. Worked math in docs/permissions-aware-rag.md. [B13]

**Alt text:** Card titled "Post-filtering permissions breaks retrieval. Quietly." Below, the formula: expected visible chunks equals k times selectivity, which is 10 times 0.05, which is 0.5 chunks, with 0.5 highlighted in red.

**First comment hashtags:** #rag #postgres #pgvector #accesscontrol #softwareengineering

## IG-03 - `cards/ig-03.png`

**Caption:** This is where Purvia's permissions actually live: inside match_chunks, in SQL, under the viewer's JWT. Owner OR chunk-level ACL, AND tenant membership resolved from auth.uid(). The backend cannot pass a tenant id, which means the backend cannot forget to pass one. A missing filter narrows; it never widens. [B2, B3, B4]

**Alt text:** Card titled "Permissions live inside the SQL," showing the actual SQL predicate: owner or chunk ACL check, and an EXISTS clause against workspace membership keyed on auth dot uid. Source: the match_chunks migration file, with a note that comments are the author's.

**First comment hashtags:** #sql #postgres #supabase #rowlevelsecurity #rag

## IG-04 - `cards/ig-04.png`

**Caption:** On every nightly run, 180 retrievals execute as a viewer who is allowed to see nothing relevant. The table reads 1.000 in every cell: zero labeled gold chunks returned, every mode, pre- and post-filter. The scope: the guarantee is exactly as complete as the gold labels, which is why the golden-set authoring guide treats an unlabeled relevant chunk as a security defect. [B6, J15, A14]

**Alt text:** Card titled "180 no-access runs per nightly. Zero labeled chunks leaked." A table shows vector, keyword, and hybrid rows, each 1.000 pre-filter and post-filter, in green.

**First comment hashtags:** #security #rag #evals #multitenancy #saas

## IG-05 - `cards/ig-05.png`

**Caption:** My support bot has no escalate() tool. The model drafts; deterministic gates decide. Weak retrieval escalates before a single token is drafted. A strong draft still has to pass a faithfulness gate, and a judge timeout counts as unfaithful. The buyer sets one risk number, a 5% false-resolve ceiling, and the weekly eval fails loudly if the measured rate crosses it. [C1, C2, C4, C7]

**Alt text:** Card titled "The bot never decides to escalate. The gates do." A code-style diagram: retrieve once, then retrieval gate; weak leads to escalate now in red; strong leads to draft, then faithfulness gate; faithful leads to answer in green; unfaithful leads to escalate in red.

**First comment hashtags:** #aisupport #chatbot #llm #customersupport #engineering

## IG-06 - `cards/ig-06.png`

**Caption:** Most RAG kits cannot draw this chart about themselves. This is keyword recall@5 across every nightly snapshot my CI published: dead at 0.110, a step to 0.140 when the golden set was extended on July 6, then the July 10 fix, then 0.917. The values are plotted verbatim from the committed JSONs, including the gap where the nightly itself was down for 18 nights and I missed that too. [A1, A5, A9]

**Alt text:** Card titled "What most RAG kits cannot tell you about their own retrieval." A line chart of keyword recall at five over time: the failing period drawn in red near 0.110 from May 19, a dashed gap, 0.140 by July 9, a dashed vertical line marked fix July 10, then the line turns green and jumps to 0.917, holding through July 15.

**First comment hashtags:** #dataviz #evals #rag #mlops

## IG-07 - `cards/ig-07.png`

**Caption:** Ten years in hardware validation and I still shipped this: a non-regression alarm that flagged improvements as failures. Red on every snapshot it published, so everyone learned to ignore the column, and a genuinely dead retrieval leg hid in plain sight for seven weeks. The rewrite is one-sided: only a real drop past tolerance fires. The bug cost one migration. The alarm that failed to catch it cost a redesign. [D10, A3]

**Alt text:** Card titled "An alarm that always fires is no alarm." Two panels: before, a two-sided check marking improvements of plus 0.210 with red crosses; after, the one-sided US-118 check marking stable metrics with green checks.

**First comment hashtags:** #testing #qualityengineering #hardware #validation #mlops

## IG-08 - `cards/ig-08.png`

**Caption:** My 10k-chunk scale benchmark is broken right now: 0.000 in every cell since June 19, red in public until I fix it. Hybrid MRR still trails vector on paraphrase. The demo corpus is 16 chunks. Users: zero. If a claim of mine ever contradicts this list, the repo wins and I fix the claim. [J2, J3, A12, J9]

**Alt text:** Card titled "What this does not do yet," lead line "If a claim of mine ever contradicts this list, the repo wins and I fix the claim," listing four items: scale benchmark broken with 0.000 cells since June 19, paraphrase MRR where hybrid 0.767 trails vector 1.000, a demo corpus of 8 documents and 16 chunks, and zero users, revenue, and testimonials.

**First comment hashtags:** #rag #evals #opensource
