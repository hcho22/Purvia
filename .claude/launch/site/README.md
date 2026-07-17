# Purvia landing page

Zero build step. `index.html` is fully self-contained (tokens inlined, favicon as a data URI, system fonts, no webfonts, no JS).

Run it either way:

```bash
open launch/site/index.html          # or double-click it
# or, if you prefer a server:
python3 -m http.server 8080 --directory launch/site
```

Notes:

- The three CI badges in the hero load live from GitHub Actions and link to the workflow files in the repo. Offline they degrade to their alt text; everything else on the page renders with zero network access.
- Screenshot-verified at 390px and 1440px; see `screenshots/`. A horizontal-overflow bug at 390px (grid `min-width:auto`) was found in the first screenshot pass and fixed (`.grid2>*{min-width:0}`).
- Every factual claim on the page traces to `../evidence/claims.md`; the "What this does not do yet" section is required content, not filler.
