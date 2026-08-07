from django.contrib import admin

from .models import ExecucaoMensal, Tarefa, VinculoTarefa


class VinculoInline(admin.TabularInline):
    model = VinculoTarefa
    extra = 0
    autocomplete_fields = ("empresa",)


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = ("nome", "departamento", "frequencia", "orgao", "dia_vencimento", "ativo")
    list_filter = ("departamento", "orgao", "ativo", "frequencia")
    search_fields = ("nome",)
    inlines = [VinculoInline]


@admin.register(VinculoTarefa)
class VinculoTarefaAdmin(admin.ModelAdmin):
    list_display = ("empresa", "tarefa", "ativo", "criado_em")
    list_filter = ("ativo", "tarefa__departamento")
    search_fields = ("empresa__id_sistema", "empresa__razao_social", "tarefa__nome")


@admin.register(ExecucaoMensal)
class ExecucaoMensalAdmin(admin.ModelAdmin):
    list_display = (
        "empresa", "tarefa", "competencia_mes", "competencia_ano",
        "status", "responsavel", "data_conclusao",
    )
    list_filter = ("status", "competencia_ano", "competencia_mes", "tarefa__departamento")
    search_fields = ("empresa__id_sistema", "tarefa__nome")
