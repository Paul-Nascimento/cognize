from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("core.urls")),
    path("conta/", include("accounts.urls")),
    path("empresas/", include("empresas.urls")),
    path("tarefas/", include("tarefas.urls")),
]
