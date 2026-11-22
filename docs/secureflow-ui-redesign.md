# SecureFlow workspace redesign

SecureFlow is an authenticated cloud-security workspace. Its primary job is to help a cloud operator see what a scan actually evaluated, identify a finding that needs attention, and open the evidence or review plan. An operator new to the workspace can start with sample data before connecting an AWS account.

## Design and engineering decisions

- **Signature.** A thin ruled line with a square marker runs through the wordmark, section heads, scan history and data plots. It keeps the interface legible at table density and gives each page one recognizable visual grammar.
- **Composition.** A fixed-width navigation rail leaves the working area for data. Overview starts with one large pass rate and a narrower priority list. Findings uses the inverse, with a short filter column beside a wider register. Settings and analytics allocate space by task.
- **Accent options.** Copper is the selected accent. It reads well on paper and deep olive and gives the ruled mark a warmer tone. Pine would tie to the neutrals but compete with completed status. Slate blue would distinguish navigation clearly but push the workspace toward a cooler visual system.
- **Type.** Instrument Sans handles display and reading. Fontsource serves its Latin and Latin Extended variable WOFF2 subsets from the build. System monospace is reserved for resource IDs, credential fields and code. The base is 16px with 1.6 line height and a 68ch prose cap. Titles and display type scale with `clamp()`. Data uses tabular figures.
- **Space, depth and motion.** Spacing uses a 4px base and an 8px rhythm for blocks. Controls use a 4px radius and overlays 8px. Flush ledgers use rules, one summary surface adds a 1px inner border, and overlays use two soft shadow layers. A static grain sits behind the sign-in illustration. A 220–240ms spring-shaped animation marks the modal and drawer opening. Reduced-motion mode removes the perceptible movement. The interface uses static loading markers and immediate chart rendering.
- **Stack.** Vite, strict TypeScript and React serve the browser application as split routes. Tailwind v4 maps the semantic CSS variables. Native dialog, labels, tables and input controls provide keyboard semantics. Lucide supplies the action icons, alongside the custom mark. Zod Mini validates credentials and review inputs before submission. The existing FastAPI endpoints own the record schema, authentication and persistence. Vite and React Router use releases that clear the prior npm audit findings.
- **Deployment.** Serve the app from the origin root with an SPA fallback for direct route URLs. The browser manifest and icons provide install metadata. Deployments can use the included social image and page metadata. Search indexing is disabled for this private workspace. The application issues requests for current records each visit.

## Tokens and contrast

The 12-step warm neutral ramp, two theme palettes, semantic colors, four-pixel spacing values, radii, type scale and elevation levels are documented in [tokens.json](../frontend/src/theme/tokens.json). [tokens.css](../frontend/src/theme/tokens.css) defines mode variables with explicit sRGB fallbacks and equivalent OKLCH values. [index.css](../frontend/src/index.css) exposes color and font variables to Tailwind in `@theme inline`.

Contrast uses WCAG relative luminance on the tokens’ sRGB equivalents. Values are rounded to two decimals. Text requires 4.5:1 and control boundaries require 3:1. Decorative divider rules have no control role. Severity uses words and a square marker as well as color. The accent is limited to line work, active navigation, links, focus indicators and the screen’s primary action. Pixel sampling near the copper token across the 13 after captures peaked at approximately 4.6%, on mobile sign-in.

