from flask import g

from localization import category_name, translate_text


def test_translation_helper_languages_fallback_and_formatting(app):
    with app.test_request_context("/"):
        g.language = "fr"
        assert translate_text("Dashboard") == "Accueil"
        assert translate_text("Step {step} of 5", step=3) == "Étape 3 sur 5"

        g.language = "ar"
        assert translate_text("Dashboard") == "الرئيسية"

        g.language = "xx"
        assert translate_text("Dashboard") == "Dashboard"
        assert translate_text("Missing source text") == "Missing source text"


def test_stable_internal_values_are_not_presentation_translated(app):
    with app.test_request_context("/"):
        g.language = "fr"
        for value in (
            "income",
            "expense",
            "weekly",
            "monthly",
            "system",
            "light",
            "dark",
        ):
            assert translate_text(value) == value


def test_category_translation_only_applies_to_unchanged_starters(
    app,
    user_factory,
    category_factory,
):
    user = user_factory()
    starter = category_factory(user, name="Food", is_default=True)
    custom = category_factory(
        user,
        name="Food plan",
        is_default=True,
    )
    user_named = category_factory(
        user,
        name="Transport",
        is_default=False,
    )

    with app.test_request_context("/"):
        g.language = "fr"
        assert category_name(starter) == "Alimentation"
        assert category_name(custom) == "Food plan"
        assert category_name(user_named) == "Transport"


def test_arabic_render_sets_direction_and_financial_isolation(
    client,
    user_factory,
    login,
):
    user = user_factory(language="ar")
    login(user)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b'lang="ar"' in response.data
    assert b'dir="rtl"' in response.data
    assert b"money-value" in response.data
    assert "لوحة المعلومات".encode() in response.data


def test_french_known_copy_does_not_fall_back_to_english(
    client,
    user_factory,
    login,
):
    user = user_factory(language="fr")
    login(user)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Accueil".encode() in response.data
    assert b"Here's your money overview." not in response.data
