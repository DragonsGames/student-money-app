import re

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import exists

from extensions import db
from forms import CategoryForm, DeleteCategoryForm, LogoutForm
from models import Budget, Category, Transaction
from routes.guards import onboarding_complete_required


categories_bp = Blueprint("categories", __name__)
HEX_COLOR_PATTERN = re.compile(r"\A#[0-9A-Fa-f]{6}\Z")


def _owned_category(category_id):
    statement = db.select(Category).where(
        Category.id == category_id,
        Category.user_id == current_user.id,
    )
    return db.session.execute(statement).scalar_one_or_none()


def _duplicate_category(name, category_type, excluded_id=None):
    statement = db.select(Category).where(
        Category.user_id == current_user.id,
        Category.name == name,
        Category.category_type == category_type,
    )

    if excluded_id is not None:
        statement = statement.where(Category.id != excluded_id)

    statement = statement.limit(1)
    return db.session.execute(statement).scalar_one_or_none()


def _category_has_transactions(category_id):
    statement = db.select(
        exists().where(Transaction.category_id == category_id)
    )
    return db.session.execute(statement).scalar_one()


# AI assistance: OpenAI Codex helped extend category protections for budget
# references and expense-type consistency; reviewed by the project author.
def _category_has_budget(category_id):
    statement = db.select(
        exists().where(Budget.category_id == category_id)
    )
    return db.session.execute(statement).scalar_one()


def _clean_optional(value):
    value = (value or "").strip()
    return value or None


def _display_color(category):
    if category.color and HEX_COLOR_PATTERN.fullmatch(category.color):
        return category.color

    if category.category_type == "expense":
        return "#a34b57"

    return "#287956"


def _render_category_form(form, mode, category=None):
    return render_template(
        "category_form.html",
        form=form,
        mode=mode,
        category=category,
        logout_form=LogoutForm(),
    )


# AI assistance: OpenAI Codex helped draft this category CRUD flow, duplicate
# checks, and ownership/delete protection; reviewed and adapted by the author.
@categories_bp.route("/categories")
@login_required
@onboarding_complete_required
def categories():
    category_statement = (
        db.select(Category)
        .where(Category.user_id == current_user.id)
        .order_by(Category.name)
    )
    user_categories = db.session.execute(
        category_statement
    ).scalars().all()

    used_statement = (
        db.select(Transaction.category_id)
        .join(Category, Transaction.category_id == Category.id)
        .where(Category.user_id == current_user.id)
        .distinct()
    )
    used_category_ids = set(
        db.session.execute(used_statement).scalars().all()
    )
    budgeted_statement = db.select(Budget.category_id).where(
        Budget.user_id == current_user.id
    )
    used_category_ids.update(
        db.session.execute(budgeted_statement).scalars().all()
    )

    return render_template(
        "categories.html",
        expense_categories=[
            category
            for category in user_categories
            if category.category_type == "expense"
        ],
        income_categories=[
            category
            for category in user_categories
            if category.category_type == "income"
        ],
        used_category_ids=used_category_ids,
        category_colors={
            category.id: _display_color(category)
            for category in user_categories
        },
        delete_form=DeleteCategoryForm(),
        logout_form=LogoutForm(),
    )


@categories_bp.route("/categories/add", methods=["GET", "POST"])
@login_required
@onboarding_complete_required
def add_category():
    form = CategoryForm()
    form.submit.label.text = "Add category"

    if form.validate_on_submit():
        name = form.name.data.strip()

        if _duplicate_category(name, form.category_type.data):
            form.name.errors.append(
                "You already have a category with this name and type."
            )
            flash("That category already exists.", "danger")
        else:
            category = Category(
                user_id=current_user.id,
                name=name,
                category_type=form.category_type.data,
                icon=_clean_optional(form.icon.data),
                color=_clean_optional(form.color.data),
                is_default=False,
            )
            db.session.add(category)
            db.session.commit()

            flash("Category added successfully.", "success")
            return redirect(url_for("categories.categories"))

    return _render_category_form(form, "add")


@categories_bp.route(
    "/categories/<int:category_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@onboarding_complete_required
def edit_category(category_id):
    category = _owned_category(category_id)

    if category is None:
        abort(404)

    form = CategoryForm(obj=category)
    form.submit.label.text = "Save changes"

    if form.validate_on_submit():
        name = form.name.data.strip()
        changes_budgeted_category_to_income = (
            category.category_type == "expense"
            and form.category_type.data == "income"
            and _category_has_budget(category.id)
        )

        if changes_budgeted_category_to_income:
            form.category_type.errors.append(
                "Remove this category's budget before changing it to income."
            )
            flash(
                "A category with a budget must remain an expense category.",
                "danger"
            )
        elif _duplicate_category(
            name,
            form.category_type.data,
            excluded_id=category.id
        ):
            form.name.errors.append(
                "You already have a category with this name and type."
            )
            flash("That category already exists.", "danger")
        else:
            category.name = name
            category.category_type = form.category_type.data
            category.icon = _clean_optional(form.icon.data)
            category.color = _clean_optional(form.color.data)
            db.session.commit()

            flash("Category updated successfully.", "success")
            return redirect(url_for("categories.categories"))

    return _render_category_form(form, "edit", category)


@categories_bp.route(
    "/categories/<int:category_id>/delete",
    methods=["POST"]
)
@login_required
@onboarding_complete_required
def delete_category(category_id):
    form = DeleteCategoryForm()

    if not form.validate_on_submit():
        abort(400)

    category = _owned_category(category_id)

    if category is None:
        abort(404)

    has_transactions = _category_has_transactions(category.id)
    has_budget = _category_has_budget(category.id)

    if has_transactions and has_budget:
        flash(
            "This category cannot be deleted because it is used by existing "
            "transactions and a budget.",
            "danger"
        )
        return redirect(url_for("categories.categories"))

    if has_transactions:
        flash(
            "This category cannot be deleted because it is used by existing "
            "transactions.",
            "danger"
        )
        return redirect(url_for("categories.categories"))

    if has_budget:
        flash(
            "This category cannot be deleted because it has a budget.",
            "danger"
        )
        return redirect(url_for("categories.categories"))

    db.session.delete(category)
    db.session.commit()
    flash("Category deleted successfully.", "success")

    return redirect(url_for("categories.categories"))
