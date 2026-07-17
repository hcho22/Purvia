# Naming evidence: domain availability + trademark sanity search

Method: DNS delegation check (`dig +short NS/A`) plus registry `whois` for the decisive domains, run locally on 2026-07-16.
Availability was CHECKED ONLY - nothing was purchased or registered (guardrail §3.1).
Trademark search: web search + page fetches on 2026-07-16. This is a directional sanity search, not formal clearance; ADR-0011 already records that a paid USPTO Class 9 + 42 clearance is pending.

## Domain availability (checked 2026-07-16)

| Domain | Signal | Reading |
|---|---|---|
| purvia.ai | Registry whois (`whois -h whois.nic.ai purvia.ai`): `Domain not found.` (registry timestamp 2026-07-16T14:05:42Z) | **Available** (registry-confirmed) |
| purvia.com | whois: `Creation Date: 2012-05-29T18:47:28Z`, Registrar TurnCommerce/NameBright; DNS parked on namebrightdns.com | **Parked since 2012** (matches ADR-0011: "purvia.com is parked (registered 2012)") |
| purvia.dev | No NS delegation | Likely available (DNS proxy; registry whois returned no record block) |
| glassbox.ai / glassbox.com | Both delegated and serving (glassbox.com behind Cloudflare) | **Taken.** Glassbox is an established session-replay analytics company - direct software-class collision for "GlassBox" |
| retrievault.com / .ai | No NS delegation | Likely available |
| verity.ai / verity.com | verity.ai on afternic.com nameservers; verity.com on `thisdomain.forsale` | **For sale / premium** - acquisition cost, plus "Verity" was a well-known enterprise-search company (name history in the exact category) |
| assert.dev / assert.ai | Both delegated (AWS DNS) | **Taken** |
| ragvault.com | Delegated (domaincontrol.com) | Taken/parked |
| ragvault.ai | No NS delegation | Likely available |
| groundwork.dev / .ai / .com | All delegated | **Taken** |

## Trademark sanity: "Purvia"

- https://ised-isde.canada.ca/cipo/trademark-search/1403254?wbdisable=true
  Fetched: 2026-07-16 (WebFetch)
  > "(1) Tabletop sweeteners; sugar substitutes" - Nice classes 1 and 30. Owner: Whole Earth Sweetener Company LLC. Status: "WITHDRAWN BY OWNER" ... withdrawal occurred on August 25, 2008.
  Why it matters: the only CIPO "PURVIA" record is a withdrawn 2008 sweetener application in food classes - no software-class conflict.
- USPTO records surfaced by web search (2026-07-16): "PURVIA WATER - Purvia Drinks LLC Trademark Registration" (uspto.report serial 99287353; also listed on trademarks.justia.com). Both pages returned HTTP 403 / Cloudflare challenges to automated fetch, so the class detail could not be quoted from the page itself. Reading (marked **inferred**): a beverage mark ("PURVIA WATER"), not software Class 9/42.
- ADR-0011 (`docs/adr/0011-product-name.md`) additionally discloses: "A consumer 'Purvia' AI face-swap app exists in a different class; it should still be formally cleared before branding spend."

**Net (inference, reasoning shown):** no identified collision in software/SaaS classes for "Purvia"; known collisions are beverage (PURVIA WATER), a withdrawn food-class application, and a consumer face-swap app noted by ADR-0011. Formal USPTO Class 9 + 42 clearance remains pending and is carried as a disclosed caveat in the brand guidelines. "GlassBox" and "Verity" have material collisions; "Assert" and "Groundwork" have no exact-match domains available in preferred TLDs.
