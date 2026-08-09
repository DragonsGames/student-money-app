from datetime import date
from decimal import Decimal

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models import (
    Budget,
    Category,
    IncomeSource,
    SavingsGoal,
    Transaction,
    User,
    UserSettings,
)


@pytest.fixture
def app(tmp_path):
    database_path = tmp_path / "test.sqlite"
    test_app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-only-secret",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path.as_posix()}",
        "WTF_CSRF_ENABLED": False,
    })

    context = test_app.app_context()
    context.push()
    db.create_all()

    yield test_app

    db.session.remove()
    db.drop_all()
    context.pop()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user_factory(app):
    counter = 0

    def create_user(
        *,
        email=None,
        password="password123",
        completed=True,
        display_name="Student",
        starting_balance=Decimal("0.000"),
        currency="TND",
        budget_period="monthly",
        appearance="system",
        language="en",
    ):
        nonlocal counter
        counter += 1
        user = User(
            email=email or f"student{counter}@example.com",
            password_hash=generate_password_hash(
                password,
                method="pbkdf2:sha256:1000",
            ),
            onboarding_completed=completed,
        )
        user.settings = UserSettings(
            display_name=display_name,
            starting_balance=starting_balance,
            currency=currency,
            budget_period=budget_period,
            appearance=appearance,
            language=language,
        )
        db.session.add(user)
        db.session.commit()
        return user

    return create_user


@pytest.fixture
def category_factory():
    def create_category(
        user,
        *,
        name="Food",
        category_type="expense",
        icon="🍔",
        color="#b6532e",
        is_default=False,
    ):
        category = Category(
            user_id=user.id,
            name=name,
            category_type=category_type,
            icon=icon,
            color=color,
            is_default=is_default,
        )
        db.session.add(category)
        db.session.commit()
        return category

    return create_category


@pytest.fixture
def transaction_factory():
    def create_transaction(
        user,
        category,
        *,
        transaction_type=None,
        amount=Decimal("10.000"),
        transaction_date=None,
        description=None,
    ):
        transaction = Transaction(
            user_id=user.id,
            category_id=category.id,
            transaction_type=transaction_type or category.category_type,
            amount=amount,
            transaction_date=transaction_date or date.today(),
            description=description,
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction

    return create_transaction


@pytest.fixture
def budget_factory():
    def create_budget(user, category, amount=Decimal("100.000")):
        budget = Budget(
            user_id=user.id,
            category_id=category.id,
            amount=amount,
        )
        db.session.add(budget)
        db.session.commit()
        return budget

    return create_budget


@pytest.fixture
def savings_factory():
    def create_goal(
        user,
        *,
        name="Laptop",
        target=Decimal("500.000"),
        saved=Decimal("0.000"),
        target_date=None,
    ):
        goal = SavingsGoal(
            user_id=user.id,
            name=name,
            target_amount=target,
            saved_amount=saved,
            target_date=target_date,
        )
        db.session.add(goal)
        db.session.commit()
        return goal

    return create_goal


@pytest.fixture
def income_source_factory():
    def create_source(user, *, name="Allowance", amount=Decimal("100.000")):
        source = IncomeSource(
            user_id=user.id,
            name=name,
            amount=amount,
            frequency="monthly",
            is_recurring=True,
        )
        db.session.add(source)
        db.session.commit()
        return source

    return create_source


@pytest.fixture
def login(client):
    def login_user(user, password="password123", remember=False):
        return client.post("/login", data={
            "email": user.email,
            "password": password,
            "remember": "y" if remember else "",
        })

    return login_user
