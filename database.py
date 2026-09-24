"""SQLite persistence and settlement calculations for Roommate Expense Splitter."""

from __future__ import annotations

import sqlite3
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable


MONEY = Decimal("0.01")
DB_PATH = Path(__file__).parent / "instance" / "roommates.db"


def money(value: Any) -> Decimal:
    """Convert a database value into a safe, two-decimal Decimal."""
    return Decimal(str(value or 0)).quantize(MONEY, rounding=ROUND_HALF_UP)


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    """Create the schema and seed demo data only for a truly empty database."""
    seeded_empty_database = False
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS roommates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount NUMERIC NOT NULL CHECK (amount > 0),
                category TEXT NOT NULL,
                paid_by INTEGER NOT NULL,
                expense_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paid_by) REFERENCES roommates (id) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS settlements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payer_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                payer TEXT NOT NULL,
                receiver TEXT NOT NULL,
                amount NUMERIC NOT NULL CHECK (amount > 0),
                settled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'completed',
                FOREIGN KEY (payer_id) REFERENCES roommates (id) ON DELETE RESTRICT,
                FOREIGN KEY (receiver_id) REFERENCES roommates (id) ON DELETE RESTRICT
            );
            """
        )

        # Migrate the original name-only settlement table without losing history.
        settlement_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(settlements)").fetchall()
        }
        if "payer_id" not in settlement_columns:
            connection.execute(
                "ALTER TABLE settlements ADD COLUMN payer_id INTEGER REFERENCES roommates(id)"
            )
        if "receiver_id" not in settlement_columns:
            connection.execute(
                "ALTER TABLE settlements ADD COLUMN receiver_id INTEGER REFERENCES roommates(id)"
            )
        connection.execute(
            """
            UPDATE settlements
            SET payer_id = (SELECT id FROM roommates WHERE roommates.name = settlements.payer)
            WHERE payer_id IS NULL
            """
        )
        connection.execute(
            """
            UPDATE settlements
            SET receiver_id = (SELECT id FROM roommates WHERE roommates.name = settlements.receiver)
            WHERE receiver_id IS NULL
            """
        )
        connection.execute(
            "UPDATE settlements SET status = lower(status) WHERE status IS NOT NULL"
        )

        seeded_empty_database = all(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
            for table in ("roommates", "expenses", "settlements")
        )

    if seeded_empty_database:
        load_demo_data()


def get_roommates() -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute(
            "SELECT id, name FROM roommates ORDER BY name COLLATE NOCASE"
        ).fetchall()


def get_expenses() -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT expenses.id, expenses.description, expenses.amount,
                   expenses.category, expenses.paid_by, expenses.expense_date,
                   roommates.name AS paid_by_name
            FROM expenses
            JOIN roommates ON roommates.id = expenses.paid_by
            ORDER BY expenses.expense_date DESC, expenses.id DESC
            """
        ).fetchall()


