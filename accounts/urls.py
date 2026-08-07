from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginCognizeView.as_view(), name="login"),
    path("logout/", views.LogoutCognizeView.as_view(), name="logout"),
    path("perfil/", views.perfil, name="perfil"),
    path("usuarios/", views.lista_usuarios, name="lista_usuarios"),
    path("usuarios/novo/", views.novo_usuario, name="novo_usuario"),
    path("usuarios/<int:pk>/editar/", views.editar_usuario, name="editar_usuario"),
]
