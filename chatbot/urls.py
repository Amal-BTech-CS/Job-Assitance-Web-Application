from django.urls import path
from . import views

urlpatterns = [

    path(
        "chatbot/",
        views.chatbot_page,
        name="chatbot"
    ),

    path(
        "chatbot/ask/",
        views.chat_api,
        name="chat_api"
    ),
]
