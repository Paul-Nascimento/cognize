from django.conf import settings
from django.db import models
from django.utils import timezone

from empresas.models import Empresa


class Departamento(models.TextChoices):
    CONTABILIDADE = "Contabilidade", "Contabilidade"
    DP = "Departamento Pessoal", "Departamento Pessoal"
    FISCAL = "Fiscal", "Fiscal"
    LEGALIZACAO = "Legalização", "Legalização"
    FINANCEIRO = "Financeiro", "Financeiro"
    CONTAS_RECEBER = "Contas a Receber", "Contas a Receber"
    CONCILIACOES = "Conciliações", "Conciliações"
    CONTAS_PAGAR = "Contas a Pagar", "Contas a Pagar"
    FECHAMENTOS = "Fechamentos e Resultados", "Fechamentos e Resultados"
    ORCAMENTOS = "Atualização de Orçamentos", "Atualização de Orçamentos"
    OUTRO = "Outro", "Outro"


class Orgao(models.TextChoices):
    FEDERAL = "Federal", "Federal"
    ESTADUAL = "Estadual", "Estadual"
    MUNICIPAL = "Municipal", "Municipal"
    EMPRESA = "Empresa", "Empresa"


class Tarefa(models.Model):
    """Definição de uma tarefa avulsa (modelo do 'Relatório')."""

    nome = models.CharField("Nome", max_length=255)
    departamento = models.CharField(
        "Departamento", max_length=40, choices=Departamento.choices,
        default=Departamento.CONTABILIDADE,
    )
    frequencia = models.CharField(
        "Frequência", max_length=40, default="Mensal",
        help_text="Ex.: Mensal, Trimestral, Anual (Janeiro), Esporádico.",
    )
    acao_qtd_dias = models.CharField("Ação (qtd dias)", max_length=20, blank=True)
    meta_qtd_dias = models.CharField("Meta (qtd dias)", max_length=20, blank=True)
    dia_vencimento = models.PositiveSmallIntegerField(
        "Dia de vencimento", null=True, blank=True,
    )
    fato_gerador = models.CharField(
        "Fato gerador (competência)", max_length=40, blank=True,
        help_text="Ex.: Mês anterior, Mesmo mês, Ano anterior.",
    )
    orgao = models.CharField(
        "Órgão", max_length=20, choices=Orgao.choices, default=Orgao.FEDERAL,
    )
    reenvio = models.CharField("Re-envio", max_length=60, blank=True)
    ativo = models.BooleanField("Ativa", default=True)

    empresas = models.ManyToManyField(
        Empresa, through="VinculoTarefa", related_name="tarefas", blank=True,
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tarefa"
        verbose_name_plural = "Tarefas"
        ordering = ["departamento", "nome"]

    def __str__(self):
        return f"{self.nome} · {self.departamento}"

    @property
    def total_empresas(self):
        return self.vinculos.count()


class VinculoTarefa(models.Model):
    """Vínculo entre uma empresa e uma tarefa."""

    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, related_name="vinculos_tarefa"
    )
    tarefa = models.ForeignKey(
        Tarefa, on_delete=models.CASCADE, related_name="vinculos"
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vínculo empresa-tarefa"
        verbose_name_plural = "Vínculos empresa-tarefa"
        unique_together = ("empresa", "tarefa")
        ordering = ["empresa__id_sistema", "tarefa__nome"]

    def __str__(self):
        return f"{self.empresa.id_sistema} → {self.tarefa.nome}"


class StatusExecucao(models.TextChoices):
    PENDENTE = "PENDENTE", "Pendente"
    ANDAMENTO = "ANDAMENTO", "Em andamento"
    CONCLUIDA = "CONCLUIDA", "Concluída"
    ATRASADA = "ATRASADA", "Atrasada"
    DISPENSADA = "DISPENSADA", "Dispensada"


class ExecucaoMensal(models.Model):
    """Instância mensal de uma tarefa para uma empresa (gestão mensal)."""

    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, related_name="execucoes"
    )
    tarefa = models.ForeignKey(
        Tarefa, on_delete=models.CASCADE, related_name="execucoes"
    )
    competencia_ano = models.PositiveSmallIntegerField()
    competencia_mes = models.PositiveSmallIntegerField()  # 1..12

    status = models.CharField(
        max_length=12, choices=StatusExecucao.choices, default=StatusExecucao.PENDENTE,
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="execucoes",
    )
    data_conclusao = models.DateField(null=True, blank=True)
    observacao = models.CharField(max_length=255, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Execução mensal"
        verbose_name_plural = "Execuções mensais"
        unique_together = ("empresa", "tarefa", "competencia_ano", "competencia_mes")
        ordering = ["-competencia_ano", "-competencia_mes", "empresa__id_sistema"]

    def __str__(self):
        return (
            f"{self.empresa.id_sistema} · {self.tarefa.nome} "
            f"· {self.competencia_mes:02d}/{self.competencia_ano}"
        )

    def marcar_concluida(self, usuario=None):
        self.status = StatusExecucao.CONCLUIDA
        self.data_conclusao = timezone.localdate()
        if usuario:
            self.responsavel = usuario
        self.save()
