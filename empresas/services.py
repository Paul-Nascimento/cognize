"""
Integração com a ReceitaWS (plano gratuito) e controle de rate limit.

O plano gratuito permite 3 consultas por minuto. Para respeitar isso sem
travar o servidor, usamos uma janela deslizante baseada na tabela
ConsultaReceitaLog: contamos quantas chamadas ocorreram nos últimos 60s.
"""
from dataclasses import dataclass
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone

from .models import ConsultaReceitaLog, somente_digitos


class ReceitaWSError(Exception):
    """Erro genérico ao consultar a ReceitaWS."""


class RateLimitError(ReceitaWSError):
    """Limite de 3 consultas/minuto atingido localmente."""

    def __init__(self, segundos_espera: int):
        self.segundos_espera = segundos_espera
        super().__init__(
            f"Limite de {settings.RECEITAWS_MAX_POR_MINUTO} consultas por minuto "
            f"atingido. Tente novamente em {segundos_espera}s."
        )


@dataclass
class OrcamentoRate:
    """Situação atual do limite de consultas."""

    disponiveis: int
    usados: int
    limite: int
    proxima_liberacao_em: int  # segundos até liberar 1 slot (0 se há saldo)


def _janela_inicio():
    return timezone.now() - timedelta(seconds=settings.RECEITAWS_JANELA_SEGUNDOS)


def orcamento_atual() -> OrcamentoRate:
    """Quantas consultas ainda cabem na janela de 60s."""
    limite = settings.RECEITAWS_MAX_POR_MINUTO
    janela = settings.RECEITAWS_JANELA_SEGUNDOS
    recentes = list(
        ConsultaReceitaLog.objects.filter(criado_em__gte=_janela_inicio())
        .order_by("criado_em")
        .values_list("criado_em", flat=True)
    )
    usados = len(recentes)
    disponiveis = max(0, limite - usados)
    proxima = 0
    if disponiveis == 0 and recentes:
        mais_antiga = recentes[0]
        libera_em = mais_antiga + timedelta(seconds=janela)
        proxima = max(0, int((libera_em - timezone.now()).total_seconds()) + 1)
    return OrcamentoRate(
        disponiveis=disponiveis, usados=usados, limite=limite,
        proxima_liberacao_em=proxima,
    )


def _registrar(cnpj: str, sucesso: bool, mensagem: str = ""):
    ConsultaReceitaLog.objects.create(cnpj=cnpj, sucesso=sucesso, mensagem=mensagem[:255])


def consultar_cnpj(cnpj: str) -> dict:
    """
    Consulta um CNPJ na ReceitaWS respeitando o rate limit.

    Levanta RateLimitError se não houver saldo na janela de 60s, ou
    ReceitaWSError em caso de falha da API / CNPJ inválido.
    """
    numeros = somente_digitos(cnpj)
    if len(numeros) != 14:
        raise ReceitaWSError("CNPJ inválido: informe os 14 dígitos.")

    orc = orcamento_atual()
    if orc.disponiveis <= 0:
        raise RateLimitError(orc.proxima_liberacao_em)

    url = f"{settings.RECEITAWS_BASE_URL}/{numeros}"
    try:
        resp = requests.get(url, timeout=settings.RECEITAWS_TIMEOUT)
    except requests.RequestException as exc:
        _registrar(cnpj, False, f"Falha de rede: {exc}")
        raise ReceitaWSError(f"Falha ao conectar na ReceitaWS: {exc}") from exc

    # A própria ReceitaWS pode devolver 429 quando estoura o limite do lado dela.
    if resp.status_code == 429:
        _registrar(cnpj, False, "429 ReceitaWS")
        raise RateLimitError(settings.RECEITAWS_JANELA_SEGUNDOS)

    if resp.status_code != 200:
        _registrar(cnpj, False, f"HTTP {resp.status_code}")
        raise ReceitaWSError(
            f"ReceitaWS respondeu HTTP {resp.status_code}. Tente mais tarde."
        )

    try:
        dados = resp.json()
    except ValueError as exc:
        _registrar(cnpj, False, "JSON inválido")
        raise ReceitaWSError("Resposta inválida da ReceitaWS.") from exc

    if dados.get("status") == "ERROR":
        msg = dados.get("message", "CNPJ não encontrado.")
        _registrar(cnpj, False, msg)
        raise ReceitaWSError(msg)

    _registrar(cnpj, True, "OK")
    return dados
