from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from extensions import db
from forms import (
    DeleteIncomeSourceForm,
    GoalsSettingsForm,
    IncomeSourceSettingsForm,
    LogoutForm,
    MoneySettingsForm,
    PreferenceSettingsForm,
    ProfileSettingsForm,
)
from models import IncomeSource, UserGoal
from routes.guards import onboarding_complete_required


settings_bp = Blueprint("settings", __name__)
ALLOWED_GOAL_TYPES = {
    "save_more",
    "stop_overspending",
    "understand_spending",
    "better_habits",
    "track_money",
    "save_for_something",
}
RECURRING_FREQUENCIES = {"weekly", "monthly"}


def _user_goals():
    statement = (
        db.select(UserGoal)
        .where(UserGoal.user_id == current_user.id)
        .order_by(UserGoal.id)
    )
    return db.session.execute(statement).scalars().all()


def _user_income_sources():
    statement = (
        db.select(IncomeSource)
        .where(IncomeSource.user_id == current_user.id)
        .order_by(IncomeSource.id)
    )
    return db.session.execute(statement).scalars().all()


def _owned_income_source(source_id):
    statement = db.select(IncomeSource).where(
        IncomeSource.id == source_id,
        IncomeSource.user_id == current_user.id,
    )
    return db.session.execute(statement).scalar_one_or_none()


def _render_settings(
    profile_form=None,
    money_form=None,
    preference_form=None,
    goals_form=None,
):
    settings = current_user.settings
    goals = _user_goals()

    if profile_form is None:
        profile_form = ProfileSettingsForm(obj=settings)

    if money_form is None:
        money_form = MoneySettingsForm(obj=settings)

    if preference_form is None:
        preference_form = PreferenceSettingsForm(obj=settings)

    if goals_form is None:
        goals_form = GoalsSettingsForm(
            goals=[goal.goal_type for goal in goals]
        )

    return render_template(
        "settings.html",
        profile_form=profile_form,
        money_form=money_form,
        preference_form=preference_form,
        goals_form=goals_form,
        income_sources=_user_income_sources(),
        delete_form=DeleteIncomeSourceForm(),
        currency=settings.currency,
        logout_form=LogoutForm(),
    )


def _render_income_source_form(form, mode, source=None):
    return render_template(
        "income_source_form.html",
        form=form,
        mode=mode,
        source=source,
        currency=current_user.settings.currency,
        logout_form=LogoutForm(),
    )


# AI assistance: OpenAI Codex helped draft these settings update routes,
# UserGoal synchronization, and owned IncomeSource CRUD; reviewed by the author.
@settings_bp.route("/settings")
@login_required
@onboarding_complete_required
def settings():
    return _render_settings()


@settings_bp.route("/settings/profile", methods=["POST"])
@login_required
@onboarding_complete_required
def update_profile():
    form = ProfileSettingsForm()

    if form.validate_on_submit():
        display_name = (form.display_name.data or "").strip()
        current_user.settings.display_name = display_name or None
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("settings.settings"))

    return _render_settings(profile_form=form)


@settings_bp.route("/settings/money", methods=["POST"])
@login_required
@onboarding_complete_required
def update_money():
    form = MoneySettingsForm()

    if form.validate_on_submit():
        settings = current_user.settings
        settings.currency = form.currency.data
        settings.starting_balance = form.starting_balance.data
        settings.budget_period = form.budget_period.data
        db.session.commit()
        flash("Money settings updated successfully.", "success")
        return redirect(url_for("settings.settings"))

    return _render_settings(money_form=form)


@settings_bp.route("/settings/preferences", methods=["POST"])
@login_required
@onboarding_complete_required
def update_preferences():
    form = PreferenceSettingsForm()

    if form.validate_on_submit():
        settings = current_user.settings
        settings.appearance = form.appearance.data
        settings.language = form.language.data
        db.session.commit()
        flash("Appearance and language updated successfully.", "success")
        return redirect(url_for("settings.settings"))

    return _render_settings(preference_form=form)


@settings_bp.route("/settings/goals", methods=["POST"])
@login_required
@onboarding_complete_required
def update_goals():
    form = GoalsSettingsForm()

    if form.validate_on_submit():
        selected_goal_types = set(form.goals.data)

        if not selected_goal_types.issubset(ALLOWED_GOAL_TYPES):
            form.goals.errors.append("Choose only the available money goals.")
            return _render_settings(goals_form=form)

        existing_goals = _user_goals()
        existing_goal_types = {goal.goal_type for goal in existing_goals}

        for goal in existing_goals:
            if goal.goal_type not in selected_goal_types:
                db.session.delete(goal)

        for goal_type in selected_goal_types - existing_goal_types:
            db.session.add(UserGoal(
                user_id=current_user.id,
                goal_type=goal_type,
            ))

        db.session.commit()
        flash("Money goals updated successfully.", "success")
        return redirect(url_for("settings.settings"))

    return _render_settings(goals_form=form)


@settings_bp.route(
    "/settings/income-sources/add",
    methods=["GET", "POST"]
)
@login_required
@onboarding_complete_required
def add_income_source():
    form = IncomeSourceSettingsForm()
    form.submit.label.text = "Add income source"

    if form.validate_on_submit():
        source = IncomeSource(
            user_id=current_user.id,
            name=form.name.data.strip(),
            amount=form.amount.data,
            frequency=form.frequency.data,
            next_payment_date=form.next_payment_date.data,
            is_recurring=form.frequency.data in RECURRING_FREQUENCIES,
        )
        db.session.add(source)
        db.session.commit()
        flash("Income source added successfully.", "success")
        return redirect(url_for("settings.settings"))

    return _render_income_source_form(form, "add")


@settings_bp.route(
    "/settings/income-sources/<int:source_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@onboarding_complete_required
def edit_income_source(source_id):
    source = _owned_income_source(source_id)

    if source is None:
        abort(404)

    form = IncomeSourceSettingsForm(obj=source)
    form.submit.label.text = "Save changes"

    if form.validate_on_submit():
        source.name = form.name.data.strip()
        source.amount = form.amount.data
        source.frequency = form.frequency.data
        source.next_payment_date = form.next_payment_date.data
        source.is_recurring = (
            form.frequency.data in RECURRING_FREQUENCIES
        )
        db.session.commit()
        flash("Income source updated successfully.", "success")
        return redirect(url_for("settings.settings"))

    return _render_income_source_form(form, "edit", source)


@settings_bp.route(
    "/settings/income-sources/<int:source_id>/delete",
    methods=["POST"]
)
@login_required
@onboarding_complete_required
def delete_income_source(source_id):
    form = DeleteIncomeSourceForm()

    if not form.validate_on_submit():
        abort(400)

    source = _owned_income_source(source_id)

    if source is None:
        abort(404)

    db.session.delete(source)
    db.session.commit()
    flash("Income source deleted successfully.", "success")
    return redirect(url_for("settings.settings"))
