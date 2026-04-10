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
    """Atualiza dados do funcionário no banco de dados - aceita qualquer valor."""
    try:
        # Garante que o ID é inteiro
        id_jovem = int(id_jovem)
        
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        
        # Primeiro verifica se o registro existe
        cursor.execute("SELECT id FROM jovens_rotas WHERE id = ?", (id_jovem,))
        existe = cursor.fetchone()
        
        if not existe:
            conexao.close()
            print(f"ERRO: Registro com ID {id_jovem} não encontrado no banco")
            return False
        
        print(f"Atualizando ID {id_jovem} com:")
        print(f"  Matrícula: {matricula}")
        print(f"  Email: {email}")
        print(f"  Celular: {celular}")
        print(f"  CEP: {cep}")
        print(f"  Número: {numero}")
        print(f"  Coordenadas: {coordenadas}")
        
        # Executa o UPDATE - aceita qualquer valor, sem validação
        cursor.execute('''
            UPDATE jovens_rotas 
            SET matricula = ?, email = ?, celular = ?, cep_casa = ?, numero_casa = ?, coordenadas = ?
            WHERE id = ?
        ''', (matricula, email, celular, cep, numero, coordenadas, id_jovem))
        
        # Verifica se alguma linha foi afetada
        linhas_afetadas = cursor.rowcount
        
        conexao.commit()
        conexao.close()
        
        print(f"✅ UPDATE executado com sucesso: {linhas_afetadas} linha(s) afetada(s)")
        return linhas_afetadas > 0
        
    except Exception as e:
        print(f"❌ ERRO na atualização: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

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

def criar_tabela_tokens():
    """
    Cria tabela tokens_assinatura se não existir.
    
    A tabela armazena tokens de assinatura digital para autenticação
    de solicitações de assinatura de Vale-Transporte.
    
    Colunas:
        - id: Chave primária auto-incremento
        - token: Token único gerado (43+ caracteres, base64url)
        - consulta_id: FK para jovens_rotas.id
        - created_at: Timestamp de criação (ISO 8601)
        - expires_at: Timestamp de expiração (ISO 8601)
        - used: Flag indicando se token foi usado (0=não usado, 1=usado)
        - used_at: Timestamp de quando foi usado (NULL se não usado)
    
    Índices criados para performance:
        - idx_token: Busca rápida por token
        - idx_consulta_id: Busca por consulta
        - idx_expires_at: Cleanup eficiente de tokens expirados
    """
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    # Criar tabela tokens_assinatura
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens_assinatura (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            consulta_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER DEFAULT 0,
            used_at TEXT,
            FOREIGN KEY (consulta_id) REFERENCES jovens_rotas(id)
        )
    ''')
    
    # Criar índice em token para lookup rápido
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_token 
        ON tokens_assinatura(token)
    ''')
    
    # Criar índice em consulta_id para queries por consulta
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_consulta_id 
        ON tokens_assinatura(consulta_id)
    ''')
    
    # Criar índice em expires_at para cleanup eficiente
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_expires_at 
        ON tokens_assinatura(expires_at)
    ''')
    
    conexao.commit()
    conexao.close()

def adicionar_colunas_assinatura():
    """
    Adiciona colunas de assinatura à tabela jovens_rotas.
    
    Adiciona as seguintes colunas:
        - assinatura_path: Caminho do arquivo PNG da assinatura
        - assinatura_data: Timestamp da assinatura (ISO 8601)
        - assinatura_ip: Endereço IP do cliente que assinou
    
    Trata graciosamente o caso onde as colunas já existem usando
    try/except OperationalError.
    """
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    colunas_novas = [
        ("assinatura_path", "TEXT"),
        ("assinatura_data", "TEXT"),
        ("assinatura_ip", "TEXT")
    ]
    
    for coluna, tipo in colunas_novas:
        try:
            cursor.execute(
                f"ALTER TABLE jovens_rotas ADD COLUMN {coluna} {tipo}"
            )
        except sqlite3.OperationalError:
            # Coluna já existe, continua para a próxima
            pass
    
    conexao.commit()
    conexao.close()

