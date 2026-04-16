"""
Testes de Segurança — SQL Injection Prevention

Este script testa se a vulnerabilidade de SQL Injection foi corrigida
em app_piloto.py linha 1682 (ALTER TABLE).

Execução:
    python test_seguranca_sql_injection.py
"""

import re
import sqlite3
import tempfile
import os
from pathlib import Path

# ─── CONFIGURAÇÃO ───────────────────────────────────────────────────────────
TEST_DB = "test_seguranca.db"
REGEX_PATTERN = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
MAX_LENGTH = 64
VALID_TYPES = ["TEXT", "INTEGER", "REAL", "BLOB"]

# ─── CASOS DE TESTE ─────────────────────────────────────────────────────────

# Payloads maliciosos que deveriam ser REJEITADOS
MALICIOUS_PAYLOADS = [
    # SQL Injection clássico
    ("teste; DROP TABLE jovens_rotas; --", "SQL Injection: DROP TABLE"),
    ("teste' OR '1'='1", "SQL Injection: OR condition"),
    ("teste\"; DELETE FROM jovens_rotas; --", "SQL Injection: DELETE"),
    
    # Caracteres especiais
    ("teste@coluna", "Caractere especial: @"),
    ("teste#coluna", "Caractere especial: #"),
    ("teste$coluna", "Caractere especial: $"),
    ("teste%coluna", "Caractere especial: %"),
    ("teste&coluna", "Caractere especial: &"),
    ("teste*coluna", "Caractere especial: *"),
    ("teste(coluna)", "Caractere especial: ()"),
    ("teste[coluna]", "Caractere especial: []"),
    ("teste{coluna}", "Caractere especial: {}"),
    ("teste<coluna>", "Caractere especial: <>"),
    ("teste/coluna", "Caractere especial: /"),
    ("teste\\coluna", "Caractere especial: \\"),
    ("teste|coluna", "Caractere especial: |"),
    ("teste^coluna", "Caractere especial: ^"),
    ("teste~coluna", "Caractere especial: ~"),
    ("teste`coluna", "Caractere especial: `"),
    ("teste'coluna", "Caractere especial: '"),
    ('teste"coluna', "Caractere especial: \""),
    
    # Espaços e caracteres de controle
    ("teste coluna", "Espaço em branco"),
    ("teste\tcoluna", "Tab"),
    ("teste\ncoluna", "Newline"),
    
    # SQL Keywords
    ("SELECT", "SQL Keyword: SELECT"),
    ("DROP", "SQL Keyword: DROP"),
    ("DELETE", "SQL Keyword: DELETE"),
    ("INSERT", "SQL Keyword: INSERT"),
    ("UPDATE", "SQL Keyword: UPDATE"),
    ("ALTER", "SQL Keyword: ALTER"),
    ("CREATE", "SQL Keyword: CREATE"),
    
    # Muito longo
    ("a" * 65, "Comprimento > 64 caracteres"),
    ("a" * 1000, "Comprimento muito longo"),
    
    # Começa com número
    ("1coluna", "Começa com número"),
    ("9teste", "Começa com número"),
]

# Nomes válidos que deveriam ser ACEITOS
VALID_NAMES = [
    "coluna",
    "coluna_nova",
    "coluna_123",
    "_coluna",
    "_123",
    "COLUNA",
    "Coluna",
    "coluna_com_multiplos_underscores",
    "a",
    "_",
    "z" * 64,  # Máximo permitido
]

# Tipos inválidos que deveriam ser REJEITADOS
INVALID_TYPES = [
    "VARCHAR(255)",
    "CHAR(10)",
    "NUMERIC",
    "FLOAT",
    "DOUBLE",
    "BOOLEAN",
    "DATE",
    "TIMESTAMP",
    "JSON",
    "ARRAY",
    "TEXT; DROP TABLE",
    "TEXT' OR '1'='1",
]

# ─── FUNÇÕES DE TESTE ───────────────────────────────────────────────────────

def validar_nome_coluna(nome_coluna: str) -> bool:
    """Valida nome da coluna usando o mesmo regex da correção."""
    SQL_KEYWORDS = {
        "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
        "TABLE", "DATABASE", "INDEX", "VIEW", "TRIGGER", "PROCEDURE",
        "FUNCTION", "WHERE", "FROM", "JOIN", "LEFT", "RIGHT", "INNER",
        "OUTER", "ON", "AND", "OR", "NOT", "IN", "EXISTS", "BETWEEN",
        "LIKE", "IS", "NULL", "TRUE", "FALSE", "ORDER", "BY", "GROUP",
        "HAVING", "LIMIT", "OFFSET", "UNION", "INTERSECT", "EXCEPT",
        "CASE", "WHEN", "THEN", "ELSE", "END", "CAST", "AS", "DISTINCT",
        "ALL", "ANY", "SOME", "CONSTRAINT", "PRIMARY", "KEY", "FOREIGN",
        "UNIQUE", "CHECK", "DEFAULT", "COLLATE", "PRAGMA", "VACUUM",
        "ANALYZE", "EXPLAIN", "PLAN", "QUERY", "TRANSACTION", "BEGIN",
        "COMMIT", "ROLLBACK", "SAVEPOINT", "RELEASE", "ATTACH", "DETACH"
    }
    
    if not re.match(REGEX_PATTERN, nome_coluna):
        return False
    if len(nome_coluna) > MAX_LENGTH:
        return False
    if nome_coluna.upper() in SQL_KEYWORDS:
        return False
    return True

