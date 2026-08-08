from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from forms import (
    OnboardingBalanceForm,
    OnboardingCategoriesForm,
    OnboardingGoalsForm,
    OnboardingIncomeForm,
    OnboardingProfileForm,
)
from models import Category, IncomeSource, UserGoal, UserSettings


onboarding_bp = Blueprint("onboarding", __name__)



@onboarding_bp.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    if current_user.onboarding_completed:
        return redirect(url_for("dashboard.dashboard"))

    form = OnboardingProfileForm()

    if form.validate_on_submit():

        settings = current_user.settings

        if settings is None:
            settings = UserSettings(
                user_id=current_user.id
            )
            db.session.add(settings)

        settings.display_name = form.display_name.data
        settings.currency = form.currency.data

        db.session.commit()

        return redirect(url_for("onboarding.onboarding_goals"))

    return render_template(
        "onboarding_profile.html",
        form=form
    )
@onboarding_bp.route("/onboarding/goals", methods=["GET", "POST"])
@login_required
def onboarding_goals():
    if current_user.onboarding_completed:
        return redirect(url_for("dashboard.dashboard"))

    form = OnboardingGoalsForm()

    if form.validate_on_submit():

        current_user.goals.clear()

        for goal in form.goals.data:
            user_goal = UserGoal(
                goal_type=goal
            )

            current_user.goals.append(user_goal)

        db.session.commit()

        return redirect(url_for("onboarding.onboarding_income"))

    return render_template(
        "onboarding_goals.html",
        form=form
    )
@onboarding_bp.route("/onboarding/income", methods=["GET", "POST"])
@login_required
def onboarding_income():
    if current_user.onboarding_completed:
        return redirect(url_for("dashboard.dashboard"))

    form = OnboardingIncomeForm()

    if form.validate_on_submit():

        current_user.income_sources.clear()

        for source_data in form.sources.data:

            source = IncomeSource(
                name=source_data["name"],
                amount=source_data["amount"],
                frequency=source_data["frequency"],
                next_payment_date=source_data["next_payment_date"],
                is_recurring=source_data["frequency"] in [
                    "weekly",
                    "monthly"
                ]
            )

            current_user.income_sources.append(source)

        db.session.commit()

        return redirect(url_for("onboarding.onboarding_balance"))

    return render_template(
        "onboarding_income.html",
        form=form
    )
@onboarding_bp.route("/onboarding/balance", methods=["GET", "POST"])
@login_required
def onboarding_balance():
    if current_user.onboarding_completed:
        return redirect(url_for("dashboard.dashboard"))

    form = OnboardingBalanceForm()

    if form.validate_on_submit():

        settings = current_user.settings

        if settings is None:
            settings = UserSettings(
                user_id=current_user.id
            )
            db.session.add(settings)

        settings.starting_balance = form.starting_balance.data

        db.session.commit()

        return redirect(url_for("onboarding.onboarding_categories"))

    return render_template(
        "onboarding_balance.html",
        form=form
    )
@onboarding_bp.route("/onboarding/categories", methods=["GET", "POST"])
@login_required
def onboarding_categories():
    if current_user.onboarding_completed:
        return redirect(url_for("dashboard.dashboard"))

    default_categories = [
        {"name": "Food", "category_type": "expense", "icon": "🍔"},
        {"name": "Transport", "category_type": "expense", "icon": "🚌"},
        {"name": "School", "category_type": "expense", "icon": "🎓"},
        {"name": "Entertainment", "category_type": "expense", "icon": "🎮"},
        {"name": "Shopping", "category_type": "expense", "icon": "🛍️"},
        {"name": "Other", "category_type": "expense", "icon": "📦"},
        {"name": "Allowance", "category_type": "income", "icon": "💰"},
        {"name": "Work", "category_type": "income", "icon": "💼"},
    ]

    if request.method == "GET" and not current_user.categories:
        form = OnboardingCategoriesForm(
            categories=default_categories
        )
    else:
        form = OnboardingCategoriesForm()

    if form.validate_on_submit():
        current_user.categories.clear()

        for data in form.categories.data:
            category = Category(
                name=data["name"],
                category_type=data["category_type"],
                icon=data["icon"],
                is_default=data["name"] in {
                    "Food",
                    "Transport",
                    "School",
                    "Entertainment",
                    "Shopping",
                    "Other",
                    "Allowance",
                    "Work"
                }
            )

            current_user.categories.append(category)

        current_user.onboarding_completed = True

        db.session.commit()

        return redirect(url_for("dashboard.dashboard"))

    return render_template(
        "onboarding_categories.html",
        form=form
    )
