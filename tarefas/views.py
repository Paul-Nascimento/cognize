from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.decorators import requer_edicao, requer_gestor
from empresas.models import Empresa
from .forms import (
    CompetenciaForm,
    ImportarTarefasForm,
    ImportarVinculosForm,
    MESES,
    TarefaForm,
    VincularForm,
)
from .imports import (
    gerar_modelo_tarefas,
    gerar_modelo_vinculos,
    importar_tarefas,
    importar_vinculos,
)
from .models import (
    ExecucaoMensal,
    StatusExecucao,
    Tarefa,
    VinculoTarefa,
)

MESES_DICT = dict(MESES)


# ---------------------------------------------------------------------------
# CRUD de tarefas
# ---------------------------------------------------------------------------
@login_required
def lista_tarefas(request):
    busca = request.GET.get("q", "").strip()
    depto = request.GET.get("departamento", "").strip()
    tarefas = Tarefa.objects.annotate(qtd_empresas=Count("vinculos"))
    if busca:
        tarefas = tarefas.filter(Q(nome__icontains=busca) | Q(frequencia__icontains=busca))
    if depto:
        tarefas = tarefas.filter(departamento=depto)
    departamentos = (
        Tarefa.objects.values_list("departamento", flat=True).distinct().order_by("departamento")
    )
    return render(
        request,
        "tarefas/lista.html",
        {"tarefas": tarefas, "busca": busca, "departamentos": departamentos, "depto_sel": depto},
    )


