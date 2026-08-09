from decimal import Decimal

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from extensions import db
from forms import HistoryFilterForm, LogoutForm
from models import Category, Transaction
from routes.guards import onboarding_complete_required


history_bp = Blueprint("history", __name__)
ZERO = Decimal("0.000")


SORT_ORDERS = {
    "newest": (
        Transaction.transaction_date.desc(),
        Transaction.created_at.desc(),
        Transaction.id.desc(),
    ),
    "oldest": (
        Transaction.transaction_date.asc(),
        Transaction.created_at.asc(),
        Transaction.id.asc(),
    ),
    "amount_high": (
        Transaction.amount.desc(),
        Transaction.transaction_date.desc(),
    ),
    "amount_low": (
        Transaction.amount.asc(),
        Transaction.transaction_date.desc(),
    ),
}


def _user_categories():
    statement = (
        db.select(Category)
        .where(Category.user_id == current_user.id)
        .order_by(Category.category_type, Category.name)
    )
    return db.session.execute(statement).scalars().all()


# AI assistance: OpenAI Codex helped draft safe transaction-history filtering,
# ownership scoping, and explicit sorting; reviewed and adapted by the author.
@history_bp.route("/history")
@login_required
@onboarding_complete_required
def history():
    categories = _user_categories()
    form = HistoryFilterForm(request.args)
    form.category_id.choices = [(0, "All categories")] + [
        (category.id, category.name)
        for category in categories
    ]

    filters = [Transaction.user_id == current_user.id]
    sort_order = SORT_ORDERS["newest"]
    filters_are_valid = form.validate()

    if filters_are_valid:
        if form.transaction_type.data != "all":
            filters.append(
                Transaction.transaction_type == form.transaction_type.data
            )

        if form.category_id.data:
            filters.append(Transaction.category_id == form.category_id.data)

        if form.start_date.data:
            filters.append(
                Transaction.transaction_date >= form.start_date.data
            )

        if form.end_date.data:
            filters.append(
                Transaction.transaction_date <= form.end_date.data
            )

        sort_order = SORT_ORDERS[form.sort.data]

    statement = (
        db.select(Transaction)
        .where(*filters)
        .options(selectinload(Transaction.category))
        .order_by(*sort_order)
    )
    transactions = db.session.execute(statement).scalars().all()

    total_income = sum(
        (
            transaction.amount
            for transaction in transactions
            if transaction.transaction_type == "income"
        ),
        ZERO
    )
    total_expenses = sum(
        (
            transaction.amount
            for transaction in transactions
            if transaction.transaction_type == "expense"
        ),
        ZERO
    )

    total_count_statement = db.select(func.count(Transaction.id)).where(
        Transaction.user_id == current_user.id
    )
    total_transaction_count = db.session.execute(
        total_count_statement
    ).scalar_one()

    settings = current_user.settings
    currency = settings.currency if settings else "TND"

    return render_template(
        "history.html",
        form=form,
        transactions=transactions,
        filtered_summary={
            "count": len(transactions),
            "income": total_income,
            "expenses": total_expenses,
            "net": total_income - total_expenses,
        },
        total_transaction_count=total_transaction_count,
        currency=currency,
        logout_form=LogoutForm(),
    )
