from django.db import models 
from django.contrib.auth.models import User

class Produto(models.Model):
    BASE_CHOICES = [
        ("Base Principal", "Base Principal"),
        ("Base Porto Velho", "Base Porto Velho"),
        ("Base Parintins", "Base Parintins"),
        ("Base Santarém", "Base Santarém"),
        ("Base Macapá", "Base Macapá"),
        ("Base Marabá", "Base Marabá"),
        ("Base Manaus", "Base Manaus"),
        ("Sala 0316", "Sala 0316"),
        ("Sala 2320", "Sala 2320"),
        ("Sala 2322", "Sala 2322"),
    ]

    DESTINO_CHOICES = [
        ("Estoque", "Estoque"),
        ("PS-ARB", "PS-ARB"),
        ("PS-JOR", "PS-JOR"),
        ("PS-VCB", "PS-VCB"),
        ("PS-JJF", "PS-JJF"),
        ("PS-ELI", "PS-ELI"),
        ("PS-ALE", "PS-ALE"),
        ("PS-JAE", "PS-JAE"),
        ("PT-HYO", "PT-HYO"),
        ("PP-JBB", "PP-JBB"),
        ("PR-JJB", "PR-JJB"),
        ("PT-YUN", "PT-YUN"),
        ("PT-YTU", "PT-YTU"),
        ("PP-JUL", "PP-JUL"),
    ]

    nome = models.CharField("Nome do Produto", max_length=100)
    pn = models.CharField("P/N", max_length=50)
    sn = models.CharField("S/N", max_length=100, blank=True, null=True)
    quantidade = models.PositiveIntegerField("Quantidade", default=0)
    validade = models.DateField("Validade", null=True, blank=True)
    observacoes = models.TextField("Observações", blank=True, null=True)
    nome_responsavel = models.CharField("Nome do Responsável", max_length=100, blank=True, null=True)
    base = models.CharField("Base", max_length=50, choices=BASE_CHOICES, default="Base Principal")
    local = models.CharField("Local", max_length=100, blank=True, null=True)
    estoque_minimo = models.IntegerField(default=0)
    destino = models.CharField("Destino", max_length=100, choices=DESTINO_CHOICES, blank=True, null=True)

    class Meta:
        unique_together = ['pn', 'base']
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.pn}) - {self.base}"

    @property
    def em_alerta(self):
        return self.quantidade <= getattr(self, "estoque_minimo", 0)
class MovimentoEstoque(models.Model):
    ENTRADA = 'E'
    SAIDA = 'S'
    TIPO_CHOICES = [
        (ENTRADA, 'Entrada'),
        (SAIDA, 'Saída'),
    ]

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    tipo = models.CharField("Tipo", max_length=1, choices=TIPO_CHOICES)
    quantidade = models.PositiveIntegerField("Quantidade")
    data_movimento = models.DateTimeField("Data do Movimento", auto_now_add=True)
    validade = models.DateField("Validade", null=True, blank=True)
    local_guardado = models.CharField("Local onde está guardado", max_length=100, blank=True)
    destino = models.CharField("Destino", max_length=100, blank=True)
    observacoes = models.TextField("Observações", blank=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.tipo == self.ENTRADA:
                self.produto.quantidade += self.quantidade
            elif self.tipo == self.SAIDA:
                if self.produto.quantidade < self.quantidade:
                    raise ValueError("Quantidade insuficiente em estoque.")
                self.produto.quantidade -= self.quantidade
            self.produto.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.produto.nome} ({self.quantidade})'
    
class SolicitacaoMaterial(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_analise', 'Em Análise'),
        ('aprovado', 'Aprovado'),
    ]
    base = models.CharField("Base", max_length=50, blank=True, null=True)
    destino = models.CharField("Destino", max_length=100, blank=True, null=True)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, null=True, blank=True)
    nome_produto = models.CharField("Nome do Produto", max_length=100)
    pn = models.CharField("P/N", max_length=50)
    quantidade = models.PositiveIntegerField("Quantidade")
    destino = models.CharField("Destino", max_length=100, blank=True, null=True)
    observacao = models.TextField("Observação", blank=True, null=True)
    data_solicitacao = models.DateTimeField("Data da Solicitação", auto_now_add=True)

    solicitante = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitacoes_criadas'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitacoes_processadas'
    )

    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default='pendente')

    def __str__(self):
        return f"{self.nome_produto} - {self.quantidade} un - {self.status}"
