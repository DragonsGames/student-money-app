from functools import wraps

from flask import redirect, url_for
from flask_login import current_user


# AI assistance: OpenAI Codex assisted with structuring this reusable
# onboarding guard; reviewed and adapted by the project author.
def onboarding_complete_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if not current_user.onboarding_completed:
            return redirect(url_for("onboarding.onboarding"))

        return view_function(*args, **kwargs)

    return wrapped_view
