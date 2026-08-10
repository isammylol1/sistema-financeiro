import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
from collections import defaultdict
from flask import Flask, render_template_string

app = Flask(__name__)

# O HTML fica guardado em uma variável string
HTML_TEMPLATE = '''
<html>
    <h1>Meu Site</h1>
    <p>Total: R$ {{ valor }}</p>  <!-- {{ }} é onde entra o Python -->
</html>
'''

@app.route('/')
def pagina_inicial():
    # Calcula os dados
    total = 1500.50
    
    # Renderiza o HTML com os dados Python
    return render_template_string(HTML_TEMPLATE, valor=total)



def inicializar_banco():
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    
    # Tabela de transações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL CHECK(tipo IN ('entrada', 'saida')),
            categoria TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Banco de dados financeiro inicializado com sucesso!")

def adicionar_entrada():
    print("\n--- REGISTRAR ENTRADA (DINHEIRO RECEBIDO) ---")
    
    descricao = input("Descrição (ex: Salário, Freelance): ")
    categoria = input("Categoria (ex: Trabalho, Investimento): ")
    
    try:
        valor = float(input("Valor recebido: R$ "))
        if valor <= 0:
            print("O valor deve ser positivo!")
            return
    except Exception as e:
        print(f"ERRO ao ler valor: {e}")
        print("Digite um valor numérico válido!")
        return
    
    print(f"\n🔍 DEBUG: Tentando salvar -> {descricao} | {categoria} | R${valor}")
    
    try:
        conn = sqlite3.connect('financas.db')
        cursor = conn.cursor()
        
        print("✅ Conexão aberta")
        
        cursor.execute('''
            INSERT INTO transacoes (tipo, categoria, descricao, valor)
            VALUES (?, ?, ?, ?)
        ''', ('entrada', categoria, descricao, valor))
        
        print(f"✅ INSERT executado, ID: {cursor.lastrowid}")
        
        conn.commit()
        print("✅ COMMIT realizado")
        
        # VERIFICAÇÃO IMEDIATA
        cursor.execute("SELECT * FROM transacoes WHERE id = ?", (cursor.lastrowid,))
        registro = cursor.fetchone()
        
        if registro:
            print(f"✅ CONFIRMADO: Dados salvos! {registro}")
        else:
            print("❌ ERRO: Dados NÃO encontrados após commit!")
        
        conn.close()
        print(f"✅ Entrada de R$ {valor:.2f} registrada: {descricao}")
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {type(e).__name__}: {e}")
        try:
            conn.close()
        except:
            pass

def adicionar_saida():
    print("\n--- REGISTRAR SAÍDA (DINHEIRO GASTO) ---")
    
    descricao = input("Descrição (ex: Aluguel, Mercado): ")
    categoria = input("Categoria (ex: Moradia, Alimentação): ")
    
    try:
        valor = float(input("Valor gasto: R$ "))
        if valor <= 0:
            print("O valor deve ser positivo!")
            return
    except Exception as e:
        print(f"ERRO ao ler valor: {e}")
        print("Digite um valor numérico válido!")
        return
    
    print(f"\n🔍 DEBUG: Tentando salvar -> {descricao} | {categoria} | R${valor}")
    
    try:
        conn = sqlite3.connect('financas.db')
        cursor = conn.cursor()
        
        print("✅ Conexão aberta")
        
        cursor.execute('''
            INSERT INTO transacoes (tipo, categoria, descricao, valor)
            VALUES (?, ?, ?, ?)
        ''', ('saida', categoria, descricao, valor))
        
        print(f"✅ INSERT executado, ID: {cursor.lastrowid}")
        
        conn.commit()
        print("✅ COMMIT realizado")
        
        # VERIFICAÇÃO IMEDIATA
        cursor.execute("SELECT * FROM transacoes WHERE id = ?", (cursor.lastrowid,))
        registro = cursor.fetchone()
        
        if registro:
            print(f"✅ CONFIRMADO: Dados salvos! {registro}")
        else:
            print("❌ ERRO: Dados NÃO encontrados após commit!")
        
        conn.close()
        print(f"✅ Saída de R$ {valor:.2f} registrada: {descricao}")
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {type(e).__name__}: {e}")
        try:
            conn.close()
        except:
            pass


