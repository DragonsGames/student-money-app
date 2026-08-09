from datetime import date, timedelta
from decimal import Decimal

import pytest

from services.budgets import get_budget_summary, get_period_start
from services.finance import get_financial_summary
from services.safe_to_spend import get_safe_to_spend_summary
from services.savings import get_savings_summary


@pytest.mark.parametrize(
    ("income", "expense", "expected"),
    [
        (None, None, "100.000"),
        ("25.500", None, "125.500"),
        (None, "40.250", "59.750"),
        ("25.500", "40.250", "85.250"),
        (None, "150.000", "-50.000"),
    ],
)
def test_financial_summary_uses_exact_decimal_math(
    user_factory,
    category_factory,
    transaction_factory,
    income,
    expense,
    expected,
):
    user = user_factory(starting_balance=Decimal("100.000"))
    if income:
        category = category_factory(
            user,
            name="Work",
            category_type="income",
        )
        transaction_factory(
            user,
            category,
            amount=Decimal(income),
        )
    if expense:
        category = category_factory(user, name="Food")
        transaction_factory(
            user,
            category,
            amount=Decimal(expense),
        )

    summary = get_financial_summary(
        user.id,
        user.settings.starting_balance,
    )

    assert summary["current_balance"] == Decimal(expected)


def test_financial_summary_supports_maximum_value_and_user_isolation(
    user_factory,
    category_factory,
    transaction_factory,
):
    user = user_factory()
    other = user_factory()
    category = category_factory(user, category_type="income")
    other_category = category_factory(
        other,
        name="Other work",
        category_type="income",
    )
    transaction_factory(
        user,
        category,
        amount=Decimal("999999999.999"),
    )
    transaction_factory(
        other,
        other_category,
        amount=Decimal("500.000"),
    )

    summary = get_financial_summary(user.id)

    assert summary["total_income"] == Decimal("999999999.999")
    assert summary["current_balance"] == Decimal("999999999.999")


def test_income_source_does_not_affect_financial_summary(
    user_factory,
    income_source_factory,
):
    user = user_factory(starting_balance=Decimal("75.000"))
    income_source_factory(user, amount=Decimal("500.000"))

    summary = get_financial_summary(user.id, user.settings.starting_balance)

    assert summary["current_balance"] == Decimal("75.000")


def test_budget_period_boundaries():
    sunday = date(2026, 8, 9)

    assert get_period_start("weekly", sunday) == date(2026, 8, 3)
    assert get_period_start("monthly", sunday) == date(2026, 8, 1)


def test_budget_summary_filters_period_type_and_budgeted_categories(
    user_factory,
    category_factory,
    transaction_factory,
    budget_factory,
):
    today = date(2026, 8, 9)
    user = user_factory(budget_period="weekly")
    food = category_factory(user, name="Food")
    transport = category_factory(user, name="Transport")
    budget_factory(user, food, Decimal("100.000"))
    transaction_factory(
        user,
        food,
        amount=Decimal("30.000"),
        transaction_date=date(2026, 8, 3),
    )
    transaction_factory(
        user,
        food,
        amount=Decimal("40.000"),
        transaction_date=date(2026, 8, 2),
    )
    transaction_factory(
        user,
        food,
        transaction_type="income",
        amount=Decimal("90.000"),
        transaction_date=today,
    )
    transaction_factory(
        user,
        transport,
        amount=Decimal("70.000"),
        transaction_date=today,
    )

    summary = get_budget_summary(user.id, "weekly", today=today)

    assert summary["period_start"] == date(2026, 8, 3)
    assert summary["total_budgeted"] == Decimal("100.000")
    assert summary["total_spent"] == Decimal("30.000")
    assert summary["total_remaining"] == Decimal("70.000")


def test_budget_summary_reports_overspending_and_caps_visual_progress(
    user_factory,
    category_factory,
    transaction_factory,
    budget_factory,
):
    user = user_factory()
    category = category_factory(user)
    budget_factory(user, category, Decimal("100.000"))
    transaction_factory(user, category, amount=Decimal("125.000"))

    summary = get_budget_summary(user.id, "monthly", today=date.today())

    assert summary["total_remaining"] == Decimal("-25.000")
    assert summary["total_percentage"] == Decimal("125.00")
    assert summary["visual_percentage"] == Decimal("100.00")
    assert summary["overspent"] is True


def test_savings_summary_handles_completed_overfunded_and_overdue_goals(
    user_factory,
    savings_factory,
):
    today = date(2026, 8, 9)
    user = user_factory()
    savings_factory(
        user,
        name="Laptop",
        target=Decimal("100.000"),
        saved=Decimal("130.000"),
    )
    savings_factory(
        user,
        name="Trip",
        target=Decimal("200.000"),
        saved=Decimal("50.000"),
        target_date=today - timedelta(days=1),
    )

    summary = get_savings_summary(user.id, today=today)

    assert summary["total_saved"] == Decimal("180.000")
    assert summary["overall_remaining"] == Decimal("150.000")
    assert summary["completed_count"] == 1
    assert summary["active_count"] == 1
    assert summary["goals"][0]["overdue"] is True
    assert summary["goals"][1]["over_target"] == Decimal("30.000")


def test_safe_to_spend_examples_and_per_budget_clamping():
    summary = get_safe_to_spend_summary(
        {"current_balance": Decimal("1000.000")},
        {"items": [
            {"remaining": Decimal("150.000")},
            {"remaining": Decimal("-20.000")},
        ]},
        {"total_saved": Decimal("200.000")},
    )
    assert summary["budget_reserved"] == Decimal("150.000")
    assert summary["safe_to_spend"] == Decimal("650.000")

    clamped = get_safe_to_spend_summary(
        {"current_balance": Decimal("500.000")},
        {"items": [
            {"remaining": Decimal("-50.000")},
            {"remaining": Decimal("100.000")},
        ]},
        {"total_saved": Decimal("0.000")},
    )
    assert clamped["budget_reserved"] == Decimal("100.000")


@pytest.mark.parametrize(
    ("balance", "savings", "budget", "safe", "shortfall", "overcommitted"),
    [
        ("300.000", "200.000", "250.000", "0.000", "150.000", True),
        ("500.000", "0.000", "0.000", "500.000", "0.000", False),
        ("-50.000", "0.000", "0.000", "0.000", "50.000", True),
        ("500.000", "130.000", "0.000", "370.000", "0.000", False),
    ],
)
def test_safe_to_spend_boundaries(
    balance,
    savings,
    budget,
    safe,
    shortfall,
    overcommitted,
):
    summary = get_safe_to_spend_summary(
        {"current_balance": Decimal(balance)},
        {"items": [{"remaining": Decimal(budget)}]},
        {"total_saved": Decimal(savings)},
    )

    assert summary["safe_to_spend"] == Decimal(safe)
    assert summary["shortfall"] == Decimal(shortfall)
    assert summary["is_overcommitted"] is overcommitted
