from decimal import Decimal


def test_dashboard_zero_state_and_safe_to_spend(
    client,
    user_factory,
    login,
):
    user = user_factory(starting_balance=Decimal("0.000"))
    login(user)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"0.000" in response.data
    assert b"Add your first transaction" in response.data


def test_dashboard_progress_is_semantic_and_true_percentage_remains_visible(
    client,
    user_factory,
    category_factory,
    transaction_factory,
    budget_factory,
    savings_factory,
    login,
):
    user = user_factory(starting_balance=Decimal("1000.000"))
    category = category_factory(user)
    budget_factory(user, category, Decimal("100.000"))
    transaction_factory(user, category, amount=Decimal("125.000"))
    savings_factory(
        user,
        target=Decimal("100.000"),
        saved=Decimal("130.000"),
    )
    login(user)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert response.data.count(b"<progress") >= 2
    assert b'value="100.00"' in response.data
    assert b"125.0%" in response.data
    assert b"130.0%" in response.data
    assert b"style=\"width:" not in response.data


def test_dashboard_renders_maximum_supported_values(
    client,
    user_factory,
    login,
):
    user = user_factory(starting_balance=Decimal("999999999.999"))
    login(user)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"999,999,999.999" in response.data
