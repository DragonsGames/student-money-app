# ILI pika
#### Video Demo: <https://youtu.be/y8OhW_vO9to>

#### Description: 

ILI pika is my CS50x final project. It is a student-focused personal finance web application built with Python, Flask, MySQL, SQLAlchemy, Jinja, HTML, CSS, and JavaScript.

I wanted to make something that I could realistically imagine using as a student. Student money is usually irregular: weekly allowance, monthly allowance, money from family, part-time work, or one-time payments. At the same time, students may want to control spending, save for something, and still know how much money is really safe to use.

At first I expected this project to be much smaller. I thought I would build a local Flask app with transactions and a dashboard. While working on it, I became more ambitious and added a real MySQL database, migrations, authentication, onboarding, budgets, savings goals, categories, filtering, settings, three languages, RTL support for Arabic, themes, automated tests, and GitHub Actions CI. I probably got a little carried away compared with a simple MVP, but that also made this project a much bigger learning experience for me.

The application is called **ILI pika**. The visual identity is inspired by the pika animal. I wanted it to feel friendly and student-focused without looking like a toy or a generic banking dashboard.

---

## Main features

A user can register with an email and password. Passwords are hashed and authentication is handled with Flask-Login.

After registration, the user goes through onboarding. The onboarding flow asks for basic profile information, goals, income information, starting balance, and starter categories. I added onboarding because I did not want a new user to arrive at a completely empty dashboard.

After onboarding, the main application includes:

- Dashboard
- Transactions
- Budgets
- Savings
- Categories
- History
- Settings

Transactions can be income or expenses. Each transaction belongs to the current user and a category. Users can create, edit, and delete their own transactions. Ownership is checked on the server so changing an ID in the URL does not allow access to another user's data.

Categories can have a custom name, type, icon, and color. I added rules so that categories cannot be changed or deleted in ways that would break existing transaction or budget data.

Budgets are category-based. The user chooses weekly or monthly budgeting in settings. The app calculates spending in the current period, remaining budget, and whether a budget is overspent.

Savings goals have a target amount, saved amount, and optional target date. The user can add or withdraw savings progress.

One important design decision is that savings progress does **not** automatically reduce the transaction balance. The money is still part of the user's balance, but it is treated as reserved in Safe-to-Spend.

Another important decision is that planned income sources do **not** count as money the user currently has. An `IncomeSource` can describe expected or recurring income, but current balance changes only when real income transactions are recorded.

---

## Safe-to-Spend

The feature I consider most specific to this project is **Safe-to-Spend**.

Current balance is:

```text
starting balance
+ actual income transactions
- actual expense transactions
```

Safe-to-Spend then protects money that is already reserved:

```text
Safe-to-Spend
=
current balance
- savings reserved
- remaining budget reserves
```

The budget reserve is calculated per budget.

Example:

```text
Food budget: 100
Food spent: 150

Transport budget: 100
Transport spent: 0
```

Food has no remaining reserve because it is already overspent, but Transport still has 100 reserved. The total reserve is therefore 100, not 50.

I chose this behavior because overspending one category should not free money that was still reserved for another category.

If the raw Safe-to-Spend result becomes negative, the app displays 0 as the safe amount while still tracking the shortfall.

---

## Money precision

I learned that normal floating-point numbers can create precision problems with money.

For that reason, the project uses Python `Decimal` values and SQL `NUMERIC(12,3)` fields.

The maximum supported monetary value is:

```text
999999999.999
```

This was one of the areas where the project became more serious than my original plan because I started thinking about edge cases and exact validation instead of only making the normal path work.

---

## Project files

### `app.py`

Contains the Flask application factory and main app configuration. It initializes the application, registers blueprints, configures extensions, error handlers, security-related headers, and application behavior.

While working on this project I learned more about Flask application factories and why larger Flask apps should not put everything in one file.

### `extensions.py`

Contains extensions such as SQLAlchemy, Flask-Migrate, and Flask-Login so they can be initialized separately from the Flask app.

### `models.py`

Contains the SQLAlchemy database models.

The main models include:

- `User`
- `UserSettings`
- `IncomeSource`
- `Category`
- `UserGoal`
- `Transaction`
- `Budget`
- `SavingsGoal`

It defines the database structure and relationships between those objects.

### `forms.py`

Contains Flask-WTF / WTForms forms and validation for authentication, onboarding, transactions, categories, budgets, savings, and settings.

### `localization.py`

Contains the lightweight localization system.

ILI pika supports:

- English
- French
- Arabic

Arabic also changes the interface to RTL.

### `routes/`

Contains the Flask blueprints for the different parts of the application.

Important files include:

- `auth.py`
- `onboarding.py`
- `dashboard.py`
- `transactions.py`
- `categories.py`
- `budgets.py`
- `savings.py`
- `history.py`
- `settings.py`
- `public.py`
- `guards.py`

### `services/`

Contains financial logic separated from the routes:

