# ComplyAI — Contract Intelligence (standalone module)

Runnable web app: **React (Vite) + FastAPI + SQLite**, with **APScheduler** (6-hour) agent runs, **WeChat** + **SMTP** hooks, and **DOCX/PDF** outputs for remediation.

## Judge presentation (frontend-only)

The **current frontend** is a **standalone React app** for courtroom / projector demos — **no backend required**.

```bash
cd complyai/frontend && npm install && npm run dev
```

See **`complyai/frontend/README.md`** for the full judge flow (dashboard, government PDF, upload, 3s update, change summary, download).

## Quick start

### Backend

```bash
cd complyai/backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API: `http://127.0.0.1:8000` — OpenAPI: `/docs`
- SQLite DB and uploads are created under `complyai/backend/data/`
- Requires **SQLAlchemy 2.x** (pinned in `requirements.txt`)

### Frontend

```bash
cd complyai/frontend
npm install
npm run dev
```

- App: `http://localhost:5173`
- Vite proxies `/api` to the backend — run both processes together.

### Demo login

After the first backend start, seed data creates:

- **Email:** `demo@complyai.com`
- **Password:** `demo123`
- Sample contracts (employment / supplier / lease) and two regulations (PIPL-style + Civil Code liability), plus dashboard alerts.

### Manual agent run (admin-style)

```http
POST http://127.0.0.1:8000/api/webhook/scrape
```

Triggers scraper → parser → analyzer → alert pipeline once.

## Configuration

Copy `backend/.env.example` to `backend/.env` and adjust:

- **SMTP_*** — real email delivery; if omitted, email sends are logged only.
- **WECHAT_*** — template messages; if omitted, WeChat sends are logged only.
- **DASHBOARD_BASE_URL** — links inside alert templates.
- **SCRAPER_USE_MOCK_FALLBACK** — when `true`, if a government site cannot be fetched, a deterministic placeholder snapshot is stored so the pipeline remains demonstrable offline.

## Architecture notes

- **Agent 1 — Scraper:** HTTP fetch + hash per source URL; inserts `regulations` when content changes (or mock fallback).
- **Agent 2 — Parser:** Rule-based JSON (`parsed_json`) — affected contract types, clause themes, severity, penalties.
- **Agent 3 — Analyzer:** Re-scores stored `clauses_json` on contracts when new parsed regulations arrive.
- **Agent 4 — Alerts:** Inserts `alerts`, sends email + WeChat when configured.
- **Agent 5 — Updater:** Invoked via `POST /api/contracts/{id}/fix` — Basic produces a guidance DOCX/PDF; Pro can merge compliant text into stored clauses and emit full contract exports.

## Frontend routes

| Route | Purpose |
|-------|---------|
| `/` | Landing |
| `/login`, `/register` | Auth |
| `/dashboard` | Score ring, alerts, quick actions |
| `/contracts` | Table of contracts |
| `/contracts/upload` | Drag-drop upload + analysis redirect |
| `/contracts/:id` | Preview + clause list + fix modal |
| `/alerts` | Filterable alert table |
| `/settings` | Profile + WeChat OpenID |

## License / scope

This is a **standalone module** for product demonstration. Scraping production government sites may be blocked by network policy; use mock fallback or respect site terms and rate limits in real deployments.
