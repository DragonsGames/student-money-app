from decimal import Decimal

from sqlalchemy import case, func

from extensions import db
from models import Transaction


ZERO = Decimal("0.000")


# AI assistance: OpenAI Codex helped draft this reusable transaction aggregate;
# reviewed and adapted by the project author.
def get_financial_summary(user_id, starting_balance=ZERO):
    statement = db.select(
        func.coalesce(
            func.sum(
                case(
                    (
                        Transaction.transaction_type == "income",
                        Transaction.amount
                    ),
                    else_=ZERO
                )
            ),
            ZERO
        ),
        func.coalesce(
            func.sum(
                case(
                    (
                        Transaction.transaction_type == "expense",
                        Transaction.amount
                    ),
                    else_=ZERO
                )
            ),
            ZERO
        )
    ).where(Transaction.user_id == user_id)

    total_income, total_expenses = db.session.execute(statement).one()
    starting_balance = starting_balance if starting_balance is not None else ZERO

    return {
        "starting_balance": starting_balance,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "current_balance": (
            starting_balance + total_income - total_expenses
        ),
    }
