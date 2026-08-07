from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import requer_admin
from .forms import EditarUsuarioForm, NovoUsuarioForm, PerfilForm
from .models import User


class LoginCognizeView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_form(self, form_class=None):
        from .forms import LoginForm

        return LoginForm(self.request, data=self.request.POST or None)


class LogoutCognizeView(LogoutView):
    pass


@login_required
def perfil(request):
    if request.method == "POST" and "salvar_perfil" in request.POST:
        form = PerfilForm(request.POST, instance=request.user)
        senha_form = PasswordChangeForm(request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado.")
            return redirect("accounts:perfil")
    elif request.method == "POST" and "trocar_senha" in request.POST:
        form = PerfilForm(instance=request.user)
        senha_form = PasswordChangeForm(request.user, request.POST)
        if senha_form.is_valid():
            user = senha_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Senha alterada com sucesso.")
            return redirect("accounts:perfil")
    else:
        form = PerfilForm(instance=request.user)
        senha_form = PasswordChangeForm(request.user)
    return render(
        request,
        "accounts/perfil.html",
        {"form": form, "senha_form": senha_form},
    )


# ---------------------------------------------------------------------------
# Gestão de usuários (somente Administrador)
# ---------------------------------------------------------------------------
@requer_admin
def lista_usuarios(request):
    usuarios = User.objects.all()
    return render(request, "accounts/lista_usuarios.html", {"usuarios": usuarios})


@requer_admin
def novo_usuario(request):
    if request.method == "POST":
        form = NovoUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuário criado com sucesso.")
            return redirect("accounts:lista_usuarios")
    else:
        form = NovoUsuarioForm()
    return render(
        request,
        "accounts/form_usuario.html",
        {"form": form, "titulo": "Novo usuário"},
    )


@requer_admin
def editar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = EditarUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuário atualizado.")
            return redirect("accounts:lista_usuarios")
    else:
        form = EditarUsuarioForm(instance=usuario)
    return render(
        request,
        "accounts/form_usuario.html",
        {"form": form, "titulo": f"Editar {usuario.username}"},
    )
