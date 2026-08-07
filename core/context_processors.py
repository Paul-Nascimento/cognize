def navegacao(request):
    """Disponibiliza informações de navegação/permissões para os templates."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    return {
        "nav_pode_editar": user.pode_editar,
        "nav_pode_excluir": user.pode_excluir,
        "nav_pode_importar": user.pode_importar,
        "nav_pode_gerenciar_usuarios": user.pode_gerenciar_usuarios,
    }
