import { access, mkdir } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { serve } from './server.mjs';

const require = createRequire(new URL('../../frontend/package.json', import.meta.url));
const { chromium } = require('playwright-core');
const [dist, output, variant = 'after'] = process.argv.slice(2);
if (!dist || !output || !['before', 'after'].includes(variant)) {
  throw new Error('Usage: node scripts/visual/capture.mjs <dist> <output> <before|after>');
}

const routes = [
  ['01-sign-in', '/login', /sign in/i],
  ['02-overview', '/dashboard', variant === 'before' ? /overview dashboard/i : /cloud posture/i],
  ['03-scans', '/scans', /scan/i],
  ['04-findings', '/vulnerabilities', /findings|vulnerabilities/i],
  ['05-analytics', '/analytics', /log and metric review/i],
  ['06-accounts', '/settings/accounts', /cloud accounts/i],
  ['07-notifications', '/settings/notifications', /notification/i],
  ['08-users', '/settings/users', /directory|users/i],
];

const server = await serve(dist);
await mkdir(output, { recursive: true });
const systemChromium = await access('/usr/bin/chromium').then(() => '/usr/bin/chromium', () => undefined);
const browser = await chromium.launch({
  executablePath: process.env.CHROME_BIN || systemChromium || chromium.executablePath(),
  headless: true,
  args: ['--no-sandbox'],
});
try {
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1000 },
    reducedMotion: 'reduce',
    timezoneId: 'UTC',
    locale: 'en-US',
  });
  await page.addInitScript(() => {
    if (location.pathname !== '/login') {
      localStorage.setItem('token', 'fixture-token');
      localStorage.setItem('refresh_token', 'fixture-refresh');
      localStorage.setItem('user', JSON.stringify({ email: 'siva@example.com' }));
    }
  });
  await page.clock.setFixedTime(new Date('2026-11-22T10:15:00Z'));
  async function open(path, heading) {
    await page.goto(server.url + path);
    await page.getByRole('heading', { name: heading }).first().waitFor();
    await page.evaluate(() => document.fonts.ready);
  }
  async function capture(name) {
    await page.screenshot({ path: resolve(output, name + '.png'), fullPage: true, animations: 'disabled' });
    console.log(name);
  }
  for (const [name, path, heading] of routes) {
    await open(path, heading);
    if (path === '/dashboard') await page.getByText('CIS', { exact: true }).waitFor();
    if (path === '/scans') await page.getByText(/DEMO_COMPLETED|Sample complete/).waitFor();
    if (path === '/vulnerabilities') await page.getByText('S3 Bucket Public Access Not Fully Blocked', { exact: true }).waitFor();
    if (path === '/settings/accounts') await page.getByText('Production AWS Account', { exact: true }).waitFor();
    if (path === '/settings/users') await page.getByText('siva@example.com', { exact: true }).last().waitFor();
    await capture(name);
    if (path === '/dashboard') {
      await page.getByRole('button', { name: 'Switch to light mode' }).click();
      await capture('09-overview-light');
      await page.getByRole('button', { name: 'Switch to dark mode' }).click();
    }
    if (path === '/scans') {
      await page.getByRole('button', { name: variant === 'before' ? 'Trigger Scan' : 'New scan' }).click();
      await page.getByRole('dialog').waitFor();
      await capture('10-scan-dialog');
    }
    if (path === '/vulnerabilities') {
      await page.getByRole('button', { name: /S3 Bucket Public Access Not Fully Blocked/ }).click();
      await page.getByRole('dialog').waitFor();
      await capture('11-finding-detail');
    }
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await open(...routes[1].slice(1));
  await page.getByText('CIS', { exact: true }).waitFor();
  await capture('12-overview-mobile');
  await page.evaluate(() => localStorage.removeItem('token'));
  await open(...routes[0].slice(1));
  await capture('13-sign-in-mobile');
} finally {
  await browser.close();
  await server.close();
}
