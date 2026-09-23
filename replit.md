# Roommate Expense Splitter

An interview-ready Flask and SQLite dashboard for tracking shared roommate expenses and settling balances.

## Run & Operate

- `pnpm --filter @workspace/roommate-expense-splitter run dev` — run the Flask app
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm --filter @workspace/roommate-expense-splitter run typecheck` — compile-check Python files
- The app stores local data in `artifacts/roommate-expense-splitter/instance/roommates.db`.

## Stack

- Python 3, Flask, SQLite, Jinja templates, vanilla JavaScript

## Where things live

- `artifacts/roommate-expense-splitter/app.py` — Flask routes, validation, and page data
- `artifacts/roommate-expense-splitter/database.py` — SQLite schema, queries, balance math, and settlement algorithm
- `artifacts/roommate-expense-splitter/templates/` — Jinja UI
- `artifacts/roommate-expense-splitter/static/` — responsive CSS and tiny client-side interactions

## Architecture decisions

- Money is handled with `Decimal` and rounded to two places at calculation boundaries.
- Settlement recommendations match debtors to creditors greedily, producing a short practical payment list.
- Roommate deletion is restricted when that person still has expenses, protecting referential integrity.

## Product

Users can add roommates, record and delete shared expenses, see equal-share balances, load demo data, generate settlement recommendations, mark payments completed, and view settlement history.

## User preferences

- Keep the project beginner-friendly and dependency-light; do not add authentication, external APIs, payments, or paid services.

## Gotchas

- The Flask workflow needs the managed artifact `PORT` environment variable.
- Loading demo data replaces the current local roommates, expenses, and settlement history after confirmation.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
