from django.urls import path

from .views import (
    conversation_detail,
    inbox,
    send_message,
    start_conversation,
)

app_name = "comunication"

urlpatterns = [
    path("", inbox, name="inbox"),
    path("start/<int:property_id>/", start_conversation, name="start_conversation"),
    path("<int:conversation_id>/", conversation_detail, name="conversation_detail"),
    path("<int:conversation_id>/send/", send_message, name="send_message"),
]