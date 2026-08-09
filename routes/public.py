from urllib.parse import unquote, urlsplit

from flask import Blueprint, redirect, render_template, request, session, url_for
from flask_login import current_user

from extensions import db
from forms import LanguagePreferenceForm


public_bp = Blueprint("public", __name__)


def _is_safe_local_redirect(target):
    decoded_target = unquote(target)

    if (
        not decoded_target.startswith("/")
        or decoded_target.startswith("//")
        or "\\" in decoded_target
        or any(ord(character) < 32 or ord(character) == 127
               for character in decoded_target)
    ):
        return False

    parsed_target = urlsplit(decoded_target)
    return not parsed_target.scheme and not parsed_target.netloc


@public_bp.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.onboarding_completed:
            return redirect(url_for("dashboard.dashboard"))
        return redirect(url_for("onboarding.onboarding"))

    return render_template("index.html")


@public_bp.route("/preferences/language", methods=["POST"])
def set_language():
    form = LanguagePreferenceForm()

    if form.validate_on_submit():
        session["language"] = form.language.data

        if current_user.is_authenticated and current_user.settings:
            current_user.settings.language = form.language.data
            db.session.commit()

    next_url = request.form.get("next", "")
    if _is_safe_local_redirect(next_url):
        return redirect(next_url)

    if current_user.is_authenticated:
        if current_user.onboarding_completed:
            return redirect(url_for("dashboard.dashboard"))
        return redirect(url_for("onboarding.onboarding"))

    return redirect(url_for("public.index"))
