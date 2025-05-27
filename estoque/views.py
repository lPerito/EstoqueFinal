from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import HttpResponse
from django.db.models import F, Q
from django.core import serializers
import csv
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.utils.dateparse import parse_date

from .models import Produto, MovimentoEstoque, SolicitacaoMaterial
from .forms import (
    MovimentoEstoqueForm,
    SolicitacaoMaterialForm,
    ProdutoForm,
    ImportarProdutosForm,
)

def grupo_permitido(grupos):
    def check(user):
        return user.is_authenticated and user.groups.filter(name__in=grupos).exists()
    return user_passes_test(check, login_url='login')

def pagina_inicial(request):
    return render(request, 'estoque/pagina_inicial.html', {'home': True})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('pagina_inicial')
    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.POST.get('next') or '/'
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('pagina_inicial')
        messages.error(request, 'Usuário ou senha inválidos.')
    return render(request, 'estoque/login.html', {'next': next_url})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    produtos = Produto.objects.all()
    produtos_alerta = [p for p in produtos if p.em_alerta]
    return render(request, 'estoque/dashboard.html', {
        'produtos': produtos,
        'produtos_alerta': produtos_alerta,
    })

@grupo_permitido(['admin', 'estoquista'])
def cadastrar_produto(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            pn = form.cleaned_data['pn']
            base = form.cleaned_data['base']
            if Produto.objects.filter(pn=pn, base=base).exists():
                messages.error(request, f"O produto com P/N '{pn}' já existe na base {base}.")
            else:
                produto = form.save(commit=False)
                quantidade_inicial = produto.quantidade
                produto.quantidade = 0
                produto.save()
                MovimentoEstoque.objects.create(
                    produto=produto,
                    tipo=MovimentoEstoque.ENTRADA,
                    quantidade=quantidade_inicial,
                    usuario=request.user,
                    observacoes="Entrada automática no cadastro de produto.",
                )
                produto.quantidade = quantidade_inicial
                produto.save()
                messages.success(request, 'Produto cadastrado com sucesso.')
                return redirect('consulta_estoque')
    else:
        form = ProdutoForm()
    return render(request, 'estoque/cadastrar_produto.html', {'form': form})

@login_required
def historico_movimentacoes(request):
    movimentos = MovimentoEstoque.objects.all().order_by('-data_movimento')
    return render(request, 'estoque/historico_movimentacoes.html', {'movimentos': movimentos})

@grupo_permitido(['admin', 'estoquista'])
def saida_estoque(request):
    produtos = Produto.objects.all().order_by('nome')
    if request.method == 'POST':
        produto_id = request.POST.get('produto_id')
        remover_total = request.POST.get('remover_total') == '1'
        quantidade = int(request.POST.get('quantidade', 0))
        produto = get_object_or_404(Produto, id=produto_id)

        if remover_total:
            MovimentoEstoque.objects.create(
                produto=produto,
                tipo=MovimentoEstoque.SAIDA,
                quantidade=produto.quantidade,
                usuario=request.user,
                observacoes="Remoção total do produto",
            )
            produto.delete()
            messages.success(request, 'Produto removido totalmente do estoque.')
        elif 0 < quantidade <= produto.quantidade:
            MovimentoEstoque.objects.create(
                produto=produto,
                tipo=MovimentoEstoque.SAIDA,
                quantidade=quantidade,
                usuario=request.user,
                observacoes="Saída registrada manualmente",
            )
            produto.quantidade -= quantidade
            produto.save()
            messages.success(request, f"{quantidade} unidade(s) removida(s).")
        else:
            messages.error(request, 'Quantidade inválida.')
        return redirect('saida_estoque')
    return render(request, 'estoque/saida_estoque.html', {'produtos': produtos})

@login_required
def consulta_estoque(request, base_forcada=None):
    bases = [
        'Base Principal', 'Base Porto Velho', 'Base Parintins', 'Base Santarém',
        'Base Macapá', 'Base Marabá', 'Base Manaus', 'Sala 0316', 'Sala 2320', 'Sala 2322',
    ]
    base_sel = base_forcada or request.GET.get('base', '').strip()
    busca = request.GET.get('q', '').strip()

    produtos = Produto.objects.all()
    if base_sel:
        produtos = produtos.filter(base__iexact=base_sel)
    if busca:
        produtos = produtos.filter(Q(nome__icontains=busca) | Q(pn__icontains=busca) | Q(sn__icontains=busca))

    return render(request, 'estoque/consulta_estoque.html', {
        'produtos': produtos,
        'bases': bases,
        'base': base_sel or None,
        'busca': busca,
        'base_fixa': base_forcada is not None,
    })

@login_required
def consulta_por_base(request, nome_base_slug):
    slug_map = {
        'base-principal': 'Base Principal',
        'base-porto-velho': 'Base Porto Velho',
        'base-parintins': 'Base Parintins',
        'base-santarem': 'Base Santarém',
        'base-macapa': 'Base Macapá',
        'base-maraba': 'Base Marabá',
        'base-manaus': 'Base Manaus',
        'sala-0316': 'Sala 0316',
        'sala-2320': 'Sala 2320',
        'sala-2322': 'Sala 2322',
    }
    nome_base = slug_map.get(nome_base_slug.lower())
    if not nome_base:
        return redirect('consulta_estoque')
    return consulta_estoque(request, base_forcada=nome_base)

@login_required
def historico_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    movimentos = MovimentoEstoque.objects.filter(produto=produto).order_by('-data_movimento')
    return render(request, 'estoque/historico_produto.html', {'produto': produto, 'movimentos': movimentos})

@login_required
def exportar_pdf(request):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.setFont('Helvetica', 12)
    y = 800
    p.drawString(100, y, 'Relatório de Estoque')
    y -= 30
    for prod in Produto.objects.all():
        p.drawString(80, y, f"{prod.nome} - PN: {prod.pn} - Qtde: {prod.quantidade}")
        y -= 20
        if y < 50:
            p.showPage(); p.setFont('Helvetica', 12); y = 800
    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

@login_required
def exportar_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="relatorio_estoque.csv"'
    writer = csv.writer(response)
    writer.writerow(['Nome', 'PN', 'Quantidade', 'Base', 'Validade'])
    for p in Produto.objects.all():
        writer.writerow([p.nome, p.pn, p.quantidade, p.base, p.validade])
    return response

@login_required
def backup_dados(request):
    data = serializers.serialize("json", Produto.objects.all())
    response = HttpResponse(data, content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename=backup_produtos.json'
    return response

@login_required
def solicitar_material(request):
    if request.method == 'POST':
        form = SolicitacaoMaterialForm(request.POST)
        if form.is_valid():
            solicitacao = form.save(commit=False)
            solicitacao.solicitante = request.user
            solicitacao.base = request.POST.get('base')
            solicitacao.destino = request.POST.get('destino')
            solicitacao.save()
            messages.success(request, 'Solicitação registrada com sucesso.')
            return redirect('solicitar_material')
    else:
        form = SolicitacaoMaterialForm()
    return render(request, 'estoque/solicitar_material.html', {'form': form})

@grupo_permitido(['admin', 'estoquista'])
def solicitacoes_pendentes(request):
    if request.method == 'POST':
        solicitacao_id = request.POST.get('solicitacao_id')
        if 'delete' in request.POST:
            try:
                SolicitacaoMaterial.objects.get(id=solicitacao_id).delete()
                messages.success(request, 'Solicitação removida com sucesso.')
            except SolicitacaoMaterial.DoesNotExist:
                messages.error(request, 'Solicitação não encontrada.')
        else:
            novo_status = request.POST.get('status')
            try:
                solicitacao = SolicitacaoMaterial.objects.get(id=solicitacao_id)
                solicitacao.status = novo_status
                solicitacao.save()
                messages.success(request, f'Status atualizado para "{novo_status}".')
            except SolicitacaoMaterial.DoesNotExist:
                messages.error(request, 'Solicitação não encontrada.')
        return redirect('solicitacoes_pendentes')
    solicitacoes = SolicitacaoMaterial.objects.all().order_by('-data_solicitacao')
    return render(request, 'estoque/solicitacoes_pendentes.html', {'solicitacoes': solicitacoes})

@grupo_permitido(['admin', 'estoquista'])
@login_required
def alerta_estoque_minimo(request):
    produtos_alerta = Produto.objects.filter(quantidade__lt=F('estoque_minimo'))
    return render(request, 'estoque/alerta_estoque.html', {'produtos_alerta': produtos_alerta})

@grupo_permitido(['admin', 'estoquista'])
@login_required
def importar_produtos(request):
    if request.method == 'POST':
        form = ImportarProdutosForm(request.POST, request.FILES)
        if form.is_valid():
            import pandas as pd
            import traceback
            try:
                arquivo = request.FILES['arquivo']
                df = pd.read_excel(arquivo)
                df.columns = df.columns.str.strip()
                colunas_necessarias = ['Descrição', 'PNR', 'QTD']
                for coluna in colunas_necessarias:
                    if coluna not in df.columns:
                        messages.error(request, f"Coluna obrigatória '{coluna}' não encontrada.")
                        return render(request, 'estoque/importar_produtos.html', {'form': form})
                for _, row in df.iterrows():
                    try:
                        Produto.objects.create(
                            nome=row['Descrição'],
                            pn=row['PNR'],
                            quantidade=int(row['QTD']),
                            base=row.get('Base', 'Base Principal'),
                            local=row.get('Local', ''),
                            validade=parse_date(str(row.get('validade'))) if row.get('validade') else None,
                            observacoes=row.get('Observações', '')
                        )
                    except Exception as e:
                        messages.error(request, f"Erro ao importar linha: {row.to_dict()} - {e}")
                        traceback.print_exc()
                messages.success(request, "Importação concluída com sucesso.")
                return redirect('consulta_estoque')
            except Exception as e:
                messages.error(request, f"Erro ao processar o arquivo: {e}")
                traceback.print_exc()
    else:
        form = ImportarProdutosForm()
    return render(request, 'estoque/importar_produtos.html', {'form': form})