- `finance.py`
- `budgets.py`
- `savings.py`
- `safe_to_spend.py`

I separated these calculations because I did not want all financial logic mixed directly into route functions. It also made the logic easier to test.

### `templates/`

Contains Jinja templates for the landing page, authentication, onboarding, dashboard, transactions, budgets, savings, categories, history, settings, error pages, and reusable UI components.

### `static/`

Contains the CSS, JavaScript, icons, and ILI pika visual assets.

### `migrations/`

Contains the Alembic / Flask-Migrate migration history.

Before this project, I had not worked deeply with database migrations. I learned how to create a database, configure a MySQL user, apply migrations, check the current revision, check migration heads, and rebuild the schema from an empty database.

### `tests/`

Contains the pytest test suite.

There are currently **112 automated tests** covering authentication, onboarding, transactions, budgets, savings, categories, history, localization, security, financial calculations, migration behavior, and a full user flow.

Current overall coverage is around **94%**.

### `.github/workflows/ci.yml`

Contains the GitHub Actions CI workflow.

It creates a clean Linux environment, starts MySQL 8.4, installs dependencies, runs code checks, applies migrations to an empty database, and runs the test suite.

This taught me an important lesson because my tests passed locally on Windows while CI failed at first. One issue was how pytest imported the app, and another was a Windows/Linux file-ordering difference. Fixing those problems helped me understand why "it works on my machine" is not enough.

---

## MySQL and database work

One of the biggest new things I learned was how to work with MySQL in a real project.

I learned how to:

- create a database
- create a database user
- configure credentials with environment variables
- connect Flask and SQLAlchemy to MySQL
- define relationships
- use foreign keys and unique constraints
- use `Numeric` for money
- use Flask-Migrate and Alembic
- apply and inspect migrations
- test migrations on an empty database

I also learned why migrations matter when the structure of an application changes over time.

---

## Git and GitHub

I became much more comfortable with Git and GitHub during this project.

I used Git to create checkpoints while the application evolved instead of manually copying project folders.

Commands I used regularly include:

```bash
git status
git add
git commit
git push
```

I also learned how GitHub Actions connects to a repository and how a push can automatically create a clean test run.

Before this project, Git and GitHub felt more like tools I knew about. During this project, they became part of my normal development process.

---

## Flask and command-line learning

This project also forced me to become more comfortable with the command line and virtual environments.

I learned how to:

- create and activate a virtual environment
- select the correct Python interpreter
- install dependencies
- run Flask applications
- run pytest
- run coverage
- use Flask-Migrate commands
- debug PowerShell path problems
- understand the difference between my local Windows environment and GitHub's Linux environment

I also learned Flask in more depth, including:

- application factories
- blueprints
- routes
- decorators
- Flask-Login
- forms
- CSRF
- Jinja
- redirects
- HTTP methods
- error handlers
- SQLAlchemy sessions
- server-side ownership checks

---

## Security and ownership

I tried to make this behave like a real multi-user application instead of assuming users would only use the interface normally.

A user cannot change a URL ID to edit or delete another user's transaction, budget, savings goal, category, or income source.

The project also uses:

- CSRF protection
- POST-only destructive actions
- password hashing
- safer redirect validation
- cookie settings
- Jinja autoescaping
- category color validation
- custom 404, 405, and 500 pages

This project made the difference between authentication ("who are you?") and authorization ("are you allowed to access this resource?") much clearer to me.

---

## Design choices I debated

A lot of the work was not only writing code. I had to decide what the app should actually mean.

### Should expected income affect balance?

I decided no.

An expected allowance or payment is not money the user currently has. Only actual income transactions change current balance.

### Should adding money to a savings goal reduce balance?

I decided no.

The savings goal represents reserved money, not a bank transfer. It reduces Safe-to-Spend instead.

### Should overspending one category reduce another category's reserve?

I decided no.

Budget reserves are calculated separately per category.

### Should starting balance count as income?

I decided no.

Starting balance represents money that existed before the transaction history started.

### Should I stop at a simple local MVP?

Originally, yes.

But I became interested in making the project feel more complete. That is why I added MySQL, migrations, stronger security, tests, CI, localization, and a much more polished interface.

I probably became more ambitious than was necessary for the assignment, but I learned much more because of it.

---

## AI use and academic honesty

I used external AI tools during this final project, mainly ChatGPT and OpenAI Codex.

I want to describe that clearly because AI was a significant helper in this project, but it did not choose the project for me or decide what the product should be.

The original idea, product direction, feature decisions, financial behavior, what I accepted or rejected, manual testing, and overall vision were mine.

I planned the application step by step and repeatedly decided how each feature should behave before accepting an implementation.

I also manually ran the project throughout development, found problems, tested fixes, changed behavior, and continued improving it over time.

### AI for learning

ChatGPT helped explain Flask, SQLAlchemy, WTForms, MySQL, migrations, Git, GitHub, testing, CSRF, authorization, and debugging while I was building the project.

