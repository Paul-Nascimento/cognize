from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import requer_edicao, requer_gestor
from .forms import EmpresaEdicaoForm, EmpresaForm, ImportarEmpresasForm
from .imports import exportar_empresas, gerar_modelo_empresas, importar_empresas
from .models import Empresa, StatusConsulta
from .services import (
    RateLimitError,
    ReceitaWSError,
    consultar_cnpj,
    orcamento_atual,
)


def _filtrar_empresas(request):
    """Aplica busca e filtro de status a partir dos parâmetros GET."""
    busca = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    empresas = Empresa.objects.all()
    if busca:
        empresas = empresas.filter(
            Q(id_sistema__icontains=busca)
            | Q(razao_social__icontains=busca)
            | Q(nome_fantasia__icontains=busca)
            | Q(cnpj__icontains=busca)
        )
    if status:
        empresas = empresas.filter(status_consulta=status)
    return empresas, busca, status


@login_required
def lista_empresas(request):
    empresas, busca, status = _filtrar_empresas(request)

    orc = orcamento_atual()
    pendentes = Empresa.objects.filter(status_consulta=StatusConsulta.PENDENTE).count()
    return render(
        request,
        "empresas/lista.html",
        {
            "empresas": empresas,
            "busca": busca,
            "status_sel": status,
            "orcamento": orc,
            "pendentes": pendentes,
            "StatusConsulta": StatusConsulta,
        },
    )


@login_required
def detalhe_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    return render(request, "empresas/detalhe.html", {"empresa": empresa})


@requer_edicao
def nova_empresa(request):
    """Cadastro unitário: usuário informa os campos e a API puxa o resto."""
    if request.method == "POST":
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save(commit=False)
            empresa.criado_por = request.user
            # Tenta enriquecer imediatamente, respeitando o rate limit.
            consultar = "salvar_sem_consultar" not in request.POST
            if consultar:
                try:
                    dados = consultar_cnpj(empresa.cnpj)
                    empresa.aplicar_dados_receita(dados)
                    messages.success(
                        request,
                        f"Empresa cadastrada e dados da ReceitaWS carregados: "
                        f"{empresa.razao_social}.",
                    )
                except RateLimitError as exc:
                    empresa.status_consulta = StatusConsulta.PENDENTE
                    empresa.mensagem_consulta = str(exc)
                    messages.warning(
                        request,
                        f"Empresa salva, mas o limite de consultas foi atingido "
                        f"({exc.segundos_espera}s). Ela ficou na fila de "
                        f"enriquecimento.",
                    )
                except ReceitaWSError as exc:
                    empresa.status_consulta = StatusConsulta.ERRO
                    empresa.mensagem_consulta = str(exc)
                    messages.warning(
                        request,
                        f"Empresa salva, mas houve erro na ReceitaWS: {exc}",
                    )
            else:
                messages.success(request, "Empresa salva sem consultar a ReceitaWS.")
            empresa.save()
            return redirect("empresas:detalhe", pk=empresa.pk)
    else:
        form = EmpresaForm()
    return render(
        request,
        "empresas/form.html",
        {"form": form, "orcamento": orcamento_atual()},
    )


@requer_edicao
def editar_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == "POST":
        form = EmpresaEdicaoForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, "Empresa atualizada.")
            return redirect("empresas:detalhe", pk=empresa.pk)
    else:
        form = EmpresaEdicaoForm(instance=empresa)
    return render(
        request, "empresas/form.html", {"form": form, "empresa": empresa, "edicao": True}
    )


@requer_gestor
@require_POST
def excluir_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    empresa.delete()
    messages.success(request, "Empresa excluída.")
    return redirect("empresas:lista")


