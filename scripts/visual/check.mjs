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
    if (path === '/settings/accounts') await page.getByText('Production AWS Account', { exact: true }).waitFor();
    if (path === '/settings/users') await page.getByText('siva@example.com', { exact: true }).waitFor();
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
  const login = page.waitForRequest(request => request.url().endsWith('/auth/login'));
  await page.getByLabel('Email address').fill('siva@example.com');
  await page.getByLabel('Password').fill('local-fixture-password');
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

  await open('/analytics', 'Log and metric review');
  await page.getByRole('button', { name: 'Review log' }).click();
  await page.getByText('Flagged for review').waitFor();
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

  await page.setViewportSize({ width: 320, height: 900 });
  for (const [path, heading] of paths) {
    await page.evaluate(signedIn => {
      if (signedIn) localStorage.setItem('token', 'fixture-token');
      else localStorage.removeItem('token');
    }, path !== '/login');
    await open(path, heading);
    await assertNoOverflow(path);
  }
  assert.deepEqual(pageErrors, []);
  console.log('Passed login, dashboard, scan dialog, finding review, analytics, notification persistence and sign-out flows.');
  console.log('Passed 24 axe audits and 320px overflow checks on 11 routes.');

  const existing = await promisify(execFile)(process.execPath, [new URL('../../frontend/tests/demo-modes.cjs', import.meta.url).pathname], {
    env: { ...process.env, BASE_URL: server.url, CHROME_BIN: executablePath },
  });
  process.stdout.write(existing.stdout);
} finally {
  await browser.close();
  await server.close();
}
