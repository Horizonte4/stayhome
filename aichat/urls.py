from django.urls import path

from . import views

app_name = "aichat"

urlpatterns = [
    path("message/", views.send_message, name="send_message"),
    path("history/", views.history, name="history"),
]
