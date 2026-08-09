from werkzeug.security import check_password_hash

from extensions import db
from models import User


def test_registration_hashes_password_and_logs_user_in(client):
    response = client.post("/register", data={
        "email": "new@example.com",
        "password": "correct-password",
        "confirmation": "correct-password",
    })

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/onboarding")
    user = db.session.execute(
        db.select(User).where(User.email == "new@example.com")
    ).scalar_one()
    assert user.password_hash != "correct-password"
    assert check_password_hash(user.password_hash, "correct-password")
    with client.session_transaction() as session:
        assert session["_user_id"] == str(user.id)


def test_duplicate_email_is_rejected(client, user_factory):
    user_factory(email="same@example.com")

    response = client.post("/register", data={
        "email": "same@example.com",
        "password": "password123",
        "confirmation": "password123",
    })

    assert response.status_code == 200
    assert db.session.scalar(db.select(db.func.count(User.id))) == 1
    assert b"already exists" in response.data


def test_invalid_registration_data_is_rejected(client):
    response = client.post("/register", data={
        "email": "not-an-email",
        "password": "short",
        "confirmation": "different",
    })

    assert response.status_code == 200
    assert db.session.scalar(db.select(db.func.count(User.id))) == 0


def test_registration_email_respects_model_limit(client):
    response = client.post("/register", data={
        "email": f"{'a' * 250}@example.com",
        "password": "password123",
        "confirmation": "password123",
    })

    assert response.status_code == 200
    assert db.session.scalar(db.select(db.func.count(User.id))) == 0


def test_login_success_routes_completed_user_to_dashboard(
    client,
    user_factory,
):
    user = user_factory(completed=True)

    response = client.post("/login", data={
        "email": user.email,
        "password": "password123",
    })

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_login_success_routes_incomplete_user_to_onboarding(
    client,
    user_factory,
):
    user = user_factory(completed=False)

    response = client.post("/login", data={
        "email": user.email,
        "password": "password123",
    })

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/onboarding")


def test_login_rejects_wrong_password(client, user_factory):
    user = user_factory()

    response = client.post("/login", data={
        "email": user.email,
        "password": "wrong-password",
    })

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data
    with client.session_transaction() as session:
        assert "_user_id" not in session


def test_login_unknown_email_uses_same_error(client):
    response = client.post("/login", data={
        "email": "missing@example.com",
        "password": "wrong-password",
    })

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_remember_login_sets_cookie(client, user_factory, login):
    user = user_factory()

    response = login(user, remember=True)

    cookies = response.headers.getlist("Set-Cookie")
    assert any("remember_token=" in cookie for cookie in cookies)


def test_logout_is_post_only_and_clears_login(client, user_factory, login):
    user = user_factory()
    login(user)

    assert client.get("/logout").status_code == 405
    response = client.post("/logout")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    with client.session_transaction() as session:
        assert "_user_id" not in session


def test_anonymous_protected_route_redirects_to_login(client):
    response = client.get("/dashboard")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_authenticated_entry_routes(client, user_factory, login):
    completed = user_factory(completed=True)
    login(completed)

    for path in ("/", "/login", "/register"):
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/dashboard")
