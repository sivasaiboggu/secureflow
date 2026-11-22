import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { createRequire } from 'node:module';
import { promisify } from 'node:util';
import { access } from 'node:fs/promises';
import { serve } from './server.mjs';

const require = createRequire(new URL('../../frontend/package.json', import.meta.url));
const { chromium } = require('playwright-core');
const { AxeBuilder } = require('@axe-core/playwright');
const { color } = require('./src/theme/tokens.json');
const dist = process.argv[2] || 'frontend/dist';
const systemChromium = await access('/usr/bin/chromium').then(() => '/usr/bin/chromium', () => undefined);
const executablePath = process.env.CHROME_BIN || systemChromium || chromium.executablePath();
const server = await serve(dist);
const browser = await chromium.launch({ executablePath, headless: true, args: ['--no-sandbox'] });
const paths = [
  ['/login', 'Sign in'],
  ['/dashboard', 'Cloud posture'],
  ['/scans', 'Scans'],
  ['/vulnerabilities', 'Findings'],
  ['/policies', 'Policy checks'],
  ['/analytics', 'Log and metric review'],
  ['/settings/accounts', 'Cloud accounts'],
  ['/settings/notifications', 'Notifications'],
  ['/settings/users', 'User directory'],
  ['/privacy', 'Data and privacy'],
  ['/usage', 'Usage scope'],
  ['/missing', 'Page not found'],
];

