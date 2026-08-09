from datetime import date, timedelta
from decimal import Decimal

from extensions import db
from models import Transaction


def transaction_data(category, **overrides):
    data = {
        "transaction_type": category.category_type,
        "category_id": str(category.id),
        "amount": "25.000",
        "transaction_date": date.today().isoformat(),
        "description": "Lunch",
    }
    data.update(overrides)
    return data


def test_create_income_and_expense_transactions(
    client,
    user_factory,
    category_factory,
    login,
):
    user = user_factory()
    expense = category_factory(user, name="Food")
    income = category_factory(user, name="Work", category_type="income")
    login(user)

    assert client.post(
        "/transactions/add",
        data=transaction_data(expense),
    ).status_code == 302
    assert client.post(
        "/transactions/add",
        data=transaction_data(income, amount="100.000"),
    ).status_code == 302

    transactions = db.session.execute(
        db.select(Transaction).order_by(Transaction.id)
    ).scalars().all()
    assert [item.transaction_type for item in transactions] == [
        "expense",
        "income",
    ]


def test_edit_and_delete_transaction(
    client,
    user_factory,
    category_factory,
    transaction_factory,
    login,
):
    user = user_factory()
    food = category_factory(user)
    transport = category_factory(user, name="Transport")
    transaction = transaction_factory(user, food)
    login(user)

    response = client.post(
        f"/transactions/{transaction.id}/edit",
        data=transaction_data(
            transport,
            amount="75.500",
            description="Bus pass",
        ),
    )
    assert response.status_code == 302
    db.session.refresh(transaction)
    assert transaction.category_id == transport.id
    assert transaction.amount == Decimal("75.500")

    response = client.post(f"/transactions/{transaction.id}/delete")
    assert response.status_code == 302
    assert db.session.get(Transaction, transaction.id) is None


def test_transaction_validation_rejects_date_and_amount_boundaries(
    client,
    user_factory,
    category_factory,
    login,
):
    user = user_factory()
    category = category_factory(user)
    login(user)

    invalid_rows = [
        {"amount": "0.000"},
        {"amount": "1000000000.000"},
        {"transaction_date": (date.today() + timedelta(days=1)).isoformat()},
    ]
    for overrides in invalid_rows:
        response = client.post(
            "/transactions/add",
            data=transaction_data(category, **overrides),
        )
        assert response.status_code == 200

    assert db.session.scalar(db.select(db.func.count(Transaction.id))) == 0


def test_category_must_match_type_and_owner(
    client,
    user_factory,
    category_factory,
    login,
):
    user = user_factory()
    other = user_factory()
    expense = category_factory(user)
    foreign = category_factory(other, name="Foreign")
    login(user)

    mismatch = client.post(
        "/transactions/add",
        data=transaction_data(expense, transaction_type="income"),
    )
    foreign_response = client.post(
        "/transactions/add",
        data=transaction_data(foreign),
    )

    assert mismatch.status_code == 200
    assert foreign_response.status_code == 200
    assert db.session.scalar(db.select(db.func.count(Transaction.id))) == 0


def test_foreign_transaction_edit_and_delete_return_404(
    client,
    user_factory,
    category_factory,
    transaction_factory,
    login,
):
    owner = user_factory()
    attacker = user_factory()
    category = category_factory(owner)
    transaction = transaction_factory(owner, category)
    login(attacker)

    assert client.get(f"/transactions/{transaction.id}/edit").status_code == 404
    assert client.post(
        f"/transactions/{transaction.id}/delete"
    ).status_code == 404
    assert db.session.get(Transaction, transaction.id) is not None


def test_transaction_delete_is_post_only(
    client,
    user_factory,
    category_factory,
    transaction_factory,
    login,
):
    user = user_factory()
    category = category_factory(user)
    transaction = transaction_factory(user, category)
    login(user)

    assert client.get(f"/transactions/{transaction.id}/delete").status_code == 405


def test_user_text_is_html_escaped(
    client,
    user_factory,
    category_factory,
    transaction_factory,
    login,
):
    user = user_factory(display_name="<script>alert(1)</script>")
    category = category_factory(user, name="<b>Food</b>")
    transaction_factory(
        user,
        category,
        description="<img src=x onerror=alert(1)>",
    )
    login(user)

    response = client.get("/transactions")

    assert response.status_code == 200
    assert b"<img src=x" not in response.data
    assert b"&lt;img src=x" in response.data
