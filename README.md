# ILI pika

> A student-focused personal finance web application built with Flask and MySQL.

![CI](https://github.com/DragonsGames/student-money-app/actions/workflows/ci.yml/badge.svg)

ILI pika is a personal money-management web app designed for students who want a simple way to understand where their money goes, plan spending, build savings, and know how much is genuinely safe to spend.

It began as my CS50 final project and grew into a complete full-stack application with authentication, onboarding, transactions, budgets, savings goals, multilingual support, RTL layouts, dark mode, automated testing, and CI.

---

## Why I built it

Student finances are often irregular. A student may receive a weekly or monthly allowance, occasional income, money from family, part-time earnings, or one-time payments.

At the same time, they may want to track daily spending, stay within category budgets, save for something specific, and avoid spending money they already mentally reserved.

ILI pika is built around that reality.

Instead of treating every planned source of money as already available, the app separates actual transactions, income-source planning, budgets, savings, and current balance.

---

## Core features

### Authentication and onboarding

- Account registration and login
- Password hashing with Werkzeug
- Remember-me support
- POST-only logout with CSRF protection
- Five-step onboarding flow
- Redirects incomplete users back to onboarding
- Already-authenticated users skip the public landing page and go directly to the appropriate app page

### Transactions

- Add income and expenses
- Edit and delete transactions
- Custom descriptions and transaction dates
- User-owned categories
- Future transaction dates are rejected
- Category type must match transaction type
- User ownership is enforced server-side

### Categories

- Separate income and expense categories
- Custom category names
- Emoji/icon picker
- Native color picker plus curated swatches
- Safe `#RRGGBB` validation
- Used categories are protected from unsafe deletion
- Budgeted expense categories cannot be converted to income categories

### Budgets

- Category-level budgets
- Weekly or monthly budget periods
- Current-period spending
- Remaining budget and overspending state
- Per-category progress
- Global budget summary
- Unbudgeted expenses stay separate from budget usage

### Savings goals

- Create, edit, and delete savings goals
- Target amount and optional target date
- Add or withdraw saved money
- Completion and overfunding support
- Savings progress does not create transactions or change current balance

### History

- Filter by transaction type, category, and date range
- Sort by newest, oldest, highest amount, or lowest amount
- Filtered count, income, expense, and net summaries
- User-scoped results only
- Separate empty states for no history and no matching results

### Dashboard

The dashboard brings together:

- Current balance
- Safe-to-Spend
- Budget progress
- Savings progress
- Recent transactions
- Quick actions
- Contextual next-step guidance

---

## Safe-to-Spend

One of the main custom features in ILI pika is the **Safe-to-Spend** calculation.

Current balance is:

```text
starting balance
+ actual income transactions
- actual expense transactions
```

Safe-to-Spend then protects money already reserved for savings and remaining budgets:

```text
raw safe to spend
=
current balance
- savings reserved
- budget reserved
```

Where:

```text
savings reserved
=
sum of SavingsGoal.saved_amount
```

and:

```text
budget reserved
=
sum of max(budget amount - current-period spending, 0)
for every budget
```

The per-budget clamp matters.

Example:

```text
Food budget:       100
Food spent:        150
Food reserve:        0

Transport budget:  100
Transport spent:     0
Transport reserve: 100
```

The total budget reserve is `100`, not `50`.

Overspending one category never frees money reserved for another category.

If the raw result is negative, the displayed Safe-to-Spend amount is `0`, while the app keeps the real shortfall so the user can understand that their planned commitments exceed their current balance.

Expected or scheduled income sources are deliberately excluded until money is recorded as an actual transaction.

---

## Internationalization

ILI pika currently supports:

- English
- French
- Arabic

Arabic includes RTL layout support.

The localization system covers navigation, forms, validation messages, flash messages, financial summaries, empty states, settings, onboarding, landing/auth pages, and accessibility labels.

Stable internal values such as `income`, `expense`, `weekly`, and `monthly` remain language-independent in the database.

---

## Appearance

The interface supports:

- System theme
- Light mode
- Dark mode

Authenticated users have their preference stored in `UserSettings`.

Anonymous visitors can still use theme and language preferences on public pages.

The visual identity is warm, compact, student-friendly, and inspired by the pika animal without becoming cartoon-like.

---

## Security

Current protections include:

- Password hashing
- Flask-WTF CSRF protection
- POST-only destructive operations
- Per-user ownership checks
- Foreign user resources return `404` where appropriate
- Category ownership/type validation
- Open-redirect protection
- Safe category color validation
- Jinja autoescaping
- `HttpOnly` cookies
- `SameSite=Lax`
- Environment-controlled secure cookies for HTTPS deployment
- Conservative cache headers for authenticated HTML
- Security response headers including:
  - `X-Content-Type-Options`
  - `X-Frame-Options`
  - `Referrer-Policy`
  - `Permissions-Policy`
- No hardcoded production debug mode

No custom cryptography is used.

---

## Testing

The project has an automated test suite built with `pytest`.

Current result:

```text
112 tests passed
94% overall coverage
```

The core financial services currently have 100% coverage:

- `services/finance.py`
- `services/budgets.py`
- `services/savings.py`
- `services/safe_to_spend.py`

The tests cover:

- registration and login
- logout
- onboarding
- redirects
- transactions
- categories
- budgets
- savings
- history filters
- settings
- localization and RTL
- Safe-to-Spend
- Decimal money boundaries
- CSRF
- HTTP method safety
- ownership/IDOR attempts
- open redirects
- error pages
- migration behavior
- a full user workflow

Tests use isolated temporary databases and never operate on the normal development database.

Run the suite:

```bash
python -m pytest
```

Run with coverage:

```bash
python -m pytest --cov=app --cov=forms --cov=localization --cov=models --cov=routes --cov=services --cov-report=term-missing
```

---

## Continuous Integration

GitHub Actions runs CI on pushes and pull requests.

The workflow:

1. Checks out the repository
2. Sets up Python 3.11
3. Starts an isolated MySQL 8.4 service
4. Installs runtime and development dependencies
5. Runs `pip check`
6. Compiles the Python source
7. Runs Ruff
8. Migrates an empty MySQL database to the current Alembic head
9. Runs the full pytest suite with coverage

This catches missing dependencies, migration problems, syntax issues, Linux/Windows differences, and application regressions.

---

## Technology stack

### Backend

- Python 3.11
- Flask
- Flask-Login
- Flask-WTF
- WTForms
- Flask-SQLAlchemy
- SQLAlchemy
- Flask-Migrate
- Alembic
- Werkzeug

### Database

- MySQL
- PyMySQL

### Frontend

- Jinja
- HTML
- CSS
- Bootstrap CSS
- Vanilla JavaScript
- Local SVG assets

### Development and quality

- pytest
- pytest-cov
- Ruff
- GitHub Actions

---

## Money precision

Money is not stored or calculated using binary floating-point values.

The application uses `Decimal` in Python and `NUMERIC(12,3)` in the database.

The maximum supported monetary value is:

```text
999999999.999
```

This avoids binary floating-point errors in financial calculations.

---

## Project structure

```text
student-money-app/
│
├── app.py
├── extensions.py
├── forms.py
├── localization.py
├── models.py
│
├── routes/
│   ├── auth.py
│   ├── budgets.py
│   ├── categories.py
│   ├── dashboard.py
│   ├── guards.py
│   ├── history.py
│   ├── onboarding.py
│   ├── public.py
│   ├── savings.py
│   ├── settings.py
│   └── transactions.py
│
├── services/
│   ├── budgets.py
│   ├── finance.py
│   ├── safe_to_spend.py
│   └── savings.py
│
├── templates/
├── static/
├── migrations/
├── tests/
│
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── .github/
    └── workflows/
        └── ci.yml
```

---

# Local setup

## 1. Clone the repository

```bash
git clone https://github.com/DragonsGames/student-money-app.git
cd student-money-app
```

## 2. Create a virtual environment

Windows:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

For development/testing:

```bash
python -m pip install -r requirements-dev.txt
```

## 4. Configure environment variables

Copy `.env.example` to `.env` and fill in your local configuration.

The application expects a secret key and MySQL connection settings.

Never commit `.env`.

## 5. Create the MySQL database

Create a local MySQL database and user matching the values in `.env`.

The schema itself is managed with Alembic migrations.

## 6. Apply migrations

```bash
flask db upgrade
```

## 7. Run the app

```bash
python app.py
```

Then open the local URL printed by Flask.

---

## Useful migration commands

Current revision:

```bash
flask db current
```

Migration head:

```bash
flask db heads
```

Upgrade:

```bash
flask db upgrade
```

---

## Error handling

The application includes branded handlers for:

- `404 Not Found`
- `405 Method Not Allowed`
- `500 Internal Server Error`

Internal exception details are not intentionally exposed to users.

---

## Accessibility

The project includes:

- semantic headings
- visible focus states
- skip navigation
- form labels
- localized validation errors
- accessible button labels
- reduced-motion support
- semantic progress elements
- status information expressed through text as well as color
- Arabic RTL support
- LTR isolation for financial values within RTL pages

---

# CS50 final project

ILI pika was developed as my CS50 final project.

The architecture was intentionally kept understandable and maintainable:

- Flask server-rendered pages
- SQLAlchemy models
- MySQL
- WTForms
- Jinja
- vanilla JavaScript
- normal CSS

I deliberately avoided turning the project into a large SPA or adding infrastructure purely for complexity.

---

# AI assistance disclosure

AI tools, including ChatGPT and OpenAI Codex, were used during development as engineering assistants.

They were used for tasks including:

- explaining concepts while I learned Flask, SQLAlchemy, WTForms, migrations, and testing
- reviewing code and debugging errors
- helping structure implementation steps
- assisting with the visual redesign
- identifying edge cases and security concerns
- helping draft portions of automated tests and CI configuration
- reviewing localization and RTL behavior
- assisting with documentation

The product direction, feature decisions, financial rules, manual testing, iteration, and final review remained under my control.

Important financial behavior was explicitly reviewed and tested, including:

- starting balance is separate from transaction income
- `IncomeSource` does not automatically create money
- savings progress does not mutate transaction balance
- budget usage is based on actual expense transactions
- Safe-to-Spend reserves remaining budget per category
- money calculations use decimal-safe arithmetic

AI-assisted code was reviewed and adapted before being accepted into the project.

This disclosure is included to be transparent about how AI tools were used during development.

---

## Current status

Core application development is complete.

```text
112 automated tests passing
94% overall coverage
GitHub Actions CI passing
MySQL migration CI passing
Ruff passing
Python compile checks passing
```

Remaining work is primarily deployment configuration, the final CS50 demo video, screenshots/project presentation, and final submission preparation.

---

## Future possibilities

Intentionally outside the current MVP:

- automatic recurring-income transactions
- notifications/reminders
- advanced analytics and charts
- CSV import/export
- optional AI financial guidance
- pagination for very large histories
- additional deployment-specific hardening

---

## Author

**Mohammed Sellami**

Built as a CS50 final project and developed into a portfolio-ready student finance application.

Repository: https://github.com/DragonsGames/student-money-app
