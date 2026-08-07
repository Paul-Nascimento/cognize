from django.contrib import admin

from .models import ConsultaReceitaLog, Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = (
        "id_sistema", "razao_social", "cnpj", "regime_tributario",
        "status_consulta", "ultima_consulta",
    )
    list_filter = ("regime_tributario", "status_consulta", "uf")
    search_fields = ("id_sistema", "razao_social", "nome_fantasia", "cnpj")
    readonly_fields = ("criado_em", "atualizado_em", "ultima_consulta")


@admin.register(ConsultaReceitaLog)
class ConsultaReceitaLogAdmin(admin.ModelAdmin):
    list_display = ("cnpj", "sucesso", "mensagem", "criado_em")
    list_filter = ("sucesso",)
    search_fields = ("cnpj",)
