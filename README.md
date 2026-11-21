# Moki

Moki is a personal finance application built as one project: React + Vite frontend, FastAPI backend, and Neon PostgreSQL database. The browser loads the React application and calls the FastAPI endpoints through the same origin (`/api/...`), so the production deployment does not need CORS configuration.

## Features

### v1.2.0 refinements
- User Profile page for editing full name, username, and password. Password changes verify the current password and keep the active session while revoking other sessions.
- Administrator Profile page for editing the administrator username and password with current-password verification.
- Clickable account identity blocks in both sidebars open the respective Profile page.
- Administrator User Management displays itemized Income and Expense entries across months, with month filters.
- Modern month/year picker with explicit month choices; no low-contrast browser-native calendar icon.
- Simplified mobile-friendly user login/register screen and light/dark controls available before signing in to either portal.
- Refined Expense Limit and Create Administrator form layouts. The Moki brand mark now features a cat mascot.

### User workspace
- Username-based registration and sign-in. Usernames are 3–50 characters (`a-z`, `0-9`, `_`); passwords are 6–128 characters.
- Private financial data per account, session cookies, CSRF protection, profile management, and dark/light theme support from the login screen onward.
- Dashboard month selector. Each dashboard metric and chart is calculated for the selected month, including months with no transactions.
- Twelve dashboard cards: ten monthly metrics (Expense Limit, Total Income, Fixed Income, Additional Income, Total Expenses, Fixed Expenses, Additional Expenses, Surplus / Deficit, Fixed Income Balance, and Remaining Fixed Income) plus All-Time Income and All-Time Expenses through the selected month.
- Expense Limit Overview and Fixed Expense Limit Overview.
- Income Allocation donut chart: every expense description is shown as a portion of total income, with Remaining Income as its own component. When expenses exceed income, the deficit is shown separately because a negative remainder cannot be represented as a positive donut slice.
- Expense breakdown grouped by description.
- Bulk Income and Bulk Expense entry. Each submission uses one selected month and can contain multiple rows. Existing records can be edited and deleted.
- Monthly Expense Limits made of Fixed and Additional components. A month with no explicit plan inherits the most recent plan from an earlier month. Before the first plan, the effective limit is Rp0. Adding, editing, or deleting a plan changes the inherited result for subsequent months until the next explicit plan.

### Administrator portal
- Separate administrator sign-in at `/admin` using a username and password.
- Overview statistics for registered, active, inactive, and deleted users and administrators.
- User Management: list and inspect users, view itemized income and expense records by month, deactivate/reactivate accounts, reset user passwords, and soft-delete users.
- Create additional administrator accounts.
- Administrator accounts cannot be deactivated or deleted through the portal. There is no restore or hard-delete action for soft-deleted users in this version.
- Initial administrator account is created from the command line with `python create_admin.py`.

## Technology

- Python 3.12+
- FastAPI, SQLAlchemy 2, Alembic
- Neon PostgreSQL (pooled URL for application traffic; direct URL for migrations)
- React 18, Vite 6, Lucide React
- GitHub and Vercel Hobby

## Project layout

```text
moki/
├── api/
│   └── index.py                 # Vercel FastAPI entry point
├── backend/
│   └── app/
│       ├── core/                # config, database, security, auth dependencies
│       ├── models/              # user, admin, session, income, expense, limit
│       ├── routers/             # API routers
│       ├── schemas/             # request validation
│       └── services/            # Expense Limit inheritance logic
├── frontend/
│   ├── src/                     # React UI
│   └── package.json
├── migrations/                  # Alembic migrations
├── tests/
├── create_admin.py
├── build.py
├── alembic.ini
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── vercel.json
└── .env.example
```

## Local setup on macOS

### 1. Install prerequisites

Install Python 3.12 or newer and Node.js. npm is installed together with Node.js. With Homebrew:

```bash
brew install python@3.12 node
```

Check the versions:

```bash
python3 --version
node -v
npm -v
```

### 2. Create the Python environment

From the extracted `moki` project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

It is fine to keep `.venv` active while running `npm` and `node`; the Python virtual environment does not isolate or disable Node.js.

### 3. Configure Neon

Create a Neon PostgreSQL database. Copy `.env.example` to `.env` and fill in the connection values:

```bash
cp .env.example .env
```

Set:

- `DATABASE_URL`: Neon pooled connection string. Use the hostname containing `-pooler` for application traffic.
- `DIRECT_URL`: Neon direct (non-pooled) connection string. Alembic uses this for schema migrations. It can be the same as `DATABASE_URL` for a local test database, but prefer the direct URL on Neon.
- `APP_ENV=development` for local development.
- `AUTO_CREATE_TABLES=false`. Use Alembic migrations rather than automatic table creation.

### 4. Create / migrate the database

For a new, empty database, apply all migrations:

```bash
alembic upgrade head
```

For an existing database created by the previous Moki ZIP, first back up Neon. Then check the migration state:

```bash
alembic current
```

- If the database is already at `0001_initial`, run `alembic upgrade head`.
- If it contains the old Moki v1 tables but has no Alembic version record (the earlier ZIP could create tables with `AUTO_CREATE_TABLES=true`), mark that existing schema as the initial revision, then apply the new migration:

```bash
alembic stamp 0001_initial
alembic upgrade head
```

