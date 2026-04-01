import sqlite3

#  Cria a conexão (se o arquivo não existir, o Python cria ele na hora)
conexao = sqlite3.connect('mobilidade_renapsi.db')
cursor = conexao.cursor()

#  SQL para criar a tabela
cursor.execute('''
    CREATE TABLE IF NOT EXISTS jovens_rotas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        cpf TEXT,
        cep_casa TEXT,
        cep_trabalho TEXT
    )
''')

#  Limpa a tabela caso rode o código duas vezes
cursor.execute('DELETE FROM jovens_rotas')

# 4. Inserindo nossos Jovens de Teste (CEPs reais de SP, CPFs falsos)
jovens_teste = [
    ('João Teste', '11122233344', '01310100', '04538133'), # Casa na Paulista, Trabalho no Itaim
    ('Maria Teste', '55566677788', '08210040', '01014000'), # Casa em Itaquera, Trabalho no Centro
    ('Pedro Teste', '99900011122', '05001200', '05425070')  # Casa em Perdizes, Trabalho em Pinheiros
]

cursor.executemany('''
    INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho)
    VALUES (?, ?, ?, ?)
''', jovens_teste)

# 5. Salva (Commit) e fecha o banco
conexao.commit()
conexao.close()

print("✅ Banco de dados 'mobilidade_renapsi.db' criado e populado com sucesso!")