def inicializar_banco_completo():
    """
    Inicializa todas as estruturas do banco de dados.
    
    Executa todas as funções de setup do banco de dados em ordem:
    1. atualizar_banco_geral() - Adiciona colunas gerais à tabela jovens_rotas
    2. atualizar_banco_para_contestacoes() - Cria tabela de contestações
    3. criar_tabela_tokens() - Cria tabela de tokens de assinatura
    4. adicionar_colunas_assinatura() - Adiciona colunas de assinatura
    
    Esta função é idempotente - pode ser executada múltiplas vezes sem
    causar erros, pois cada função individual trata graciosamente o caso
    onde as estruturas já existem.
    
    Deve ser chamada no início da aplicação para garantir que todas as
    estruturas necessárias estejam presentes no banco de dados.
    """
    atualizar_banco_geral()
    atualizar_banco_para_contestacoes()
    criar_tabela_tokens()
    adicionar_colunas_assinatura()

def atualizar_consulta_com_assinatura(
    consulta_id: int,
    filepath: str,
    ip_address: str
) -> bool:
    """
    Atualiza consulta com dados da assinatura e muda status para Implantado.
    
    Esta função realiza uma atualização atômica usando transação para garantir
    que todas as mudanças sejam aplicadas juntas ou nenhuma seja aplicada.
    
    Args:
        consulta_id: ID da consulta na tabela jovens_rotas
        filepath: Caminho do arquivo PNG da assinatura
        ip_address: Endereço IP do cliente que assinou
        
    Returns:
        True se a atualização foi bem-sucedida, False caso contrário
        
    Validates:
        - Requirements 6.9: Atualiza status_rota para 'Implantado'
        - Requirements 9.4: Armazena assinatura_path
        - Requirements 9.5: Armazena assinatura_data com timestamp atual
        - Requirements 9.6: Armazena assinatura_ip
    """
    try:
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        
        # Gera timestamp atual no formato ISO 8601
        timestamp_atual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Inicia transação explícita para garantir atomicidade
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Atualiza todos os campos em uma única operação atômica
            cursor.execute('''
                UPDATE jovens_rotas 
                SET status_rota = 'Implantado',
                    assinatura_path = ?,
                    assinatura_data = ?,
                    assinatura_ip = ?
                WHERE id = ?
            ''', (filepath, timestamp_atual, ip_address, consulta_id))
            
            # Verifica se alguma linha foi afetada
            linhas_afetadas = cursor.rowcount
            
            if linhas_afetadas == 0:
                # Nenhuma linha foi atualizada - consulta_id não existe
                conexao.rollback()
                conexao.close()
                print(f"ERRO: Consulta com ID {consulta_id} não encontrada")
                return False
            
            # Commit da transação
            conexao.commit()
            print(f"✅ Consulta {consulta_id} atualizada com sucesso: status='Implantado', assinatura salva")
            
            conexao.close()
            return True
            
        except Exception as e:
            # Rollback em caso de erro durante a transação
            conexao.rollback()
            conexao.close()
            print(f"❌ ERRO na transação: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        # Erro ao conectar ao banco
        print(f"❌ ERRO ao conectar ao banco: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def obter_status_consulta(consulta_id: int) -> str:
    """
    Obtém o status atual de uma consulta.
    
    Esta função é usada para verificar o status de uma consulta específica,
    útil para testes e lógica de UI.
    
    Args:
        consulta_id: ID da consulta na tabela jovens_rotas
        
    Returns:
        String com o status da consulta ("Otimizado", "Implantado", "Não Optante")
        ou None se a consulta não existir
        
    Validates:
        - Requirements 1.8: Suporta verificação de status para lógica de UI
    """
    try:
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        
        cursor.execute(
            "SELECT status_rota FROM jovens_rotas WHERE id = ?",
            (consulta_id,)
        )
        
        resultado = cursor.fetchone()
        conexao.close()
        
        if resultado is None:
            return None
        
        return resultado[0]
        
    except Exception as e:
        print(f"❌ ERRO ao obter status da consulta: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def verificar_token_usado(token: str) -> bool:
    """
    Verifica se um token já foi usado.
    
    Esta função consulta a tabela tokens_assinatura para verificar
    se um token específico já foi marcado como usado.
    
    Args:
        token: Token de assinatura a ser verificado
        
    Returns:
        True se o token foi usado (used=1), False caso contrário
        False também é retornado se o token não existir
        
    Validates:
        - Requirements 1.8: Suporta verificação de token para testes e lógica de UI
    """
    try:
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        
        cursor.execute(
            "SELECT used FROM tokens_assinatura WHERE token = ?",
            (token,)
        )
        
        resultado = cursor.fetchone()
        conexao.close()
        
        if resultado is None:
            # Token não existe
            return False
        
        # Retorna True se used=1, False se used=0
        return resultado[0] == 1
        
    except Exception as e:
        print(f"❌ ERRO ao verificar token: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
