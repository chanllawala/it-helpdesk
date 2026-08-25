# IT Helpdesk / Ticket Management System

A full-stack support ticketing system: user/agent/admin roles, ticket CRUD with
priority and category, assignment, a status workflow (Open → In Progress →
Resolved → Closed), a comment thread per ticket, a dashboard with ticket
counts and average resolution time, simulated update notifications (logged to
the `notifications` table and stdout), and search/filtering by status,
priority, assignee, date range, and free text.

## Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite, JWT auth (`python-jose` +
  `passlib`/`bcrypt`)
- **Frontend:** React + TypeScript + Vite, React Router

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
  in `backend/.env` for a Postgres URL to run against Postgres.
- "Notifications" are simulated: each ticket create/assign/status
  change/comment writes a row to the `notifications` table and prints to
  stdout, standing in for a real email/Slack integration.
