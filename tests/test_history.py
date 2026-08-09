from datetime import date
from decimal import Decimal


def setup_history(
    user_factory,
    category_factory,
    transaction_factory,
):
    user = user_factory()
    income = category_factory(user, name="Work", category_type="income")
    food = category_factory(user, name="Food")
    transport = category_factory(user, name="Transport")
    transaction_factory(
        user,
        income,
        amount=Decimal("100.000"),
        transaction_date=date(2026, 8, 1),
        description="Income row",
    )
    transaction_factory(
        user,
        food,
        amount=Decimal("30.000"),
        transaction_date=date(2026, 8, 2),
        description="Food row",
    )
    transaction_factory(
        user,
        transport,
        amount=Decimal("50.000"),
        transaction_date=date(2026, 8, 3),
        description="Transport row",
    )
    return user, income, food, transport


def test_history_type_category_and_date_filters(
    client,
    user_factory,
    category_factory,
    transaction_factory,
    login,
):
    user, _, food, _ = setup_history(
        user_factory,
        category_factory,
        transaction_factory,
    )
    login(user)

    expense = client.get("/history?transaction_type=expense&sort=newest")
    assert b"Food row" in expense.data
    assert b"Transport row" in expense.data
    assert b"Income row" not in expense.data

    category = client.get(
        f"/history?transaction_type=all&category_id={food.id}&sort=newest"
    )
    assert b"Food row" in category.data
    assert b"Transport row" not in category.data

    inclusive = client.get(
        "/history?transaction_type=all&start_date=2026-08-02"
        "&end_date=2026-08-03&sort=newest"
    )
    assert b"Food row" in inclusive.data
    assert b"Transport row" in inclusive.data
    assert b"Income row" not in inclusive.data


def test_history_sort_orders_and_combined_filters(
    client,
    user_factory,
    category_factory,
    transaction_factory,
    login,
):
    user, _, _, _ = setup_history(
        user_factory,
        category_factory,
        transaction_factory,
    )
    login(user)

    newest = client.get("/history?transaction_type=all&sort=newest").data
    oldest = client.get("/history?transaction_type=all&sort=oldest").data
    high = client.get("/history?transaction_type=all&sort=amount_high").data
    low = client.get("/history?transaction_type=all&sort=amount_low").data

    assert newest.index(b"Transport row") < newest.index(b"Income row")
    assert oldest.index(b"Income row") < oldest.index(b"Transport row")
    assert high.index(b"Income row") < high.index(b"Food row")
    assert low.index(b"Food row") < low.index(b"Income row")

    combined = client.get(
        "/history?transaction_type=expense&start_date=2026-08-03"
        "&end_date=2026-08-03&sort=amount_low"
    )
    assert b"Transport row" in combined.data
    assert b"Food row" not in combined.data


def test_invalid_date_range_does_not_apply_partial_filters(
    client,
    user_factory,
    category_factory,
    transaction_factory,
    login,
):
    user, _, _, _ = setup_history(
        user_factory,
        category_factory,
        transaction_factory,
    )
    login(user)

    response = client.get(
        "/history?transaction_type=expense&start_date=2026-08-03"
        "&end_date=2026-08-01&sort=newest"
    )

    assert response.status_code == 200
    assert b"Income row" in response.data
    assert b"start date" in response.data


def test_history_isolates_users_and_rejects_foreign_category_filter(
    client,
    user_factory,
    category_factory,
    transaction_factory,
    login,
):
    user, _, _, _ = setup_history(
        user_factory,
        category_factory,
        transaction_factory,
    )
    other = user_factory()
    foreign_category = category_factory(other, name="Foreign")
    transaction_factory(
        other,
        foreign_category,
        description="Foreign row",
    )
    login(user)

    response = client.get(
        f"/history?transaction_type=all&category_id={foreign_category.id}"
        "&sort=newest"
    )

    assert response.status_code == 200
    assert b"Foreign row" not in response.data


def test_history_empty_and_no_match_states(
    client,
    user_factory,
    category_factory,
    transaction_factory,
    login,
):
    user = user_factory()
    login(user)

    empty = client.get("/history")
    assert b"No transaction history yet" in empty.data

    category = category_factory(user, name="Food")
    transaction_factory(
        user,
        category,
        transaction_date=date(2026, 8, 3),
    )

    no_match = client.get(
        "/history?transaction_type=income&start_date=2026-01-01"
        "&end_date=2026-01-02&sort=newest"
    )
    assert b"No transactions match these filters" in no_match.data


def test_history_is_get_only(client, user_factory, login):
    user = user_factory()
    login(user)

    assert client.post("/history").status_code == 405
