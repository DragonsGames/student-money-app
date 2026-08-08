from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required
from forms import LogoutForm
dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():

    if not current_user.onboarding_completed:
        return redirect(url_for("onboarding.onboarding"))

    logout_form = LogoutForm()

    return render_template(
        "dashboard.html",
        user=current_user,
        logout_form=logout_form
    )