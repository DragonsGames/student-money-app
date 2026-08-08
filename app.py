import os

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from sqlalchemy import URL
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, migrate, login_manager
from forms import (
    LoginForm,
    OnboardingGoalsForm,
    OnboardingIncomeForm,
    OnboardingProfileForm,
    RegistrationForm
)

from models import (
    Category,
    IncomeSource,
    User,
    UserGoal,
    UserSettings
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)
from forms import (
    LoginForm,
    OnboardingBalanceForm,
    OnboardingCategoriesForm,
    OnboardingGoalsForm,
    OnboardingIncomeForm,
    OnboardingProfileForm,
    RegistrationForm
)


load_dotenv()

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

db.init_app(app)
migrate.init_app(app, db)

login_manager.init_app(app)
login_manager.login_view = "login"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = RegistrationForm()

    if form.validate_on_submit():

        existing_user = db.session.execute(
            db.select(User).where(User.email == form.email.data)
        ).scalar_one_or_none()

        if existing_user:
            flash("An account with that email already exists.")
            return render_template("register.html", form=form)

        user = User(
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )

        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Account created successfully!")
        return redirect(url_for("onboarding"))

    return render_template("register.html", form=form)

@app.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    if current_user.onboarding_completed:
        return redirect(url_for("dashboard"))

    form = OnboardingProfileForm()

    if form.validate_on_submit():

        settings = current_user.settings

        if settings is None:
            settings = UserSettings(
                user_id=current_user.id
            )
            db.session.add(settings)

        settings.display_name = form.display_name.data
        settings.currency = form.currency.data

        db.session.commit()

        return redirect(url_for("onboarding_goals"))

    return render_template(
        "onboarding_profile.html",
        form=form
    )
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if form.validate_on_submit():

        user = db.session.execute(
            db.select(User).where(User.email == form.email.data)
        ).scalar_one_or_none()

        if user is None:
            flash("Invalid email or password.")
            return render_template("login.html", form=form)

        if not check_password_hash(
            user.password_hash,
            form.password.data
        ):
            flash("Invalid email or password.")
            return render_template("login.html", form=form)

        login_user(user, remember=form.remember.data)

        return redirect(url_for("dashboard"))

    return render_template("login.html", form=form)


@app.route("/dashboard")
@login_required
def dashboard():
    return f"Welcome {current_user.email}! You are logged in."
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/onboarding/goals", methods=["GET", "POST"])
@login_required
def onboarding_goals():
    if current_user.onboarding_completed:
        return redirect(url_for("dashboard"))

    form = OnboardingGoalsForm()

    if form.validate_on_submit():

        current_user.goals.clear()

        for goal in form.goals.data:
            user_goal = UserGoal(
                goal_type=goal
            )

            current_user.goals.append(user_goal)

        db.session.commit()

        return redirect(url_for("onboarding_income"))

    return render_template(
        "onboarding_goals.html",
        form=form
    )
@app.route("/onboarding/income", methods=["GET", "POST"])
@login_required
def onboarding_income():
    if current_user.onboarding_completed:
        return redirect(url_for("dashboard"))

    form = OnboardingIncomeForm()

    if form.validate_on_submit():

        current_user.income_sources.clear()

        for source_data in form.sources.data:

            source = IncomeSource(
                name=source_data["name"],
                amount=source_data["amount"],
                frequency=source_data["frequency"],
                next_payment_date=source_data["next_payment_date"],
                is_recurring=source_data["frequency"] in [
                    "weekly",
                    "monthly"
                ]
            )

            current_user.income_sources.append(source)

        db.session.commit()

        return redirect(url_for("onboarding_balance"))

    return render_template(
        "onboarding_income.html",
        form=form
    )
@app.route("/onboarding/balance", methods=["GET", "POST"])
@login_required
def onboarding_balance():
    if current_user.onboarding_completed:
        return redirect(url_for("dashboard"))

    form = OnboardingBalanceForm()

    if form.validate_on_submit():

        settings = current_user.settings

        if settings is None:
            settings = UserSettings(
                user_id=current_user.id
            )
            db.session.add(settings)

        settings.starting_balance = form.starting_balance.data

        db.session.commit()

        return redirect(url_for("onboarding_categories"))

    return render_template(
        "onboarding_balance.html",
        form=form
    )
@app.route("/onboarding/categories", methods=["GET", "POST"])
@login_required
def onboarding_categories():
    if current_user.onboarding_completed:
        return redirect(url_for("dashboard"))

    default_categories = [
        {"name": "Food", "category_type": "expense", "icon": "🍔"},
        {"name": "Transport", "category_type": "expense", "icon": "🚌"},
        {"name": "School", "category_type": "expense", "icon": "🎓"},
        {"name": "Entertainment", "category_type": "expense", "icon": "🎮"},
        {"name": "Shopping", "category_type": "expense", "icon": "🛍️"},
        {"name": "Other", "category_type": "expense", "icon": "📦"},
        {"name": "Allowance", "category_type": "income", "icon": "💰"},
        {"name": "Work", "category_type": "income", "icon": "💼"},
    ]

    if request.method == "GET" and not current_user.categories:
        form = OnboardingCategoriesForm(
            categories=default_categories
        )
    else:
        form = OnboardingCategoriesForm()

    if form.validate_on_submit():
        current_user.categories.clear()

        for data in form.categories.data:
            category = Category(
                name=data["name"],
                category_type=data["category_type"],
                icon=data["icon"],
                is_default=data["name"] in {
                    "Food",
                    "Transport",
                    "School",
                    "Entertainment",
                    "Shopping",
                    "Other",
                    "Allowance",
                    "Work"
                }
            )

            current_user.categories.append(category)

        current_user.onboarding_completed = True

        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template(
        "onboarding_categories.html",
        form=form
    )

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

if __name__ == "__main__":
    app.run(debug=True)