def ver_resumo_mes():
    print("\n--- RESUMO DO MÊS ATUAL ---")
    
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    
    # Mês atual
    mes_atual = datetime.now().strftime('%Y-%m')
    
    # Total de entradas
    cursor.execute('''
        SELECT COALESCE(SUM(valor), 0) FROM transacoes 
        WHERE tipo = 'entrada' AND strftime('%Y-%m', data) = ?
    ''', (mes_atual,))
    total_entradas = cursor.fetchone()[0]
    
    # Total de saídas
    cursor.execute('''
        SELECT COALESCE(SUM(valor), 0) FROM transacoes 
        WHERE tipo = 'saida' AND strftime('%Y-%m', data) = ?
    ''', (mes_atual,))
    total_saidas = cursor.fetchone()[0]
    
    # Saldo do mês
    saldo_mes = total_entradas - total_saidas
    
    print("="*50)
    print(f"📊 RESUMO DE {datetime.now().strftime('%B/%Y').upper()}")
    print("="*50)
    print(f"💰 Total de Entradas:  R$ {total_entradas:>10.2f}")
    print(f"💸 Total de Saídas:    R$ {total_saidas:>10.2f}")
    print("-"*50)
    
    if saldo_mes >= 0:
        print(f"✅ SALDO POSITIVO:     R$ {saldo_mes:>10.2f}")
    else:
        print(f"🔴 DÉFICIT:           R$ {saldo_mes:>10.2f}")
    
    # Gastos por categoria
    print("\n📋 GASTOS POR CATEGORIA:")
    cursor.execute('''
        SELECT categoria, SUM(valor) FROM transacoes 
        WHERE tipo = 'saida' AND strftime('%Y-%m', data) = ?
        GROUP BY categoria ORDER BY SUM(valor) DESC
    ''', (mes_atual,))
    
    categorias = cursor.fetchall()
    for cat, valor in categorias:
        print(f"  {cat:<20} R$ {valor:>8.2f}")
    
    conn.close()

def consultar_mes_especifico():
    print("\n--- CONSULTAR MÊS ESPECÍFICO ---")
    print("Digite o mês no formato: MM/AAAA (ex: 03/2026)")
    
    mes_input = input("Mês: ")
    
    try:
        mes, ano = mes_input.split('/')
        mes_ano = f"{ano}-{mes}"
        datetime(int(ano), int(mes), 1)  # Validar data
    except:
        print("❌ Formato inválido! Use MM/AAAA")
        return
    
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    
    # Verificar se existem transações
    cursor.execute('''
        SELECT tipo, categoria, descricao, valor, data 
        FROM transacoes 
        WHERE strftime('%Y-%m', data) = ?
        ORDER BY data DESC
    ''', (mes_ano,))
    
    transacoes = cursor.fetchall()
    
    if not transacoes:
        print(f"📭 Nenhuma transação encontrada em {mes}/{ano}")
        conn.close()
        return
    
    print(f"\n📅 TRANSAÇÕES DE {mes}/{ano}")
    print("="*80)
    print(f"{'Data':<12} {'Tipo':<8} {'Categoria':<15} {'Descrição':<20} {'Valor':>10}")
    print("-"*80)
    
    total_entradas = 0
    total_saidas = 0
    
    for tipo, categoria, descricao, valor, data in transacoes:
        data_formatada = data[:10]
        tipo_icone = "💰" if tipo == 'entrada' else "💸"
        
        print(f"{data_formatada:<12} {tipo_icone} {tipo:<6} {categoria:<15} {descricao:<20} R$ {valor:>8.2f}")
        
        if tipo == 'entrada':
            total_entradas += valor
        else:
            total_saidas += valor
    
    print("-"*80)
    print(f"{'':>12} {'TOTAL ENTRADAS:':<35} R$ {total_entradas:>8.2f}")
    print(f"{'':>12} {'TOTAL SAÍDAS:':<35} R$ {total_saidas:>8.2f}")
    
    saldo = total_entradas - total_saidas
    if saldo >= 0:
        print(f"{'':>12} {'✅ SALDO:':<35} R$ {saldo:>8.2f}")
    else:
        print(f"{'':>12} {'🔴 DÉFICIT:':<35} R$ {saldo:>8.2f}")
    
    conn.close()

