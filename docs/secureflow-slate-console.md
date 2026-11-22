# SecureFlow slate console

SecureFlow helps cloud security teams run AWS checks, review the resulting findings, and track their response. The workflow starts with a scan, moves through policy evidence and triage, and ends with a recorded decision or a Terraform plan saved for review.

## Reference study

| Reference | Application |
| --- | --- |
| [21st.dev table filter](https://mcp.21st.dev/%40uniquesonu/components/data-table-filter) | Keep search, status and severity in one toolbar above the findings table. |
| [Designeer archived directory](https://archive.vn/2026.09.26-133235/https%3A/designeer.xyz/) | Follow its distinction between shipped product flows and motion references. The live domain and its www variant were unreachable. |
| [React Bits Fade Content](https://reactbits.dev/animations/fade-content) | Use a short view reveal with a small vertical offset. |
| [Magic UI Animated List](https://magicui.design/docs/components/animated-list) | Stagger only the first few rows when fresh results appear. |
| [Uiverse buttons](https://uiverse.io/buttons) | Give real controls a brief press displacement and visible keyboard focus. |
| [Mobbin](https://mobbin.com/) | Use a direct sign-in sequence with persistent labels and a password visibility control. The deep-link pattern gallery was unavailable. The public showcase and help flow were used. |
| [Inspora quick-action menu](https://www.inspora.design/posts/one-tap-menu-bypass) | Offer a keyboard shortcut to jump between views. |
| [Refero Styles dashboard examples](https://styles.refero.design/examples/dashboard-ui-design) | Place the aggregate pass rate beside the historical chart and leave priority findings in a separate pane. |

## Design system

The signature is a set of square scan brackets. A low-opacity grain softens the sign-in scope panel. They form the brand mark and recur where the console introduces the sign-in scope or a posture reading. An asymmetric overview pairs scan history with the queue. Findings use a table and drawer. Policy checks use a scope selector and inline disclosure so reviewers can compare evidence in place.

| Accent considered | Decision |
| --- | --- |
| Ice blue | Used for focus, navigation state, links and the primary action. It is readable in both modes and leaves warm colors available for severity. |
| Muted mint | It fits slate, but overlaps with passed checks and resolved items. |
| Muted amber | It is readable against dark slate, but competes with medium severity and warning messages. |

JetBrains Mono is the display, body and data family. The console uses separate weight and size roles, fluid headings, a 16px body at 1.6 line height, a 68-character text measure and 13px secondary data. Fontsource supplies licensed variable WOFF2 subsets. Vite serves the font from the app origin and preloads the Latin subset.

The 4px base unit sets gaps of 4–8px within a control, 12–16px inside rows, 16–24px between panels and 32–48px for page insets. Controls generally have a 44px target, a 6px radius and a visible focus outline. Panels use a 12px radius and a one-pixel inset edge. Canvas, panels and elevated dialogs are the three levels. The palette and spacing are in `frontend/src/theme/tokens.json` and `tokens.css`, with Tailwind aliases in `frontend/src/index.css`. Both themes share a 12-step slate ramp, a blue accent and severity signals. Sparse use of the accent keeps the page quiet and status labels carry meaning in text.

| Measured WCAG contrast pair | Dark | Light |
| --- | ---: | ---: |
| Primary text on canvas | 15.43:1 | 15.60:1 |
| Primary text on panels | 13.63:1 | 16.63:1 |
| Secondary text on hovered rows | 6.44:1 | 5.59:1 |
| Secondary text on navigation or sign-in scope | 9.19:1 | 5.59:1 |
| Accent on panels | 8.92:1 | 7.32:1 |
| Accent on hovered rows | 7.48:1 | 6.25:1 |
| Primary button label on accent | 10.21:1 | 7.32:1 |
| Control boundary on panels | 3.71:1 | 3.91:1 |
| Control boundary on hovered rows | 3.12:1 | 3.34:1 |
| Critical signal on hovered rows | 6.80:1 | 5.74:1 |
| High signal on hovered rows | 7.50:1 | 5.69:1 |
| Medium signal on hovered rows | 8.37:1 | 5.52:1 |
| Success signal on hovered rows | 7.80:1 | 5.74:1 |

Ratios use WCAG relative luminance in sRGB from the hex equivalents of the OKLCH tokens. Hover is the lowest-contrast tested severity surface. Color is paired with text or a meaningful state.

Press feedback takes 150ms, view and disclosure entrances 220ms, drawers 240ms, and meters 320ms. List entrances stagger by 40ms across the first five rows. All motion uses opacity or transform and switches off with reduced motion. The overview refreshes every 30 seconds in visible tabs and keeps the last successful snapshot if refresh fails.

## Routes and data

| Surface | Flow |
| --- | --- |
| Sign-in | Email and password → requested view. Simultaneous expired requests share one refresh. If credentials expire, sign-in restores the original view and its query. |
| Overview and scans | Read current posture, start a sample or live scan, and open checks for a finished run. |
| Findings | Search by title or resource, filter by severity and status, open a shareable detail, and record triage. A competing status update prompts a fresh review. |
| Policy checks | Filter finished scans by outcome, distinguish control results from resource evidence, and open related findings. |
| Analytics | Review a CloudTrail event, inspect the action and actor, and open findings for a referenced S3 bucket. Metric review remains a separate form. |
| Settings and reference | Cloud accounts, notifications, users, data and privacy, usage scope, and a missing-page route. |

The frontend keeps the existing Vite, strict TypeScript, React and Tailwind architecture. Lazy routes keep feature code out of sign-in. FastAPI continues to own organization boundaries, SQLAlchemy queries and writes. Finding status and actor are recorded in the existing vulnerability and audit tables in one transaction. Policy checks use the existing scan and check rows, including pre-control-level evidence. This change requires no database migration. Browser data for screenshots and automated UI checks is synthetic.

## Reproduce the checks

Use Node 22.13 or later, Python 3.12 and the locked frontend dependencies. Main’s existing React 18 and TypeScript 5 versions stay pinned. The new font is pinned to `@fontsource-variable/jetbrains-mono@5.3.0`.

```sh
npm --prefix frontend ci
npm --prefix frontend exec -- playwright-core install chromium
VITE_API_URL=/api/v1 npm --prefix frontend run build
npm --prefix frontend run lint
npm --prefix frontend test
cd backend
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lite.txt pytest==9.2.0
DATABASE_URL=sqlite:////tmp/secureflow-v2.sqlite .venv/bin/python -m pytest tests -q
```

From the repository root, use the custom capture runner with a build from main and a build from this branch. The runner fixes viewport, time, fonts and fixtures.

```sh
node scripts/visual/capture.mjs /path/to/main-build /tmp/secureflow-before before
node scripts/visual/capture.mjs frontend/dist /tmp/secureflow-after after
npm install --prefix /tmp/secureflow-lighthouse --save-exact lighthouse@13.6.0
node scripts/visual/lighthouse.mjs frontend/dist /tmp/secureflow-reports /tmp/secureflow-lighthouse
```

Set `CHROME_BIN` when system Chromium is installed at a different path. For local live development, see the [root setup instructions](../README.md) and configure the deployed API using [the environment template](../.env.example). The same-origin build flag above serves fixture data for browser checks.

## Launch checklist

- [x] Render all routes in dark and light modes and check narrow, tablet and desktop widths.
- [x] Exercise sign-in, triage, policy evidence and scan setup in the browser.
- [x] Capture the merged main and the redesigned console with the same fixture data.
- [x] Record mobile Lighthouse for sign-in and the authenticated overview.
- [ ] Check the configured staging API, workspace permissions and one authorized AWS account before rollout.

The score summarizes the implemented CIS checks. Sample scans remain labeled. A triage status records an analyst’s decision, and plan creation records a review item. Production latency and AWS account connectivity depend on deployment configuration. The private console uses `noindex, noarchive`, which is reflected in the Lighthouse SEO score.

## Follow-up ideas

1. Assign findings to an active organization member.
2. Show a read-only triage history on each finding.
3. Compare control outcomes between two runs of the same account.
4. Add saved team filters for recurring review queues.
5. Offer a tenant-scoped export of policy evidence.
6. Group recurring findings by resource and control.
7. Report scanner coverage and skipped checks by account.
8. Add configurable reminders for aging critical findings.
9. Add organization SSO and server-side session revocation.
10. Expose scan queue health and backoff to workspace administrators.
