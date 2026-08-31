# Servio — unified frontend

One Next.js app for the whole Servio product: voice/text/photo intake + live
classification, provider matching & ranking, the bandit research dashboard,
provider admin, and auth. It talks to **two backends**:

| Backend | Default URL | Used for |
|---|---|---|
| Servio dispatch API (`../backend`) | `http://localhost:8000` | `/request` intake, `/chat`, media, WebSocket stage events |
| Provider Match API (`../backend-find-nearby-service`) | `http://localhost:8001` | provider ranking (`/request`), `/feedback`, `/providers`, `/auth/*`, `ws/bandit` |

## Getting started

```bash
cp .env.example .env.local   # optional — the defaults above are baked in
npm install
npm run dev                  # http://localhost:3000
```

Run both backends alongside it (see each backend's README / RUNBOOK).

## Routes

| Route | What |
|---|---|
| `/` | Landing |
| `/request` | Chained flow: voice/text/photo → classification → auto hand-off → ranked providers → select |
| `/chat` | Multi-turn voice assistant chat (full-screen, own shell) |
| `/providers` | Provider directory admin (admin login required) |
| `/dashboard` | Account + live ranking-bandit dashboard (tabs) |
| `/auth/login`, `/auth/register`, `/auth/admin` | Auth (Provider Match backend) |
| `/docs` | Voice recorder docs |

## Layout

- `app/(main)/*` — pages inside the shared `SiteHeader` / `SiteFooter` shell.
- `app/chat/` — outside that shell (keeps its own full-screen dark UI).
- `components/ui/*` — shadcn/ui primitives (the shared design system).
- `components/servio/*` — the intake/classification UI (Servio brand tokens).
- `components/match/*` — provider-matching + bandit UI.
- `components/request/UnifiedRequest.tsx` — wires the intake result into a
  Provider Match `/request` call (`service-type-map.ts` bridges the two
  service-type vocabularies).
- `lib/servio-api.ts`, `lib/match-api.ts`, `lib/useBanditSocket.ts`, `lib/auth.ts`.
