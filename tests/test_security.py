from decimal import Decimal

import pytest

from extensions import db
from models import Budget, Category, Transaction


@pytest.mark.parametrize(
    "target",
    ["/", "/login", "/register", "/settings", "/history?type=expense"],
)
def test_language_redirect_accepts_safe_local_paths(client, target):
    response = client.post("/preferences/language", data={
        "language": "fr",
        "next": target,
    })

    assert response.status_code == 302
    assert response.headers["Location"].endswith(target)


@pytest.mark.parametrize(
    "target",
    [
        "https://evil.example/",
        "http://evil.example/",
        "//evil.example/",
        "/\\evil.example/",
        "/%5cevil.example/",
        "/%2f%2fevil.example/",
        "/%0devil.example/",
        "/%0aevil.example/",
    ],
)
def test_language_redirect_never_accepts_external_or_malformed_targets(
    client,
    target,
):
    response = client.post("/preferences/language", data={
        "language": "ar",
        "next": target,
    })

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    assert "evil.example" not in response.headers["Location"]


def test_representative_mutations_reject_missing_csrf(
    app,
    client,
    user_factory,
    category_factory,
    transaction_factory,
    budget_factory,
    savings_factory,
    login,
):
    user = user_factory(starting_balance=Decimal("10.000"))
    category = category_factory(user)
    transaction = transaction_factory(user, category)
    budget = budget_factory(user, category)
    goal = savings_factory(user, saved=Decimal("10.000"))
    login(user)
    app.config["WTF_CSRF_ENABLED"] = True

    assert client.post(f"/transactions/{transaction.id}/delete").status_code == 400
    assert client.post(f"/categories/{category.id}/delete").status_code == 400
    assert client.post(f"/budgets/{budget.id}/delete").status_code == 400

    savings_response = client.post(f"/savings/{goal.id}/amount", data={
        "action": "add",
        "amount": "5.000",
    })
    assert savings_response.status_code == 200
    db.session.refresh(goal)
    assert goal.saved_amount == Decimal("10.000")

    settings_response = client.post("/settings/money", data={
        "currency": "EUR",
        "starting_balance": "50.000",
        "budget_period": "weekly",
    })
    assert settings_response.status_code == 200
    db.session.refresh(user.settings)
    assert user.settings.starting_balance == Decimal("10.000")

    logout_response = client.post("/logout")
    assert logout_response.status_code == 302
    with client.session_transaction() as session:
        assert session.get("_user_id") == str(user.id)

    assert db.session.get(Transaction, transaction.id) is not None
    assert db.session.get(Category, category.id) is not None
    assert db.session.get(Budget, budget.id) is not None


def test_language_update_rejects_missing_csrf(app, client):
    app.config["WTF_CSRF_ENABLED"] = True

    client.post("/preferences/language", data={
        "language": "ar",
        "next": "/",
    })

    with client.session_transaction() as session:
        assert session.get("language") is None


def test_invalid_csrf_token_is_rejected(
    app,
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
    app.config["WTF_CSRF_ENABLED"] = True

    response = client.post(
        f"/transactions/{transaction.id}/delete",
        data={"csrf_token": "not-a-valid-token"},
    )

    assert response.status_code == 400
    assert db.session.get(Transaction, transaction.id) is not None


def test_security_headers_and_authenticated_cache_control(
    client,
    user_factory,
    login,
):
    public_response = client.get("/")
    assert public_response.headers["X-Content-Type-Options"] == "nosniff"
    assert public_response.headers["X-Frame-Options"] == "DENY"
    assert public_response.headers["Referrer-Policy"] == (
        "strict-origin-when-cross-origin"
    )
    assert "camera=()" in public_response.headers["Permissions-Policy"]
    assert "no-store" not in public_response.headers.get("Cache-Control", "")

    user = user_factory()
    login(user)
    private_response = client.get("/dashboard")
    assert private_response.headers["Cache-Control"] == "no-store, private"


def test_cookie_security_defaults(app):
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["REMEMBER_COOKIE_HTTPONLY"] is True
    assert app.config["REMEMBER_COOKIE_SAMESITE"] == "Lax"
    assert app.config["SESSION_COOKIE_SECURE"] is False


def test_password_hash_is_not_rendered(client, user_factory, login):
    user = user_factory()
    login(user)

    response = client.get("/settings")

    assert user.password_hash.encode() not in response.data
