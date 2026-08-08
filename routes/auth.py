from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from forms import LoginForm, LogoutForm, RegistrationForm
from extensions import db
from forms import LoginForm, RegistrationForm
from models import User
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))
    form = RegistrationForm()

    if form.validate_on_submit():

        existing_user = db.session.execute(
            db.select(User).where(User.email == form.email.data)
        ).scalar_one_or_none()

        if existing_user:
            flash(
    "An account with that email already exists.",
    "danger"
)
            return render_template("register.html", form=form)

        user = User(
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )

        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Account created successfully!", "success")
        return redirect(url_for("onboarding.onboarding"))

    return render_template("register.html", form=form)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))
    if form.validate_on_submit():

        user = db.session.execute(
            db.select(User).where(User.email == form.email.data)
        ).scalar_one_or_none()

        if user is None:
            flash("Invalid email or password.", "danger")
            return render_template("login.html", form=form)

        if not check_password_hash(
            user.password_hash,
            form.password.data
        ):
            flash("Invalid email or password.", "danger")
            return render_template("login.html", form=form)

        login_user(user, remember=form.remember.data)
        if user.onboarding_completed:
            return redirect(url_for("dashboard.dashboard"))
        return redirect(url_for("onboarding.onboarding"))

    return render_template("login.html", form=form)

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    form = LogoutForm()

    if form.validate_on_submit():
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for("public.index"))

    return redirect(url_for("dashboard.dashboard"))
