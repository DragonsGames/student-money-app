from datetime import date, timedelta
from decimal import Decimal

from extensions import db
from models import SavingsGoal, Transaction
from services.finance import get_financial_summary


def test_savings_goal_crud(client, user_factory, login):
    user = user_factory(starting_balance=Decimal("500.000"))
    login(user)
    past_date = date.today() - timedelta(days=1)

    response = client.post("/savings/add", data={
        "name": "Laptop",
        "target_amount": "1000.000",
        "target_date": past_date.isoformat(),
    })
    assert response.status_code == 302
    goal = db.session.scalar(db.select(SavingsGoal))
    assert goal.saved_amount == Decimal("0.000")

    response = client.post(f"/savings/{goal.id}/edit", data={
        "name": "New laptop",
        "target_amount": "900.000",
        "target_date": "",
    })
    assert response.status_code == 302
    db.session.refresh(goal)
    assert goal.name == "New laptop"
    assert goal.target_amount == Decimal("900.000")

    assert client.post(f"/savings/{goal.id}/delete").status_code == 302
    assert db.session.get(SavingsGoal, goal.id) is None


def test_add_withdraw_and_overfund_savings(
    client,
    user_factory,
    savings_factory,
    login,
):
    user = user_factory()
    goal = savings_factory(user, target=Decimal("100.000"))
    login(user)

    assert client.post(f"/savings/{goal.id}/amount", data={
        "action": "add",
        "amount": "130.000",
    }).status_code == 302
    db.session.refresh(goal)
    assert goal.saved_amount == Decimal("130.000")

    assert client.post(f"/savings/{goal.id}/amount", data={
        "action": "withdraw",
        "amount": "30.000",
    }).status_code == 302
    db.session.refresh(goal)
    assert goal.saved_amount == Decimal("100.000")


def test_savings_cannot_go_negative_or_overflow(
    client,
    user_factory,
    savings_factory,
    login,
):
    user = user_factory()
    goal = savings_factory(
        user,
        saved=Decimal("10.000"),
        target=Decimal("100.000"),
    )
    login(user)

    withdrawal = client.post(f"/savings/{goal.id}/amount", data={
        "action": "withdraw",
        "amount": "10.001",
    })
    assert withdrawal.status_code == 200

    goal.saved_amount = Decimal("999999999.999")
    db.session.commit()

    addition = client.post(f"/savings/{goal.id}/amount", data={
        "action": "add",
        "amount": "0.001",
    })
    assert addition.status_code == 200
    db.session.refresh(goal)
    assert goal.saved_amount == Decimal("999999999.999")


def test_savings_progress_never_creates_transaction_or_changes_balance(
    client,
    user_factory,
    savings_factory,
    login,
):
    user = user_factory(starting_balance=Decimal("250.000"))
    goal = savings_factory(user)
    login(user)

    client.post(f"/savings/{goal.id}/amount", data={
        "action": "add",
        "amount": "75.000",
    })

    assert db.session.scalar(db.select(db.func.count(Transaction.id))) == 0
    summary = get_financial_summary(user.id, user.settings.starting_balance)
    assert summary["current_balance"] == Decimal("250.000")


def test_foreign_savings_goal_is_hidden(
    client,
    user_factory,
    savings_factory,
    login,
):
    owner = user_factory()
    attacker = user_factory()
    goal = savings_factory(owner)
    login(attacker)

    assert client.get(f"/savings/{goal.id}/edit").status_code == 404
    assert client.get(f"/savings/{goal.id}/amount").status_code == 404
    assert client.post(f"/savings/{goal.id}/delete").status_code == 404


def test_savings_delete_is_post_only(
    client,
    user_factory,
    savings_factory,
    login,
):
    user = user_factory()
    goal = savings_factory(user)
    login(user)

    assert client.get(f"/savings/{goal.id}/delete").status_code == 405
