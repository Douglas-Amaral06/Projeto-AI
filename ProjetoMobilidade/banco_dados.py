import sqlite3
import pandas as pd
import datetime

def carregar_dados():
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    df = pd.read_sql_query("SELECT * FROM jovens_rotas", conexao)
    conexao.close()
    return df

def inserir_novo_jovem(nome, cpf, cep_casa, cep_trabalho, matricula):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    status_rota = "Otimizado"
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota))
    conexao.commit()
    conexao.close()

def cpf_ja_existe(cpf):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    cursor.execute("SELECT COUNT(*) FROM jovens_rotas WHERE cpf = ?", (cpf,))
    resultado = cursor.fetchone()[0]
    conexao.close()
    return resultado > 0

def excluir_jovem(id_jovem):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM jovens_rotas WHERE id = ?", (id_jovem,))
    conexao.commit()
    conexao.close()

def atualizar_banco_geral():
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    colunas_novas = [
        ("data_consulta", "TEXT"), ("sla_segundos", "REAL"), ("matricula", "TEXT"),
        ("status_rota", "TEXT DEFAULT 'Otimizado'"), ("email", "TEXT"),
        ("celular", "TEXT"), ("numero_casa", "TEXT"), ("coordenadas", "TEXT")
    ]
    for coluna, tipo in colunas_novas:
        try:
            cursor.execute(f"ALTER TABLE jovens_rotas ADD COLUMN {coluna} {tipo}")
        except sqlite3.OperationalError:
            pass
    cursor.execute("UPDATE jovens_rotas SET status_rota = 'Otimizado' WHERE status_rota IS NULL")
    conexao.commit()
    conexao.close()

def atualizar_dados_funcionario(id_jovem, matricula, email, celular, cep, numero, coordenadas):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    cursor.execute('''
        UPDATE jovens_rotas 
        SET matricula = ?, email = ?, celular = ?, cep_casa = ?, numero_casa = ?, coordenadas = ?
        WHERE id = ?
    ''', (matricula, email, celular, cep, numero, coordenadas, id_jovem))
    conexao.commit()
    conexao.close()

def obter_dados_dashboard():
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    mes_ano_atual = datetime.datetime.now().strftime("%Y-%m")
    cursor.execute("SELECT COUNT(DISTINCT id), AVG(sla_segundos) FROM jovens_rotas WHERE data_consulta LIKE ?", (f"{mes_ano_atual}%",))
    resultado = cursor.fetchone()
    conexao.close()
    return (resultado[0] if resultado[0] else 0), (resultado[1] if resultado[1] else 0.0)

def atualizar_banco_para_contestacoes():
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contestacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome_jovem TEXT, cidade_residencia TEXT,
            cidade_trabalho TEXT, motivo TEXT, data_geracao TEXT, status TEXT DEFAULT 'Pendente', tratativa TEXT
        )
    ''')
    try:
        cursor.execute("ALTER TABLE contestacoes ADD COLUMN status TEXT DEFAULT 'Pendente'")
        cursor.execute("ALTER TABLE contestacoes ADD COLUMN tratativa TEXT")
    except sqlite3.OperationalError:
        pass
    conexao.commit()
    conexao.close()

def resolver_contestacao(id_contestacao, tratativa):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    cursor.execute("UPDATE contestacoes SET status = 'Resolvido', tratativa = ? WHERE id = ?", (tratativa, id_contestacao))
    conexao.commit()
    conexao.close()

def registrar_contestacao(nome, cid_res, cid_trab, motivo):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    data_atual = datetime.datetime.now().strftime("%d/%m/%Y às %Hh%Mm")
    cursor.execute('''
        INSERT INTO contestacoes (nome_jovem, cidade_residencia, cidade_trabalho, motivo, data_geracao)
        VALUES (?, ?, ?, ?, ?)
    ''', (nome, cid_res, cid_trab, motivo, data_atual))
    conexao.commit()
    conexao.close()