- If the database is empty, do not run `stamp`; use `alembic upgrade head` directly.

The new migration converts existing email local-parts into usernames (adding a suffix if two users share the same local-part), invalidates old sessions, and removes the obsolete Expense Standards reference-catalogue table and email column. Existing password hashes, Income, Expense, and monthly Expense Limit plans are retained. Any rows that existed only in the old standalone Expense Standards catalogue are not imported; that catalogue is retired because Moki now uses the monthly Expense Limit plan as the single source of spending limits.

### 5. Create the first administrator

```bash
python create_admin.py
```

Enter an administrator username and password when prompted. Passwords must contain at least 6 characters. The initial administrator is not created automatically, so an administrator must be deliberately provisioned by the project owner.

### 6. Install frontend packages

```bash
npm install --prefix frontend
```

### 7. Run the application

Open two Terminal tabs, both from the project root. Keep `.venv` active in the backend tab.

Backend:

```bash
uvicorn backend.app.main:app --reload --env-file .env
```

Frontend:

```bash
npm run dev --prefix frontend
```

Open `http://localhost:5173`. Vite proxies `/api` requests to FastAPI on `http://127.0.0.1:8000`, so local development also uses one browser origin and does not require CORS.

The administrator portal is available at `http://localhost:5173/admin`.

## Database migration notes

When applying a migration to a remote Neon database, make sure the direct connection string is set in `.env` as `DIRECT_URL`. Alembic loads `.env` automatically and uses `DIRECT_URL` for migrations.

The migration from the previous Moki ZIP removes only the obsolete `expense_standards` table and unused email field. It does not delete Income, Expense, or Expense Limit data. Old login sessions are intentionally invalidated because Moki now uses session-bound CSRF tokens and separate user/admin sessions; users need to sign in again after upgrading. Take a database backup before running an upgrade on existing data.

## Deploy to Vercel Hobby

1. Push the complete `moki` directory to a GitHub repository. Keep the repository root as the Vercel Root Directory.
2. Import that repository into Vercel.
3. Vercel detects the FastAPI app from `api/index.py`. The build script in `pyproject.toml` runs `python build.py`, which installs the frontend packages and builds React into `frontend/dist`.
4. Add these Environment Variables in Vercel:
   - `DATABASE_URL`: Neon pooled connection string.
   - `DIRECT_URL`: Neon direct connection string (needed when running Alembic migrations from a trusted local shell; it is not required by the running application if migrations have already been applied).
   - `APP_ENV=production`.
   - `AUTO_CREATE_TABLES=false`.
   - `SESSION_DAYS=30`.
5. Apply `alembic upgrade head` to Neon before opening the deployed app.
6. Create the initial admin using `python create_admin.py` with the same Neon `DATABASE_URL` loaded in the local shell, then deploy / visit `/admin`.

The application serves React and FastAPI from the same Moki app and domain. React API requests use relative `/api` paths. Vercel promotes FastAPI frontend/static-file routes to its CDN when supported by the installed FastAPI runtime; the Python FastAPI application remains the owner of the API routes.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/auth/csrf` | Issue pre-auth CSRF cookie |
| POST | `/api/auth/register` | Register with username and password |
| POST | `/api/auth/login` | User login |
| GET | `/api/auth/me` | Current user |
| PATCH | `/api/auth/profile` | Update full name, username, and optionally password |
| POST | `/api/auth/logout` | User logout |
| GET | `/api/dashboard?month=YYYY-MM` | Selected-month dashboard |
| GET / POST | `/api/incomes` | List / create income (bulk creation endpoint below) |
| POST | `/api/incomes/bulk` | Bulk income for one month |
| PATCH / DELETE | `/api/incomes/{id}` | Edit / delete income |
| GET / POST | `/api/expenses` | List / create expense (bulk creation endpoint below) |
| POST | `/api/expenses/bulk` | Bulk expense for one month |
| PATCH / DELETE | `/api/expenses/{id}` | Edit / delete expense |
| GET | `/api/expense-limits?month=YYYY-MM` | Effective limit for a month |
| GET | `/api/expense-limits/history` | Explicit limit history |
| PUT / DELETE | `/api/expense-limits/{YYYY-MM}` | Set / remove a month's explicit limit |
| GET | `/api/admin/csrf` | Issue admin pre-auth CSRF cookie |
| POST | `/api/admin/login` | Administrator login |
| GET | `/api/admin/me` | Current administrator |
| PATCH | `/api/admin/profile` | Update administrator username and optionally password |
| GET | `/api/admin/dashboard` | Admin overview statistics |
| GET | `/api/admin/users` | User list |
| GET | `/api/admin/users/{id}` | User detail, transaction totals, and itemized income/expense records |
| POST | `/api/admin/users/{id}/status` | Deactivate / reactivate user |
| POST | `/api/admin/users/{id}/password` | Reset user password |
| POST | `/api/admin/users/{id}/delete` | Soft-delete user |
| GET / POST | `/api/admin/administrators` | List / create administrator accounts |
| POST | `/api/admin/logout` | Administrator logout |

## Verification

Run the tests from the project root with `.venv` active:

```bash
python -m pytest -q
python -m compileall -q backend api create_admin.py
```

Build the frontend:

```bash
npm run build --prefix frontend
```