This was useful because I could ask why something was failing instead of only getting a final answer.

### AI for planning

I used ChatGPT to turn my feature ideas into smaller steps and later into detailed Codex prompts.

Learning how to manage a coding-agent prompt became part of the experience for me.

I learned that telling an AI "make this application" is not enough if I want to stay in control. My later prompts became specific about:

- what could be changed
- what should not be changed
- expected behavior
- financial rules
- database rules
- security requirements
- testing requirements
- what files should be reviewed
- when Codex should stop and report instead of continuing

### AI for implementation

AI-assisted code generation was significant.

A rough estimate, not a measured line count, is that the final literal code may be around **40–50% directly written by me and around 50–60% AI-assisted or AI-generated**.

I do not think line count tells the full story because automatically generated tests and UI code can be much longer than the small product rules they implement or verify.

My contribution was much higher in decisions, behavior, testing, debugging, and direction.

My rough personal estimate is:

- original idea/problem: around 95–100% mine
- product vision: around 90–95% mine
- feature decisions: around 85–95% mine
- financial behavior/rules: around 80–90% mine
- manual testing and deciding whether behavior was correct: mostly mine
- final code typing/implementation: much more mixed between me and AI

These percentages are only my attempt to describe the collaboration honestly. They are not measured statistics.

### AI-heavy UI redesign

The application already existed and worked before the final visual redesign.

Later I used AI much more heavily to improve the appearance, mobile layout, themes, localization presentation, and general polish.

This was one of the most AI-heavy parts of the project.

I gave the design direction, rejected styles I did not want, described the feeling and constraints I wanted, and manually tested the result, but Codex wrote a large part of the final UI implementation.

### AI-heavy testing and CI phase

AI also helped heavily with the final testing and engineering-hardening phase.

Codex helped create many automated tests, CI configuration, and quality checks.

I then ran them, reviewed failures, manually tested the application, and fixed issues that appeared.

For example, the suite passed locally but GitHub Actions still failed because of differences between Windows and Linux. I inspected the logs, understood the issue, changed the test, pushed again, and verified the final CI run passed.

### Reviewing AI-generated work

I did not treat AI-generated output as automatically correct.

Changes were run locally, tested manually, reviewed, and adjusted over time.

There were also many times where I changed the requirements or rejected behavior after seeing the result.

AI use is also cited in comments in code where AI materially assisted.

I understand the final-project rule that AI should amplify rather than supplant my work. I believe the strongest part of what I personally did was deciding what the application should be, learning the technologies needed to make it possible, breaking the work into stages, testing it, understanding problems, and continuing to improve it.

Without AI I probably would have stopped at a much smaller MVP. AI made it possible for me to explore a more polished version, but it also forced me to learn how to review, test, debug, and control generated code instead of blindly accepting it.

---

## Testing

The final application currently has:

```text
112 automated tests passing
approximately 94% total coverage
GitHub Actions CI passing
MySQL migration test passing in CI
Ruff passing
Python compile checks passing
```

The tests cover normal behavior and edge cases such as:

- authentication
- duplicate registration
- onboarding redirects
- transaction ownership
- category ownership
- budget ownership
- savings ownership
- CSRF
- HTTP method restrictions
- open redirects
- financial precision
- Safe-to-Spend
- budget calculations
- savings calculations
- localization
- error pages
- migration behavior

I also performed manual testing because automated tests do not tell me whether the interface actually feels usable.

---

## What I learned

This project taught me much more than I expected when I started it.

Technically, I learned more about:

- Python
- Flask
- SQLAlchemy
- MySQL
- database relationships
- migrations
- Jinja
- WTForms
- authentication
- authorization
- CSRF
- Decimal money handling
- pytest
- code coverage
- Git
- GitHub
- GitHub Actions
- virtual environments
- PowerShell
- debugging differences between Windows and Linux

I also learned that building software involves a lot of decision making.

A feature that sounds simple, like "add savings", immediately creates questions:

- Does it reduce balance?
- Can the user withdraw more than they saved?
- What happens after the target is reached?
- Can the user over-save?
- Does it affect budgets?
- How does it affect Safe-to-Spend?

I had to answer questions like these throughout the project.

I also learned that using an AI coding tool effectively is not the same as asking it to build something and accepting the result. The more serious the project became, the more specific I had to become about requirements, boundaries, testing, and expected behavior.

---

## Final result

ILI pika became much larger than the project I first imagined.

It is not perfect and there are still things I could add in the future, such as advanced analytics, automatic recurring transactions, CSV import/export, notifications, and pagination for very large histories.

However, I decided to stop adding core features and treat the current version as the completed CS50 final project.

For me, the most important result is not only that the application works. It is that I now understand much more about how a real web application is structured, how a database evolves, how to use Git and GitHub during development, how to test software, how to debug environment problems, and how to use AI as a development tool while still keeping control over the product I am building.
