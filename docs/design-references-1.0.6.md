# Design references — SecureFlow 1.0.6 (playbook pass, 22 Nov 2026)

Collected before the playbook rebuild, per `~/workspace/design-playbook.md`.
Design from these notes, never from tool defaults.

## References (one line each: what to borrow)

1. **Mobbin — "Good Dashboard Design: What 2,108 Dashboards Do Differently"** (mobbin.com/blog/what-good-dashboard-design-looks-like) — borrow: a dashboard is a shield between the user and the mess; one verdict number up top (our compliance score), restraint in what to leave out.
2. **Mobbin search patterns (dashboard is the #1 searched term)** — borrow: dashboards that "read the data for you" — one plain sentence above the chart that says what it means (Fey/Origin pattern); our "Top Critical Findings" list does this job.
3. **Page Flows — Pipedrive onboarding recording** (pageflows.com/post/desktop-web/onboarding/pipedrive/) — borrow: the first-run path matters more than chrome; sign-in lands straight on the dashboard, no tour, no setup wizard.
4. **UI Sources / DESIGN.md — data-dense dashboard** (designmd.app/library/data-dense-dashboard/) — borrow: 8px spacing grid, color only for functional meaning (severity), tabular numerals, tables as first-class citizens.
5. **UX Encyclopedia — data tables & dashboards** (ux.detroit3d.com/patterns/data-tables-dashboards.html) — borrow: right-aligned numbers with tabular figures, row borders (not zebra), fixed headers, sort state visible.
6. **Dashboard-design skill patterns** — borrow: most critical KPI top-left, 4/8/12/16/24/32/48/64 spacing scale, row hover highlight, hairline borders.
7. **Torresburriel — dense data without the spreadsheet feeling** — borrow: group by question, not by chart type ("What's happening now?" / "Where are the problems?") — the dashboard already groups this way.
8. **Linear** — borrow: command-K density, keyboard-first (Esc closes drawer and modal), precise spacing, solid surfaces.
9. **Stripe Dashboard** — borrow: data-dense tables, honest numbers, clean empty/loading/error states.
10. **Vercel dashboard** — borrow: dark, sharp, confident; solid surfaces, one accent, no frost.

## Decisions (chosen before components, verified against the above)

- **Type:** Geist (display/body) + Geist Mono (labels, data, code). One strong family plus a mono for figures — tabular numerals on every stat, score and table number.
- **Palette:** near-black `#080b12` / warm paper `#F4F1E9`, one lime accent `#E7FF72`; severity colors (red/orange/amber/green) only where they mean something. No purple-blue, no gradients.
- **Icons:** Lucide only, one size language (14–18px, stroke 2).
- **Primitives:** MUI customized through the Nexus theme (restyled spacing, radii, colors — not stock); Radix-style patterns (dialog, drawer) hand-built on the same tokens.
- **Surfaces:** solid, never frosted — no backdrop blur, no dot-pattern background, no radial glow. Topbar, drawer, modal, tooltip and table headers are solid.
- **Motion:** only for state changes — drawer slide, modal scale, progress/bar fills, theme toggle. No staggered entrances, no shimmer, no breathing dots, no hover lifts.
- **Imagery:** none needed — this is a data console, not a landing page; no stock photos, no illustrations, no decorative patterns.
