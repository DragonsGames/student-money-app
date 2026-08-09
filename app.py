import os

from dotenv import load_dotenv
from flask import Flask
from sqlalchemy import URL

from extensions import db, login_manager, migrate


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

    # Import blueprints here to avoid circular imports
    from routes.application import application_bp
    from routes.auth import auth_bp
    from routes.categories import categories_bp
    from routes.dashboard import dashboard_bp
    from routes.onboarding import onboarding_bp
    from routes.public import public_bp
    from routes.transactions import transactions_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(application_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(categories_bp)

    return app


@login_manager.user_loader
def load_user(user_id):
    from models import User

    return db.session.get(User, int(user_id))


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
