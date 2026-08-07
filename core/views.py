from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from empresas.models import Empresa, StatusConsulta
from empresas.services import orcamento_atual
from tarefas.models import ExecucaoMensal, StatusExecucao, Tarefa, VinculoTarefa


@login_required
def dashboard(request):
    hoje = date.today()
    execucoes_mes = ExecucaoMensal.objects.filter(
        competencia_ano=hoje.year, competencia_mes=hoje.month
    )
    resumo_status = {s.value: 0 for s in StatusExecucao}
    for row in execucoes_mes.values("status").annotate(qtd=Count("id")):
        resumo_status[row["status"]] = row["qtd"]

    total_exec = execucoes_mes.count()
    concluidas = resumo_status.get(StatusExecucao.CONCLUIDA, 0)
    progresso = round((concluidas / total_exec) * 100) if total_exec else 0

    # tarefas por departamento
    por_departamento = (
        Tarefa.objects.values("departamento")
        .annotate(qtd=Count("id"))
        .order_by("-qtd")
    )

    contexto = {
        "total_empresas": Empresa.objects.count(),
        "empresas_pendentes": Empresa.objects.filter(
            status_consulta=StatusConsulta.PENDENTE
        ).count(),
        "empresas_ok": Empresa.objects.filter(
            status_consulta=StatusConsulta.OK
        ).count(),
        "total_tarefas": Tarefa.objects.count(),
        "total_vinculos": VinculoTarefa.objects.count(),
        "resumo_status": resumo_status,
        "total_exec": total_exec,
        "progresso": progresso,
        "por_departamento": por_departamento,
        "orcamento": orcamento_atual(),
        "mes_atual": hoje.month,
        "ano_atual": hoje.year,
        "StatusExecucao": StatusExecucao,
    }
    return render(request, "core/dashboard.html", contexto)
