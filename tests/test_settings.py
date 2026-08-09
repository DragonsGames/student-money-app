from datetime import date
from decimal import Decimal

from extensions import db
from models import IncomeSource, Transaction, UserGoal
from services.finance import get_financial_summary


def test_profile_update_normalizes_empty_name_and_email_is_read_only(
    client,
    user_factory,
    login,
):
    user = user_factory(display_name="Maya")
    login(user)

    page = client.get("/settings")
    assert user.email.encode() in page.data
    assert b"readonly" in page.data

    response = client.post(
        "/settings/profile",
        data={"display_name": "   ", "email": "changed@example.com"},
    )
    assert response.status_code == 302
    db.session.refresh(user.settings)
    db.session.refresh(user)
    assert user.settings.display_name is None
    assert user.email != "changed@example.com"


def test_money_settings_update_and_zero_balance(
    client,
    user_factory,
    login,
):
    user = user_factory(starting_balance=Decimal("10.000"))
    login(user)

    response = client.post("/settings/money", data={
        "currency": "EUR",
        "starting_balance": "0.000",
        "budget_period": "weekly",
    })

    assert response.status_code == 302
    db.session.refresh(user.settings)
    assert user.settings.currency == "EUR"
    assert user.settings.starting_balance == Decimal("0.000")
    assert user.settings.budget_period == "weekly"


def test_goal_settings_synchronize_rows(client, user_factory, login):
    user = user_factory()
    db.session.add(UserGoal(user_id=user.id, goal_type="save_more"))
    db.session.commit()
    login(user)

    response = client.post("/settings/goals", data={
        "goals": ["track_money", "better_habits"],
    })

    assert response.status_code == 302
    goals = db.session.execute(
        db.select(UserGoal.goal_type).where(UserGoal.user_id == user.id)
    ).scalars().all()
    assert set(goals) == {"track_money", "better_habits"}


def test_income_source_crud_does_not_change_balance(
    client,
    user_factory,
    login,
):
    user = user_factory(starting_balance=Decimal("80.000"))
    login(user)

    response = client.post("/settings/income-sources/add", data={
        "name": "Part-time work",
        "amount": "300.000",
        "frequency": "monthly",
        "next_payment_date": date.today().isoformat(),
    })
    assert response.status_code == 302
    source = db.session.scalar(db.select(IncomeSource))
    assert source.is_recurring is True

    response = client.post(
        f"/settings/income-sources/{source.id}/edit",
        data={
            "name": "One-off project",
            "amount": "450.000",
            "frequency": "one_time",
            "next_payment_date": "",
        },
    )
    assert response.status_code == 302
    db.session.refresh(source)
    assert source.is_recurring is False
    assert source.amount == Decimal("450.000")
    assert db.session.scalar(db.select(db.func.count(Transaction.id))) == 0
    assert get_financial_summary(
        user.id,
        user.settings.starting_balance,
    )["current_balance"] == Decimal("80.000")

    assert client.post(
        f"/settings/income-sources/{source.id}/delete"
    ).status_code == 302
    assert db.session.get(IncomeSource, source.id) is None


def test_preferences_accept_supported_values_and_reject_invalid_values(
    client,
    user_factory,
    login,
):
    user = user_factory()
    login(user)

    for appearance, language in (
        ("system", "en"),
        ("light", "fr"),
        ("dark", "ar"),
    ):
        response = client.post("/settings/preferences", data={
            "appearance": appearance,
            "language": language,
        })
        assert response.status_code == 302
        db.session.refresh(user.settings)
        assert user.settings.appearance == appearance
        assert user.settings.language == language

    invalid = client.post("/settings/preferences", data={
        "appearance": "neon",
        "language": "xx",
    })
    assert invalid.status_code == 200
    db.session.refresh(user.settings)
    assert user.settings.appearance == "dark"
    assert user.settings.language == "ar"


def test_foreign_income_source_is_hidden(
    client,
    user_factory,
    income_source_factory,
    login,
):
    owner = user_factory()
    attacker = user_factory()
    source = income_source_factory(owner)
    login(attacker)

    assert client.get(
        f"/settings/income-sources/{source.id}/edit"
    ).status_code == 404
    assert client.post(
        f"/settings/income-sources/{source.id}/delete"
    ).status_code == 404


def test_income_source_delete_is_post_only(
    client,
    user_factory,
    income_source_factory,
    login,
):
    user = user_factory()
    source = income_source_factory(user)
    login(user)

    assert client.get(
        f"/settings/income-sources/{source.id}/delete"
    ).status_code == 405
