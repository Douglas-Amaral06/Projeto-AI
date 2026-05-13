"""
Script para exportar dados do banco local para um arquivo SQL de seed.
Anonimiza CPF, e-mail e celular para proteger dados pessoais.
Execute localmente: python exportar_seed.py
"""
import sqlite3
import os
import re

db_path = os.path.join(os.path.dirname(__file__), 'mobilidade_renapsi.db')
output_path = os.path.join(os.path.dirname(__file__), 'Projeto_RH', 'seed_dados.sql')

def anonimizar_cpf(cpf):
    if not cpf:
        return cpf
    limpo = re.sub(r'\D', '', str(cpf))
    if len(limpo) == 11:
        return f"{limpo[:3]}.***.***-{limpo[-2:]}"
    return "***.***.***-**"

def anonimizar_email(email):
    if not email or '@' not in str(email):
        return email
    partes = str(email).split('@')
    usuario = partes[0]
    dominio = partes[1] if len(partes) > 1 else 'email.com'
    return f"{usuario[0]}***@{dominio}"

def anonimizar_celular(cel):
    if not cel:
        return cel
    limpo = re.sub(r'\D', '', str(cel))
    if len(limpo) >= 8:
        return f"({limpo[:2]}) *****-{limpo[-4:]}"
    return "(**) *****-****"

def escape_sql(val):
    if val is None:
        return 'NULL'
    if isinstance(val, (int, float)):
        return str(val)
    val_str = str(val).replace("'", "''")
    return f"'{val_str}'"

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

linhas_sql = []
linhas_sql.append("-- Seed de dados exportado automaticamente")
linhas_sql.append("-- CPFs, e-mails e celulares foram anonimizados")
linhas_sql.append("-- Execute este arquivo na inicialização do banco\n")

# ── jovens_rotas ──────────────────────────────────────────────────────────────
cursor = conn.execute("SELECT * FROM jovens_rotas ORDER BY id")
rows = cursor.fetchall()
cols = [d[0] for d in cursor.description]

linhas_sql.append("-- ═══ JOVENS ROTAS ═══")
for row in rows:
    row_dict = dict(row)
    # Anonimiza dados sensíveis
    row_dict['cpf']     = anonimizar_cpf(row_dict.get('cpf'))
    row_dict['email']   = anonimizar_email(row_dict.get('email'))
    row_dict['celular'] = anonimizar_celular(row_dict.get('celular'))
    # Remove assinatura digital (pode conter dados binários grandes)
    row_dict['assinatura_digital'] = None
    row_dict['assinatura_path']    = None

    valores = ', '.join(escape_sql(row_dict[c]) for c in cols)
    colunas = ', '.join(cols)
    linhas_sql.append(
        f"INSERT OR IGNORE INTO jovens_rotas ({colunas}) VALUES ({valores});"
    )

linhas_sql.append("")

# ── locais_trabalho ───────────────────────────────────────────────────────────
cursor = conn.execute("SELECT * FROM locais_trabalho ORDER BY id")
rows = cursor.fetchall()
cols = [d[0] for d in cursor.description]

linhas_sql.append("-- ═══ LOCAIS DE TRABALHO ═══")
for row in rows:
    row_dict = dict(row)
    valores = ', '.join(escape_sql(row_dict[c]) for c in cols)
    colunas = ', '.join(cols)
    linhas_sql.append(
        f"INSERT OR IGNORE INTO locais_trabalho ({colunas}) VALUES ({valores});"
    )

linhas_sql.append("")

# ── contestacoes ──────────────────────────────────────────────────────────────
cursor = conn.execute("SELECT * FROM contestacoes ORDER BY id")
rows = cursor.fetchall()
cols = [d[0] for d in cursor.description]

linhas_sql.append("-- ═══ CONTESTAÇÕES ═══")
for row in rows:
    row_dict = dict(row)
    valores = ', '.join(escape_sql(row_dict[c]) for c in cols)
    colunas = ', '.join(cols)
    linhas_sql.append(
        f"INSERT OR IGNORE INTO contestacoes ({colunas}) VALUES ({valores});"
    )

conn.close()

# Salva o arquivo SQL
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(linhas_sql))

print(f"✅ Seed exportado para: {output_path}")
print(f"   {len([r for r in linhas_sql if 'INSERT' in r])} registros exportados")
