from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    UserChangeForm,
)

from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuário",
        widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "seu.usuario"}),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
    )


class NovoUsuarioForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "cargo",
            "departamento",
            "telefone",
        )


class EditarUsuarioForm(UserChangeForm):
    password = None  # não editar senha por este formulário

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "cargo",
            "departamento",
            "telefone",
            "is_active",
        )


class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "telefone")