def get_settlements() -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT id, payer_id, receiver_id, payer, receiver, amount,
                   settled_at, status
            FROM settlements
            ORDER BY settled_at DESC, id DESC
            """
        ).fetchall()


def calculate_balances(
    roommates: list[sqlite3.Row],
    expenses: list[sqlite3.Row],
    settlements: Iterable[sqlite3.Row] = (),
) -> tuple[Decimal, Decimal, list[dict[str, Any]]]:
    """Calculate original balances, then subtract completed settlement payments."""
    total = sum((money(expense["amount"]) for expense in expenses), Decimal("0.00"))
    share = (
        (total / len(roommates)).quantize(MONEY, rounding=ROUND_HALF_UP)
        if roommates
        else Decimal("0.00")
    )
    paid = {roommate["id"]: Decimal("0.00") for roommate in roommates}
    for expense in expenses:
        paid[expense["paid_by"]] += money(expense["amount"])

    name_to_id = {roommate["name"]: roommate["id"] for roommate in roommates}
    outstanding = {
        roommate["id"]: (paid[roommate["id"]] - share).quantize(
            MONEY, rounding=ROUND_HALF_UP
        )
        for roommate in roommates
    }

    for settlement in settlements:
        status = str(settlement["status"] or "").lower()
        if status != "completed":
            continue
        payer_id = settlement["payer_id"] or name_to_id.get(settlement["payer"])
        receiver_id = settlement["receiver_id"] or name_to_id.get(
            settlement["receiver"]
        )
        if payer_id in outstanding and receiver_id in outstanding:
            amount = money(settlement["amount"])
            outstanding[payer_id] += amount
            outstanding[receiver_id] -= amount

    balances = []
    for roommate in roommates:
        balance = outstanding[roommate["id"]].quantize(
            MONEY, rounding=ROUND_HALF_UP
        )
        balances.append(
            {
                "id": roommate["id"],
                "name": roommate["name"],
                "paid": paid[roommate["id"]].quantize(MONEY),
                "share": share,
                "balance": balance,
                "status": "Gets back"
                if balance > 0
                else "Owes"
                if balance < 0
                else "Settled",
            }
        )
    return total.quantize(MONEY), share, balances


def build_settlement_plan(balances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Match debtors to creditors to produce a short, practical payment plan."""
    debtors = [
        {"id": item["id"], "name": item["name"], "amount": abs(item["balance"])}
        for item in balances
        if item["balance"] < 0
    ]
    creditors = [
        {"id": item["id"], "name": item["name"], "amount": item["balance"]}
        for item in balances
        if item["balance"] > 0
    ]
    transactions = []
    debtor_index = creditor_index = 0
    while debtor_index < len(debtors) and creditor_index < len(creditors):
        debtor = debtors[debtor_index]
        creditor = creditors[creditor_index]
        amount = min(debtor["amount"], creditor["amount"]).quantize(
            MONEY, rounding=ROUND_HALF_UP
        )
        if amount > 0:
            transactions.append(
                {
                    "payer_id": debtor["id"],
                    "payer": debtor["name"],
                    "receiver_id": creditor["id"],
                    "receiver": creditor["name"],
                    "amount": amount,
                }
            )
        debtor["amount"] -= amount
        creditor["amount"] -= amount
        if debtor["amount"] <= 0:
            debtor_index += 1
        if creditor["amount"] <= 0:
            creditor_index += 1
    return transactions


def add_roommate(name: str) -> None:
    with get_connection() as connection:
        connection.execute("INSERT INTO roommates (name) VALUES (?)", (name.strip(),))


def delete_roommate(roommate_id: int) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM roommates WHERE id = ?", (roommate_id,))


def add_expense(
    description: str, amount: Decimal, category: str, paid_by: int, expense_date: str
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO expenses (description, amount, category, paid_by, expense_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (description.strip(), str(amount), category, paid_by, expense_date),
        )


def update_expense(
    expense_id: int,
    description: str,
    amount: Decimal,
    category: str,
    paid_by: int,
    expense_date: str,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE expenses
            SET description = ?, amount = ?, category = ?, paid_by = ?, expense_date = ?
            WHERE id = ?
            """,
            (description.strip(), str(amount), category, paid_by, expense_date, expense_id),
        )


def delete_expense(expense_id: int) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))


def add_settlement(payer_id: int, receiver_id: int, amount: Decimal) -> None:
    with get_connection() as connection:
        people = connection.execute(
            """
            SELECT id, name FROM roommates
            WHERE id IN (?, ?)
            """,
            (payer_id, receiver_id),
        ).fetchall()
        names = {person["id"]: person["name"] for person in people}
        if payer_id not in names or receiver_id not in names:
            raise ValueError("That settlement has an invalid roommate.")
        connection.execute(
            """
            INSERT INTO settlements
                (payer_id, receiver_id, payer, receiver, amount, status)
            VALUES (?, ?, ?, ?, ?, 'completed')
            """,
            (
                payer_id,
                receiver_id,
                names[payer_id],
                names[receiver_id],
                str(amount),
            ),
        )


def load_demo_data() -> None:
    """Explicitly replace local data with the documented demo household."""
    with get_connection() as connection:
        connection.execute("DELETE FROM settlements")
        connection.execute("DELETE FROM expenses")
        connection.execute("DELETE FROM roommates")
        connection.executemany(
            "INSERT INTO roommates (name) VALUES (?)",
            [("A",), ("B",), ("C",), ("D",)],
        )
        ids = {
            row["name"]: row["id"]
            for row in connection.execute("SELECT id, name FROM roommates").fetchall()
        }
        from datetime import date

        today = date.today().isoformat()
        connection.executemany(
            """
            INSERT INTO expenses (description, amount, category, paid_by, expense_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("Groceries", "800.00", "Groceries", ids["A"], today),
                ("Electricity", "1200.00", "Electricity", ids["B"], today),
                ("Internet", "600.00", "Internet", ids["C"], today),
                ("Cleaning", "400.00", "Cleaning", ids["D"], today),
            ],
        )