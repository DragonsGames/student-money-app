from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy.orm import selectinload

from extensions import db
from forms import LogoutForm
from models import Transaction
from routes.guards import onboarding_complete_required
from services.budgets import get_budget_summary
from services.finance import ZERO, get_financial_summary
from services.safe_to_spend import get_safe_to_spend_summary
from services.savings import get_savings_summary


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
@onboarding_complete_required
def dashboard():

    settings = current_user.settings
    display_name = (
        settings.display_name
        if settings and settings.display_name
        else current_user.email
    )
    starting_balance = settings.starting_balance if settings else ZERO
    currency = settings.currency if settings else "TND"

    recent_statement = (
        db.select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .options(selectinload(Transaction.category))
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.created_at.desc(),
            Transaction.id.desc(),
        )
        .limit(5)
    )
    recent_transactions = db.session.execute(
        recent_statement
    ).scalars().all()
    financial_summary = get_financial_summary(
        current_user.id,
        starting_balance
    )
    budget_summary = get_budget_summary(
        current_user.id,
        settings.budget_period
    )
    savings_summary = get_savings_summary(current_user.id)

    return render_template(
        "dashboard.html",
        display_name=display_name,
        settings=settings,
        currency=currency,
        financial_summary=financial_summary,
        budget_summary=budget_summary,
        savings_summary=savings_summary,
        safe_to_spend_summary=get_safe_to_spend_summary(
            financial_summary,
            budget_summary,
            savings_summary,
        ),
        recent_transactions=recent_transactions,
        logout_form=LogoutForm(),
    )
