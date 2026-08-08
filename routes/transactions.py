from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.orm import selectinload

from extensions import db
from forms import DeleteTransactionForm, LogoutForm, TransactionForm
from models import Category, Transaction
from routes.guards import onboarding_complete_required
from services.finance import ZERO, get_financial_summary


transactions_bp = Blueprint("transactions", __name__)


def _user_categories():
    statement = (
        db.select(Category)
        .where(Category.user_id == current_user.id)
        .order_by(Category.category_type, Category.name)
    )
    return db.session.execute(statement).scalars().all()


def _set_category_choices(form, categories):
    form.category_id.choices = [(0, "Choose a category")] + [
        (category.id, category.name)
        for category in categories
    ]


def _matching_user_category(category_id, transaction_type):
    statement = db.select(Category).where(
        Category.id == category_id,
        Category.user_id == current_user.id,
        Category.category_type == transaction_type,
    )
    return db.session.execute(statement).scalar_one_or_none()


def _render_transaction_form(form, categories, mode, transaction=None):
    return render_template(
        "transaction_form.html",
        form=form,
        categories=categories,
        mode=mode,
        transaction=transaction,
        logout_form=LogoutForm(),
    )


# AI assistance: OpenAI Codex helped draft this transaction CRUD flow and its
# ownership/category validation; reviewed and adapted by the project author.
@transactions_bp.route("/transactions")
@login_required
@onboarding_complete_required
def transactions():
    statement = (
        db.select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .options(selectinload(Transaction.category))
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.created_at.desc(),
            Transaction.id.desc(),
        )
    )
    user_transactions = db.session.execute(statement).scalars().all()

    settings = current_user.settings
    starting_balance = settings.starting_balance if settings else ZERO
    currency = settings.currency if settings else "TND"

    return render_template(
        "transactions.html",
        transactions=user_transactions,
        financial_summary=get_financial_summary(
            current_user.id,
            starting_balance
        ),
        currency=currency,
        delete_form=DeleteTransactionForm(),
        logout_form=LogoutForm(),
    )


@transactions_bp.route("/transactions/add", methods=["GET", "POST"])
@login_required
@onboarding_complete_required
def add_transaction():
    form = TransactionForm()
    categories = _user_categories()
    _set_category_choices(form, categories)
    form.submit.label.text = "Add transaction"

    if form.validate_on_submit():
        category = _matching_user_category(
            form.category_id.data,
            form.transaction_type.data
        )

        if category is None:
            form.category_id.errors.append(
                "Choose one of your categories matching the transaction type."
            )
            flash("Please choose a valid category.", "danger")
        else:
            description = (form.description.data or "").strip()
            transaction = Transaction(
                user_id=current_user.id,
                category_id=category.id,
                transaction_type=form.transaction_type.data,
                amount=form.amount.data,
                description=description or None,
                transaction_date=form.transaction_date.data,
            )
            db.session.add(transaction)
            db.session.commit()

            flash("Transaction added successfully.", "success")
            return redirect(url_for("transactions.transactions"))

    return _render_transaction_form(form, categories, "add")


@transactions_bp.route(
    "/transactions/<int:transaction_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@onboarding_complete_required
def edit_transaction(transaction_id):
    statement = db.select(Transaction).where(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
    )
    transaction = db.session.execute(statement).scalar_one_or_none()

    if transaction is None:
        abort(404)

    form = TransactionForm(obj=transaction)
    categories = _user_categories()
    _set_category_choices(form, categories)
    form.submit.label.text = "Save changes"

    if form.validate_on_submit():
        category = _matching_user_category(
            form.category_id.data,
            form.transaction_type.data
        )

        if category is None:
            form.category_id.errors.append(
                "Choose one of your categories matching the transaction type."
            )
            flash("Please choose a valid category.", "danger")
        else:
            description = (form.description.data or "").strip()
            transaction.category_id = category.id
            transaction.transaction_type = form.transaction_type.data
            transaction.amount = form.amount.data
            transaction.description = description or None
            transaction.transaction_date = form.transaction_date.data
            db.session.commit()

            flash("Transaction updated successfully.", "success")
            return redirect(url_for("transactions.transactions"))

    return _render_transaction_form(
        form,
        categories,
        "edit",
        transaction
    )


@transactions_bp.route(
    "/transactions/<int:transaction_id>/delete",
    methods=["POST"]
)
@login_required
@onboarding_complete_required
def delete_transaction(transaction_id):
    form = DeleteTransactionForm()

    if not form.validate_on_submit():
        abort(400)

    statement = db.select(Transaction).where(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
    )
    transaction = db.session.execute(statement).scalar_one_or_none()

    if transaction is None:
        abort(404)

    db.session.delete(transaction)
    db.session.commit()
    flash("Transaction deleted successfully.", "success")

    return redirect(url_for("transactions.transactions"))
