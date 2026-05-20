from django.urls import path

from .views import register_view, login_view, board, edit_profile, logout_view

urlpatterns = [
    path("registration/", register_view, name="registration"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("board/", board, name="board"),
    path("edit_profile/", edit_profile, name="edit_profile"),
]
