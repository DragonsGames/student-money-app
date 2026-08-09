from decimal import Decimal

from extensions import db
from models import Budget


def test_budget_crud_uses_expense_categories_only(
    client,
    user_factory,
    category_factory,
    login,
):
    user = user_factory()
    food = category_factory(user)
    transport = category_factory(user, name="Transport")
    income = category_factory(user, name="Work", category_type="income")
    login(user)

    invalid = client.post("/budgets/add", data={
        "category_id": income.id,
        "amount": "100.000",
    })
    assert invalid.status_code == 200

    assert client.post("/budgets/add", data={
        "category_id": food.id,
        "amount": "100.000",
    }).status_code == 302
    budget = db.session.scalar(db.select(Budget))

    assert client.post(f"/budgets/{budget.id}/edit", data={
        "category_id": transport.id,
        "amount": "250.500",
    }).status_code == 302
    db.session.refresh(budget)
    assert budget.category_id == transport.id
    assert budget.amount == Decimal("250.500")

    assert client.post(f"/budgets/{budget.id}/delete").status_code == 302
    assert db.session.get(Budget, budget.id) is None


def test_one_budget_per_category_is_enforced(
    client,
    user_factory,
    category_factory,
    budget_factory,
    login,
):
    user = user_factory()
    category = category_factory(user)
    budget_factory(user, category)
    login(user)

    response = client.post("/budgets/add", data={
        "category_id": category.id,
        "amount": "200.000",
    })

    assert response.status_code == 200
    assert db.session.scalar(db.select(db.func.count(Budget.id))) == 1


def test_budget_amount_boundaries(client, user_factory, category_factory, login):
    user = user_factory()
    category = category_factory(user)
    login(user)

    for amount in ("0.000", "-1.000", "1000000000.000"):
        response = client.post("/budgets/add", data={
            "category_id": category.id,
            "amount": amount,
        })
        assert response.status_code == 200

    assert db.session.scalar(db.select(db.func.count(Budget.id))) == 0

    assert client.post("/budgets/add", data={
        "category_id": category.id,
        "amount": "999999999.999",
    }).status_code == 302


def test_budget_period_updates_weekly_and_monthly(
    client,
    user_factory,
    login,
):
    user = user_factory(budget_period="monthly")
    login(user)

    for period in ("weekly", "monthly"):
        response = client.post(
            "/budgets/period",
            data={"budget_period": period},
        )
        assert response.status_code == 302
        db.session.refresh(user.settings)
        assert user.settings.budget_period == period


def test_foreign_budget_mutations_are_blocked(
    client,
    user_factory,
    category_factory,
    budget_factory,
    login,
):
    owner = user_factory()
    attacker = user_factory()
    category = category_factory(owner)
    budget = budget_factory(owner, category)
    login(attacker)

    assert client.get(f"/budgets/{budget.id}/edit").status_code == 404
    assert client.post(f"/budgets/{budget.id}/delete").status_code == 404


def test_budget_delete_is_post_only(
    client,
    user_factory,
    category_factory,
    budget_factory,
    login,
):
    user = user_factory()
    category = category_factory(user)
    budget = budget_factory(user, category)
    login(user)

    assert client.get(f"/budgets/{budget.id}/delete").status_code == 405
