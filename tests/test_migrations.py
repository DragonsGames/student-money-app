from sqlalchemy import inspect, text

from app import create_app
from extensions import db
from flask_migrate import downgrade, upgrade


def test_migration_chain_and_preference_defaults(tmp_path):
    database_path = tmp_path / "migration.sqlite"
    migration_app = create_app({
        "TESTING": True,
        "SECRET_KEY": "migration-test-key",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path.as_posix()}",
        "WTF_CSRF_ENABLED": False,
    })

    with migration_app.app_context():
        upgrade(directory="migrations", revision="d9a6e3f71b42")
        db.session.execute(text(
            "INSERT INTO users "
            "(email, password_hash, created_at, onboarding_completed) "
            "VALUES "
            "('migration@example.com', 'hash', CURRENT_TIMESTAMP, 1)"
        ))
        user_id = db.session.execute(text(
            "SELECT id FROM users WHERE email = 'migration@example.com'"
        )).scalar_one()
        db.session.execute(text(
            "INSERT INTO user_settings "
            "(user_id, currency, starting_balance, budget_period) "
            "VALUES (:user_id, 'TND', 0.000, 'monthly')"
        ), {"user_id": user_id})
        db.session.commit()

        upgrade(directory="migrations")
        columns = {
            column["name"]
            for column in inspect(db.engine).get_columns("user_settings")
        }
        preferences = db.session.execute(text(
            "SELECT appearance, language FROM user_settings "
            "WHERE user_id = :user_id"
        ), {"user_id": user_id}).one()

        assert {"appearance", "language"}.issubset(columns)
        assert preferences == ("system", "en")

        downgrade(directory="migrations", revision="d9a6e3f71b42")
        downgraded_columns = {
            column["name"]
            for column in inspect(db.engine).get_columns("user_settings")
        }
        assert "appearance" not in downgraded_columns
        assert "language" not in downgraded_columns

        upgrade(directory="migrations")
        assert db.session.execute(text(
            "SELECT version_num FROM alembic_version"
        )).scalar_one() == "e4b7a1c9d203"

        db.session.remove()
        db.engine.dispose()
