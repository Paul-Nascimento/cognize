from django import forms

from empresas.models import Empresa
from .models import Tarefa


class TarefaForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = (
            "nome", "departamento", "frequencia", "acao_qtd_dias",
            "meta_qtd_dias", "dia_vencimento", "fato_gerador", "orgao",
            "reenvio", "ativo",
        )
        widgets = {
            "nome": forms.TextInput(attrs={"placeholder": "Ex.: DAS SIMPLES"}),
            "frequencia": forms.TextInput(attrs={"placeholder": "Ex.: Mensal"}),
            "fato_gerador": forms.TextInput(attrs={"placeholder": "Ex.: Mês anterior"}),
        }


class VincularForm(forms.Form):
    """Vincula várias tarefas a várias empresas de uma vez."""

    empresas = forms.ModelMultipleChoiceField(
        queryset=Empresa.objects.all(),
        widget=forms.SelectMultiple(attrs={"size": 14}),
        label="Empresas",
    )
    tarefas = forms.ModelMultipleChoiceField(
        queryset=Tarefa.objects.filter(ativo=True),
        widget=forms.SelectMultiple(attrs={"size": 14}),
        label="Tarefas",
    )


class ImportarTarefasForm(forms.Form):
    arquivo = forms.FileField(
        label="Planilha de tarefas (.xlsx)",
        help_text="Colunas: Departamento, Nome, Frequência, Ação(qtd dias), "
        "Meta(qtd dias), Dia Vencimento, Fato Gerador, Órgão, Status.",
    )


class ImportarVinculosForm(forms.Form):
    arquivo = forms.FileField(
        label="Planilha de vínculos (.xlsx)",
        help_text="Colunas: ID Empresa, Tarefa (nome exato). Uma linha por vínculo.",
    )


MESES = [
    (1, "Janeiro"), (2, "Fevereiro"), (3, "Março"), (4, "Abril"),
    (5, "Maio"), (6, "Junho"), (7, "Julho"), (8, "Agosto"),
    (9, "Setembro"), (10, "Outubro"), (11, "Novembro"), (12, "Dezembro"),
]


class CompetenciaForm(forms.Form):
    mes = forms.ChoiceField(choices=MESES, label="Mês")
    ano = forms.IntegerField(label="Ano", min_value=2000, max_value=2100)
