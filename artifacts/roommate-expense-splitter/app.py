from __future__ import annotations

import os
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Flask, flash, redirect, render_template, request, url_for

from database import (
    add_expense,
    add_roommate,
    add_settlement,
    build_settlement_plan,
    calculate_balances,
    delete_expense,
    delete_roommate,
    get_expenses,
    get_roommates,
    get_settlements,
    init_db,
    load_demo_data,
    money,
    update_expense,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "roommate-expense-dev-secret")
app.config["TEMPLATES_AUTO_RELOAD"] = True

CATEGORIES = [
    "Rent",
    "Groceries",
    "Electricity",
    "Internet",
    "Water",
    "Cleaning",
    "Transportation",
    "Other",
]


def dashboard_data() -> dict:
    roommates = get_roommates()
    expenses = get_expenses()
    settlements = get_settlements()
    total, share, balances = calculate_balances(roommates, expenses, settlements)
    plan = build_settlement_plan(balances)
    return {
        "roommates": roommates,
        "expenses": expenses,
        "settlements": settlements,
        "total": total,
        "share": share,
        "balances": balances,
        "settlement_plan": plan,
        "settlement_total": sum((item["amount"] for item in plan), Decimal("0.00")),
        "categories": CATEGORIES,
        "today": date.today().isoformat(),
    }


@app.template_filter("inr")
def format_inr(value) -> str:
    return f"₹{money(value):,.2f}"


@app.template_filter("date_display")
def format_date(value: str) -> str:
    try:
        return date.fromisoformat(value).strftime("%d %b %Y")
    except (TypeError, ValueError):
        return value or "—"


@app.route("/")
def index():
    section = request.args.get("section", "dashboard")
    if section not in {"dashboard", "roommates", "expenses", "settle", "history"}:
        section = "dashboard"
    data = dashboard_data()
    editing_id = request.args.get("edit", type=int)
    data["editing_expense"] = next(
        (expense for expense in data["expenses"] if expense["id"] == editing_id), None
    )
    return render_template("dashboard.html", active_section=section, **data)


@app.post("/demo")
def demo():
    load_demo_data()
    flash("Demo data loaded. Your dashboard is ready to explore.", "success")
    return redirect(url_for("index", section="dashboard"))


@app.post("/roommates")
def create_roommate():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Enter a roommate name first.", "error")
    elif len(name) > 40:
        flash("Roommate names must be 40 characters or fewer.", "error")
    else:
        try:
            add_roommate(name)
            flash(f"{name} was added to the household.", "success")
        except sqlite3.IntegrityError:
            flash("That roommate name is already in use.", "error")
    return redirect(url_for("index", section="roommates"))


@app.post("/roommates/<int:roommate_id>/delete")
def remove_roommate(roommate_id: int):
    try:
        delete_roommate(roommate_id)
        flash("Roommate removed.", "success")
    except sqlite3.IntegrityError:
        flash("Remove this roommate's expenses before deleting them.", "error")
    return redirect(url_for("index", section="roommates"))


def expense_values():
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "Other")
    paid_by_raw = request.form.get("paid_by", "")
    expense_date = request.form.get("expense_date", "")
    try:
        amount = Decimal(request.form.get("amount", "0")).quantize(Decimal("0.01"))
        paid_by = int(paid_by_raw)
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid amount and roommate.")
    if not description:
        raise ValueError("Description cannot be empty.")
    if amount <= 0:
        raise ValueError("Amount must be greater than ₹0.00.")
    if category not in CATEGORIES:
        raise ValueError("Choose a valid expense category.")
    if not expense_date:
        raise ValueError("Choose a date for this expense.")
    if not any(roommate["id"] == paid_by for roommate in get_roommates()):
        raise ValueError("Choose a valid roommate who paid.")
    return description, amount, category, paid_by, expense_date


@app.post("/expenses")
def create_expense():
    try:
        add_expense(*expense_values())
        flash("Expense added and balances recalculated.", "success")
    except (ValueError, sqlite3.IntegrityError) as error:
        flash(str(error), "error")
    return redirect(url_for("index", section="expenses"))


@app.post("/expenses/<int:expense_id>/edit")
def edit_expense(expense_id: int):
    try:
        update_expense(expense_id, *expense_values())
        flash("Expense updated.", "success")
    except (ValueError, sqlite3.IntegrityError) as error:
        flash(str(error), "error")
    return redirect(url_for("index", section="expenses"))


@app.post("/expenses/<int:expense_id>/delete")
def remove_expense(expense_id: int):
    delete_expense(expense_id)
    flash("Expense deleted and balances recalculated.", "success")
    return redirect(url_for("index", section="expenses"))


@app.post("/settlements")
def complete_settlement():
    try:
        payer_id = int(request.form.get("payer_id", "0"))
        receiver_id = int(request.form.get("receiver_id", "0"))
        amount = Decimal(request.form.get("amount", "0")).quantize(Decimal("0.01"))
        data = dashboard_data()
        matching_plan = next(
            (
                item
                for item in data["settlement_plan"]
                if item["payer_id"] == payer_id
                and item["receiver_id"] == receiver_id
                and item["amount"] == amount
            ),
            None,
        )
        if not matching_plan:
            raise ValueError
        add_settlement(payer_id, receiver_id, amount)
        flash(
            f"Settlement recorded: {matching_plan['payer']} paid "
            f"{matching_plan['receiver']}.",
            "success",
        )
    except (InvalidOperation, ValueError):
        flash("That settlement could not be recorded.", "error")
    return redirect(url_for("index", section="settle"))


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("NODE_ENV") == "development",
    )