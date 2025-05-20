from django import forms
from .models import MovimentoEstoque, SolicitacaoMaterial, Produto


class MovimentoEstoqueForm(forms.ModelForm):
    class Meta:
        model = MovimentoEstoque
        fields = [
            'produto',
            'quantidade',
            'validade',
            'local_guardado',
            'destino',
            'observacoes',
        ]
        widgets = {
            'validade': forms.DateInput(attrs={'type': 'date'}),
            'local_guardado': forms.TextInput(attrs={'placeholder': 'Ex: Prateleira A, Sala 2'}),
            'destino': forms.TextInput(attrs={'placeholder': 'Ex: Setor Manutenção'}),
            'observacoes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observações adicionais (opcional)'}),
        }

    def __init__(self, *args, **kwargs):
        self.tipo = kwargs.pop('tipo', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        produto = cleaned_data.get('produto')
        quantidade = cleaned_data.get('quantidade')

        if self.tipo == MovimentoEstoque.SAIDA:
            if produto and quantidade and quantidade > produto.quantidade:
                raise forms.ValidationError(
                    f"Quantidade insuficiente: disponível {produto.quantidade} unidade(s)."
                )
        return cleaned_data


class SolicitacaoMaterialForm(forms.ModelForm):
    class Meta:
        model = SolicitacaoMaterial
        fields = ['nome_produto', 'pn', 'quantidade', 'destino', 'observacao']
        widgets = {
            'observacao': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Detalhes adicionais (opcional)...'}),
            'destino': forms.Select(),  # dropdown com opções pré-definidas
        }

    def clean_quantidade(self):
        quantidade = self.cleaned_data.get('quantidade')
        if quantidade <= 0:
            raise forms.ValidationError("A quantidade deve ser maior que zero.")
        return quantidade


class ProdutoForm(forms.ModelForm):
    validade = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Validade",
        help_text="Deixe em branco se não houver validade."
    )

    class Meta:
        model = Produto
        fields = [
            'nome',
            'pn',
            'sn',
            'quantidade',
            'validade',
            'observacoes',
            'nome_responsavel',
            'base',
            'local',
            'estoque_minimo',
            'destino',
        ]
        labels = {
            'base': 'Base (ex: Manaus, GoodStorage)',
            'local': 'Local interno (ex: Sala 0316)',
            'destino': 'Destino (opcional)',
        }
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observações adicionais (opcional)'}),
            'local': forms.TextInput(attrs={'placeholder': 'Ex: Sala 0316, SALA B'}),
            'destino': forms.Select(),
        }

    def clean(self):
        cleaned_data = super().clean()
        pn = cleaned_data.get('pn')
        base = cleaned_data.get('base')

        if Produto.objects.filter(pn=pn, base=base).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Já existe um produto com esse P/N nesta base.")
        return cleaned_data


class TransferenciaForm(forms.Form):
    produto = forms.ModelChoiceField(queryset=Produto.objects.all(), label="Produto")
    quantidade = forms.IntegerField(min_value=1, label="Quantidade a transferir")
    base_origem = forms.CharField(widget=forms.HiddenInput())
    base_destino = forms.ChoiceField(choices=Produto.BASE_CHOICES, label="Destino")
    observacoes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Observações"
    )

    def clean(self):
        cleaned_data = super().clean()
        produto = cleaned_data.get('produto')
        quantidade = cleaned_data.get('quantidade')
        base_origem = cleaned_data.get('base_origem')

        if produto and quantidade:
            if produto.base != base_origem:
                raise forms.ValidationError("Produto não pertence à base de origem.")
            if quantidade > produto.quantidade:
                raise forms.ValidationError(f"Estoque insuficiente: {produto.quantidade} unidade(s) disponíveis.")
        return cleaned_data
