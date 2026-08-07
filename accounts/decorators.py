"""Decorators e mixins para controle de acesso baseado em cargo."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def nivel_minimo(nivel):
    """Exige que o usuário tenha pelo menos o nível informado (1..4)."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.nivel < nivel:
                messages.error(
                    request,
                    "Seu cargo não tem permissão para essa ação.",
                )
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


# Atalhos semânticos
requer_edicao = nivel_minimo(2)
requer_gestor = nivel_minimo(3)
requer_admin = nivel_minimo(4)


class NivelMinimoMixin:
    """Mixin para CBVs que exige um nível mínimo de cargo."""

    nivel_requerido = 1

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if request.user.nivel < self.nivel_requerido:
            messages.error(request, "Seu cargo não tem permissão para essa ação.")
            return redirect("core:dashboard")
        return super().dispatch(request, *args, **kwargs)