| Foreground / background | Light | Dark | Minimum |
| --- | ---: | ---: | ---: |
| `text` / `canvas` | 15.50:1 | 14.93:1 | 4.50:1 |
| `text` / `surface` | 16.77:1 | 13.95:1 | 4.50:1 |
| `subtle` / `canvas` | 5.94:1 | 7.74:1 | 4.50:1 |
| `subtle` / `surface` | 6.42:1 | 7.23:1 | 4.50:1 |
| `subtle` / `rail` | 5.43:1 | 8.14:1 | 4.50:1 |
| `subtle` / `hover` | 4.83:1 | 6.26:1 | 4.50:1 |
| `accent` / `canvas` | 6.28:1 | 8.50:1 | 4.50:1 |
| `accent` / `surface` | 6.79:1 | 7.94:1 | 4.50:1 |
| `accent` / `hover` | 5.10:1 | 6.88:1 | 4.50:1 |
| `on-accent` / `accent` | 6.73:1 | 8.73:1 | 4.50:1 |
| `danger` / `hover` | 5.22:1 | 6.83:1 | 4.50:1 |
| `high` / `hover` | 5.03:1 | 7.69:1 | 4.50:1 |
| `warning` / `hover` | 4.95:1 | 8.19:1 | 4.50:1 |
| `success` / `hover` | 5.17:1 | 7.68:1 | 4.50:1 |
| `control` / `surface` | 3.62:1 | 3.31:1 | 3.00:1 |
| `control` / `canvas` | 3.34:1 | 3.54:1 | 3.00:1 |
| `control` / `rail` | 3.06:1 | 3.73:1 | 3.00:1 |
| `accent` / `line` | 4.41:1 | 5.42:1 | 3.00:1 |

## Screen plan and implementation

| Screen | Applied design | Flow and data |
| --- | --- | --- |
| Sign in · `/login` | Two unequal columns. The left sets AWS scope and uses the ruled illustration. Credentials and recovery feedback sit on the right. The columns stack on phones. | OAuth-compatible form fields post to the existing login endpoint. Password managers can fill both fields. The user sees inline submit and error feedback. |
| Overview · `/dashboard` | One large check pass rate, three compact totals, and a severity-ranked priority list. Secondary ledgers hold the trend, severity and resource counts, and framework scores. | Fetches scans, findings, and summaries. Pass rate uses evaluated checks on finished runs, including sample runs with an explicit label. Chart values open in a text list. A priority finding opens its drawer. Refresh failures retain the prior snapshot. |
| Scans · `/scans` | A ruled history table shows friendly account names, status, progress, finding count and timestamp. The only primary action opens a focused account selector. | Active accounts can be scanned. The list polls while visible. Sample, running and failed runs are labelled. The dialog reports submission errors and returns focus when closed. |
| Findings · `/vulnerabilities` | A narrow filter column and wider register show severity, resource and score. An edge drawer gives the description, steps, controls and Terraform plan a reading order. | Search, status and severity filters combine. The drawer can copy code or save a review plan through the existing endpoint. It restores focus. The finding stays open after a plan save. |
| Analytics · `/analytics` | The multiline log editor gets the wide column. The eight-value metric check fits the narrow one. Each result appears next to its input. | Calls the existing analysis endpoints. Invalid metric input, an unavailable detector, and uncalibrated output have separate messages. |
| Cloud accounts · `/settings/accounts` | The account register gets the larger column. A compact registration form places the sample-data choice ahead of the credential fields. | AWS is the available provider for new accounts. Demo registration sends only the demo mode. Live registration passes required fields to the existing API. Success offers a link to Scans. |
| Notifications · `/settings/notifications` | Three labelled, full-width checkbox rows and a short scope note. | Saves the original Slack, email and PagerDuty preference keys locally. Sign-out preserves browser preferences. |
| User directory · `/settings/users` | An aligned, read-only member table with a clear role and status column. | Loads the organization directory through the current endpoint. Empty and failed loads have different states. |
| Data and privacy · `/privacy`, usage · `/usage` | Short, public reference pages accessible from sign-in. | Explain deployment data handling and supported usage. The administrator supplies deployment-specific terms, retention and request procedures. |
| Missing page and render error | Short recovery pages with one next action. | The root redirects by session. Unknown paths offer a route home. The render boundary offers a reload after a view fails. |

The existing data model is organization → accounts → scans → findings → review plans. Statistics come from scan results and summary endpoints, and notification preferences are browser-local. Fetching and auth stay under `frontend/src/services`, route views stay under `frontend/src/components`, and reusable presentation and tokens live under `components/common` and `theme`. Locale-aware formatters handle dates and time, and CSS logical properties handle inline spacing. The interface ships in English.

### First session

Sign in, open Cloud accounts, register an AWS demo account with **Use sample data**, then follow **Go to scans**. Select the demo account and start the first run. The scan history shows its state. After completion, open Findings and review a result. The first milestone is a queued sample scan. Worker completion time depends on the deployment.

### Section review

