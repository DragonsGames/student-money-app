from flask import Blueprint, abort, render_template
from flask_login import login_required

from forms import LogoutForm
from routes.guards import onboarding_complete_required


application_bp = Blueprint("application", __name__)


# AI assistance: OpenAI Codex helped organize these authenticated placeholder
# destinations; reviewed and adapted by the project author.
PLACEHOLDER_PAGES = {
    "budgets": {
        "title": "Budgets",
        "subtitle": "Give your spending a simple plan.",
        "empty_title": "Budget tools are coming later",
        "description": (
            "Future budget features will live here. No budget amounts have "
            "been calculated or invented."
        ),
        "symbol": "▤",
    },
    "savings": {
        "title": "Savings",
        "subtitle": "Keep future goals visible and achievable.",
        "empty_title": "Savings tools are coming later",
        "description": (
            "This space will support savings plans in a future phase."
        ),
        "symbol": "◇",
    },
    "categories": {
        "title": "Categories",
        "subtitle": "Keep the way you organize money personal.",
        "empty_title": "Category management is coming later",
        "description": (
            "The categories created during onboarding are saved. Editing "
            "them from the app will be added in a later phase."
        ),
        "symbol": "◫",
    },
    "history": {
        "title": "History",
        "subtitle": "Look back at how your money changes over time.",
        "empty_title": "There is no history to show yet",
        "description": (
            "History will appear here after the app supports financial "
            "activity in a later phase."
        ),
        "symbol": "↶",
    },
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
