from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from extensions import db
from forms import (
    DeleteSavingsGoalForm,
    LogoutForm,
    SavingsAmountForm,
    SavingsGoalForm,
)
from models import SavingsGoal
from routes.guards import onboarding_complete_required
from services.savings import ZERO, get_savings_summary


savings_bp = Blueprint("savings", __name__)
MAX_MONEY = Decimal("999999999.999")


def _owned_goal(goal_id):
    statement = db.select(SavingsGoal).where(
        SavingsGoal.id == goal_id,
        SavingsGoal.user_id == current_user.id,
    )
    return db.session.execute(statement).scalar_one_or_none()


def _render_goal_form(form, mode, currency, goal=None):
    return render_template(
        "savings_goal_form.html",
        form=form,
        mode=mode,
        currency=currency,
        goal=goal,
        logout_form=LogoutForm(),
    )


# AI assistance: OpenAI Codex helped draft savings-goal CRUD, ownership
# validation, and safe Decimal progress adjustments; reviewed by the author.
@savings_bp.route("/savings")
@login_required
@onboarding_complete_required
def savings():
    return render_template(
        "savings.html",
        savings_summary=get_savings_summary(current_user.id),
        currency=current_user.settings.currency,
        delete_form=DeleteSavingsGoalForm(),
        logout_form=LogoutForm(),
    )


@savings_bp.route("/savings/add", methods=["GET", "POST"])
@login_required
@onboarding_complete_required
def add_goal():
    form = SavingsGoalForm()
    form.submit.label.text = "Add goal"

    if form.validate_on_submit():
        goal = SavingsGoal(
            user_id=current_user.id,
            name=form.name.data.strip(),
            target_amount=form.target_amount.data,
            saved_amount=ZERO,
            target_date=form.target_date.data,
        )
        db.session.add(goal)
        db.session.commit()

        flash("Savings goal added successfully.", "success")
        return redirect(url_for("savings.savings"))

    return _render_goal_form(
        form,
        "add",
        current_user.settings.currency
    )


@savings_bp.route(
    "/savings/<int:goal_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@onboarding_complete_required
def edit_goal(goal_id):
    goal = _owned_goal(goal_id)

    if goal is None:
        abort(404)

    form = SavingsGoalForm(obj=goal)
    form.submit.label.text = "Save changes"

    if form.validate_on_submit():
        goal.name = form.name.data.strip()
        goal.target_amount = form.target_amount.data
        goal.target_date = form.target_date.data
        db.session.commit()

        flash("Savings goal updated successfully.", "success")
        return redirect(url_for("savings.savings"))

    return _render_goal_form(
        form,
        "edit",
        current_user.settings.currency,
        goal
    )


@savings_bp.route(
    "/savings/<int:goal_id>/amount",
    methods=["GET", "POST"]
)
@login_required
@onboarding_complete_required
def update_amount(goal_id):
    goal = _owned_goal(goal_id)

    if goal is None:
        abort(404)

    form = SavingsAmountForm()

    if form.validate_on_submit():
        if form.action.data == "withdraw":
            if form.amount.data > goal.saved_amount:
                form.amount.errors.append(
                    "You cannot withdraw more than the amount currently saved."
                )
                flash("That withdrawal would make savings negative.", "danger")
            else:
                goal.saved_amount -= form.amount.data
                db.session.commit()
                flash("Savings amount updated successfully.", "success")
                return redirect(url_for("savings.savings"))
        else:
            new_saved_amount = goal.saved_amount + form.amount.data

            if new_saved_amount > MAX_MONEY:
                form.amount.errors.append(
                    "The resulting saved amount cannot exceed 999,999,999.999."
                )
                flash("That addition is larger than the supported limit.", "danger")
            else:
                goal.saved_amount = new_saved_amount
                db.session.commit()
                flash("Savings amount updated successfully.", "success")
                return redirect(url_for("savings.savings"))

    return render_template(
        "savings_amount_form.html",
        form=form,
        goal=goal,
        currency=current_user.settings.currency,
        logout_form=LogoutForm(),
    )


@savings_bp.route("/savings/<int:goal_id>/delete", methods=["POST"])
@login_required
@onboarding_complete_required
def delete_goal(goal_id):
    form = DeleteSavingsGoalForm()

    if not form.validate_on_submit():
        abort(400)

    goal = _owned_goal(goal_id)

    if goal is None:
        abort(404)

    db.session.delete(goal)
    db.session.commit()
    flash("Savings goal deleted successfully.", "success")

    return redirect(url_for("savings.savings"))