def mostrar_historico_meses():
    print("\n--- HISTÓRICO DE TODOS OS MESES ---")
    
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT strftime('%Y-%m', data) as mes,
               SUM(CASE WHEN tipo='entrada' THEN valor ELSE 0 END) as entradas,
               SUM(CASE WHEN tipo='saida' THEN valor ELSE 0 END) as saidas,
               SUM(CASE WHEN tipo='entrada' THEN valor ELSE -valor END) as saldo
        FROM transacoes
        GROUP BY mes
        ORDER BY mes DESC
    ''')
    
    meses = cursor.fetchall()
    
    if not meses:
        print("📭 Nenhum histórico disponível!")
        conn.close()
        return
    
    print("="*70)
    print(f"{'Mês':<12} {'Entradas':>12} {'Saídas':>12} {'Saldo':>12} {'Status':>10}")
    print("-"*70)
    
    for mes, entradas, saidas, saldo in meses:
        ano, mes_num = mes.split('-')
        status = "✅ POSITIVO" if saldo >= 0 else "🔴 DÉFICIT"
        
        print(f"{mes_num}/{ano:<7} R$ {entradas:>9.2f} R$ {saidas:>9.2f} R$ {saldo:>9.2f} {status}")
    
    # Total geral
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN tipo='entrada' THEN valor ELSE 0 END),
            SUM(CASE WHEN tipo='saida' THEN valor ELSE 0 END),
            SUM(CASE WHEN tipo='entrada' THEN valor ELSE -valor END)
        FROM transacoes
    ''')
    
    total_ent, total_said, total_geral = cursor.fetchone()
    
    print("-"*70)
    print(f"{'TOTAL GERAL':<12} R$ {total_ent:>9.2f} R$ {total_said:>9.2f} R$ {total_geral:>9.2f}")
    
    conn.close()

def mostrar_dashboard():
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    
    plt.style.use('default')
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('DASHBOARD FINANCEIRO', fontsize=16, fontweight='bold')
    
    # 1. Últimos 6 meses (Entradas vs Saídas)
    cursor.execute('''
        SELECT strftime('%Y-%m', data) as mes,
               SUM(CASE WHEN tipo='entrada' THEN valor ELSE 0 END),
               SUM(CASE WHEN tipo='saida' THEN valor ELSE 0 END)
        FROM transacoes
        GROUP BY mes
        ORDER BY mes DESC
        LIMIT 6
    ''')
    
    dados_meses = cursor.fetchall()
    if dados_meses:
        meses = [m[0] for m in reversed(dados_meses)]
        entradas = [m[1] for m in reversed(dados_meses)]
        saidas = [m[2] for m in reversed(dados_meses)]
        
        x = range(len(meses))
        axes[0, 0].bar([i - 0.2 for i in x], entradas, 0.4, label='Entradas', color='green', alpha=0.7)
        axes[0, 0].bar([i + 0.2 for i in x], saidas, 0.4, label='Saídas', color='red', alpha=0.7)
        axes[0, 0].set_xticks(x)
        axes[0, 0].set_xticklabels(meses, rotation=45)
        axes[0, 0].set_title('Últimos 6 Meses')
        axes[0, 0].legend()
        axes[0, 0].set_ylabel('Valor (R$)')
    
    # 2. Gastos por categoria (pizza)
    cursor.execute('''
        SELECT categoria, SUM(valor) FROM transacoes
        WHERE tipo = 'saida'
        GROUP BY categoria
        ORDER BY SUM(valor) DESC
        LIMIT 8
    ''')
    
    cats_gastos = cursor.fetchall()
    if cats_gastos:
        labels, valores = zip(*cats_gastos)
        axes[0, 1].pie(valores, labels=labels, autopct='%1.1f%%')
        axes[0, 1].set_title('Distribuição de Gastos')
    
    # 3. Evolução do saldo acumulado
    cursor.execute('''
        SELECT strftime('%Y-%m', data) as mes,
               SUM(CASE WHEN tipo='entrada' THEN valor ELSE -valor END)
        FROM transacoes
        GROUP BY mes
        ORDER BY mes
    ''')
    
    saldo_mensal = cursor.fetchall()
    if saldo_mensal:
        meses_saldo = [s[0] for s in saldo_mensal]
        saldos = [s[1] for s in saldo_mensal]
        
        # Calcular saldo acumulado
        saldo_acumulado = []
        acum = 0
        for s in saldos:
            acum += s
            saldo_acumulado.append(acum)
        
        axes[1, 0].plot(meses_saldo, saldo_acumulado, marker='o', linewidth=2, color='blue')
        axes[1, 0].set_title('Evolução do Saldo Acumulado')
        axes[1, 0].tick_params(axis='x', rotation=45)
        axes[1, 0].set_ylabel('Saldo (R$)')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Colorir área positiva/negativa
        axes[1, 0].fill_between(range(len(meses_saldo)), saldo_acumulado, 0, 
                                alpha=0.3, color=['green' if s >= 0 else 'red' for s in saldo_acumulado])
    
    # 4. Resumo rápido
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN tipo='entrada' THEN valor ELSE 0 END),
            SUM(CASE WHEN tipo='saida' THEN valor ELSE 0 END),
            COUNT(*)
        FROM transacoes
    ''')
    
    total_ent, total_said, total_trans = cursor.fetchone()
    saldo_total = total_ent - total_said
    
    axes[1, 1].axis('off')
    resumo_texto = f"""
    📊 RESUMO GERAL
    
    💰 Total Entradas:
    R$ {total_ent:,.2f}
    
    💸 Total Saídas:
    R$ {total_said:,.2f}
    
    {'✅' if saldo_total >= 0 else '🔴'} Saldo Total:
    R$ {saldo_total:,.2f}
    
    📝 Total Transações:
    {total_trans}
    """
    
    axes[1, 1].text(0.1, 0.5, resumo_texto, fontsize=12, verticalalignment='center',
                    family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.show()
    
    conn.close()

def excluir_transacao():
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM transacoes")
    total = cursor.fetchone()[0]
    
    if total == 0:
        print("❌ Não há transações cadastradas!")
        conn.close()
        return
    
    print("\n--- ÚLTIMAS 10 TRANSAÇÕES ---")
    cursor.execute('''
        SELECT id, tipo, categoria, descricao, valor, data 
        FROM transacoes 
        ORDER BY data DESC 
        LIMIT 10
    ''')
    
    transacoes = cursor.fetchall()
    
    for id_trans, tipo, cat, desc, valor, data in transacoes:
        icone = "💰" if tipo == 'entrada' else "💸"
        print(f"ID: {id_trans:<3} {icone} {data[:10]} - {desc:<20} R$ {valor:>8.2f} ({cat})")
    
    try:
        id_excluir = int(input("\nDigite o ID da transação para excluir: "))
    except:
        print("❌ ID inválido!")
        conn.close()
        return
    
    cursor.execute("SELECT * FROM transacoes WHERE id = ?", (id_excluir,))
    trans = cursor.fetchone()
    
    if trans:
        confirm = input(f"Tem certeza que deseja excluir '{trans[3]}' de R$ {trans[4]:.2f}? (s/n): ")
        if confirm.lower() == 's':
            cursor.execute("DELETE FROM transacoes WHERE id = ?", (id_excluir,))
            conn.commit()
            print("✅ Transação excluída com sucesso!")
        else:
            print("❌ Exclusão cancelada.")
    else:
        print("❌ Transação não encontrada!")
    
    conn.close()

def teste_rapido():
    """Função para testar se o banco está funcionando"""
    print("\n🧪 TESTE RÁPIDO DE GRAVAÇÃO")
    try:
        conn = sqlite3.connect('financas.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transacoes (tipo, categoria, descricao, valor)
            VALUES ('entrada', 'TESTE', 'Teste automático', 999.99)
        ''')
        conn.commit()
        
        cursor.execute("SELECT * FROM transacoes ORDER BY id DESC LIMIT 1")
        ultimo = cursor.fetchone()
        print(f"✅ Teste OK! Último registro: {ultimo}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Falha no teste: {e}")