# ---------------------------------------------------------------------------
# Consulta / fila de enriquecimento (AJAX) — respeita 3 consultas/minuto
# ---------------------------------------------------------------------------
@requer_edicao
@require_POST
def consultar_empresa(request, pk):
    """Consulta uma empresa específica na ReceitaWS (usado no detalhe)."""
    empresa = get_object_or_404(Empresa, pk=pk)
    try:
        dados = consultar_cnpj(empresa.cnpj)
        empresa.aplicar_dados_receita(dados)
        empresa.save()
        return JsonResponse(
            {"ok": True, "razao_social": empresa.razao_social,
             "mensagem": "Dados atualizados pela ReceitaWS."}
        )
    except RateLimitError as exc:
        return JsonResponse(
            {"ok": False, "rate_limit": True, "espera": exc.segundos_espera,
             "mensagem": str(exc)},
            status=429,
        )
    except ReceitaWSError as exc:
        empresa.status_consulta = StatusConsulta.ERRO
        empresa.mensagem_consulta = str(exc)
        empresa.save(update_fields=["status_consulta", "mensagem_consulta"])
        return JsonResponse({"ok": False, "mensagem": str(exc)}, status=400)


@requer_edicao
@require_POST
def processar_fila(request):
    """
    Processa a fila de empresas pendentes consumindo o saldo atual do rate limit.
    Chamado repetidamente pelo JS até esvaziar a fila. Retorna quantas foram
    processadas nesta rodada e quantas ainda faltam.
    """
    orc = orcamento_atual()
    processadas = []
    erros = []
    pendentes_qs = Empresa.objects.filter(
        status_consulta__in=[StatusConsulta.PENDENTE, StatusConsulta.ERRO]
    ).order_by("id_sistema")

    for empresa in pendentes_qs[: orc.disponiveis]:
        try:
            dados = consultar_cnpj(empresa.cnpj)
            empresa.aplicar_dados_receita(dados)
            empresa.save()
            processadas.append(
                {"id": empresa.pk, "id_sistema": empresa.id_sistema,
                 "razao_social": empresa.razao_social}
            )
        except RateLimitError:
            break
        except ReceitaWSError as exc:
            empresa.status_consulta = StatusConsulta.ERRO
            empresa.mensagem_consulta = str(exc)
            empresa.save(update_fields=["status_consulta", "mensagem_consulta"])
            erros.append({"id_sistema": empresa.id_sistema, "mensagem": str(exc)})

    restantes = Empresa.objects.filter(
        status_consulta__in=[StatusConsulta.PENDENTE, StatusConsulta.ERRO]
    ).count()
    novo_orc = orcamento_atual()
    return JsonResponse(
        {
            "processadas": processadas,
            "erros": erros,
            "restantes": restantes,
            "espera": novo_orc.proxima_liberacao_em,
            "disponiveis": novo_orc.disponiveis,
        }
    )


@login_required
def status_rate_limit(request):
    """Endpoint leve para o frontend saber o saldo atual de consultas."""
    orc = orcamento_atual()
    return JsonResponse(
        {"disponiveis": orc.disponiveis, "usados": orc.usados,
         "limite": orc.limite, "espera": orc.proxima_liberacao_em}
    )


# ---------------------------------------------------------------------------
# Importação
# ---------------------------------------------------------------------------
@requer_gestor
def importar(request):
    resultado = None
    if request.method == "POST":
        form = ImportarEmpresasForm(request.POST, request.FILES)
        if form.is_valid():
            resultado = importar_empresas(
                form.cleaned_data["arquivo"], usuario=request.user
            )
            msg = (
                f"{resultado['criadas']} criadas, "
                f"{resultado['atualizadas']} atualizadas."
            )
            if resultado["erros"]:
                messages.warning(request, f"{msg} {len(resultado['erros'])} com erro.")
            else:
                messages.success(request, f"Importação concluída: {msg}")
    else:
        form = ImportarEmpresasForm()
    return render(
        request,
        "empresas/importar.html",
        {"form": form, "resultado": resultado},
    )


@login_required
def exportar(request):
    """Baixa um .xlsx com todas as empresas (respeitando os filtros da lista)."""
    empresas, _, _ = _filtrar_empresas(request)
    conteudo = exportar_empresas(empresas)
    resp = HttpResponse(
        conteudo,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = 'attachment; filename="empresas.xlsx"'
    return resp


@requer_gestor
def baixar_modelo(request):
    conteudo = gerar_modelo_empresas()
    resp = HttpResponse(
        conteudo,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = 'attachment; filename="modelo_empresas.xlsx"'
    return resp
