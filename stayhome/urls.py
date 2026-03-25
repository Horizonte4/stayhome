from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.i18n import i18n_patterns
from .views import home

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),  # ← maneja cambio de idioma
    path("admin/", admin.site.urls),
]

urlpatterns += i18n_patterns(
    path("", home, name="home"),
    path("users/", include("users.urls")),
    path("properties/", include("properties.urls")),
    path("transactions/", include("transactions.urls")),
    path("chat/", include("comunication.urls")),
    prefix_default_language=False, 
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)