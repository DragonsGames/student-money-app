from flask import Blueprint, abort, render_template
from flask_login import login_required

from forms import LogoutForm
from routes.guards import onboarding_complete_required


application_bp = Blueprint("application", __name__)


# AI assistance: OpenAI Codex helped organize these authenticated placeholder
# destinations; reviewed and adapted by the project author.
PLACEHOLDER_PAGES = {
    "settings": {
        "title": "Profile & settings",
        "subtitle": "Manage your personal app preferences.",
        "empty_title": "Settings controls are coming later",
        "description": (
            "Your onboarding preferences are saved. Editing them here will "
            "be added in a later phase."
        ),
        "symbol": "⚙",
    },
}


@application_bp.route("/<page_key>")
@login_required
@onboarding_complete_required
def placeholder(page_key):
    page = PLACEHOLDER_PAGES.get(page_key)

    if page is None:
        abort(404)

    return render_template(
        "app_placeholder.html",
        page=page,
        page_key=page_key,
        logout_form=LogoutForm(),
    )