The token pass tightened muted text on the light hover surface. The primitive pass moved dialogs to the browser top layer and covered their focus return. The page pass made sample checks explicit in the overview, aligned the chart marks with their plotted points, moved alert preferences to browser-local wording, and reduced mobile navigation to two compact rows. The deployment pass checked every nested entry point and moved assets to root-relative URLs.

## Reproduce locally

Use Node.js 22.13+ and Python with the backend’s requirements. The full package and transitive dependency versions are in the lockfile. For a connected build, set `VITE_API_URL` to the deployment's `/api/v1` base. Local development may omit it to use `http://127.0.0.1:8000/api/v1`. Follow the repository’s environment examples for backend authentication, database setup and `CLOUD_CREDENTIALS_KEY` for live account registration.

```sh
cd frontend
npm ci
npm run lint
npm run build
VITE_API_URL=/api/v1 npm run build
npx playwright-core install chromium
npm test
```

`CHROME_BIN` can select an installed Chromium. The fixture build and browser test server route calls to data in `scripts/visual/fixtures.mjs`. CI installs Chromium and runs the lint, type-checked build and browser regression checks. The backend job runs the documented suite against SQLite.

From the repository root after the fixture build, capture the redesign with the following. For a baseline, build commit `09dc940` with the same `VITE_API_URL` in a separate checkout, then pass its `dist` directory and `before` as the final argument. Both builds use the same local fixtures and viewport sizes. The capture server maps the baseline’s relative bundle URLs on nested routes so those pages can render.

```sh
node scripts/shots.mjs frontend/dist /tmp/secureflow-after after
node scripts/shots.mjs /path/to/baseline/frontend/dist /tmp/secureflow-before before
```

## Verification

| Check | Result |
| --- | --- |
| Backend suite with disposable SQLite | 190 passed |
| Legacy service verification | 2 passed, 2 baseline failures reproduced on `09dc940`. The old assertions expect implicit demo mode and numeric confidence for rule-based scoring. |
| Frontend | Type-checked production and fixture builds passed. ESLint passed. npm audit reported zero known findings. |
| Browser regression | Workflow and payload checks passed. Axe found zero violations in 24 WCAG A/AA audits across dark and light modes. The 11 routes fit at 320px. The demo account and scan regression also passed at 320, 390 and 1280px. |
| Sign-in Lighthouse | Performance 100, accessibility 100, best practices 100. LCP 0.6s. |
| Overview Lighthouse | Performance 99, accessibility 100, best practices 100. LCP 1.3s. |

Lighthouse 13 ran against the compressed fixture build with mobile simulation. The intentional `noindex` directive produces an SEO score of 60. Lab results depend on the host and fixture latency.

## Launch checklist

- [x] Confirm each existing main screen and both overlays in paired captures.
- [x] Verify known typography and control pairs against the contrast thresholds.
- [x] Run the backend test suite, frontend lint, type-checked build, and browser flow checks.
- [x] Check both themes for automated accessibility issues and check 320px layouts.
- [ ] Verify production hosting with deep links, HTTPS, CSP, the deployment API URL, and the hosted social-image URL.
- [ ] Walk through a real authorized test account, worker completion, review-plan save and token expiry in staging.
- [ ] Confirm deployment-specific privacy terms, retention, credentials handling and telemetry ownership.
- [ ] Recheck production performance with realistic API latency and inspect focus order on Safari and Firefox.

### Launch risks

Browser checks use Chromium and synthetic data. Live scan timing and storage depend on the worker and deployment. API calls use a browser session token as before, and production origin controls and token storage deserve a deployment review. The 404 view is an SPA view. Hosting determines HTTP status and response headers. Preview hosting, monitoring and alert delivery need configured services before their behavior can be verified.

### Ten follow-up ideas

1. Server-backed alert preferences and a send-test action.
2. Resumable scan history filters and pagination.
3. Saved finding filters for common triage work.
4. Per-account and live-only compliance comparisons.
5. Evidence provenance and scan completeness in the finding drawer.
6. Finding review ownership and notes.
7. Remediation plan history and export.
8. Account-scoped read-only roles for reviewers.
9. Locale message bundles and translated layouts.
10. Production telemetry for queue time, API errors and field Web Vitals.
