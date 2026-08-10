import sqlite3
import telebot
import os
import csv
from telebot import types
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

CHAVE_API = "8922995862:AAFeVwzm5J88i85X6CngtslQlkbuwdQfS_s"
bot = telebot.TeleBot(CHAVE_API)

# ==========================================
# BANCO DE DADOS E FUNÇÕES AUXILIARES
# ==========================================

def inicializar_banco():
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    
    # Tabela de transações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('entrada', 'saida')),
            categoria TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela para controlar quem já viu o tutorial
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    
    conn.commit()
    conn.close()

def verificar_primeiro_acesso(user_id):
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM usuarios WHERE user_id = ?', (user_id,))
    resultado = cursor.fetchone()
    
    if not resultado:
        # Se não existe, insere para ele não ver mais o tutorial completo
        cursor.execute('INSERT INTO usuarios (user_id) VALUES (?)', (user_id,))
        conn.commit()
        conn.close()
        return True # É o primeiro acesso!
    
    conn.close()
    return False

def obter_resumo_mes(user_id):
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    mes_atual = datetime.now().strftime('%Y-%m')

    cursor.execute('''
        SELECT COALESCE(SUM(valor), 0) FROM transacoes
        WHERE user_id = ? AND tipo = 'entrada' AND strftime('%Y-%m', data) = ?
    ''', (user_id, mes_atual))
    total_entradas = cursor.fetchone()[0]

    cursor.execute('''
        SELECT COALESCE(SUM(valor), 0) FROM transacoes
        WHERE user_id = ? AND tipo = 'saida' AND strftime('%Y-%m', data) = ?
    ''', (user_id, mes_atual))
    total_saidas = cursor.fetchone()[0]

    cursor.execute('''
        SELECT categoria, SUM(valor) FROM transacoes
        WHERE user_id = ? AND tipo = 'saida' AND strftime('%Y-%m', data) = ?
        GROUP BY categoria ORDER BY SUM(valor) DESC
    ''', (user_id, mes_atual))
    categorias = cursor.fetchall()

    conn.close()
    return total_entradas, total_saidas, categorias

def gerar_grafico_gastos(user_id):
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    mes_atual = datetime.now().strftime('%Y-%m')

    cursor.execute('''
        SELECT categoria, SUM(valor)
        FROM transacoes
        WHERE user_id = ? AND tipo = 'saida' AND strftime('%Y-%m', data) = ?
        GROUP BY categoria ORDER BY SUM(valor) DESC
    ''', (user_id, mes_atual))

    dados = cursor.fetchall()
    conn.close()

    if not dados:
        return None

    categorias = [item[0] for item in dados]
    valores = [item[1] for item in dados]

    cores = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#1A535C', '#FF9F1C', '#9B5DE5', '#F15BB5']

    plt.figure(figsize=(6, 6))
    plt.pie(
        valores,
        labels=categorias,
        autopct='%1.1f%%',
        startangle=140,
        colors=cores[:len(categorias)],
        wedgeprops={'edgecolor': 'white', 'linewidth': 2}
    )

    plt.title(f'Distribuição de Gastos ({datetime.now().strftime("%m/%Y")})', fontsize=12, fontweight='bold')
    plt.tight_layout()

    caminho_imagem = f"grafico_{user_id}.png"
    plt.savefig(caminho_imagem, dpi=120)
    plt.close()

    return caminho_imagem

def obter_mes_especifico(user_id, mes_ano):
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT tipo, categoria, descricao, valor, data
        FROM transacoes
        WHERE user_id = ? AND strftime('%Y-%m', data) = ?
        ORDER BY data DESC
    ''', (user_id, mes_ano))
    transacoes = cursor.fetchall()

    conn.close()
    return transacoes

def obter_historico_detalhado(user_id):
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT tipo, categoria, descricao, valor, data
        FROM transacoes
        WHERE user_id = ?
        ORDER BY data DESC
    ''', (user_id,))
    transacoes = cursor.fetchall()

    cursor.execute('''
        SELECT
            COALESCE(SUM(CASE WHEN tipo='entrada' THEN valor ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN tipo='saida' THEN valor ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN tipo='entrada' THEN valor ELSE -valor END), 0)
        FROM transacoes WHERE user_id = ?
    ''', (user_id,))
    total_geral = cursor.fetchone()

    conn.close()
    return transacoes, total_geral

