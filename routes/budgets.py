from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from extensions import db
from forms import (
    BudgetForm,
    BudgetPeriodForm,
    DeleteBudgetForm,
    LogoutForm,
)
from models import Budget, Category
from routes.guards import onboarding_complete_required
from services.budgets import get_budget_summary


budgets_bp = Blueprint("budgets", __name__)


def _owned_budget(budget_id):
    statement = db.select(Budget).where(
        Budget.id == budget_id,
        Budget.user_id == current_user.id,
    )
    return db.session.execute(statement).scalar_one_or_none()


def _available_expense_categories(excluded_budget_id=None):
    category_statement = (
        db.select(Category)
        .where(
            Category.user_id == current_user.id,
            Category.category_type == "expense",
        )
        .order_by(Category.name)
    )
    expense_categories = db.session.execute(
        category_statement
    ).scalars().all()

    budget_statement = db.select(Budget.category_id).where(
        Budget.user_id == current_user.id
    )
    if excluded_budget_id is not None:
        budget_statement = budget_statement.where(
            Budget.id != excluded_budget_id
        )

    unavailable_category_ids = set(
        db.session.execute(budget_statement).scalars().all()
    )
    return [
        category
        for category in expense_categories
        if category.id not in unavailable_category_ids
    ]


def _set_category_choices(form, categories):
    form.category_id.choices = [(0, "Choose an expense category")] + [
        (category.id, category.name)
        for category in categories
    ]


def _matching_expense_category(category_id):
    statement = db.select(Category).where(
        Category.id == category_id,
        Category.user_id == current_user.id,
        Category.category_type == "expense",
    )
    return db.session.execute(statement).scalar_one_or_none()


def _duplicate_budget(category_id, excluded_budget_id=None):
    statement = db.select(Budget).where(
        Budget.user_id == current_user.id,
        Budget.category_id == category_id,
    )
    if excluded_budget_id is not None:
        statement = statement.where(Budget.id != excluded_budget_id)

    return db.session.execute(statement.limit(1)).scalar_one_or_none()


def _render_budget_form(form, categories, currency, mode, budget=None):
    return render_template(
        "budget_form.html",
        form=form,
        categories=categories,
        currency=currency,
        mode=mode,
        budget=budget,
        logout_form=LogoutForm(),
    )


# AI assistance: OpenAI Codex helped draft this budget CRUD flow, category
# validation, ownership checks, and period update; reviewed by the project author.
@budgets_bp.route("/budgets")
@login_required
@onboarding_complete_required
def budgets():
    settings = current_user.settings
    budget_summary = get_budget_summary(
        current_user.id,
        settings.budget_period
    )
    period_form = BudgetPeriodForm(
        budget_period=budget_summary["period"]
    )

    return render_template(
        "budgets.html",
        budget_summary=budget_summary,
        period_form=period_form,
        delete_form=DeleteBudgetForm(),
        currency=settings.currency,
        logout_form=LogoutForm(),
    )


@budgets_bp.route("/budgets/add", methods=["GET", "POST"])
@login_required
@onboarding_complete_required
def add_budget():
    settings = current_user.settings
    form = BudgetForm()
    categories = _available_expense_categories()
    _set_category_choices(form, categories)
    form.submit.label.text = "Add budget"

    if form.validate_on_submit():
        category = _matching_expense_category(form.category_id.data)

        if category is None:
            form.category_id.errors.append(
                "Choose one of your expense categories."
            )
            flash("Please choose a valid expense category.", "danger")
        elif _duplicate_budget(category.id):
            form.category_id.errors.append(
                "This category already has a budget."
            )
            flash("That category already has a budget.", "danger")
        else:
            budget = Budget(
                user_id=current_user.id,
                category_id=category.id,
                amount=form.amount.data,
            )
            db.session.add(budget)
            db.session.commit()

            flash("Budget added successfully.", "success")
            return redirect(url_for("budgets.budgets"))

    return _render_budget_form(
        form,
        categories,
        settings.currency,
        "add"
    )


@budgets_bp.route(
    "/budgets/<int:budget_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@onboarding_complete_required
def edit_budget(budget_id):
    budget = _owned_budget(budget_id)

    if budget is None:
        abort(404)

    settings = current_user.settings
    form = BudgetForm(obj=budget)
    categories = _available_expense_categories(
        excluded_budget_id=budget.id
    )
    _set_category_choices(form, categories)
    form.submit.label.text = "Save changes"

    if form.validate_on_submit():
        category = _matching_expense_category(form.category_id.data)

        if category is None:
            form.category_id.errors.append(
                "Choose one of your expense categories."
            )
            flash("Please choose a valid expense category.", "danger")
        elif _duplicate_budget(category.id, excluded_budget_id=budget.id):
            form.category_id.errors.append(
                "This category already has a budget."
            )
            flash("That category already has a budget.", "danger")
        else:
            budget.category_id = category.id
            budget.amount = form.amount.data
            db.session.commit()

            flash("Budget updated successfully.", "success")
            return redirect(url_for("budgets.budgets"))

    return _render_budget_form(
        form,
        categories,
        settings.currency,
        "edit",
        budget
    )


@budgets_bp.route("/budgets/<int:budget_id>/delete", methods=["POST"])
@login_required
@onboarding_complete_required
def delete_budget(budget_id):
    form = DeleteBudgetForm()

    if not form.validate_on_submit():
        abort(400)

    budget = _owned_budget(budget_id)

    if budget is None:
        abort(404)

    db.session.delete(budget)
    db.session.commit()
    flash("Budget deleted successfully.", "success")

    return redirect(url_for("budgets.budgets"))


@budgets_bp.route("/budgets/period", methods=["POST"])
@login_required
@onboarding_complete_required
def update_period():
    form = BudgetPeriodForm()

    if not form.validate_on_submit():
        abort(400)

    current_user.settings.budget_period = form.budget_period.data
    db.session.commit()
    flash("Budget period updated successfully.", "success")

    return redirect(url_for("budgets.budgets"))
