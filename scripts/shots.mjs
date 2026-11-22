// Fresh visual renders for review: desktop 1280px + phone 390px.
// Run: node scripts/shots.mjs
// Writes docs/visual-proof-<version>/*.png. Modelled on the kirana recipe
// for this VM: Hatch Chrome needs a WebGL domain-policy file just to start.
//
// Two VM facts shape this script:
// - Chrome blocks navigation to localhost (Local Network Access checks),
//   so the SPA is loaded over file:// from a throwaway build that bakes
//   VITE_API_URL (the shipped dist keeps its default; the throwaway build
//   differs only in that constant and is never committed).
// - The app uses BrowserRouter, so after it mounts the URL is mangled to
//   file:///login or file:///dashboard and location.reload() 404s. This
//   script never reloads: it seeds the session token with an eval and
//   re-enters through CDP Page.navigate, and switches theme by clicking
//   the real toggle button.
// The API is served by CDP Fetch interception — no backend, database or
// network calls — with canned responses shaped like the app's real demo
// findings (titles copied from the S3/IAM/VPC demo scanners). CORS
// preflights are answered by the interceptor, so no --disable-web-security
// is needed; there is no live-mode flag in the product.
import { spawn, spawnSync } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(fileURLToPath(import.meta.url)) + '/..';
const VERSION = JSON.parse(fs.readFileSync(path.join(ROOT, 'frontend/package.json'), 'utf8')).version;
const OUT = path.join(ROOT, `docs/visual-proof-${VERSION}`);
fs.mkdirSync(OUT, { recursive: true });

// Throwaway build for renders only: same sources, same relative base,
// only the API URL baked in so the file:// page calls the mocked API.
const SHOTS_DIST = '/tmp/secureflow-shots-dist';
const build = spawnSync('npx', ['vite', 'build', '--outDir', SHOTS_DIST, '--emptyOutDir'],
  { cwd: path.join(ROOT, 'frontend'), env: { ...process.env, VITE_API_URL: 'http://127.0.0.1:8000/api/v1' }, encoding: 'utf8' });
if (build.status !== 0) { console.error(build.stdout, build.stderr); throw new Error('shots build failed'); }

const CHROME = '/opt/meta-chromium/chrome';
const DEBUG_PORT = 9228;
const API = 'http://127.0.0.1:8000/api/v1';
const INDEX_URL = `file://${SHOTS_DIST}/index.html`;

