import os

from dotenv import load_dotenv
from flask import Flask, before_render_template, g, render_template, session
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


def create_app(test_config=None):
    app = Flask(__name__)

    database_settings = {
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_NAME": os.getenv("DB_NAME"),
    }
    if test_config is None:
        missing_settings = [
            name
            for name, value in database_settings.items()
            if not value
        ]
        if missing_settings:
            missing_names = ", ".join(missing_settings)
            raise RuntimeError(
                f"Missing required database configuration: {missing_names}."
            )

    cookie_secure = os.getenv("COOKIE_SECURE", "false").lower() in {
        "1",
        "true",
        "yes",
    }

    database_url = URL.create(
        drivername="mysql+pymysql",
        username=database_settings["DB_USER"],
        password=database_settings["DB_PASSWORD"],
        host=database_settings["DB_HOST"],
        database=database_settings["DB_NAME"],
    )

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=cookie_secure,
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_SECURE=cookie_secure,
    )

    if test_config is not None:
        app.config.update(test_config)

    if not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY must be configured.")

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

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )

        if current_user.is_authenticated and response.mimetype == "text/html":
            response.headers["Cache-Control"] = "no-store, private"

        return response

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template(
            "error.html",
            status_code=404,
            heading="Page not found",
            message="The page you requested could not be found.",
        ), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return render_template(
            "error.html",
            status_code=405,
            heading="Method not allowed",
            message="That action is not available for this request.",
        ), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template(
            "error.html",
            status_code=500,
            heading="Something went wrong",
            message="Please try again in a moment.",
        ), 500

    return app


@login_manager.user_loader
def load_user(user_id):
    from models import User

    return db.session.get(User, int(user_id))


app = create_app()


if __name__ == "__main__":
    app.run()