def mostrar_menu():
    print("\n" + "="*50)
    print("     💰 SISTEMA FINANCEIRO PESSOAL")
    print("="*50)
    print("1. 💵 Registrar Entrada (dinheiro recebido)")
    print("2. 💳 Registrar Saída (dinheiro gasto)")
    print("3. 📊 Ver Resumo do Mês Atual")
    print("4. 📅 Consultar Mês Específico")
    print("5. 📈 Histórico de Todos os Meses")
    print("6. 📊 Dashboard Gráfico")
    print("7. 🗑️  Excluir Transação")
    print("8. 🚪 Sair do Programa")
    print("9. 🧪 Teste rápido de gravação")
    print("="*50)
    

if __name__ == "__main__":
    print("💵 Bem-vindo ao Sistema Financeiro Pessoal!")
    inicializar_banco()

    while True:
        mostrar_menu()
        
        opcao = input("\nEscolha uma opção (1-8): ")
        
        if opcao == "1":
            adicionar_entrada()
        elif opcao == "2":
            adicionar_saida()
        elif opcao == "3":
            ver_resumo_mes()
        elif opcao == "4":
            consultar_mes_especifico()
        elif opcao == "5":
            mostrar_historico_meses()
        elif opcao == "6":
            mostrar_dashboard()
        elif opcao == "7":
            excluir_transacao()
        elif opcao == "8":
            print("👋 Obrigado por usar o Sistema Financeiro. Até mais!")
            break
        elif opcao == "9":
            teste_rapido()
        else:
            print("❌ Opção inválida! Digite um número de 1 a 9.")
        