// Canned API data. Synthetic, shaped like real demo-scan output; the app
// itself labels demo results as sample data.
const SCANS = [
  { id: 'a1b2c3d4-e5f6-4a5b-8c9d-001122334455', cloud_account_id: 'demo-account-id', status: 'DEMO_COMPLETED', progress: 100, vulnerabilities_found: 5, passed_checks: 4, failed_checks: 3, created_at: '2026-11-21T10:00:00Z', completed_at: '2026-11-21T10:04:00Z' },
  { id: 'b2c3d4e5-f6a7-4b5c-9d0e-112233445566', cloud_account_id: 'prod-account-id', status: 'COMPLETED', progress: 100, vulnerabilities_found: 2, passed_checks: 12, failed_checks: 2, created_at: '2026-11-20T09:00:00Z', completed_at: '2026-11-20T09:05:00Z' },
  { id: 'c3d4e5f6-a7b8-4c5d-0e1f-223344556677', cloud_account_id: 'demo-account-id', status: 'RUNNING', progress: 45, vulnerabilities_found: 0, passed_checks: 0, failed_checks: 0, created_at: '2026-11-22T00:00:00Z', completed_at: null },
];
const TF_S3 = 'resource "aws_s3_bucket_public_access_block" "customer_invoice_uploads_temp_remediated" {\n  bucket = "customer-invoice-uploads-temp"\n\n  block_public_acls       = true\n  block_public_policy     = true\n  ignore_public_acls      = true\n  restrict_public_buckets = true\n}\n';
const VULNS = [
  { id: 'v-1', resource_type: 'S3', resource_id: 'customer-invoice-uploads-temp', resource_name: 'customer-invoice-uploads-temp', vulnerability_type: 'PUBLIC_ACCESS_NOT_BLOCKED', severity: 'CRITICAL', title: 'S3 Bucket Public Access Not Fully Blocked', description: "S3 bucket 'customer-invoice-uploads-temp' is configured with public write/read permissions, allowing global directory exposure.", recommendation: 'Enable all S3 Block Public Access policies immediately at the account or bucket level. Then verify the bucket policy denies public access.', terraform_fix: TF_S3, compliance_frameworks: ['CIS AWS 2.1.5', 'PCI-DSS 3.4'], cvss_score: 9.8, status: 'OPEN', evidence: {} },
  { id: 'v-2', resource_type: 'S3', resource_id: 'corp-internal-wiki-docs', resource_name: 'corp-internal-wiki-docs', vulnerability_type: 'NO_ENCRYPTION_AT_REST', severity: 'HIGH', title: 'S3 Bucket Default Encryption Disabled', description: "S3 bucket 'corp-internal-wiki-docs' is not configured with default server-side encryption (SSE). Unencrypted files pose structural compliance failures.", recommendation: 'Configure default bucket encryption with AES-256 (SSE-S3) or an AWS KMS key (SSE-KMS).', terraform_fix: TF_S3, compliance_frameworks: ['CIS AWS 2.1.1', 'HIPAA 164.312'], cvss_score: 7.5, status: 'OPEN', evidence: {} },
  { id: 'v-3', resource_type: 'S3', resource_id: 'secureflow-production-assets', resource_name: 'secureflow-production-assets', vulnerability_type: 'SSL_NOT_ENFORCED', severity: 'MEDIUM', title: 'S3 Bucket Does Not Enforce SSL/TLS', description: "S3 bucket 'secureflow-production-assets' does not enforce encryption-in-transit, leaving endpoints vulnerable to interception.", recommendation: 'Deploy a bucket policy setting aws:SecureTransport parameter to false in a Deny rule block.', terraform_fix: TF_S3, compliance_frameworks: ['CIS AWS 2.1.2', 'PCI-DSS 4.1'], cvss_score: 5.3, status: 'OPEN', evidence: {} },
  { id: 'v-4', resource_type: 'VPC', resource_id: 'vpc-0a1b2c3d4e5f6a7b8', resource_name: 'prod-vpc', vulnerability_type: 'FLOW_LOGS_DISABLED', severity: 'HIGH', title: 'VPC Flow Logs Disabled', description: 'VPC prod-vpc has no flow logs enabled, so network traffic cannot be audited after an incident.', recommendation: 'Enable VPC flow logs to CloudWatch Logs for all production VPCs. Review the logs weekly.', terraform_fix: TF_S3, compliance_frameworks: ['CIS AWS 3.9'], cvss_score: 7.1, status: 'OPEN', evidence: {} },
  { id: 'v-5', resource_type: 'IAM', resource_id: 'AKIAIOSFODNN7EXAMPLE', resource_name: 'deploy-user', vulnerability_type: 'OLD_ACCESS_KEY', severity: 'MEDIUM', title: 'IAM Access Key Older Than 90 Days', description: 'Access key for deploy-user was created more than 90 days ago and has not been rotated.', recommendation: 'Rotate the access key and remove the old one. Then confirm the user can still deploy.', terraform_fix: '', compliance_frameworks: ['CIS AWS 1.4'], cvss_score: 5.0, status: 'OPEN', evidence: {} },
];
const SUMMARY = { total_open_vulnerabilities: 5, average_cvss_score: 7.14, severity_distribution: { CRITICAL: 1, HIGH: 2, MEDIUM: 2, LOW: 0 }, resource_distribution: { S3: 3, VPC: 1, IAM: 1 } };
const COMPLIANCE = { CIS: 68, PCI_DSS: 75, HIPAA: 80 };
const ACCOUNTS = [
  { id: 'demo-account-id', name: 'Demo AWS Account', provider: 'aws', is_active: true },
  { id: 'prod-account-id', name: 'Production AWS Account', provider: 'aws', is_active: true },
];
const USERS = [
  { email: 'siva@example.com', full_name: 'Sivasai Boggu', role: 'admin', is_active: true },
  { email: 'teammate@example.com', full_name: 'Teammate One', role: 'user', is_active: true },
];

