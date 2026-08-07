import re

from django.conf import settings
from django.db import models
from django.utils import timezone


class RegimeTributario(models.TextChoices):
    SIMPLES = "SIMPLES", "Simples Nacional"
    MEI = "MEI", "MEI"
    PRESUMIDO = "PRESUMIDO", "Lucro Presumido"
    REAL = "REAL", "Lucro Real"
    IMUNE = "IMUNE", "Imune / Isenta"


class StatusConsulta(models.TextChoices):
    PENDENTE = "PENDENTE", "Pendente de consulta"
    OK = "OK", "Consultado"
    ERRO = "ERRO", "Erro na consulta"


def somente_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


class Empresa(models.Model):
    """Empresa cliente. Campos manuais + dados enriquecidos pela ReceitaWS."""

    # ---- Campos informados manualmente pelo usuário ----
    id_sistema = models.CharField(
        "ID no sistema", max_length=20, unique=True,
        help_text="Código interno da empresa (ex.: 300, 401).",
    )
    cnpj = models.CharField(
        "CNPJ", max_length=18, unique=True,
        help_text="Usado para consultar a ReceitaWS.",
    )
    regime_tributario = models.CharField(
        "Regime tributário", max_length=12, choices=RegimeTributario.choices,
    )
    inscricao_iss = models.CharField("Inscrição ISS", max_length=30, blank=True)
    inscricao_icms = models.CharField("Inscrição ICMS", max_length=30, blank=True)
    observacoes = models.TextField("Observações", blank=True)

    # ---- Campos preenchidos pela API ReceitaWS ----
    razao_social = models.CharField("Razão social", max_length=255, blank=True)
    nome_fantasia = models.CharField("Nome fantasia", max_length=255, blank=True)
    situacao_cadastral = models.CharField("Situação cadastral", max_length=60, blank=True)
    data_situacao = models.CharField("Data da situação", max_length=20, blank=True)
    motivo_situacao = models.CharField("Motivo da situação", max_length=255, blank=True)
    tipo = models.CharField("Tipo (matriz/filial)", max_length=30, blank=True)
    porte = models.CharField("Porte", max_length=60, blank=True)
    natureza_juridica = models.CharField("Natureza jurídica", max_length=255, blank=True)
    data_abertura = models.CharField("Data de abertura", max_length=20, blank=True)
    capital_social = models.CharField("Capital social", max_length=40, blank=True)

    atividade_principal_codigo = models.CharField(max_length=20, blank=True)
    atividade_principal_texto = models.CharField(max_length=255, blank=True)
    atividades_secundarias = models.JSONField(default=list, blank=True)
    quadro_societario = models.JSONField(default=list, blank=True)

    # Endereço
    logradouro = models.CharField(max_length=255, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=120, blank=True)
    bairro = models.CharField(max_length=120, blank=True)
    municipio = models.CharField(max_length=120, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    cep = models.CharField(max_length=12, blank=True)

    # Contato
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=60, blank=True)

    # Simples/MEI (informação oficial da Receita)
    simples_optante = models.BooleanField(null=True, blank=True)
    simples_data_opcao = models.CharField(max_length=20, blank=True)
    simei_optante = models.BooleanField(null=True, blank=True)

    # ---- Controle ----
    status_consulta = models.CharField(
        max_length=10, choices=StatusConsulta.choices, default=StatusConsulta.PENDENTE,
    )
    mensagem_consulta = models.CharField(max_length=255, blank=True)
    ultima_consulta = models.DateTimeField(null=True, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="empresas_criadas",
    )

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["id_sistema"]

    def __str__(self):
        return f"{self.id_sistema} — {self.razao_social or self.cnpj}"

    def save(self, *args, **kwargs):
        self.cnpj = self.cnpj_formatado
        super().save(*args, **kwargs)

    @property
    def cnpj_numeros(self) -> str:
        return somente_digitos(self.cnpj)

    @property
    def cnpj_formatado(self) -> str:
        d = self.cnpj_numeros.zfill(14)[:14]
        if len(d) != 14:
            return self.cnpj
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"

    @property
    def endereco_completo(self) -> str:
        partes = [
            self.logradouro,
            self.numero,
            self.complemento,
            self.bairro,
            f"{self.municipio}/{self.uf}" if self.municipio else "",
            self.cep,
        ]
        return " · ".join(p for p in partes if p)

    def aplicar_dados_receita(self, dados: dict):
        """Preenche os campos vindos da resposta da ReceitaWS."""
        self.razao_social = dados.get("nome", "") or self.razao_social
        self.nome_fantasia = dados.get("fantasia", "")
        self.situacao_cadastral = dados.get("situacao", "")
        self.data_situacao = dados.get("data_situacao", "")
        self.motivo_situacao = dados.get("motivo_situacao", "")
        self.tipo = dados.get("tipo", "")
        self.porte = dados.get("porte", "")
        self.natureza_juridica = dados.get("natureza_juridica", "")
        self.data_abertura = dados.get("abertura", "")
        self.capital_social = str(dados.get("capital_social", "") or "")

        principal = (dados.get("atividade_principal") or [{}])[0]
        self.atividade_principal_codigo = principal.get("code", "")
        self.atividade_principal_texto = principal.get("text", "")
        self.atividades_secundarias = dados.get("atividades_secundarias", []) or []
        self.quadro_societario = dados.get("qsa", []) or []

        self.logradouro = dados.get("logradouro", "")
        self.numero = dados.get("numero", "")
        self.complemento = dados.get("complemento", "")
        self.bairro = dados.get("bairro", "")
        self.municipio = dados.get("municipio", "")
        self.uf = dados.get("uf", "")
        self.cep = dados.get("cep", "")

        self.email = dados.get("email", "") or ""
        self.telefone = dados.get("telefone", "")

        simples = dados.get("simples") or {}
        simei = dados.get("simei") or {}
        self.simples_optante = simples.get("optante")
        self.simples_data_opcao = simples.get("data_opcao", "") or ""
        self.simei_optante = simei.get("optante")

        self.status_consulta = StatusConsulta.OK
        self.mensagem_consulta = ""
        self.ultima_consulta = timezone.now()


class ConsultaReceitaLog(models.Model):
    """Registro de cada chamada à ReceitaWS — usado para o rate limit (3/min)."""

    cnpj = models.CharField(max_length=18)
    sucesso = models.BooleanField(default=False)
    mensagem = models.CharField(max_length=255, blank=True)
    criado_em = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "Log de consulta ReceitaWS"
        verbose_name_plural = "Logs de consulta ReceitaWS"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.cnpj} @ {self.criado_em:%d/%m %H:%M:%S}"
