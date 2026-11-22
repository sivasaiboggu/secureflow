# Design tokens — SecureFlow 1.0.7 (master-prompt polish, 22 Nov 2026)

Built on the 1.0.6 playbook pass (`docs/design-references-1.0.6.md`).
Same identity, deepened — nothing redesigned from scratch. References
for this round: Linear (density, solid surfaces, one accent), Stripe
Dashboard (data-dense tables, honest numbers, plain empty states),
Vercel dashboard (dark, sharp, confident).

## Section 1 brief (filled)

- **Name:** SecureFlow
- **Type:** dashboard / security tool
- **What it does:** scans a cloud setup, lists real vulnerabilities,
  scores compliance against CIS controls, and writes Terraform fixes.
- **Target user:** a small team that cannot afford an enterprise
  scanner, and needs to know what is open and what to fix first.
- **Core promise:** a real scan with real findings and a real
  compliance number — the score is a pass rate over the 8 CIS
  controls evaluated by that scan, never a default.
- **Tone:** precise, technical, plain.
- **Platforms:** web (React + FastAPI).
- **Must-have features:** demo and real AWS scans, findings with
  Terraform remediation, compliance overview, analytics forecast,
  cloud-account and user management.

## Signature idea: the ledger line

Every section opens the same way: a mono uppercase label, a hairline
rule, and a tabular numeral. The lime accent appears only as a 2px
rule, a score bar, or a primary action — under 10% of any screen.
The idea is repeated with discipline: dashboard stat cards carry a
2px top rule in their meaning colour, the framework bars are flat
fills at 8% opacity, and the login page now ends its brand panel
with the same ledger strip (hairline rule, 2px lime segment, real
numbers) instead of the decorative tab labels that used to sit there
and do nothing.

## Accent

One accent: lime. Dark theme `#E7FF72`, oklch(0.955 0.167 117.8) —
near-white lightness with a strong chroma, so it reads as a signal
colour on the near-black background and holds 17.76:1 as text.
Light theme the accent steps down to `#4D7C0F`,
oklch(0.532 0.141 131.6) for bars and `#46700E`,
oklch(0.495 0.130 131.3) for text, because the bright lime fails
contrast on paper. Cyan `#06B6D4` is kept only as the secondary
accent for the scans stat and running states; it is never a second
brand colour. Severity colours (red/orange/amber/green) are
functional only — they mean a severity, never decoration.

## Type

Geist (display/body) + Geist Mono (labels, data, code). Tight
heading tracking (-0.03em to -0.05em), body 13-14px in the console
with 1.5-1.7 line height, tabular numerals on every stat, score and
table number so values do not jitter when they change.

## Tokens (OKLCH canonical, hex fallback in `index.css`)

Full machine-readable set: `frontend/src/theme/tokens.json`.

| token | dark hex | dark OKLCH | light hex | light OKLCH |
|---|---|---|---|---|
| bg | #080b12 | oklch(0.150 0.016 265.8) | #F4F1E9 | oklch(0.958 0.011 89.7) |
| surface | #0e121b | oklch(0.183 0.020 265.9) | #ffffff | oklch(1.000 0.000 0.0) |
| surface-strong | #131824 | oklch(0.210 0.025 266.8) | #ffffff | oklch(1.000 0.000 0.0) |
| text-primary | #F4F0E8 | oklch(0.956 0.011 84.6) | #171B22 | oklch(0.221 0.015 261.6) |
| text-muted | #9EA3A0 | oklch(0.711 0.007 160.0) | #5A615C | oklch(0.485 0.012 154.8) |
| accent | #E7FF72 | oklch(0.955 0.167 117.8) | #4D7C0F | oklch(0.532 0.141 131.6) |
| accent-text | #E7FF72 | oklch(0.955 0.167 117.8) | #46700E | oklch(0.495 0.130 131.3) |
| accent-secondary | #06B6D4 | oklch(0.715 0.126 215.2) | #0E7490 | oklch(0.520 0.094 223.1) |
| sev-critical | #f87171 | oklch(0.711 0.166 22.2) | #DC2626 | oklch(0.577 0.215 27.3) |
| sev-high | #fb923c | oklch(0.758 0.159 55.9) | #C2410C | oklch(0.553 0.174 38.4) |
| sev-medium | #fbbf24 | oklch(0.837 0.164 84.4) | #8A6100 | oklch(0.522 0.108 79.7) |
| sev-low | #4ade80 | oklch(0.800 0.182 151.7) | #166534 | oklch(0.448 0.108 151.3) |

