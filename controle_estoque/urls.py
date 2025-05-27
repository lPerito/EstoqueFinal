from django.contrib import admin
from django.urls import path
from estoque import views
from estoque.views import alerta_estoque_minimo

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Autenticação
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Página inicial
    path('', views.pagina_inicial, name='pagina_inicial'),

    # Consulta geral e por base via slug
    path('consulta/', views.consulta_estoque, name='consulta_estoque'),
    path('estoque/<str:nome_base_slug>/', views.consulta_por_base, name='consulta_por_base'),

    # Saída de estoque

    path('saida-estoque/', views.saida_estoque, name='saida_estoque'),


    # Cadastro de produto
    path('produtos/novo/', views.cadastrar_produto, name='cadastrar_produto'),

    # Importação de planilha Excel
    path('importar-produtos/', views.importar_produtos, name='importar_produtos'),

    # Histórico por produto e geral
    path('produto/<int:produto_id>/historico/', views.historico_produto, name='historico_produto'),
    path('historico-movimentacoes/', views.historico_movimentacoes, name='historico_movimentacoes'),

    # Exportações
    path('exportar/pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('exportar/csv/', views.exportar_csv, name='exportar_csv'),

    # Backup
    path('backup/', views.backup_dados, name='backup_dados'),

    # Solicitações de material
    path('solicitar/', views.solicitar_material, name='solicitar_material'),
    path('solicitacoes/pendentes/', views.solicitacoes_pendentes, name='solicitacoes_pendentes'),

    # Alerta de estoque mínimo
    path('alerta-estoque/', alerta_estoque_minimo, name='alerta_estoque'),
]
