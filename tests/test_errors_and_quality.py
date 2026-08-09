from pathlib import Path

import pytest

from app import create_app


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_all_templates_parse(app):
    for template_name in app.jinja_env.list_templates():
        app.jinja_env.get_template(template_name)


def test_branded_error_pages_hide_internal_details(app, client):
    @app.route("/_test/internal-error")
    def internal_error():
        raise RuntimeError("sensitive internal detail")

    app.config["PROPAGATE_EXCEPTIONS"] = False

    not_found = client.get("/missing-page")
    assert not_found.status_code == 404
    assert b"ILI pika" in not_found.data
    assert b"Traceback" not in not_found.data

    method = client.post("/")
    assert method.status_code == 405
    assert b"Method not allowed" in method.data

    failed = client.get("/_test/internal-error")
    assert failed.status_code == 500
    assert b"Something went wrong" in failed.data
    assert b"sensitive internal detail" not in failed.data
    assert b"Traceback" not in failed.data


def test_javascript_avoids_unsafe_dynamic_execution():
    javascript = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (PROJECT_ROOT / "static").glob("*.js")
    )

    assert "innerHTML" not in javascript
    assert "insertAdjacentHTML" not in javascript
    assert "eval(" not in javascript
    assert "new Function" not in javascript


def test_only_validated_color_features_keep_jinja_inline_styles():
    matches = []
    for template in (PROJECT_ROOT / "templates").glob("*.html"):
        for line_number, line in enumerate(
            template.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if "style=" in line and "{{" in line:
                matches.append((template.name, line_number))

    assert sorted(matches) == [
        ("_category_card.html", 3),
        ("_color_picker.html", 15),
    ]


def test_external_resources_use_https_without_bootstrap_javascript():
    templates = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (PROJECT_ROOT / "templates").glob("*.html")
    )

    assert 'href="http://' not in templates
    assert 'src="http://' not in templates
    assert "bootstrap.min.js" not in templates


def test_example_environment_contains_placeholders_only():
    example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "replace-with-a-long-random-secret" in example
    assert "your-database-password" in example


def test_production_factory_reports_missing_database_settings(monkeypatch):
    for setting in ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME"):
        monkeypatch.delenv(setting, raising=False)

    with pytest.raises(
        RuntimeError,
        match="Missing required database configuration",
    ):
        create_app()


def test_factory_reports_missing_secret_key(monkeypatch):
    monkeypatch.setenv("DB_USER", "test-user")
    monkeypatch.setenv("DB_PASSWORD", "test-password")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_NAME", "test-database")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SECRET_KEY must be configured"):
        create_app()
