from extensions import db
from localization import category_name
from models import Category


def category_data(**overrides):
    data = {
        "name": "Café",
        "category_type": "expense",
        "icon": "🎓",
        "color": "#A1b2C3",
    }
    data.update(overrides)
    return data


def test_create_category_and_distinguish_income_from_expense(
    client,
    user_factory,
    login,
):
    user = user_factory()
    login(user)

    assert client.post(
        "/categories/add",
        data=category_data(),
    ).status_code == 302
    assert client.post(
        "/categories/add",
        data=category_data(category_type="income"),
    ).status_code == 302

    categories = db.session.execute(
        db.select(Category).order_by(Category.category_type)
    ).scalars().all()
    assert len(categories) == 2
    assert {category.category_type for category in categories} == {
        "expense",
        "income",
    }


def test_duplicate_same_name_and_type_is_rejected(
    client,
    user_factory,
    category_factory,
    login,
):
    user = user_factory()
    category_factory(user, name="Food")
    login(user)

    response = client.post(
        "/categories/add",
        data=category_data(name="Food"),
    )

    assert response.status_code == 200
    assert db.session.scalar(db.select(db.func.count(Category.id))) == 1


def test_edit_category_fields_and_clear_starter_status(
    client,
    user_factory,
    category_factory,
    login,
):
    user = user_factory()
    category = category_factory(user, is_default=True)
    login(user)

    response = client.post(
        f"/categories/{category.id}/edit",
        data=category_data(name="Transport", icon="🚌", color="#123456"),
    )

    assert response.status_code == 302
    db.session.refresh(category)
    assert category.name == "Transport"
    assert category.icon == "🚌"
    assert category.color == "#123456"
    assert category.is_default is False
    assert category_name(category) == "Transport"


def test_invalid_color_is_rejected(client, user_factory, login):
    user = user_factory()
    login(user)

    for color in ("red", "#12345", "#123456; color:red", "<script>"):
        response = client.post(
            "/categories/add",
            data=category_data(name=f"Color {color}", color=color),
        )
        assert response.status_code == 200

    assert db.session.scalar(db.select(db.func.count(Category.id))) == 0


def test_used_category_cannot_be_deleted(
    client,
    user_factory,
    category_factory,
    transaction_factory,
    login,
):
    user = user_factory()
    category = category_factory(user)
    transaction_factory(user, category)
    login(user)

    response = client.post(f"/categories/{category.id}/delete")

    assert response.status_code == 302
    assert db.session.get(Category, category.id) is not None


def test_budgeted_category_cannot_be_deleted_or_changed_to_income(
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

    assert client.post(f"/categories/{category.id}/delete").status_code == 302
    response = client.post(
        f"/categories/{category.id}/edit",
        data=category_data(name="Food", category_type="income"),
    )

    assert response.status_code == 200
    db.session.refresh(category)
    assert category.category_type == "expense"


def test_foreign_category_mutations_are_blocked(
    client,
    user_factory,
    category_factory,
    login,
):
    owner = user_factory()
    attacker = user_factory()
    category = category_factory(owner)
    login(attacker)

    assert client.get(f"/categories/{category.id}/edit").status_code == 404
    assert client.post(f"/categories/{category.id}/delete").status_code == 404
    assert db.session.get(Category, category.id) is not None


def test_category_delete_is_post_only(
    client,
    user_factory,
    category_factory,
    login,
):
    user = user_factory()
    category = category_factory(user)
    login(user)

    assert client.get(f"/categories/{category.id}/delete").status_code == 405