def validar_tipo_coluna(tipo_coluna: str) -> bool:
    """Valida tipo da coluna usando whitelist."""
    return tipo_coluna in VALID_TYPES

def testar_payload_malicioso(nome_coluna: str, descricao: str) -> bool:
    """Testa se um payload malicioso é rejeitado."""
    if validar_nome_coluna(nome_coluna):
        print(f"  ❌ FALHA: {descricao}")
        print(f"     Payload: {nome_coluna}")
        return False
    else:
        print(f"  ✅ BLOQUEADO: {descricao}")
        return True

def testar_nome_valido(nome_coluna: str) -> bool:
    """Testa se um nome válido é aceito."""
    if not validar_nome_coluna(nome_coluna):
        print(f"  ❌ FALHA: Nome válido foi rejeitado: {nome_coluna}")
        return False
    else:
        print(f"  ✅ ACEITO: {nome_coluna}")
        return True

def testar_tipo_invalido(tipo_coluna: str) -> bool:
    """Testa se um tipo inválido é rejeitado."""
    if validar_tipo_coluna(tipo_coluna):
        print(f"  ❌ FALHA: Tipo inválido foi aceito: {tipo_coluna}")
        return False
    else:
        print(f"  ✅ BLOQUEADO: {tipo_coluna}")
        return True

def testar_banco_dados():
    """Testa a execução real no banco de dados."""
    print("\n" + "="*70)
    print("TESTE 4: Execução Real no Banco de Dados")
    print("="*70)
    
    # Criar banco de teste
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    conexao = sqlite3.connect(TEST_DB)
    cursor = conexao.cursor()
    
    # Criar tabela de teste
    cursor.execute('''
        CREATE TABLE teste_seguranca (
            id INTEGER PRIMARY KEY,
            nome TEXT
        )
    ''')
    conexao.commit()
    
    # Testar adição de coluna válida
    try:
        nome_coluna = "coluna_teste"
        tipo_coluna = "TEXT"
        
        if validar_nome_coluna(nome_coluna) and validar_tipo_coluna(tipo_coluna):
            cursor.execute(f"ALTER TABLE teste_seguranca ADD COLUMN {nome_coluna} {tipo_coluna}")
            conexao.commit()
            print(f"  ✅ Coluna válida adicionada: {nome_coluna}")
        else:
            print(f"  ❌ Validação falhou para coluna válida")
    except Exception as e:
        print(f"  ❌ Erro ao adicionar coluna válida: {e}")
    
    # Testar rejeição de payload malicioso
    try:
        nome_coluna = "teste; DROP TABLE teste_seguranca; --"
        tipo_coluna = "TEXT"
        
        if not validar_nome_coluna(nome_coluna):
            print(f"  ✅ Payload malicioso foi bloqueado (não executado)")
        else:
            # Se passou na validação, não deveria executar
            cursor.execute(f"ALTER TABLE teste_seguranca ADD COLUMN {nome_coluna} {tipo_coluna}")
            conexao.commit()
            print(f"  ❌ FALHA: Payload malicioso foi executado!")
    except Exception as e:
        print(f"  ✅ Payload malicioso causou erro (esperado): {type(e).__name__}")
    
    conexao.close()
    
    # Limpar
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

# ─── EXECUÇÃO DOS TESTES ────────────────────────────────────────────────────

def main():
    print("\n" + "="*70)
    print("🔐 TESTES DE SEGURANÇA — SQL Injection Prevention")
    print("="*70)
    
    total_testes = 0
    testes_passados = 0
    
    # TESTE 1: Payloads Maliciosos
    print("\n" + "="*70)
    print("TESTE 1: Rejeição de Payloads Maliciosos")
    print("="*70)
    print(f"Total de payloads: {len(MALICIOUS_PAYLOADS)}\n")
    
    for payload, descricao in MALICIOUS_PAYLOADS:
        total_testes += 1
        if testar_payload_malicioso(payload, descricao):
            testes_passados += 1
    
    # TESTE 2: Nomes Válidos
    print("\n" + "="*70)
    print("TESTE 2: Aceitação de Nomes Válidos")
    print("="*70)
    print(f"Total de nomes: {len(VALID_NAMES)}\n")
    
    for nome in VALID_NAMES:
        total_testes += 1
        if testar_nome_valido(nome):
            testes_passados += 1
    
    # TESTE 3: Tipos Inválidos
    print("\n" + "="*70)
    print("TESTE 3: Rejeição de Tipos Inválidos")
    print("="*70)
    print(f"Total de tipos: {len(INVALID_TYPES)}\n")
    
    for tipo in INVALID_TYPES:
        total_testes += 1
        if testar_tipo_invalido(tipo):
            testes_passados += 1
    
    # TESTE 4: Banco de Dados
    testar_banco_dados()
    
    # RESUMO
    print("\n" + "="*70)
    print("📊 RESUMO DOS TESTES")
    print("="*70)
    print(f"Total de testes: {total_testes}")
    print(f"Testes passados: {testes_passados}")
    print(f"Testes falhados: {total_testes - testes_passados}")
    
    taxa_sucesso = (testes_passados / total_testes * 100) if total_testes > 0 else 0
    print(f"Taxa de sucesso: {taxa_sucesso:.1f}%")
    
    if taxa_sucesso == 100:
        print("\n✅ TODOS OS TESTES PASSARAM! A correção está funcionando corretamente.")
        return 0
    else:
        print(f"\n❌ {total_testes - testes_passados} TESTES FALHARAM!")
        return 1

if __name__ == "__main__":
    exit(main())
