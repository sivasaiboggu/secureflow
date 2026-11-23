import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { gzipSync } from 'node:zlib';
import { resolve, extname } from 'node:path';
import { createFixture } from './fixtures.mjs';

const mime = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html', '.woff2': 'font/woff2', '.svg': 'image/svg+xml', '.png': 'image/png', '.webmanifest': 'application/manifest+json' };

export async function serve(dist, port = 0) {
  const root = resolve(dist);
  const fixture = createFixture();
  const server = createServer(async (req, res) => {
    const { pathname, searchParams } = new URL(req.url, 'http://localhost');
    if (pathname.startsWith('/api/v1/')) {
      let body;
      if (req.method === 'PATCH') {
        const chunks = [];
        for await (const chunk of req) chunks.push(chunk);
        try {
          body = JSON.parse(Buffer.concat(chunks).toString());
        } catch {
          res.writeHead(400).end();
          return;
        }
      } else {
        req.resume();
      }
      const data = fixture(pathname.slice('/api/v1'.length), req.method, searchParams, body);
      res.writeHead(data === null ? 404 : 200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(data));
      return;
    }
    // Baseline builds use a relative asset base, including on nested routes.
    const assetPath = pathname.match(/\/assets\/[^/]+$/)?.[0] || pathname;
    const target = resolve(root, '.' + assetPath);
    if (!target.startsWith(root + '/') && target !== root) {
      res.writeHead(404).end();
      return;
    }
    const file = extname(target) ? target : resolve(root, 'index.html');
    try {
      const ext = extname(file);
      const body = await readFile(file);
      const headers = { 'Content-Type': mime[ext] || 'application/octet-stream' };
      if (assetPath.startsWith('/assets/')) headers['Cache-Control'] = 'public, max-age=31536000, immutable';
      if (['.js', '.css', '.html'].includes(ext) && req.headers['accept-encoding']?.includes('gzip')) {
        headers['Content-Encoding'] = 'gzip';
        headers.Vary = 'Accept-Encoding';
        res.writeHead(200, headers).end(gzipSync(body));
        return;
      }
      res.writeHead(200, headers).end(body);
    } catch {
      res.writeHead(404).end();
    }
  });
  await new Promise((done, reject) => {
    server.once('error', reject);
    server.listen(port, '127.0.0.1', done);
  });
  return {
    url: `http://127.0.0.1:${server.address().port}`,
    close: () => new Promise(done => server.close(done)),
  };
}
