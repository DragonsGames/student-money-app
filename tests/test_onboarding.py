from datetime import date, timedelta
from decimal import Decimal

from extensions import db
from models import Category, IncomeSource, UserGoal


def test_incomplete_user_cannot_bypass_onboarding(
    client,
    user_factory,
    login,
):
    user = user_factory(completed=False)
    login(user)

    for path in ("/dashboard", "/transactions", "/settings"):
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/onboarding")


def test_profile_step_updates_settings(client, user_factory, login):
    user = user_factory(completed=False, display_name=None)
    login(user)

    response = client.post("/onboarding", data={
        "display_name": "Maya",
        "currency": "EUR",
    })

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/onboarding/goals")
    db.session.refresh(user.settings)
    assert user.settings.display_name == "Maya"
    assert user.settings.currency == "EUR"


def test_goals_step_requires_a_choice(client, user_factory, login):
    user = user_factory(completed=False)
    login(user)

    response = client.post("/onboarding/goals", data={})

    assert response.status_code == 200
    assert not user.goals


def test_income_step_rejects_past_payment_date(
    client,
    user_factory,
    login,
):
    user = user_factory(completed=False)
    login(user)
    yesterday = date.today() - timedelta(days=1)

    response = client.post("/onboarding/income", data={
        "sources-0-name": "Allowance",
        "sources-0-amount": "50.000",
        "sources-0-frequency": "monthly",
        "sources-0-next_payment_date": yesterday.isoformat(),
    })

    assert response.status_code == 200
    assert not user.income_sources


def test_balance_step_accepts_zero_and_rejects_negative(
    client,
    user_factory,
    login,
):
    user = user_factory(completed=False, starting_balance=Decimal("10.000"))
    login(user)

    invalid = client.post(
        "/onboarding/balance",
        data={"starting_balance": "-0.001"},
    )
    assert invalid.status_code == 200
    db.session.refresh(user.settings)
    assert user.settings.starting_balance == Decimal("10.000")

    valid = client.post(
        "/onboarding/balance",
        data={"starting_balance": "0.000"},
    )
    assert valid.status_code == 302
    db.session.refresh(user.settings)
    assert user.settings.starting_balance == Decimal("0.000")


def test_full_five_step_onboarding_flow(client, user_factory, login):
    user = user_factory(completed=False, display_name=None)
    login(user)

    assert client.post("/onboarding", data={
        "display_name": "Étudiante",
        "currency": "TND",
    }).headers["Location"].endswith("/onboarding/goals")

    assert client.post("/onboarding/goals", data={
        "goals": ["save_more", "track_money"],
    }).headers["Location"].endswith("/onboarding/income")

    assert client.post("/onboarding/income", data={
        "sources-0-name": "Café work",
        "sources-0-amount": "125.500",
        "sources-0-frequency": "monthly",
        "sources-0-next_payment_date": "",
    }).headers["Location"].endswith("/onboarding/balance")

    assert client.post("/onboarding/balance", data={
        "starting_balance": "0.000",
    }).headers["Location"].endswith("/onboarding/categories")

    response = client.post("/onboarding/categories", data={
        "categories-0-name": "Food",
        "categories-0-category_type": "expense",
        "categories-0-icon": "🍔",
        "categories-1-name": "عمل",
        "categories-1-category_type": "income",
        "categories-1-icon": "🎓",
    })

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    db.session.refresh(user)
    assert user.onboarding_completed is True
    assert db.session.scalar(
        db.select(db.func.count(UserGoal.id)).where(UserGoal.user_id == user.id)
    ) == 2
    assert db.session.scalar(
        db.select(db.func.count(IncomeSource.id)).where(
            IncomeSource.user_id == user.id
        )
    ) == 1
    categories = db.session.execute(
        db.select(Category).where(Category.user_id == user.id)
    ).scalars().all()
    assert [category.name for category in categories] == ["Food", "عمل"]
    assert categories[0].is_default is True
    assert categories[1].is_default is False


def test_renamed_starter_category_is_no_longer_marked_default(
    client,
    user_factory,
    login,
):
    user = user_factory(completed=False)
    login(user)

    response = client.post("/onboarding/categories", data={
        "categories-0-name": "Meals",
        "categories-0-category_type": "expense",
        "categories-0-icon": "🍔",
    })

    assert response.status_code == 302
    category = db.session.scalar(
        db.select(Category).where(Category.user_id == user.id)
    )
    assert category.name == "Meals"
    assert category.is_default is False