function canned(url, method) {
  const p = url.replace(API, '');
  if (method === 'POST' && p === '/auth/login') return { access_token: 'synthetic-shot-token', refresh_token: 'synthetic-shot-refresh', token_type: 'bearer', user: USERS[0] };
  if (p === '/scans') return SCANS;
  if (p === '/vulnerabilities') return VULNS;
  if (p === '/analytics/summary') return SUMMARY;
  if (p === '/compliance/summary') return COMPLIANCE;
  if (p === '/scans/cloud-accounts') return ACCOUNTS;
  if (p === '/users') return USERS;
  if (p === '/vulnerabilities/analyze-log') return { is_threat: true, confidence: null, classification: 'FLAGGED', method: 'heuristic_rules', calibrated: false };
  if (p === '/vulnerabilities/analyze-metrics') return { is_anomaly: null, anomaly_score: null, method: 'unavailable', calibrated: false, error: 'No local anomaly model is available. No assessment was performed.' };
  return null;
}

const CORS = [
  { name: 'Access-Control-Allow-Origin', value: '*' },
  { name: 'Access-Control-Allow-Headers', value: 'Authorization, Content-Type' },
  { name: 'Access-Control-Allow-Methods', value: 'GET, POST, OPTIONS' },
];

function chromeArgs(firstUrl) {
  const policy = 'hatch-webgl-allowed-domains-v1\nexample.com\n';
  const file = path.join(os.tmpdir(), 'secureflow-webgl-policy.txt');
  fs.writeFileSync(file, policy);
  const sha = createHash('sha256').update(policy).digest('hex');
  return [
    '--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
    '--allow-file-access-from-files',
    // Test-harness flag only, never a product change. Two file:// needs:
    // the mocked API is cross-origin (CORS), and React Router's
    // replaceState('/login') throws a SecurityError on a file:// origin
    // without it — without the flag the app mounts to a black page.
    // (That also means opening dist/index.html directly in a normal
    // browser is a black page: BrowserRouter needs an HTTP origin.
    // Static hosting works; file:// direct open is not supported.)
    '--disable-web-security',
    `--user-data-dir=${fs.mkdtempSync(path.join(os.tmpdir(), 'secureflow-chrome-'))}`,
    `--hatch-webgl-allowed-domains-file=${file}`,
    `--hatch-webgl-allowed-domains-sha256=${sha}`,
    `--remote-debugging-port=${DEBUG_PORT}`,
    '--window-size=1280,900',
    firstUrl,
  ];
}

class Cdp {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.nextId = 1;
    this.pending = new Map();
    this.ready = new Promise((resolve, reject) => { this.ws.onopen = resolve; this.ws.onerror = reject; });
    this.ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        if (msg.error) reject(new Error(JSON.stringify(msg.error)));
        else resolve(msg.result);
      } else if (msg.method === 'Fetch.requestPaused') {
        this.handleFetch(msg.params);
      }
    };
  }
  async call(method, params = {}) {
    await this.ready;
    const id = this.nextId++;
    const done = new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
    this.ws.send(JSON.stringify({ id, method, params }));
    return done;
  }
  async handleFetch(params) {
    const { requestId, request } = params;
    if (request.method === 'OPTIONS') {
      await this.call('Fetch.fulfillRequest', { requestId, responseCode: 204, responseHeaders: CORS, body: '' });
      return;
    }
    const data = canned(request.url, request.method);
    if (data !== null) {
      const body = Buffer.from(JSON.stringify(data)).toString('base64');
      await this.call('Fetch.fulfillRequest', { requestId, responseCode: 200,
        responseHeaders: [{ name: 'Content-Type', value: 'application/json' }, ...CORS], body });
    } else {
      await this.call('Fetch.continueRequest', { requestId });
    }
  }
  async eval(expression) {
    const r = await this.call('Runtime.evaluate', { expression, returnByValue: true });
    if (r.exceptionDetails) throw new Error('eval failed: ' + JSON.stringify(r.exceptionDetails).slice(0, 400));
    return r.result?.value;
  }
  async shot(name) {
    const r = await this.call('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
    fs.writeFileSync(path.join(OUT, name), Buffer.from(r.data, 'base64'));
    console.log('wrote', name);
  }
}

const sleep = (ms) => delay(ms);

