from django.contrib import admin
from django.contrib.admin import DateFieldListFilter
from .models import Produto, MovimentoEstoque

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'pn', 'quantidade', 'base', 'validade']
    list_filter = ['base']
    search_fields = ['nome', 'pn', 'sn']


@admin.register(MovimentoEstoque)
class MovimentoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['produto', 'tipo', 'quantidade', 'data_movimento', 'usuario']
    list_filter = ['tipo', ('data_movimento', DateFieldListFilter)]
    search_fields = ['produto__nome']
    readonly_fields = ['usuario']

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Só define o usuário na criação
            obj.usuario = request.user
        super().save_model(request, obj, form, change)
