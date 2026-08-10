import sqlite3
import telebot
from datetime import datetime

CHAVE_API = "tokendotelegram"  
bot = telebot.TeleBot(CHAVE_API)

def inicializar_banco():
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()

def adicionar_registro(user_id, tipo, categoria, descricao, valor):
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transacoes (user_id, tipo, categoria, descricao, valor)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, tipo, categoria, descricao, valor))
    conn.commit()
    conn.close()

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

    # Gastos por categoria
    cursor.execute('''
        SELECT categoria, SUM(valor) FROM transacoes 
        WHERE user_id = ? AND tipo = 'saida' AND strftime('%Y-%m', data) = ?
        GROUP BY categoria ORDER BY SUM(valor) DESC
    ''', (user_id, mes_atual))
    categorias = cursor.fetchall()

    conn.close()
    return total_entradas, total_saidas, categorias

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

def obter_historico(user_id):
    conn = sqlite3.connect('financas.db')
def obter_historico(user_id):
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT strftime('%Y-%m', data) as mes,
               SUM(CASE WHEN tipo='entrada' THEN valor ELSE 0 END),
               SUM(CASE WHEN tipo='saida' THEN valor ELSE 0 END),
               SUM(CASE WHEN tipo='entrada' THEN valor ELSE -valor END)
        FROM transacoes WHERE user_id = ?
        GROUP BY mes ORDER BY mes DESC LIMIT 12
    ''', (user_id,))
    meses = cursor.fetchall()

    # Total geral
    cursor.execute('''
        SELECT 
            COALESCE(SUM(CASE WHEN tipo='entrada' THEN valor ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN tipo='saida' THEN valor ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN tipo='entrada' THEN valor ELSE -valor END), 0)
        FROM transacoes WHERE user_id = ?
    ''', (user_id,))
    total_geral = cursor.fetchone()

    conn.close()
    return meses, total_geral

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

# ==========================================
# COMANDOS DO BOT
# ==========================================

@bot.message_handler(commands=['start', 'help'])
def enviar_boas_vindas(mensagem):
    texto = (
        "💰 *Bem-vindo ao seu Controle Financeiro!*\n\n"
        "📥 *Registrar:*\n"
        "• `/entrada Categoria Descricao Valor`\n"
        "  _Ex: /entrada Trabalho Salario 2500_\n"
        "• `/saida Categoria Descricao Valor`\n"
        "  _Ex: /saida Alimentacao Mercado 150.50_\n\n"
        "📊 *Consultar:*\n"
        "• `/resumo` - Mês atual\n"
        "• `/mes MM/AAAA` - Mês específico\n"
        "  _Ex: /mes 03/2026_\n"
        "• `/historico` - Todos os meses\n\n"
        "🗑 *Corrigir:*\n"
        "• `/excluir` - Remove última transação"
    )
    bot.reply_to(mensagem, texto, parse_mode="Markdown")

@bot.message_handler(commands=['entrada'])
def cadastrar_entrada(mensagem):
    try:
        partes = mensagem.text.split(maxsplit=3)
        categoria = partes[1]
        descricao = partes[2]
        valor = float(partes[3].replace(',', '.'))

        user_id = mensagem.from_user.id
        adicionar_registro(user_id, 'entrada', categoria, descricao, valor)
        bot.reply_to(mensagem, f"✅ Entrada registrada!\n💰 *R$ {valor:,.2f}* - {descricao} ({categoria})", parse_mode="Markdown")
    except (IndexError, ValueError):
        bot.reply_to(mensagem, "❌ *Formato inválido!*\nUse: `/entrada Categoria Descricao Valor`\nEx: `/entrada Trabalho Salario 1500,00`", parse_mode="Markdown")

@bot.message_handler(commands=['saida'])
def cadastrar_saida(mensagem):
    try:
        partes = mensagem.text.split(maxsplit=3)
        categoria = partes[1]
        descricao = partes[2]
        valor = float(partes[3].replace(',', '.'))

        user_id = mensagem.from_user.id
        adicionar_registro(user_id, 'saida', categoria, descricao, valor)
        bot.reply_to(mensagem, f"💸 Saída registrada!\n🔴 *R$ {valor:,.2f}* - {descricao} ({categoria})", parse_mode="Markdown")
    except (IndexError, ValueError):
        bot.reply_to(mensagem, "❌ *Formato inválido!*\nUse: `/saida Categoria Descricao Valor`\nEx: `/saida Alimentacao Almoco 35,50`", parse_mode="Markdown")

@bot.message_handler(commands=['resumo'])
def mostrar_resumo(mensagem):
    user_id = mensagem.from_user.id
    entradas, saidas, categorias = obter_resumo_mes(user_id)
    saldo = entradas - saidas

    mes_nome = datetime.now().strftime('%B/%Y').upper()
    status = "✅ POSITIVO" if saldo >= 0 else "🔴 DÉFICIT"

    resposta = (
        f"📊 *RESUMO DE {mes_nome}*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Entradas: *R$ {entradas:,.2f}*\n"
        f"💸 Saídas:   *R$ {saidas:,.2f}*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💵 Saldo:    *R$ {saldo:,.2f}*\n"
        f"Status: {status}"
    )

    if categorias:
        resposta += "\n\n📋 *Gastos por Categoria:*\n"
        for cat, val in categorias:
            resposta += f"  • {cat}: R$ {val:,.2f}\n"

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
    meses, total_geral = obter_historico(user_id)

    if not meses:
        bot.reply_to(mensagem, "📭 Nenhum histórico ainda!")
        return

    resposta = "📈 *HISTÓRICO DE MESES*\n━━━━━━━━━━━━━━━━━━━\n"

    for mes, ent, said, saldo in meses:
        ano, mes_num = mes.split('-')
        status = "✅" if saldo >= 0 else "🔴"
        resposta += f"{status} {mes_num}/{ano}: +R${ent:,.2f} | -R${said:,.2f} | =R${saldo:,.2f}\n"

    if total_geral:
        resposta += (
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *TOTAL GERAL*\n"
            f"Entradas: R$ {total_geral[0]:,.2f}\n"
            f"Saídas: R$ {total_geral[1]:,.2f}\n"
            f"Saldo: *R$ {total_geral[2]:,.2f}*"
        )

    bot.reply_to(mensagem, resposta, parse_mode="Markdown")

@bot.message_handler(commands=['excluir'])
def excluir_ultima_transacao(mensagem):
    user_id = mensagem.from_user.id
    info = excluir_ultima(user_id)

    if info:
        id_trans, tipo, desc, valor = info
        icone = "💰" if tipo == 'entrada' else "💸"
        bot.reply_to(mensagem, f"🗑 *Excluído:* {icone} R$ {valor:,.2f} - {desc}", parse_mode="Markdown")
    else:
        bot.reply_to(mensagem, "📭 Nenhuma transação para excluir!")

# Inicialização
if __name__ == "__main__":
    inicializar_banco()
    print("🤖 Bot Financeiro rodando no Telegram...")
    bot.polling()
