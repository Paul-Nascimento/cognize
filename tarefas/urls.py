from django.urls import path

from . import views

app_name = "tarefas"

urlpatterns = [
    path("", views.lista_tarefas, name="lista"),
    path("nova/", views.nova_tarefa, name="nova"),
    path("vincular/", views.vincular, name="vincular"),
    path("vinculo/<int:pk>/remover/", views.remover_vinculo, name="remover_vinculo"),
    path("mensal/", views.gestao_mensal, name="gestao_mensal"),
    path("mensal/gerar/", views.gerar_competencia, name="gerar_competencia"),
    path("execucao/<int:pk>/status/", views.atualizar_execucao, name="atualizar_execucao"),
    path("importar/tarefas/", views.importar_tarefas_view, name="importar_tarefas"),
    path("importar/vinculos/", views.importar_vinculos_view, name="importar_vinculos"),
    path("modelo/tarefas/", views.baixar_modelo_tarefas, name="modelo_tarefas"),
    path("modelo/vinculos/", views.baixar_modelo_vinculos, name="modelo_vinculos"),
    path("<int:pk>/", views.detalhe_tarefa, name="detalhe"),
    path("<int:pk>/editar/", views.editar_tarefa, name="editar"),
    path("<int:pk>/excluir/", views.excluir_tarefa, name="excluir"),
]
