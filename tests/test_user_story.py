from datetime import date

from extensions import db
from models import Budget, Category, SavingsGoal, Transaction, User


def test_complete_student_user_story(client):
    assert client.post("/register", data={
        "email": "story@example.com",
        "password": "password123",
        "confirmation": "password123",
    }).headers["Location"].endswith("/onboarding")

    client.post("/onboarding", data={
        "display_name": "Maya",
        "currency": "TND",
    })
    client.post("/onboarding/goals", data={"goals": ["track_money"]})
    client.post("/onboarding/income", data={
        "sources-0-name": "Allowance",
        "sources-0-amount": "100.000",
        "sources-0-frequency": "monthly",
        "sources-0-next_payment_date": "",
    })
    client.post("/onboarding/balance", data={"starting_balance": "500.000"})
    completed = client.post("/onboarding/categories", data={
        "categories-0-name": "Food",
        "categories-0-category_type": "expense",
        "categories-0-icon": "🍔",
        "categories-1-name": "Work",
        "categories-1-category_type": "income",
        "categories-1-icon": "💼",
    })
    assert completed.headers["Location"].endswith("/dashboard")

    user = db.session.scalar(
        db.select(User).where(User.email == "story@example.com")
    )
    food = db.session.scalar(
        db.select(Category).where(
            Category.user_id == user.id,
            Category.name == "Food",
        )
    )

    transaction_response = client.post("/transactions/add", data={
        "transaction_type": "expense",
        "category_id": food.id,
        "amount": "25.000",
        "description": "Lunch",
        "transaction_date": date.today().isoformat(),
    })
    assert transaction_response.status_code == 302

    budget_response = client.post("/budgets/add", data={
        "category_id": food.id,
        "amount": "100.000",
    })
    assert budget_response.status_code == 302

    savings_response = client.post("/savings/add", data={
        "name": "Laptop",
        "target_amount": "900.000",
        "target_date": "",
    })
    assert savings_response.status_code == 302

    history = client.get("/history?transaction_type=expense&sort=newest")
    assert history.status_code == 200
    assert b"Lunch" in history.data

    settings = client.post("/settings/preferences", data={
        "appearance": "dark",
        "language": "fr",
    })
    assert settings.status_code == 302

    db.session.refresh(user.settings)
    assert user.settings.appearance == "dark"
    assert user.settings.language == "fr"
    assert db.session.scalar(db.select(db.func.count(Transaction.id))) == 1
    assert db.session.scalar(db.select(db.func.count(Budget.id))) == 1
    assert db.session.scalar(db.select(db.func.count(SavingsGoal.id))) == 1