try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
  const page = await context.newPage();
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  const open = async (path, heading) => {
    await page.goto(server.url + path);
    await page.getByRole('heading', { name: heading, exact: true }).waitFor();
    await page.evaluate(() => document.fonts.ready);
    if (path === '/dashboard') await page.getByText('CIS', { exact: true }).waitFor();
    if (path === '/scans') await page.getByText('Sample complete', { exact: true }).waitFor();
    if (path === '/vulnerabilities') await page.getByRole('button', { name: /VPC Flow Logs Disabled/ }).waitFor();
    if (path === '/policies') await page.getByText('Block public access to S3 buckets', { exact: true }).waitFor();
    if (path === '/settings/accounts') await page.getByText('Production AWS Account', { exact: true }).waitFor();
    if (path === '/settings/users') await page.getByText('siva@example.com').filter({ visible: true }).waitFor();
  };
  const audit = async label => {
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
    assert.deepEqual(result.violations.map(({ id, nodes }) => ({ id, selectors: nodes.map(({ target, failureSummary }) => [target, failureSummary]) })), [], label);
  };
  const assertNoOverflow = async label => assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth), false, label,
  );

  await open('/login', 'Sign in');
  await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(() => document.activeElement.textContent), 'Skip to content');
  await page.keyboard.press('Enter');
  assert.equal(await page.evaluate(() => document.activeElement.id), 'main');
  await page.getByLabel('Email address').fill('siva@example.com');
  await page.getByLabel('Password', { exact: true }).fill('local-fixture-password');
  await page.getByRole('button', { name: 'Show password' }).click();
  assert.equal(await page.getByLabel('Password', { exact: true }).getAttribute('type'), 'text');
  await page.getByRole('button', { name: 'Hide password' }).click();
  assert.equal(await page.getByLabel('Password', { exact: true }).getAttribute('type'), 'password');
  const login = page.waitForRequest(request => request.url().endsWith('/auth/login'));
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  assert.equal(new URLSearchParams((await login).postData()).get('username'), 'siva@example.com');
  await page.getByRole('heading', { name: 'Cloud posture' }).waitFor();
  await page.getByText('7 of 16 checks passed across finished scans.').waitFor();
  await page.getByRole('button', { name: 'Switch to light mode' }).click();
  await page.reload();
  await page.getByRole('button', { name: 'Switch to dark mode' }).click();
  await page.getByText('7 of 16 checks passed across finished scans.').waitFor();
  await page.getByRole('link', { name: /S3 Bucket Public Access Not Fully Blocked/ }).click();
  await page.getByRole('dialog').waitFor();
  await page.keyboard.press('Escape');
  await page.getByRole('dialog').waitFor({ state: 'hidden' });

  await open('/scans', 'Scans');
  await page.getByText('Sample complete', { exact: true }).waitFor();
  const newScan = page.getByRole('button', { name: 'New scan', exact: true });
  await newScan.focus();
  await page.keyboard.press('Enter');
  await page.getByRole('dialog', { name: 'Start a scan' }).waitFor();
  await audit('scan dialog in dark mode');
  await page.keyboard.press('Escape');
  await page.getByRole('dialog').waitFor({ state: 'hidden' });
  assert.equal(await newScan.evaluate(button => button === document.activeElement), true);
  await newScan.click();
  await page.getByLabel('Cloud account', { exact: true }).selectOption('demo-account-id');
  const scan = page.waitForRequest(request => request.url().endsWith('/scans') && request.method() === 'POST');
  await page.getByRole('button', { name: 'Start scan', exact: true }).click();
  assert.deepEqual((await scan).postDataJSON(), { cloud_account_id: 'demo-account-id' });
  await page.getByText('Scan queued.', { exact: false }).waitFor();

  await open('/vulnerabilities', 'Findings');
  const logFinding = page.getByRole('button', { name: /VPC Flow Logs Disabled/ });
  await page.getByRole('searchbox').fill('VPC');
  await logFinding.waitFor();
  await page.getByRole('radio', { name: /Critical/ }).check();
  await page.getByText('No findings match these filters').waitFor();
  await page.getByRole('button', { name: 'Clear filters' }).click();
  const finding = page.getByRole('button', { name: /S3 Bucket Public Access Not Fully Blocked/ });
  await finding.click();
  await audit('finding drawer in dark mode');
  const plan = page.waitForRequest(request => request.url().endsWith('/vulnerabilities/remediate'));
  await page.getByRole('button', { name: 'Save plan for review' }).click();
  assert.deepEqual((await plan).postDataJSON(), { vulnerability_id: 'v-1' });
  await page.getByText('Plan saved for review.', { exact: true }).waitFor();
  await page.keyboard.press('Escape');
  assert.equal(await finding.evaluate(button => button === document.activeElement), true);

  await page.getByRole('button', { name: /S3 Bucket Public Access Not Fully Blocked/ }).click();
  await page.getByLabel('Triage status').selectOption('IN_PROGRESS');
  const triage = page.waitForRequest(request => request.method() === 'PATCH' && request.url().endsWith('/v-1/triage'));
  await page.getByRole('button', { name: 'Save status' }).click();
  assert.deepEqual((await triage).postDataJSON(), { status: 'IN_PROGRESS', expected_status: 'OPEN' });
  await page.getByText('Triage status saved.', { exact: true }).waitFor();
  await page.keyboard.press('Escape');
  await page.getByLabel('Status', { exact: true }).selectOption('IN_PROGRESS');
  await page.getByRole('button', { name: /S3 Bucket Public Access Not Fully Blocked/ }).waitFor();
  assert.equal(await page.getByRole('button', { name: /VPC Flow Logs Disabled/ }).count(), 0);

  const stale = '**/api/v1/vulnerabilities/v-1/triage';
  await page.route(stale, route => route.fulfill({ status: 409, json: { detail: 'This finding changed.' } }));
  await page.getByRole('button', { name: /S3 Bucket Public Access Not Fully Blocked/ }).click();
  await page.getByLabel('Triage status').selectOption('IGNORED');
  await page.getByRole('button', { name: 'Save status' }).click();
  await page.getByRole('alert').getByText('This finding changed.').waitFor();
  assert.equal(await page.getByLabel('Triage status').inputValue(), 'IN_PROGRESS');
  await page.unroute(stale);
  await page.getByRole('link', { name: 'Policy checks for this scan' }).click();
  await page.getByText('Block public access to S3 buckets', { exact: true }).click();
  await audit('expanded policy evidence in dark mode');
  await page.getByLabel('Outcome').selectOption('FAIL');
  await page.getByText('Block public access to S3 buckets', { exact: true }).click();
  assert.equal(await page.getByText('Require MFA for IAM users with a password', { exact: true }).count(), 0);
  await page.getByRole('link', { name: 'customer-invoice-uploads-temp', exact: true }).click();
  assert.equal(await page.getByRole('searchbox').inputValue(), 'customer-invoice-uploads-temp');
  await page.getByRole('button', { name: /S3 Bucket Public Access Not Fully Blocked/ }).waitFor();

  await page.keyboard.press('Control+k');
  await page.getByRole('dialog', { name: 'Go to view' }).waitFor();
  await page.getByLabel('Find a view').fill('policy');
  await audit('view picker in dark mode');
  await page.getByRole('dialog').getByRole('link', { name: 'Policy checks' }).click();
  await page.getByRole('heading', { name: 'Policy checks', exact: true }).waitFor();

  await open('/analytics', 'Log and metric review');
  await page.getByRole('button', { name: 'Review log' }).click();
  await page.getByText('Flagged for review').waitFor();
  await page.getByText('GetBucketLocation', { exact: true }).waitFor();
  await page.getByRole('link', { name: 'example-backup-bucket' }).waitFor();
  await page.getByLabel('Metric values').fill('1,2,3');
  await page.getByRole('button', { name: 'Check metrics' }).click();
  await page.getByText('Enter exactly 8 numbers, separated by commas.').waitFor();
  await page.getByLabel('Metric values').fill('1,2,3,4,5,6,7,8');
  await page.getByRole('button', { name: 'Check metrics' }).click();
  await page.getByText('Detector unavailable').waitFor();

  await open('/settings/notifications', 'Notifications');
  await page.getByRole('checkbox', { name: 'PagerDuty' }).check();
  await page.getByRole('button', { name: 'Save preferences' }).click();
  await page.getByText('Preferences saved in this browser.').waitFor();
  await page.reload();
  assert.equal(await page.getByRole('checkbox', { name: 'PagerDuty' }).isChecked(), true);
  await page.getByRole('button', { name: 'Sign out' }).click();
  await page.getByRole('heading', { name: 'Sign in', exact: true }).waitFor();
  assert.equal(await page.evaluate(() => localStorage.getItem('token')), null);
  assert.equal(await page.evaluate(() => JSON.parse(localStorage.getItem('secureflow.notificationPreferences')).pagerduty), true);

  for (const [path, heading] of paths) {
    for (const mode of ['dark', 'light']) {
      await page.evaluate(({ mode, signedIn }) => {
        localStorage.setItem('secureflow-theme', mode);
        if (signedIn) localStorage.setItem('token', 'fixture-token');
        else localStorage.removeItem('token');
      }, { mode, signedIn: path !== '/login' });
      await open(path, heading);
      assert.equal(await page.locator('html').getAttribute('data-theme'), mode);
      const themeScope = page.locator('.workspace, .public-shell');
      assert.equal(await themeScope.getAttribute('data-theme'), mode);
      const textIsCurrent = await themeScope.evaluate((shell, ink) => {
        const canvas = document.createElement('canvas');
        const pixels = canvas.getContext('2d', { willReadFrequently: true });
        function srgb(cssColor) {
          pixels.fillStyle = cssColor;
          pixels.fillRect(0, 0, 1, 1);
          return pixels.getImageData(0, 0, 1, 1).data;
        }
        const expected = srgb(ink);
        const brand = shell.querySelector('.brand');
        return [shell, brand].filter(Boolean).every(element =>
          srgb(getComputedStyle(element).color).every((channel, index) => Math.abs(channel - expected[index]) <= 1)
        );
      }, color[mode].text.hex);
      assert.equal(textIsCurrent, true, `${path} text uses the ${mode} token`);
      await audit(`${path} in ${mode} mode`);
    }
  }

  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const [path, heading] of paths) {
      await page.evaluate(signedIn => {
        if (signedIn) localStorage.setItem('token', 'fixture-token');
        else localStorage.removeItem('token');
      }, path !== '/login');
      await open(path, heading);
      await assertNoOverflow(`${path} at ${width}px`);
      assert.equal(await page.locator('.table-wrap').evaluateAll(tables =>
        tables.some(table => table.scrollWidth > table.clientWidth)), false, `${path} table at ${width}px`);
      if (width === 390) await audit(`${path} on mobile in light mode`);
    }
  }
  assert.deepEqual(pageErrors, []);
  console.log('Passed login, dashboard, scan, finding triage, policy evidence, analytics, notification persistence and sign-out flows.');
  console.log('Passed 40 axe audits and overflow checks on 12 routes at 320, 390, 768 and 1440px.');

  const sessionPage = await context.newPage();
  let refreshes = 0;
  let currentAccess = 'expired';
  await sessionPage.route('**/api/v1/auth/refresh', async route => {
    refreshes++;
    await route.fulfill({ json: { access_token: 'fresh', refresh_token: 'fixture-refresh' } });
  });
  await sessionPage.route('**/api/v1/**', async route => {
    if (route.request().url().includes('/auth/')) return route.fallback();
    if (route.request().headers().authorization === 'Bearer ' + currentAccess) {
      return route.fulfill({ status: 401, json: { detail: 'Session timed out.' } });
    }
    return route.continue();
  });
  await sessionPage.addInitScript(() => {
    if (!localStorage.getItem('session-test-seeded')) {
      localStorage.setItem('session-test-seeded', '1');
      localStorage.setItem('token', 'expired');
      localStorage.setItem('refresh_token', 'fixture-refresh');
    }
  });
  await sessionPage.goto(server.url + '/dashboard');
  await sessionPage.getByText('7 of 16 checks passed across finished scans.').waitFor();
  assert.equal(refreshes, 1);
  currentAccess = 'fresh';
  await sessionPage.unroute('**/api/v1/auth/refresh');
  await sessionPage.route('**/api/v1/auth/refresh', route => route.fulfill({ status: 401, json: { detail: 'Session timed out.' } }));
  await sessionPage.goto(server.url + '/vulnerabilities?finding=v-1');
  await sessionPage.getByText('Your session ended. Sign in to return to your last view.').waitFor();
  currentAccess = 'none';
  await sessionPage.getByLabel('Email address').fill('siva@example.com');
  await sessionPage.getByLabel('Password', { exact: true }).fill('local-fixture-password');
  await sessionPage.getByRole('button', { name: 'Sign in', exact: true }).click();
  await sessionPage.getByRole('dialog', { name: 'S3 Bucket Public Access Not Fully Blocked' }).waitFor();
  assert.equal(new URL(sessionPage.url()).searchParams.get('finding'), 'v-1');
  await sessionPage.close();
  console.log('Passed concurrent session refresh and expired-session return to a finding.');

  const existing = await promisify(execFile)(process.execPath, [new URL('../../frontend/tests/demo-modes.cjs', import.meta.url).pathname], {
    env: { ...process.env, BASE_URL: server.url, CHROME_BIN: executablePath },
  });
  process.stdout.write(existing.stdout);
} finally {
  await browser.close();
  await server.close();
}
