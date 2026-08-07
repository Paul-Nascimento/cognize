from django import forms

from .models import Empresa


class EmpresaForm(forms.ModelForm):
    """Formulário com os campos que o usuário informa manualmente."""

    class Meta:
        model = Empresa
        fields = (
            "id_sistema",
            "cnpj",
            "regime_tributario",
            "inscricao_iss",
            "inscricao_icms",
            "observacoes",
        )
        widgets = {
            "id_sistema": forms.TextInput(attrs={"placeholder": "Ex.: 300"}),
            "cnpj": forms.TextInput(attrs={"placeholder": "00.000.000/0001-00"}),
            "inscricao_iss": forms.TextInput(attrs={"placeholder": "Opcional"}),
            "inscricao_icms": forms.TextInput(attrs={"placeholder": "Opcional"}),
            "observacoes": forms.Textarea(attrs={"rows": 3, "placeholder": "Observações internas"}),
        }

    def clean_cnpj(self):
        import re

        cnpj = re.sub(r"\D", "", self.cleaned_data["cnpj"] or "")
        if len(cnpj) != 14:
            raise forms.ValidationError("Informe um CNPJ com 14 dígitos.")
        return cnpj


class EmpresaEdicaoForm(forms.ModelForm):
    """Edição permite ajustar também alguns dados vindos da API, se necessário."""

    class Meta:
        model = Empresa
        fields = (
            "id_sistema",
            "cnpj",
            "regime_tributario",
            "inscricao_iss",
            "inscricao_icms",
            "observacoes",
            "razao_social",
            "nome_fantasia",
            "email",
            "telefone",
        )
        widgets = {
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }


class ImportarEmpresasForm(forms.Form):
    arquivo = forms.FileField(
        label="Planilha de empresas (.xlsx)",
        help_text="Colunas: ID Sistema, CNPJ, Regime Tributário, Inscrição ISS, "
        "Inscrição ICMS, Observações.",
    )
    consultar_api = forms.BooleanField(
        label="Consultar ReceitaWS automaticamente após importar",
        required=False,
        help_text="Se marcado, as empresas entram na fila de enriquecimento (3/min).",
    )
