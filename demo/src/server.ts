import {
  AngularNodeAppEngine,
  createNodeRequestHandler,
  isMainModule,
  writeResponseToNodeResponse,
} from '@angular/ssr/node';
import express from 'express';
import { join } from 'node:path';
import { Readable } from 'node:stream';
import type { ReadableStream as NodeReadableStream } from 'node:stream/web';

const browserDistFolder = join(import.meta.dirname, '../browser');
const coreApiUrl = (process.env['CORE_API_URL'] ?? 'http://localhost:8000').replace(/\/$/, '');
const coreApiTimeoutMs = Number(process.env['CORE_API_TIMEOUT_MS'] ?? 300_000);

// Request headers forwarded to the core API; everything else (cookies, auth...) stays here
const FORWARDED_REQUEST_HEADERS = ['accept', 'content-type', 'content-length'];
// Response headers that must not be copied: the body is re-streamed by this server
const SKIPPED_RESPONSE_HEADERS = new Set([
  'connection',
  'content-encoding',
  'content-length',
  'transfer-encoding',
]);

const app = express();
const angularApp = new AngularNodeAppEngine();

/**
 * Same-origin proxy to the core anonymisation API: the browser never talks to it directly,
 * so the API needs no CORS setup nor public exposure.
 */
app.use('/api', async (req, res) => {
  const headers = new Headers();
  for (const name of FORWARDED_REQUEST_HEADERS) {
    const value = req.headers[name];
    if (typeof value === 'string') {
      headers.set(name, value);
    }
  }
  const hasBody = !['GET', 'HEAD'].includes(req.method);
  try {
    const upstream = await fetch(`${coreApiUrl}${req.url}`, {
      method: req.method,
      headers,
      body: hasBody ? (Readable.toWeb(req) as ReadableStream) : undefined,
      duplex: 'half',
      signal: AbortSignal.timeout(coreApiTimeoutMs),
    } as RequestInit);
    res.status(upstream.status);
    upstream.headers.forEach((value, name) => {
      if (!SKIPPED_RESPONSE_HEADERS.has(name)) {
        res.setHeader(name, value);
      }
    });
    if (upstream.body) {
      Readable.fromWeb(upstream.body as NodeReadableStream).pipe(res);
    } else {
      res.end();
    }
  } catch (error) {
    const timedOut = error instanceof DOMException && error.name === 'TimeoutError';
    res.status(timedOut ? 504 : 502).json({ detail: 'The anonymization service is unavailable.' });
  }
});

/**
 * Serve static files from /browser
 */
app.use(
  express.static(browserDistFolder, {
    maxAge: '1y',
    index: false,
    redirect: false,
  }),
);

/**
 * Handle all other requests by rendering the Angular application.
 */
app.use((req, res, next) => {
  angularApp
    .handle(req)
    .then((response) => (response ? writeResponseToNodeResponse(response, res) : next()))
    .catch(next);
});

/**
 * Start the server if this module is the main entry point, or it is ran via PM2.
 * The server listens on the port defined by the `PORT` environment variable, or defaults to 4000.
 */
if (isMainModule(import.meta.url) || process.env['pm_id']) {
  const port = process.env['PORT'] || 4000;
  app.listen(port, (error) => {
    if (error) {
      throw error;
    }

    console.log(`Node Express server listening on http://localhost:${port}`);
  });
}

/**
 * Request handler used by the Angular CLI (for dev-server and during build) or Firebase Cloud Functions.
 */
export const reqHandler = createNodeRequestHandler(app);
