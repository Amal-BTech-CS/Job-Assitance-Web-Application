import json

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from accounts.ai.chatbot.chatbot import ask


@login_required
@never_cache
def chatbot_page(request):
    """
    Renders the AI Career Assistant chat UI.
    Only accessible to logged-in jobseekers.
    """
    if request.user.user_type != "jobseeker":
        return redirect("home")

    return render(request, "accounts/chatbot.html")


@login_required
@require_POST
def chat_api(request):
    """
    JSON endpoint called by the chatbot frontend.

    Expects:  POST { "message": "..." }
    Returns:  { "answer": "..." } or { "error": "..." }
    """
    try:
        body = json.loads(request.body)
        message = body.get("message", "").strip()

        if not message:
            return JsonResponse(
                {"error": "Please type a message."},
                status=400
            )

        answer = ask(request.user, message)

        return JsonResponse({"answer": answer})

    except Exception as e:
        return JsonResponse(
            {"error": f"Something went wrong: {str(e)}"},
            status=500
        )
