#!/usr/bin/env python3
"""
Script para inicializar/recriar o banco de dados SQLite local
"""
import sqlite3
import os

# Aponta para o banco de dados na raiz do projeto (diretório pai)
DATABASE_FILE = os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db')

def criar_tabela_jovens_rotas():
    """Cria a tabela principal jovens_rotas com todas as colunas necessárias"""
    conexao = sqlite3.connect(DATABASE_FILE)
    cursor = conexao.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jovens_rotas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE NOT NULL,
            cep_casa TEXT,
            cep_trabalho TEXT,
            matricula TEXT,
            status_rota TEXT DEFAULT 'Otimizado',
            email TEXT,
            celular TEXT,
            numero_casa TEXT,
            coordenadas TEXT,
            data_consulta TEXT,
            sla_segundos REAL,
            assinatura_path TEXT,
            assinatura_data TEXT,
            assinatura_ip TEXT
        )
    ''')
    
    conexao.commit()
    conexao.close()
    print("✅ Tabela 'jovens_rotas' criada com sucesso")

def criar_tabela_contestacoes():
    """Cria a tabela de contestações"""
    conexao = sqlite3.connect(DATABASE_FILE)
    cursor = conexao.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contestacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_jovem TEXT,
            cidade_residencia TEXT,
            cidade_trabalho TEXT,
            motivo TEXT,
            data_geracao TEXT,
            status TEXT DEFAULT 'Pendente',
            tratativa TEXT
        )
    ''')
    
    conexao.commit()
    conexao.close()
    print("✅ Tabela 'contestacoes' criada com sucesso")

def criar_tabela_tokens():
    """Cria a tabela de tokens de assinatura"""
    conexao = sqlite3.connect(DATABASE_FILE)
    cursor = conexao.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens_assinatura (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            consulta_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER DEFAULT 0,
            used_at TEXT
        )
    ''')
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_token ON tokens_assinatura(token)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_consulta_id ON tokens_assinatura(consulta_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON tokens_assinatura(expires_at)")
    
    conexao.commit()
    conexao.close()
    print("✅ Tabela 'tokens_assinatura' criada com sucesso")

def verificar_tabelas():
    """Verifica quais tabelas existem no banco"""
    conexao = sqlite3.connect(DATABASE_FILE)
    cursor = conexao.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tabelas = cursor.fetchall()
    conexao.close()
    
    print("\n📋 Tabelas existentes no banco:")
    for tabela in tabelas:
        if tabela[0] != 'sqlite_sequence':
            print(f"   ✓ {tabela[0]}")
    
    return [t[0] for t in tabelas]

if __name__ == "__main__":
    print("🔧 Inicializando banco de dados SQLite local...")
    print(f"📁 Arquivo: {DATABASE_FILE}\n")
    
    # Cria todas as tabelas
    criar_tabela_jovens_rotas()
    criar_tabela_contestacoes()
    criar_tabela_tokens()
    
    # Verifica o resultado
    tabelas = verificar_tabelas()
    
    print(f"\n✅ Banco de dados inicializado com sucesso!")
    print(f"📊 Total de tabelas: {len([t for t in tabelas if t != 'sqlite_sequence'])}")