def excluir_ultima(user_id):
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, tipo, descricao, valor FROM transacoes WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,)
    )
    ultima = cursor.fetchone()

    if ultima:
        cursor.execute("DELETE FROM transacoes WHERE id = ?", (ultima[0],))
        conn.commit()
        info = ultima
    else:
        info = None

    conn.close()
    return info

def gerar_arquivo_csv(user_id):
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, tipo, categoria, descricao, valor, data
        FROM transacoes
        WHERE user_id = ?
        ORDER BY data DESC
    ''', (user_id,))

    transacoes = cursor.fetchall()
    conn.close()

    if not transacoes:
        return None

    caminho_csv = f"relatorio_{user_id}.csv"

    with open(caminho_csv, mode='w', newline='', encoding='utf-8-sig') as arquivo:
        escritor = csv.writer(arquivo, delimiter=';')
        escritor.writerow(['ID', 'Tipo', 'Categoria', 'Descrição', 'Valor (R$)', 'Data/Hora'])

        for t in transacoes:
            valor_formatado = f"{t[4]:.2f}".replace('.', ',')
            escritor.writerow([t[0], t[1].capitalize(), t[2], t[3], valor_formatado, t[5]])

    return caminho_csv

# ==========================================
# MENUS E BOTÕES
# ==========================================

def criar_menu_principal():
    markup = types.InlineKeyboardMarkup(row_width=2)

    btn_nova_entrada = types.InlineKeyboardButton("➕ Nova Entrada", callback_data="btn_nova_entrada")
    btn_nova_saida = types.InlineKeyboardButton("➖ Nova Saída", callback_data="btn_nova_saida")
    btn_resumo = types.InlineKeyboardButton("📊 Resumo", callback_data="btn_resumo")
    btn_historico = types.InlineKeyboardButton("📈 Histórico", callback_data="btn_historico")
    btn_excluir = types.InlineKeyboardButton("🗑 Excluir Última", callback_data="btn_excluir")
    btn_exportar = types.InlineKeyboardButton("📥 Exportar CSV", callback_data="btn_exportar")

    markup.add(btn_nova_entrada, btn_nova_saida)
    markup.add(btn_resumo, btn_historico)
    markup.add(btn_excluir, btn_exportar)
    return markup

def criar_teclado_cancelar():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Cancelar / Menu", callback_data="btn_cancelar"))
    return markup


# ==========================================
# COMANDOS DO BOT
# ==========================================

dados_usuario = {}

@bot.message_handler(commands=['start', 'menu', 'help'])
def enviar_menu(mensagem):
    user_id = mensagem.chat.id
    
    if user_id in dados_usuario:
        del dados_usuario[user_id]

    # Verifica se é a primeira vez que a pessoa usa o bot
    primeiro_acesso = verificar_primeiro_acesso(user_id)

    if primeiro_acesso:
        tutorial = (
            "👋 *Olá! Seja muito bem-vindo(a) ao seu Controle Financeiro!*\n\n"
            "📖 *Como usar este bot (Guia Rápido):*\n"
            "Este bot serve para te ajudar a controlar todo o dinheiro que entra e sai de forma simples.\n\n"
            "• **➕ Nova Entrada:** Use para anotar dinheiro que você recebeu (Salário, Pix, Vendas).\n"
            "• **➖ Nova Saída:** Use para anotar seus gastos do dia a dia (Almercado, Contas, Uber).\n"
            "• **📊 Resumo:** Mostra o balanço do mês atual junto com um gráfico visual dos seus gastos.\n"
            "• **📈 Histórico:** Mostra a lista completa de tudo o que você já registrou.\n"
            "• **🗑 Excluir Última:** Apaga o último lançamento caso tenha errado.\n"
            "• **📥 Exportar CSV:** Baixa uma planilha com todos os seus dados.\n\n"
            "💡 *Dica:* Em qualquer momento do cadastro, se quiser voltar, basta clicar no botão de cancelar.\n\n"
            "Toque em uma das opções abaixo para começar:"
        )
        bot.send_message(user_id, tutorial, reply_markup=criar_menu_principal(), parse_mode="Markdown")
    else:
        texto = (
            "👋 *Olá novamente! O que deseja fazer hoje?*"
        )
        bot.send_message(user_id, texto, reply_markup=criar_menu_principal(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def tratar_cliques_botoes(call):
    bot.answer_callback_query(call.id)
    call.message.from_user = call.from_user
    user_id = call.message.chat.id

    if call.data == "btn_cancelar":
        if user_id in dados_usuario:
            del dados_usuario[user_id]
        bot.send_message(user_id, "❌ Operação cancelada com sucesso!", reply_markup=criar_menu_principal())
        return
    
    if user_id in dados_usuario:
        del dados_usuario[user_id]

    if call.data == "btn_nova_entrada":
        iniciar_cadastro_entrada(call.message)
    elif call.data == "btn_nova_saida":
        iniciar_cadastro_saida(call.message)
    elif call.data == "btn_resumo":
        mostrar_resumo(call.message)
    elif call.data == "btn_historico":
        mostrar_historico(call.message)
    elif call.data == "btn_excluir":
        excluir_ultima_transacao(call.message)
    elif call.data == "btn_exportar":
        exportar_dados_csv(call.message)

@bot.message_handler(commands=['entrada'])
def iniciar_cadastro_entrada(mensagem):
    user_id = mensagem.chat.id
    dados_usuario[user_id] = {'tipo': 'entrada'}

    msg = bot.send_message(
        user_id,
        "💰 *Nova Entrada*\n\nQual foi o *valor*? (Exemplo: `150` ou `150.50`)",
        parse_mode="Markdown",
        reply_markup=criar_teclado_cancelar()
    )
    bot.register_next_step_handler(msg, passo_valor_entrada)

def passo_valor_entrada(mensagem):
    user_id = mensagem.chat.id
    if mensagem.text and mensagem.text.startswith('/'):
        return

    texto = mensagem.text.replace(',', '.')

    try:
        valor = float(texto)
        dados_usuario[user_id]['valor'] = valor

        msg = bot.send_message(
            user_id,
            "🏷️ Qual a *categoria*? (Exemplo: Salário, Investimento, Pix)",
            parse_mode="Markdown",
            reply_markup=criar_teclado_cancelar()
        )
        bot.register_next_step_handler(msg, passo_categoria_entrada)
    except ValueError:
        msg = bot.send_message(
            user_id, 
            "⚠️ Por favor, digite apenas números válidos (ex: `50.00`). Tente novamente:",
            reply_markup=criar_teclado_cancelar()
        )
        bot.register_next_step_handler(msg, passo_valor_entrada)

def passo_categoria_entrada(mensagem):
    user_id = mensagem.chat.id
    dados_usuario[user_id]['categoria'] = mensagem.text.capitalize()

    msg = bot.send_message(
        user_id,
        "📝 Qual a *descrição*? (Exemplo: Salário do Mês)",
        parse_mode="Markdown",
        reply_markup=criar_teclado_cancelar()
    )
    bot.register_next_step_handler(msg, finalizar_cadastro)


# --- SAÍDA ---
@bot.message_handler(commands=['saida'])
def iniciar_cadastro_saida(mensagem):
    user_id = mensagem.chat.id
    dados_usuario[user_id] = {'tipo': 'saida'}

    msg = bot.send_message(
        user_id,
        "💸 *Nova Saída (Gasto)*\n\nQual foi o *valor*? (Exemplo: `45.90`)",
        parse_mode="Markdown",
        reply_markup=criar_teclado_cancelar()
    )
    bot.register_next_step_handler(msg, passo_valor_saida)

def passo_valor_saida(mensagem):
    user_id = mensagem.chat.id
    texto = mensagem.text.replace(',', '.')

    try:
        valor = float(texto)
        dados_usuario[user_id]['valor'] = valor

        msg = bot.send_message(
            user_id,
            "🏷️ Qual a *categoria*? (Exemplo: Alimentação, Mercado, Uber)",
            parse_mode="Markdown",
            reply_markup=criar_teclado_cancelar()
        )
        bot.register_next_step_handler(msg, passo_categoria_saida)
    except ValueError:
        msg = bot.send_message(
            user_id, 
            "⚠️ Por favor, digite apenas números válidos (ex: `45.90`). Tente novamente:",
            reply_markup=criar_teclado_cancelar()
        )
        bot.register_next_step_handler(msg, passo_valor_saida)

def passo_categoria_saida(mensagem):
    user_id = mensagem.chat.id
    dados_usuario[user_id]['categoria'] = mensagem.text.capitalize()

    msg = bot.send_message(
        user_id,
        "📝 Qual a *descrição*? (Exemplo: Almoço de domingo)",
        parse_mode="Markdown",
        reply_markup=criar_teclado_cancelar()
    )
    bot.register_next_step_handler(msg, finalizar_cadastro)


# --- FINALIZAÇÃO ---
def finalizar_cadastro(mensagem):
    user_id = mensagem.chat.id
    dados_usuario[user_id]['descricao'] = mensagem.text

    tipo = dados_usuario[user_id]['tipo']
    categoria = dados_usuario[user_id]['categoria']
    descricao = dados_usuario[user_id]['descricao']
    valor = dados_usuario[user_id]['valor']
    data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transacoes (user_id, tipo, categoria, descricao, valor, data)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, tipo, categoria, descricao, valor, data_atual))
    conn.commit()
    conn.close()

    emoji = "✅" if tipo == 'entrada' else "💸"
    titulo = "Entrada cadastrada!" if tipo == 'entrada' else "Saída cadastrada!"

    texto_sucesso = (
        f"{emoji} *{titulo}*\n\n"
        f"• *Tipo:* {tipo.capitalize()}\n"
        f"• *Categoria:* {categoria}\n"
        f"• *Descrição:* {descricao}\n"
        f"• *Valor:* R$ {valor:,.2f}"
    )

    bot.send_message(user_id, texto_sucesso, parse_mode="Markdown", reply_markup=criar_menu_principal())
    del dados_usuario[user_id]


# ------------------------------------------
# RELATÓRIOS E CONSULTAS
# ------------------------------------------

@bot.message_handler(commands=['resumo'])
def mostrar_resumo(mensagem):
    user_id = mensagem.from_user.id
    entradas, saidas, categorias = obter_resumo_mes(user_id)
    saldo = entradas - saidas
    meses_pt = {
        "01": "JANEIRO", "02": "FEVEREIRO", "03": "MARÇO", "04": "ABRIL",
        "05": "MAIO", "06": "JUNHO", "07": "JULHO", "08": "AGOSTO",
        "09": "SETEMBRO", "10": "OUTUBRO", "11": "NOVEMBRO", "12": "DEZEMBRO"
    }
    mes_atual_num = datetime.now().strftime('%m')
    ano_atual = datetime.now().strftime('%Y')
    mes_nome = f"{meses_pt[mes_atual_num]}/{ano_atual}"
    status = "✅ POSITIVO" if saldo >= 0 else "🔴 DÉFICIT"

    resposta = (
        f"📊 *RESUMO DE {mes_nome}*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Entradas: *R$ {entradas:,.2f}*\n"
        f"💸 Saídas:    *R$ {saidas:,.2f}*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💵 Saldo:     *R$ {saldo:,.2f}*\n"
        f"Status: {status}"
    )

    caminho_grafico = gerar_grafico_gastos(user_id)

    if caminho_grafico:
        with open(caminho_grafico, 'rb') as foto:
            bot.send_photo(mensagem.chat.id, foto, caption=resposta, parse_mode="Markdown")
        os.remove(caminho_grafico)
    else:
        bot.reply_to(mensagem, resposta, parse_mode="Markdown")


@bot.message_handler(commands=['mes'])
def consultar_mes(mensagem):
    try:
        user_id = mensagem.from_user.id
        texto = mensagem.text.replace('/mes', '').strip()
        mes, ano = texto.split('/')
        mes_ano = f"{ano}-{mes}"

        transacoes = obter_mes_especifico(user_id, mes_ano)

        if not transacoes:
            bot.reply_to(mensagem, f"📭 Nenhuma transação em {mes}/{ano}")
            return

        entradas = sum(t[3] for t in transacoes if t[0] == 'entrada')
        saidas = sum(t[3] for t in transacoes if t[0] == 'saida')
        saldo = entradas - saidas

        resposta = f"📅 *TRANSAÇÕES DE {mes}/{ano}*\n━━━━━━━━━━━━━━━━━━━\n"

        for tipo, cat, desc, val, data in transacoes[:15]:
            icone = "💰" if tipo == 'entrada' else "💸"
            resposta += f"{icone} R$ {val:,.2f} - {desc} ({cat})\n"

        resposta += (
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Entradas: *R$ {entradas:,.2f}*\n"
            f"💸 Saídas: *R$ {saidas:,.2f}*\n"
            f"{'✅' if saldo >= 0 else '🔴'} Saldo: *R$ {saldo:,.2f}*"
        )

        bot.reply_to(mensagem, resposta, parse_mode="Markdown")

    except:
        bot.reply_to(mensagem, "❌ *Formato inválido!*\nUse: `/mes MM/AAAA`\nEx: `/mes 03/2026`", parse_mode="Markdown")


@bot.message_handler(commands=['historico'])
def mostrar_historico(mensagem):
    user_id = mensagem.from_user.id
    transacoes, total_geral = obter_historico_detalhado(user_id)

    if not transacoes:
        bot.reply_to(mensagem, "📭 Nenhum histórico ainda!")
        return

    resposta = "📈 *HISTÓRICO COMPLETO*\n━━━━━━━━━━━━━━━━━━━\n"

    for tipo, categoria, descricao, valor, data in transacoes[:20]:
        icone = "💰" if tipo == 'entrada' else "💸"
        try:
            data_formatada = datetime.strptime(data, '%Y-%m-%d %H:%M:%S').strftime('%d/%m %H:%M')
        except:
            data_formatada = data[:10]
            
        resposta += f"{icone} *R$ {valor:,.2f}* - {descricao} ({categoria}) 📅 {data_formatada}\n"

    tot_ent, tot_said, tot_saldo = total_geral
    status_geral = "✅" if tot_saldo >= 0 else "🔴"
    
    resposta += (
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *TOTAL GERAL*\n"
        f"💰 Entradas: R$ {tot_ent:,.2f}\n"
        f"💸 Saídas: R$ {tot_said:,.2f}\n"
        f"{status_geral} Saldo Geral: R$ {tot_saldo:,.2f}"
    )

    bot.reply_to(mensagem, resposta, parse_mode="Markdown")


def excluir_ultima_transacao(mensagem):
    user_id = mensagem.chat.id
    removido = excluir_ultima(user_id)
    if removido:
        _, tipo, desc, val = removido
        bot.send_message(user_id, f"🗑️ Última transação apagada com sucesso!\n• {tipo.capitalize()}: R$ {val:,.2f} ({desc})", reply_markup=criar_menu_principal())
    else:
        bot.send_message(user_id, "📭 Você não tem transações para excluir.", reply_markup=criar_menu_principal())

def exportar_dados_csv(mensagem):
    user_id = mensagem.chat.id
    caminho = gerar_arquivo_csv(user_id)
    if caminho:
        with open(caminho, 'rb') as arquivo:
            bot.send_document(user_id, arquivo, caption="📥 Aqui está o seu relatório em CSV!")
        os.remove(caminho)
    else:
        bot.send_message(user_id, "📭 Nenhum dado encontrado para exportar.", reply_markup=criar_menu_principal())


# ==========================================
# INICIALIZAÇÃO DO BOT
# ==========================================
if __name__ == "__main__":
    inicializar_banco()
    print("🤖 Bot Financeiro rodando no Telegram...")
    bot.polling(none_stop=True)
