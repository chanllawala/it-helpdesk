# IT Helpdesk / Ticket Management System

A full-stack support ticketing system: user/agent/admin roles, ticket CRUD with
priority and category, assignment, a status workflow (Open → In Progress →
Resolved → Closed), a comment thread per ticket, a dashboard with ticket
counts and average resolution time, simulated update notifications (logged to
the `notifications` table and stdout), and search/filtering by status,
priority, assignee, date range, and free text.

## Live demo

**App:** https://it-helpdesk-frontend-3lpf.onrender.com
**API docs (interactive):** https://it-helpdesk-backend-5s1n.onrender.com/docs

Sign in with any of the seeded accounts to see how the role changes what you
can do:

| Email | Password | Role | What they can do |
| --- | --- | --- | --- |
| `admin@helpdesk.example` | `admin123` | admin | Everything |
| `agent@helpdesk.example` | `agent123` | agent | See all tickets, assign, change status |
| `user@helpdesk.example` | `user123` | user | Only their own tickets; no management panel |

> Hosted on Render's free tier, which sleeps after ~15 minutes idle — the first
> request can take 30–60 seconds to wake the service.

## Stack

- **Backend:** FastAPI + SQLAlchemy, JWT auth (`python-jose` +
  `passlib`/`bcrypt`); SQLite locally, PostgreSQL in production
- **Frontend:** React + TypeScript + Vite, React Router
- **Deploy:** Render, provisioned from [`render.yaml`](render.yaml) as
  infrastructure-as-code (web service + static site + managed Postgres)

## What this demonstrates

- **Role-based access control** enforced server-side, not just hidden in the
  UI — a standard user's ticket list is filtered in the query itself, and the
  assign/status endpoints reject non-staff with a 403.
- **A realistic support workflow** — status transitions record `resolved_at` /
  `closed_at` timestamps, which is what makes the dashboard's average
  resolution time a real measurement rather than a decorative number.
- **An auditable history** — every ticket carries its own comment thread, the
  way a real service desk keeps correspondence attached to the case.

## Backend

```bash
cd backend
python -m venv venv
./venv/Scripts/pip install -r requirements.txt   # Windows
# source venv/bin/activate && pip install -r requirements.txt   # macOS/Linux
cp .env.example .env
./venv/Scripts/python -m app.seed                # creates demo users + tickets
./venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

API docs at `http://127.0.0.1:8000/docs`.

Demo accounts (seeded): `admin@helpdesk.example` / `admin123`,
`agent@helpdesk.example` / `agent123`, `user@helpdesk.example` / `user123`.

## Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Runs at `http://localhost:5173` and talks to the API at
`VITE_API_URL` (defaults to `http://127.0.0.1:8000`).

## Roles

- **user** — creates tickets, sees and comments on their own tickets.
- **agent** — sees all tickets, gets assigned tickets, changes status,
  assigns tickets to other agents/admins.
- **admin** — same as agent, plus is the only role that can be granted at
  registration (the very first registered user becomes admin; everyone after
  that registers as a standard user).

## Notes

- SQLite is used for local dev (`backend/helpdesk.db`); swap `DATABASE_URL`
  in `backend/.env` for a Postgres URL to run against Postgres. Render-style
  `postgres://` URLs are rewritten to `postgresql://` automatically, since
  SQLAlchemy 2.x dropped the older scheme.
- The deployed backend seeds demo data on boot. Seeding is idempotent — it
  no-ops once users exist — which is how the demo accounts reach the
  production database, as Render's Shell and Jobs features are paid-only.
- "Notifications" are simulated: each ticket create/assign/status
  change/comment writes a row to the `notifications` table and prints to
  stdout, standing in for a real email/Slack integration.
