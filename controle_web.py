# Instale antes: pip install flask
# Execute: python controle_web.py
# Acesse: http://localhost:5000

from flask import Flask, render_template_string, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ==================== HTML DA PÁGINA PRINCIPAL ====================
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>💰 Financeiro Pessoal</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f5f5f5; }
        .card { border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .card-resumo { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h1 class="text-center mb-4">💰 Sistema Financeiro</h1>
        
        <!-- Cards de Resumo -->
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="card card-resumo p-3">
                    <h5>📥 Entradas</h5>
                    <h3>R$ {{ "%.2f"|format(entradas) }}</h3>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card bg-light p-3">
                    <h5>📤 Saídas</h5>
                    <h3>R$ {{ "%.2f"|format(saidas) }}</h3>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card {{ 'bg-success' if saldo >= 0 else 'bg-danger' }} text-white p-3">
                    <h5>{{ '✅ Superávit' if saldo >= 0 else '🔴 Déficit' }}</h5>
                    <h3>R$ {{ "%.2f"|format(saldo) }}</h3>
                </div>
            </div>
        </div>
        
        <!-- Botões de Ação -->
        <div class="d-flex gap-2 mb-4">
            <button class="btn btn-success btn-lg" data-bs-toggle="modal" data-bs-target="#modalEntrada">
                ➕ Nova Entrada
            </button>
            <button class="btn btn-danger btn-lg" data-bs-toggle="modal" data-bs-target="#modalSaida">
                ➖ Nova Saída
            </button>
            <a href="/historico" class="btn btn-info btn-lg">📈 Histórico</a>
        </div>
        
        <!-- Tabela de Transações -->
        <div class="card">
            <div class="card-header bg-dark text-white">
                <h5 class="mb-0">Últimas Transações</h5>
            </div>
            <div class="card-body">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Data</th>
                            <th>Tipo</th>
                            <th>Categoria</th>
                            <th>Descrição</th>
                            <th>Valor</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for t in transacoes %}
                        <tr>
                            <td>{{ t[5][:10] if t[5] else '' }}</td>
                            <td>
                                <span class="badge {{ 'bg-success' if t[1] == 'entrada' else 'bg-danger' }}">
                                    {{ '💰 Entrada' if t[1] == 'entrada' else '💸 Saída' }}
                                </span>
                            </td>
                            <td>{{ t[2] }}</td>
                            <td>{{ t[3] }}</td>
                            <td>R$ {{ "%.2f"|format(t[4]) }}</td>
                            <td>
                                <a href="/excluir/{{ t[0] }}" class="btn btn-sm btn-outline-danger" 
                                   onclick="return confirm('Excluir esta transação?')">
                                    🗑
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Modal Entrada -->
    <div class="modal fade" id="modalEntrada">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header bg-success text-white">
                    <h5 class="modal-title">💰 Nova Entrada</h5>
                </div>
                <form action="/adicionar/entrada" method="POST">
                    <div class="modal-body">
                        <input class="form-control mb-2" name="descricao" placeholder="Descrição" required>
                        <input class="form-control mb-2" name="categoria" placeholder="Categoria" required>
                        <input class="form-control mb-2" name="valor" placeholder="Valor (ex: 1500,50)" required>
                    </div>
                    <div class="modal-footer">
                        <button type="submit" class="btn btn-success">Salvar</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    
    <!-- Modal Saída -->
    <div class="modal fade" id="modalSaida">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header bg-danger text-white">
                    <h5 class="modal-title">💸 Nova Saída</h5>
                </div>
                <form action="/adicionar/saida" method="POST">
                    <div class="modal-body">
                        <input class="form-control mb-2" name="descricao" placeholder="Descrição" required>
                        <input class="form-control mb-2" name="categoria" placeholder="Categoria" required>
                        <input class="form-control mb-2" name="valor" placeholder="Valor (ex: 1500,50)" required>
                    </div>
                    <div class="modal-footer">
                        <button type="submit" class="btn btn-danger">Salvar</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

HISTORICO_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>📈 Histórico Financeiro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h1>📈 Histórico de Meses</h1>
        <table class="table table-hover">
            <thead>
                <tr>
                    <th>Mês</th>
                    <th>Entradas</th>
                    <th>Saídas</th>
                    <th>Saldo</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for m in meses %}
                <tr>
                    <td>{{ m[0] }}</td>
                    <td class="text-success">R$ {{ "%.2f"|format(m[1]) }}</td>
                    <td class="text-danger">R$ {{ "%.2f"|format(m[2]) }}</td>
                    <td>R$ {{ "%.2f"|format(m[3]) }}</td>
                    <td>{{ '✅' if m[3] >= 0 else '🔴' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <a href="/" class="btn btn-primary">⬅ Voltar</a>
    </div>
</body>
</html>
'''

# ==================== FUNÇÕES AUXILIARES ====================
def converter_valor(texto):
    return float(texto.replace(',', '.'))

def criar_banco():
    conn = sqlite3.connect('financas.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS transacoes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tipo TEXT, categoria TEXT, descricao TEXT,
                  valor REAL, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()

# ==================== ROTAS DO SITE ====================
@app.route('/')
def index():
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    
    mes_atual = datetime.now().strftime('%Y-%m')
    
    cursor.execute("SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='entrada' AND strftime('%Y-%m', data)=?", (mes_atual,))
    entradas = cursor.fetchone()[0]
    
    cursor.execute("SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='saida' AND strftime('%Y-%m', data)=?", (mes_atual,))
    saidas = cursor.fetchone()[0]
    
    cursor.execute("SELECT * FROM transacoes ORDER BY data DESC LIMIT 20")
    transacoes = cursor.fetchall()
    
    conn.close()
    
    return render_template_string(HTML, 
                                entradas=entradas,
                                saidas=saidas,
                                saldo=entradas-saidas,
                                transacoes=transacoes)

@app.route('/adicionar/<tipo>', methods=['POST'])
def adicionar(tipo):
    descricao = request.form['descricao']
    categoria = request.form['categoria']
    valor = converter_valor(request.form['valor'])
    
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO transacoes (tipo, categoria, descricao, valor) VALUES (?, ?, ?, ?)',
                  (tipo, categoria, descricao, valor))
    conn.commit()
    conn.close()
    
    return redirect('/')

@app.route('/excluir/<int:id>')
def excluir(id):
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transacoes WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/historico')
def historico():
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT strftime('%m/%Y', data) as mes,
               SUM(CASE WHEN tipo='entrada' THEN valor ELSE 0 END),
               SUM(CASE WHEN tipo='saida' THEN valor ELSE 0 END),
               SUM(CASE WHEN tipo='entrada' THEN valor ELSE -valor END)
        FROM transacoes
        GROUP BY mes ORDER BY mes DESC
    ''')
    
    meses = cursor.fetchall()
    conn.close()
    
    return render_template_string(HISTORICO_HTML, meses=meses)

# ==================== INICIAR SERVIDOR ====================
if __name__ == '__main__':
    criar_banco()
    print("="*50)
    print("🌐 Servidor rodando!")
    print("📱 Acesse: http://localhost:5000")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=5000)
