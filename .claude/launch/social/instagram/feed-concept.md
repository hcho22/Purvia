# Instagram feed concept: "Receipts"

Status: DRAFT ONLY - nothing posted (guardrail §3.2).

**The concept.** Every post is one receipt: a single number, table, or code block from the repo, rendered as a card in the brand system (paper background, ink text, mono numbers, one green accent that always means "verified"). The grid alternates confession cards (fail red) with proof cards (pass green), because the feed's thesis is that the two are the same discipline. No stock imagery, no gradients, no faces, no screenshots of dashboards. Numbered like lab records: RECEIPT 001, 002, ...

**Why this fits the platform.** Instagram's engineering audience saves and shares single-idea explainer cards. The cards are designed to be legible in the feed (72px headline, 30px+ body) and to survive being screenshotted out of context: every card carries its own source path and the repo URL in the footer.

**Production.** Cards are generated locally from `cards.html` (brand tokens, system fonts) and rendered to 1080x1350 PNG via headless Chromium. To regenerate: serve `launch/` with any static server, open `social/instagram/cards.html`, screenshot each `.card` element. All eight PNGs in `cards/` were rendered and visually reviewed on 2026-07-16 (`cards/_contact-sheet.png`).

**Cadence.** Two to three cards per week, alternating proof and confession, ordered so the dead-leg story (001) runs first and the "not yet" card (008) lands within the first two weeks, not buried at the end.
