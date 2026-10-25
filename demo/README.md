# Demo

Angular 22 (SSR) interface of the anonymiser. See the [main README](../README.md) for how the
system works and how to launch it.

## Development

Node 24, with the core API running on port 8000:

```bash
npm install
npm start          # dev server on http://localhost:4200
npm test           # unit tests (Vitest)
npm run build      # production build (dist/)
```

## Calls to the core API

The browser only calls the demo's own origin (`/api/...`); the SSR server (`src/server.ts`)
forwards these calls to the core API, which therefore needs no CORS setup nor public exposure.

| Variable | Default | Purpose |
|---|---|---|
| `CORE_API_URL` | `http://localhost:8000` | Core API the `/api` calls are forwarded to |
| `CORE_API_TIMEOUT_MS` | `300000` | Maximum time for one anonymisation |
| `NG_ALLOWED_HOSTS` | `localhost,127.0.0.1` (compose) | Host names accepted by the SSR server: add your domain when deploying |
| `PORT` | `4000` | Port of the SSR server (published as 4200 by compose) |

## Conventions

- Translations in `src/assets/i18n/{en,fr}.json` (keys sorted alphabetically), bundled at build
  time. French by default, then the browser language or the user's choice.
- Colours and radius are CSS variables in `src/styles.scss`; the Sora font is self-hosted.
- Documents are rendered from Markdown with `marked`: the text is HTML-escaped first and Angular's
  sanitizer runs on the result, so a PDF can never inject markup; links are shown as plain text.
