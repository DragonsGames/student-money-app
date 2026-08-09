from datetime import date
from decimal import Decimal

from extensions import db
from models import SavingsGoal


ZERO = Decimal("0.000")
ONE_HUNDRED = Decimal("100")
PERCENT_STEP = Decimal("0.01")


# AI assistance: OpenAI Codex helped draft these derived savings progress
# calculations; reviewed and adapted by the project author.
def get_savings_summary(user_id, today=None):
    today = today or date.today()
    statement = (
        db.select(SavingsGoal)
        .where(SavingsGoal.user_id == user_id)
        .order_by(SavingsGoal.created_at.desc(), SavingsGoal.id.desc())
    )
    savings_goals = db.session.execute(statement).scalars().all()

    goals = []
    total_saved = ZERO
    total_target = ZERO
    overall_remaining = ZERO
    completed_count = 0

    for goal in savings_goals:
        remaining = goal.target_amount - goal.saved_amount
        completed = goal.saved_amount >= goal.target_amount
        percentage = (
            goal.saved_amount / goal.target_amount
        ) * ONE_HUNDRED
        over_target = max(goal.saved_amount - goal.target_amount, ZERO)
        overdue = (
            goal.target_date is not None
            and goal.target_date < today
            and not completed
        )

        goals.append({
            "goal": goal,
            "remaining": max(remaining, ZERO),
            "percentage": percentage,
            "visual_percentage": min(
                percentage,
                ONE_HUNDRED
            ).quantize(PERCENT_STEP),
            "completed": completed,
            "over_target": over_target,
            "overdue": overdue,
        })

        total_saved += goal.saved_amount
        total_target += goal.target_amount
        overall_remaining += max(remaining, ZERO)

        if completed:
            completed_count += 1

    overall_percentage = (
        (total_saved / total_target) * ONE_HUNDRED
        if total_target > ZERO
        else ZERO
    )

    return {
        "goals": goals,
        "total_saved": total_saved,
        "total_target": total_target,
        "overall_remaining": overall_remaining,
        "overall_percentage": overall_percentage,
        "visual_percentage": min(
            overall_percentage,
            ONE_HUNDRED
        ).quantize(PERCENT_STEP),
        "completed_count": completed_count,
        "active_count": len(savings_goals) - completed_count,
    }
