import os

from dotenv import load_dotenv
from flask import Flask, before_render_template, g, session
from flask_login import current_user
from sqlalchemy import URL

from extensions import db, login_manager, migrate
from forms import LanguagePreferenceForm
from localization import (
    category_name,
    format_date,
    localize_form,
    translate,
    translate_text,
)


load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    database_url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    # Connect extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    @app.before_request
    def load_interface_preferences():
        settings = (
            current_user.settings
            if current_user.is_authenticated
            else None
        )
        g.language = (
            settings.language
            if settings and settings.language in {"en", "fr", "ar"}
            else session.get("language", "en")
        )
        if g.language not in {"en", "fr", "ar"}:
            g.language = "en"

        g.direction = "rtl" if g.language == "ar" else "ltr"
        g.appearance = (
            settings.appearance
            if settings and settings.appearance in {"light", "dark", "system"}
            else "system"
        )

    @app.context_processor
    def inject_interface_preferences():
        return {
            "appearance": g.get("appearance", "system"),
            "category_name": category_name,
            "direction": g.get("direction", "ltr"),
            "language": g.get("language", "en"),
            "language_form": LanguagePreferenceForm(),
            "format_date": format_date,
            "t": translate,
            "t_text": translate_text,
        }

    @before_render_template.connect_via(app)
    def localize_template_forms(sender, template, context, **extra):
        for value in context.values():
            if hasattr(value, "validate") and hasattr(value, "_fields"):
                localize_form(value)

    # Import blueprints here to avoid circular imports
    from routes.auth import auth_bp
    from routes.budgets import budgets_bp
    from routes.categories import categories_bp
    from routes.dashboard import dashboard_bp
    from routes.history import history_bp
    from routes.onboarding import onboarding_bp
    from routes.public import public_bp
    from routes.savings import savings_bp
    from routes.settings import settings_bp
    from routes.transactions import transactions_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(savings_bp)
    app.register_blueprint(settings_bp)

    return app


@login_manager.user_loader
def load_user(user_id):
    from models import User

    return db.session.get(User, int(user_id))


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
