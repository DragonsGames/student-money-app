from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import selectinload

from extensions import db
from models import Budget, Transaction


ZERO = Decimal("0.000")
ONE_HUNDRED = Decimal("100")
PERCENT_STEP = Decimal("0.01")


def get_period_start(budget_period, today=None):
    today = today or date.today()

    if budget_period == "weekly":
        return today - timedelta(days=today.weekday())

    return today.replace(day=1)


# AI assistance: OpenAI Codex helped draft this current-period budget
# aggregation; reviewed and adapted by the project author.
def get_budget_summary(user_id, budget_period, today=None):
    today = today or date.today()
    period = "weekly" if budget_period == "weekly" else "monthly"
    period_start = get_period_start(period, today)

    budget_statement = (
        db.select(Budget)
        .where(Budget.user_id == user_id)
        .options(selectinload(Budget.category))
        .order_by(Budget.id)
    )
    budgets = db.session.execute(budget_statement).scalars().all()
    budgets.sort(key=lambda budget: budget.category.name.casefold())

    spent_by_category = {}
    category_ids = [budget.category_id for budget in budgets]

    if category_ids:
        spending_statement = (
            db.select(
                Transaction.category_id,
                func.coalesce(func.sum(Transaction.amount), ZERO)
            )
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "expense",
                Transaction.category_id.in_(category_ids),
                Transaction.transaction_date >= period_start,
                Transaction.transaction_date <= today,
            )
            .group_by(Transaction.category_id)
        )
        spent_by_category = dict(
            db.session.execute(spending_statement).all()
        )

    items = []
    total_budgeted = ZERO
    total_spent = ZERO

    for budget in budgets:
        spent = spent_by_category.get(budget.category_id, ZERO)
        remaining = budget.amount - spent
        percentage = (spent / budget.amount) * ONE_HUNDRED

        items.append({
            "budget": budget,
            "spent": spent,
            "remaining": remaining,
            "percentage": percentage,
            "visual_percentage": min(
                percentage,
                ONE_HUNDRED
            ).quantize(PERCENT_STEP),
            "overspent": spent > budget.amount,
        })
        total_budgeted += budget.amount
        total_spent += spent

    total_remaining = total_budgeted - total_spent
    total_percentage = (
        (total_spent / total_budgeted) * ONE_HUNDRED
        if total_budgeted > ZERO
        else ZERO
    )

    return {
        "period": period,
        "period_start": period_start,
        "period_end": today,
        "items": items,
        "total_budgeted": total_budgeted,
        "total_spent": total_spent,
        "total_remaining": total_remaining,
        "total_percentage": total_percentage,
        "visual_percentage": min(
            total_percentage,
            ONE_HUNDRED
        ).quantize(PERCENT_STEP),
        "overspent": total_spent > total_budgeted and bool(budgets),
    }
