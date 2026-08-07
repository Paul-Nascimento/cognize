from django.urls import path

from . import views

app_name = "empresas"

urlpatterns = [
    path("", views.lista_empresas, name="lista"),
    path("nova/", views.nova_empresa, name="nova"),
    path("importar/", views.importar, name="importar"),
    path("modelo/", views.baixar_modelo, name="baixar_modelo"),
    path("fila/processar/", views.processar_fila, name="processar_fila"),
    path("rate-limit/", views.status_rate_limit, name="status_rate_limit"),
    path("<int:pk>/", views.detalhe_empresa, name="detalhe"),
    path("<int:pk>/editar/", views.editar_empresa, name="editar"),
    path("<int:pk>/excluir/", views.excluir_empresa, name="excluir"),
    path("<int:pk>/consultar/", views.consultar_empresa, name="consultar"),
]
