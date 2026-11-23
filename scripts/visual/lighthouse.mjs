import { access, mkdir, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { serve } from './server.mjs';

const [dist, output, toolDirectory] = process.argv.slice(2);
if (!dist || !output || !toolDirectory) {
  throw new Error('Usage: node scripts/visual/lighthouse.mjs <dist> <output> <lighthouse install directory>');
}
const tools = createRequire(resolve(toolDirectory, 'package.json'));
const { default: lighthouse } = await import(pathToFileURL(tools.resolve('lighthouse')));
const { launch } = await import(pathToFileURL(tools.resolve('chrome-launcher')));
const require = createRequire(new URL('../../frontend/package.json', import.meta.url));
const { chromium } = require('playwright-core');
const systemChrome = await access('/usr/bin/chromium').then(() => '/usr/bin/chromium', () => undefined);
const server = await serve(dist);
await mkdir(output, { recursive: true });
const chrome = await launch({
  chromePath: process.env.CHROME_BIN || systemChrome || chromium.executablePath(),
  chromeFlags: ['--headless', '--no-sandbox', '--disable-dev-shm-usage'],
});

try {
  const summary = {};
  for (const [name, path] of [['sign-in', '/login'], ['overview', '/dashboard']]) {
    if (name === 'overview') {
      const browser = await chromium.connectOverCDP(`http://127.0.0.1:${chrome.port}`);
      const page = await browser.contexts()[0].newPage();
      await page.goto(server.url + '/login');
      await page.evaluate(() => localStorage.setItem('token', 'fixture-token'));
      await page.close();
      await browser.close();
    }
    const { lhr, report } = await lighthouse(server.url + path, {
      port: chrome.port, output: 'json', logLevel: 'error', disableStorageReset: name === 'overview',
    });
    const metrics = ['largest-contentful-paint', 'first-contentful-paint', 'cumulative-layout-shift', 'total-blocking-time', 'speed-index'];
    summary[name] = {
      lighthouse: lhr.lighthouseVersion,
      chromium: lhr.environment.hostUserAgent.match(/Chrome\/([\d.]+)/)?.[1],
      formFactor: lhr.configSettings.formFactor,
      route: path,
      scores: Object.fromEntries(Object.entries(lhr.categories).map(([key, value]) => [key, Math.round(value.score * 100)])),
      metrics: Object.fromEntries(metrics.map(key => [key, Math.round(lhr.audits[key].numericValue * 100) / 100])),
      failedBinaryAudits: Object.values(lhr.audits).filter(audit => audit.score === 0 && audit.scoreDisplayMode === 'binary').map(audit => audit.id),
    };
    await writeFile(resolve(output, name + '-mobile.json'), report);
  }
  await writeFile(resolve(output, 'mobile-summary.json'), JSON.stringify(summary, null, 2) + '\n');
  console.log(summary);
} finally {
  await chrome.kill();
  await server.close();
}