@login_required
def detalhe_tarefa(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    vinculos = tarefa.vinculos.select_related("empresa")
    return render(request, "tarefas/detalhe.html", {"tarefa": tarefa, "vinculos": vinculos})


@requer_edicao
def nova_tarefa(request):
    form = TarefaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Tarefa criada.")
        return redirect("tarefas:lista")
    return render(request, "tarefas/form.html", {"form": form, "titulo": "Nova tarefa"})


@requer_edicao
def editar_tarefa(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    form = TarefaForm(request.POST or None, instance=tarefa)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Tarefa atualizada.")
        return redirect("tarefas:detalhe", pk=tarefa.pk)
    return render(
        request, "tarefas/form.html", {"form": form, "titulo": f"Editar {tarefa.nome}"}
    )


@requer_gestor
@require_POST
def excluir_tarefa(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    tarefa.delete()
    messages.success(request, "Tarefa excluída.")
    return redirect("tarefas:lista")


# ---------------------------------------------------------------------------
# Vínculos empresa-tarefa (várias x várias) pela interface
# ---------------------------------------------------------------------------
@requer_edicao
def vincular(request):
    form = VincularForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        empresas = form.cleaned_data["empresas"]
        tarefas = form.cleaned_data["tarefas"]
        criados = 0
        for empresa in empresas:
            for tarefa in tarefas:
                _, novo = VinculoTarefa.objects.get_or_create(empresa=empresa, tarefa=tarefa)
                criados += int(novo)
        messages.success(
            request,
            f"{criados} vínculo(s) criado(s) "
            f"({empresas.count()} empresa(s) × {tarefas.count()} tarefa(s)).",
        )
        return redirect("tarefas:vincular")
    return render(request, "tarefas/vincular.html", {"form": form})


@requer_edicao
@require_POST
def remover_vinculo(request, pk):
    vinculo = get_object_or_404(VinculoTarefa, pk=pk)
    tarefa_pk = vinculo.tarefa_id
    vinculo.delete()
    messages.success(request, "Vínculo removido.")
    destino = request.POST.get("next") or "tarefas:detalhe"
    if destino == "empresa":
        return redirect("empresas:detalhe", pk=vinculo.empresa_id)
    return redirect("tarefas:detalhe", pk=tarefa_pk)


# ---------------------------------------------------------------------------
# Gestão mensal
# ---------------------------------------------------------------------------
@login_required
def gestao_mensal(request):
    hoje = date.today()
    try:
        mes = int(request.GET.get("mes", hoje.month))
        ano = int(request.GET.get("ano", hoje.year))
    except (TypeError, ValueError):
        mes, ano = hoje.month, hoje.year

    depto = request.GET.get("departamento", "").strip()
    status = request.GET.get("status", "").strip()
    empresa_id = request.GET.get("empresa", "").strip()

    execucoes = (
        ExecucaoMensal.objects.filter(competencia_ano=ano, competencia_mes=mes)
        .select_related("empresa", "tarefa", "responsavel")
    )
    if depto:
        execucoes = execucoes.filter(tarefa__departamento=depto)
    if status:
        execucoes = execucoes.filter(status=status)
    if empresa_id:
        execucoes = execucoes.filter(empresa_id=empresa_id)

    # Resumo por status
    resumo = {s.value: 0 for s in StatusExecucao}
    for e in execucoes:
        resumo[e.status] = resumo.get(e.status, 0) + 1

    departamentos = (
        Tarefa.objects.values_list("departamento", flat=True).distinct().order_by("departamento")
    )
    return render(
        request,
        "tarefas/gestao_mensal.html",
        {
            "execucoes": execucoes,
            "mes": mes,
            "ano": ano,
            "mes_nome": MESES_DICT.get(mes, mes),
            "meses": MESES,
            "anos": range(hoje.year - 2, hoje.year + 2),
            "resumo": resumo,
            "total": execucoes.count(),
            "departamentos": departamentos,
            "depto_sel": depto,
            "status_sel": status,
            "empresa_sel": empresa_id,
            "empresas": Empresa.objects.all(),
            "StatusExecucao": StatusExecucao,
        },
    )


@requer_edicao
@require_POST
def gerar_competencia(request):
    """Cria execuções mensais para todos os vínculos ativos na competência."""
    form = CompetenciaForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Informe mês e ano válidos.")
        return redirect("tarefas:gestao_mensal")
    mes = int(form.cleaned_data["mes"])
    ano = int(form.cleaned_data["ano"])

    criadas = 0
    vinculos = VinculoTarefa.objects.filter(ativo=True, tarefa__ativo=True).select_related(
        "empresa", "tarefa"
    )
    for v in vinculos:
        _, novo = ExecucaoMensal.objects.get_or_create(
            empresa=v.empresa,
            tarefa=v.tarefa,
            competencia_ano=ano,
            competencia_mes=mes,
            defaults={"status": StatusExecucao.PENDENTE},
        )
        criadas += int(novo)
    messages.success(
        request,
        f"{criadas} execução(ões) geradas para {MESES_DICT.get(mes)}/{ano}.",
    )
    url = reverse("tarefas:gestao_mensal")
    return redirect(f"{url}?mes={mes}&ano={ano}")


@requer_edicao
@require_POST
def atualizar_execucao(request, pk):
    """Atualiza o status de uma execução (AJAX)."""
    execucao = get_object_or_404(ExecucaoMensal, pk=pk)
    novo_status = request.POST.get("status")
    validos = {s.value for s in StatusExecucao}
    if novo_status not in validos:
        return JsonResponse({"ok": False, "mensagem": "Status inválido."}, status=400)
    execucao.status = novo_status
    if novo_status == StatusExecucao.CONCLUIDA:
        execucao.data_conclusao = date.today()
        execucao.responsavel = request.user
    execucao.save()
    return JsonResponse(
        {"ok": True, "status": execucao.status,
         "label": execucao.get_status_display(),
         "responsavel": execucao.responsavel.get_full_name() if execucao.responsavel else ""}
    )


# ---------------------------------------------------------------------------
# Importações e modelos
# ---------------------------------------------------------------------------
@requer_gestor
def importar_tarefas_view(request):
    resultado = None
    if request.method == "POST":
        form = ImportarTarefasForm(request.POST, request.FILES)
        if form.is_valid():
            resultado = importar_tarefas(form.cleaned_data["arquivo"])
            messages.success(
                request,
                f"Tarefas: {resultado['criadas']} criadas, "
                f"{resultado['atualizadas']} atualizadas.",
            )
    else:
        form = ImportarTarefasForm()
    return render(
        request,
        "tarefas/importar.html",
        {"form": form, "resultado": resultado, "tipo": "tarefas",
         "titulo": "Importar tarefas", "modelo_url": "tarefas:modelo_tarefas"},
    )


@requer_gestor
def importar_vinculos_view(request):
    resultado = None
    if request.method == "POST":
        form = ImportarVinculosForm(request.POST, request.FILES)
        if form.is_valid():
            resultado = importar_vinculos(form.cleaned_data["arquivo"])
            messages.success(request, f"{resultado['criados']} vínculo(s) criado(s).")
    else:
        form = ImportarVinculosForm()
    return render(
        request,
        "tarefas/importar.html",
        {"form": form, "resultado": resultado, "tipo": "vinculos",
         "titulo": "Importar vínculos empresa-tarefa",
         "modelo_url": "tarefas:modelo_vinculos"},
    )


def _xlsx_response(conteudo, nome):
    resp = HttpResponse(
        conteudo,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="{nome}"'
    return resp


@requer_gestor
def baixar_modelo_tarefas(request):
    return _xlsx_response(gerar_modelo_tarefas(), "modelo_tarefas.xlsx")


@requer_gestor
def baixar_modelo_vinculos(request):
    return _xlsx_response(gerar_modelo_vinculos(), "modelo_vinculos.xlsx")
