from django.contrib.auth.models import AbstractUser
from django.db import models


class Cargo(models.TextChoices):
    """Cargos do sistema, em ordem crescente de privilégio."""

    VISUALIZADOR = "VISUALIZADOR", "Visualizador"
    COLABORADOR = "COLABORADOR", "Colaborador"
    GESTOR = "GESTOR", "Gestor"
    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"


# Nível numérico de cada cargo. Quanto maior, mais permissões.
NIVEL_CARGO = {
    Cargo.VISUALIZADOR: 1,
    Cargo.COLABORADOR: 2,
    Cargo.GESTOR: 3,
    Cargo.ADMINISTRADOR: 4,
}


class User(AbstractUser):
    """Usuário do sistema com cargo e departamento."""

    cargo = models.CharField(
        "Cargo",
        max_length=20,
        choices=Cargo.choices,
        default=Cargo.VISUALIZADOR,
    )
    departamento = models.CharField(
        "Departamento", max_length=60, blank=True,
        help_text="Ex.: Contabilidade, Fiscal, Departamento Pessoal.",
    )
    telefone = models.CharField("Telefone", max_length=20, blank=True)

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["first_name", "username"]

    def __str__(self):
        nome = self.get_full_name() or self.username
        return f"{nome} ({self.get_cargo_display()})"

    # ------------------------------------------------------------------
    # Regras de permissão baseadas em cargo
    # ------------------------------------------------------------------
    @property
    def nivel(self) -> int:
        if self.is_superuser:
            return 99
        return NIVEL_CARGO.get(self.cargo, 0)

    def tem_cargo(self, *cargos) -> bool:
        return self.is_superuser or self.cargo in cargos

    @property
    def pode_visualizar(self) -> bool:
        return self.nivel >= 1

    @property
    def pode_editar(self) -> bool:
        """Criar e editar empresas, tarefas e atualizar execuções."""
        return self.nivel >= 2

    @property
    def pode_excluir(self) -> bool:
        return self.nivel >= 3

    @property
    def pode_importar(self) -> bool:
        """Importações em lote e vínculos em massa (gestor+)."""
        return self.nivel >= 3

    @property
    def pode_gerenciar_usuarios(self) -> bool:
        return self.nivel >= 4