## Contrast table (WCAG, computed — not guessed)

Every text pair passes AA (4.5:1). The light theme failed this
check before 1.0.7: accent text was 4.42:1 on paper, high was 3.56:1
and medium 2.94:1 on white, low 3.30:1 — all four were deepened
(see the table). The accent bar row is a graphic (bar fill, trend
line), judged against 3:1, not 4.5:1.

| theme | pair | ratio | use |
|---|---|---|---|
| dark | text-primary on #080b12 | 17.32:1 | body text on app bg |
| dark | text-primary on #0e121b | 16.48:1 | body text on card |
| dark | text-muted on #080b12 | 7.69:1 | mono labels on app bg |
| dark | text-muted on #0e121b | 7.32:1 | mono labels on card |
| dark | text-body 75% on #080b12 | 9.82:1 | secondary text |
| dark | accent on #080b12 | 17.76:1 | lime links/scores on bg |
| dark | accent on #0e121b | 16.90:1 | lime links/scores on card |
| dark | cyan on #080b12 | 8.11:1 | secondary accent text |
| dark | sev-critical on #0e121b | 6.77:1 | critical badges/text |
| dark | sev-high on #0e121b | 8.28:1 | high badges/text |
| dark | sev-medium on #0e121b | 11.22:1 | medium badges/text |
| dark | sev-low on #0e121b | 10.75:1 | low badges/text |
| dark | button text #080b12 on accent | 17.76:1 | primary button label |
| light | text-primary on #F4F1E9 | 15.30:1 | body text on app bg |
| light | text-primary on #ffffff | 17.27:1 | body text on card |
| light | text-muted on #F4F1E9 | 5.64:1 | mono labels on app bg |
| light | text-muted on #ffffff | 6.37:1 | mono labels on card |
| light | accent-text on #F4F1E9 | 5.19:1 | lime text on bg |
| light | accent-text on #ffffff | 5.86:1 | lime text on card |
| light | accent-bar on #F4F1E9 | 4.42:1 | bar/line graphic (3:1 bar) |
| light | accent-bar on #ffffff | 4.99:1 | bar/line graphic (3:1 bar) |
| light | sev-critical on #ffffff | 4.83:1 | critical badges/text |
| light | sev-high on #ffffff | 5.18:1 | high badges/text |
| light | sev-medium on #ffffff | 5.54:1 | medium badges/text |
| light | sev-low on #ffffff | 7.13:1 | low badges/text |

## Motion

Unchanged from 1.0.6: motion only for state changes (drawer slide,
modal scale, bar/progress fills, theme toggle, login spinner).
No staggered entrances, no shimmer, no breathing dots, no hover
lifts. `prefers-reduced-motion` collapses all of it.

## What changed in 1.0.7

- Light-mode text colours deepened to pass AA (see table). The MUI
  palette in `frontend/src/theme/nexusTheme.ts` mirrors the same
  values in light mode (primary #46700E, secondary #0E7490, warning
  #8A6100, success #166534 — the old warning #D97706 was 3.19:1 and
  secondary #0891B2 was 3.68:1 on white).
- Login brand panel: decorative tab labels replaced by the ledger
  facts strip with real product numbers (7 scanners, 8 CIS
  controls, Terraform fixes).
- Screenshot fixtures (`scripts/shots.mjs`) now use numbers the
  backend really produces: demo scan 1 of 8 CIS controls pass
  (12.5%), production scan 6 of 8 (75%), mean CVSS 6.94.
- Backend (same release): the compliance score is now a pass rate
  over evaluated CIS controls — see README changelog 1.0.7.
