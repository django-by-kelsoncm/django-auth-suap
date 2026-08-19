import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def home(request):
    suap_auth = getattr(settings, "SUAP_AUTH", {})
    context = {
        "suap_client_id": suap_auth.get("CLIENT_ID", ""),
        "suap_redirect_uri": suap_auth.get("REDIRECT_URI", ""),
    }
    return render(request, "home/home.html", context)


@login_required
def dashboard(request):
    raw_json_pretty = ""
    # Retrieve profile from suap_profile (django_suap_auth.profile) or profile
    profile = getattr(request.user, "suap_profile", getattr(request.user, "profile", None))
    if profile and hasattr(profile, "raw_data") and profile.raw_data:
        raw_json_pretty = json.dumps(profile.raw_data.data, indent=2, ensure_ascii=False)

    return render(
        request,
        "home/dashboard.html",
        {
            "user": request.user,
            "profile": profile,
            "raw_json_pretty": raw_json_pretty,
        },
    )