async function main() {
  const chrome = spawn(CHROME, chromeArgs(INDEX_URL), { stdio: 'ignore' });
  try {
    let wsUrl;
    for (let i = 0; i < 40; i++) {
      await sleep(500);
      try {
        const targets = await (await fetch(`http://127.0.0.1:${DEBUG_PORT}/json`)).json();
        const page = targets.find((t) => t.type === 'page');
        if (page) { wsUrl = page.webSocketDebuggerUrl; break; }
      } catch { /* chrome not up yet */ }
    }
    if (!wsUrl) throw new Error('chrome did not expose a page target');
    const cdp = new Cdp(wsUrl);
    await cdp.call('Page.enable');
    await cdp.call('Runtime.enable');
    await cdp.call('Fetch.enable', { patterns: [{ urlPattern: `${API}/*`, requestStage: 'Request' }] });
    await sleep(3000); // let the login shell render

    // 01 login, desktop. No token yet: the app shows the sign-in form.
    await cdp.shot('01-login.png');

    // Mobile login on the same document: metrics override reflows it.
    await cdp.call('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
    await sleep(800);
    await cdp.shot('11-login-mobile.png');
    await cdp.call('Emulation.clearDeviceMetricsOverride', {});
    await sleep(800);

    // Sign in: seed the session the app itself stores, then re-enter
    // through a fresh CDP navigation (never location.reload: the router
    // has mangled the URL to file:///login by now).
    await cdp.eval(`localStorage.setItem('token','synthetic-shot-token');localStorage.setItem('refresh_token','synthetic-shot-refresh');localStorage.setItem('user',JSON.stringify({email:'siva@example.com'}));`);
    await cdp.call('Page.navigate', { url: INDEX_URL });
    await sleep(3000);
    await cdp.shot('02-dashboard-dark.png');

    // Light mode through the real toggle button, then back to dark.
    await cdp.eval(`document.querySelector('button[aria-label="Switch to light mode"]').click();`);
    await sleep(1500);
    await cdp.shot('03-dashboard-light.png');
    await cdp.eval(`document.querySelector('button[aria-label="Switch to dark mode"]').click();`);
    await sleep(1500);

    const nav = async (href, waitMs = 2500) => {
      await cdp.eval(`document.querySelector('a[href="${href}"]').click();`);
      await sleep(waitMs);
    };
    await nav('/scans');
    await cdp.shot('04-scans.png');
    await cdp.eval(`Array.from(document.querySelectorAll('button')).find(b=>b.textContent.includes('Trigger Scan')).click();`);
    await sleep(900);
    await cdp.shot('09-scan-modal.png');
    // The closed native select hides its options; verify the account list
    // loaded by counting options instead of trusting the screenshot.
    const optionCount = await cdp.eval(`document.querySelectorAll('#scan-account-select option').length`);
    console.log('scan modal account options:', optionCount);
    if (optionCount < 3) throw new Error(`expected 2 accounts + placeholder in the scan modal, found ${optionCount} options`);
    await cdp.eval(`Array.from(document.querySelectorAll('button')).find(b=>b.textContent.trim()==='Cancel').click();`);
    await sleep(500);

    await nav('/vulnerabilities');
    await cdp.shot('05-vulnerabilities.png');
    // Click a finding row by its title: the first <button> in the page is
    // a severity filter, not a finding.
    await cdp.eval(`Array.from(document.querySelectorAll('.finding-page button')).find(b=>b.textContent.includes('S3 Bucket Public Access Not Fully Blocked')).click();`);
    await sleep(1000);
    await cdp.shot('06-finding-drawer.png');
    await cdp.eval(`document.querySelector('[aria-label="Close finding details"]').click();`);
    await sleep(500);

    await nav('/analytics');
    await cdp.eval(`Array.from(document.querySelectorAll('button')).find(b=>b.textContent.includes('Run Log Classification')).click();`);
    await sleep(1500);
    await cdp.shot('07-analytics.png');
    await nav('/settings/accounts');
    await cdp.shot('10-cloud-accounts.png');
    await nav('/settings/users');
    await cdp.shot('08-users.png');

    // Mobile dashboard on the same document.
    await cdp.call('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
    await cdp.eval(`document.querySelector('a[href="/dashboard"]').click();`);
    await sleep(2500);
    await cdp.shot('12-dashboard-mobile.png');

    console.log('done ->', OUT);
  } finally {
    chrome.kill('SIGKILL');
  }
}

main().catch((e) => { console.error(e); process.exit(1); });
