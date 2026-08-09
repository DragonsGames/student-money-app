from decimal import Decimal


ZERO = Decimal("0.000")


# AI assistance: OpenAI Codex helped draft this Safe-to-Spend derived
# calculation; reviewed and adapted by the project author.
def get_safe_to_spend_summary(
    financial_summary,
    budget_summary,
    savings_summary,
):
    current_balance = financial_summary["current_balance"]
    savings_reserved = savings_summary["total_saved"]
    budget_reserved = sum(
        (
            max(item["remaining"], ZERO)
            for item in budget_summary["items"]
        ),
        ZERO
    )
    raw_safe_to_spend = (
        current_balance
        - savings_reserved
        - budget_reserved
    )

    return {
        "current_balance": current_balance,
        "savings_reserved": savings_reserved,
        "budget_reserved": budget_reserved,
        "raw_safe_to_spend": raw_safe_to_spend,
        "safe_to_spend": max(raw_safe_to_spend, ZERO),
        "shortfall": max(-raw_safe_to_spend, ZERO),
        "is_overcommitted": raw_safe_to_spend < ZERO,
    }
