import pandas as pd
import datetime
import os
import logging
import sqlite3
from dotenv import load_dotenv

# --- Configuração do Banco Local (SQLite) ---
load_dotenv()
# Aponta para o banco de dados na raiz do projeto (diretório pai)
DATABASE_FILE = os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db')
logger = logging.getLogger(__name__)

def carregar_dados():
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        df = pd.read_sql_query("SELECT * FROM jovens_rotas", conexao)
        conexao.close()
        logger.info(f"Carregados {len(df)} registros do banco local")
        return df
    except Exception as e:
        logger.exception(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def inserir_novo_jovem(nome, cpf, cep_casa, cep_trabalho, matricula):
    try:
        status_rota = "Otimizado"
        
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        cursor.execute('''
            INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota))
        conexao.commit()
        conexao.close()
            
        logger.info(f"Novo jovem inserido: {nome}")
        return True
    except Exception as e:
        logger.exception(f"Erro ao inserir novo jovem: {e}")
        return False

def cpf_ja_existe(cpf):
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        cursor.execute("SELECT COUNT(*) FROM jovens_rotas WHERE cpf = ?", (cpf,))
        resultado = cursor.fetchone()[0]
        conexao.close()
        return resultado > 0
    except Exception as e:
        logger.exception(f"Erro ao verificar CPF: {e}")
        return False

def excluir_jovem(id_jovem):
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM jovens_rotas WHERE id = ?", (id_jovem,))
        conexao.commit()
        conexao.close()
    except Exception as e:
        logger.exception(f"Erro ao excluir jovem: {e}")

def atualizar_banco_geral():
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        
        colunas_novas = [
            ("data_consulta", "TEXT"), ("sla_segundos", "REAL"), ("matricula", "TEXT"),
            ("status_rota", "TEXT DEFAULT 'Otimizado'"), ("email", "TEXT"),
            ("celular", "TEXT"), ("numero_casa", "TEXT"), ("coordenadas", "TEXT"),
            ("modo_rota", "TEXT DEFAULT 'automatica'"),
            ("tipo_bilhete_manual", "TEXT"),
            ("valor_tarifa_manual", "REAL"),
            ("descricao_itinerario_manual", "TEXT"),
            ("assinatura_digital", "TEXT")
        ]
        
        for coluna, tipo in colunas_novas:
            try:
                cursor.execute(f"ALTER TABLE jovens_rotas ADD COLUMN {coluna} {tipo}")
            except sqlite3.OperationalError:
                pass  # Coluna já existe
                
        cursor.execute("UPDATE jovens_rotas SET status_rota = 'Otimizado' WHERE status_rota IS NULL")
        cursor.execute("UPDATE jovens_rotas SET modo_rota = 'automatica' WHERE modo_rota IS NULL")
        conexao.commit()
        conexao.close()
    except Exception as e:
        logger.exception(f"Erro na atualização geral do banco: {e}")

def atualizar_dados_funcionario(id_jovem, matricula, email, celular, cep, numero, coordenadas):
    try:
        id_jovem = int(id_jovem)
        
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        
        cursor.execute("SELECT id FROM jovens_rotas WHERE id = ?", (id_jovem,))
        existe = cursor.fetchone()
        
        if not existe:
            logger.error(f"Registro com ID {id_jovem} não encontrado no banco")
            conexao.close()
            return False
            
        cursor.execute('''
            UPDATE jovens_rotas 
            SET matricula = ?, email = ?, celular = ?, 
                cep_casa = ?, numero_casa = ?, coordenadas = ?
            WHERE id = ?
        ''', (matricula, email, celular, cep, numero, coordenadas, id_jovem))
        
        conexao.commit()
        sucesso = cursor.rowcount > 0
        conexao.close()
        return sucesso
    except Exception as e:
        logger.exception(f"ERRO na atualização: {str(e)}")
        return False

def salvar_rota_manual(id_jovem, tipo_bilhete, valor_tarifa, descricao_itinerario):
    """Salva os dados da rota manual no banco de dados"""
    try:
        id_jovem = int(id_jovem)
        
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        
        cursor.execute('''
            UPDATE jovens_rotas 
            SET modo_rota = 'manual',
                tipo_bilhete_manual = ?,
                valor_tarifa_manual = ?,
                descricao_itinerario_manual = ?
            WHERE id = ?
        ''', (tipo_bilhete, valor_tarifa, descricao_itinerario, id_jovem))
        
        conexao.commit()
        sucesso = cursor.rowcount > 0
        conexao.close()
        
        if sucesso:
            logger.info(f"Rota manual salva para ID {id_jovem}")
        else:
            logger.error(f"Falha ao salvar rota manual para ID {id_jovem}")
            
        return sucesso
    except Exception as e:
        logger.exception(f"ERRO ao salvar rota manual: {str(e)}")
        return False

def obter_dados_dashboard():
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        
        # Total de Consultas (rotas únicas abertas)
        cursor.execute("SELECT COUNT(DISTINCT id) FROM jovens_rotas")
        total_consultas = cursor.fetchone()[0] or 0
        
        # SLA Médio (tempo médio de consulta em segundos)
        cursor.execute("SELECT AVG(sla_segundos) FROM jovens_rotas WHERE sla_segundos IS NOT NULL")
        sla_medio = cursor.fetchone()[0] or 0.0
        
        # Total de Contestações (todas, mesmo as resolvidas)
        cursor.execute("SELECT COUNT(*) FROM contestacoes")
        total_contestacoes = cursor.fetchone()[0] or 0
        
        # Implantações (funcionários com status IMPLANTADO no momento)
        cursor.execute("SELECT COUNT(*) FROM jovens_rotas WHERE status_rota = 'Implantado'")
        total_implantados = cursor.fetchone()[0] or 0
        
        conexao.close()
        return total_consultas, sla_medio, total_contestacoes, total_implantados
    except Exception as e:
        logger.exception(f"Erro ao obter dados do dashboard: {e}")
        return 0, 0.0, 0, 0

def atualizar_banco_para_contestacoes():
    try:
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
        
        # Adiciona colunas se não existirem
        try:
            cursor.execute("ALTER TABLE contestacoes ADD COLUMN status TEXT DEFAULT 'Pendente'")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE contestacoes ADD COLUMN tratativa TEXT")
        except sqlite3.OperationalError:
            pass
            
        conexao.commit()
        conexao.close()
    except Exception as e:
        logger.exception(f"Erro ao atualizar banco de contestações: {e}")

def resolver_contestacao(id_contestacao, tratativa):
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        
        # Atualiza a contestação
        cursor.execute("UPDATE contestacoes SET status = 'Resolvido', tratativa = ? WHERE id = ?", 
                       (tratativa, id_contestacao))
        
        # Busca o nome do jovem para atualizar o status dele
        cursor.execute("SELECT nome_jovem FROM contestacoes WHERE id = ?", (id_contestacao,))
        resultado = cursor.fetchone()
        
        if resultado:
            nome_jovem = resultado[0]
            # Volta o status para Otimizado
            cursor.execute("UPDATE jovens_rotas SET status_rota = 'Otimizado' WHERE nome = ?", (nome_jovem,))
        
        conexao.commit()
        conexao.close()
    except Exception as e:
        logger.exception(f"Erro ao resolver contestação: {e}")

def registrar_contestacao(nome, cid_res, cid_trab, motivo):
    try:
        data_atual = datetime.datetime.now().strftime("%d/%m/%Y às %Hh%Mm")
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        cursor.execute('''
            INSERT INTO contestacoes (nome_jovem, cidade_residencia, cidade_trabalho, motivo, data_geracao)
            VALUES (?, ?, ?, ?, ?)
        ''', (nome, cid_res, cid_trab, motivo, data_atual))
        conexao.commit()
        conexao.close()
    except Exception as e:
        logger.exception(f"Erro ao registrar contestação: {e}")

def criar_tabela_tokens():
    try:
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
    except Exception as e:
        logger.exception(f"Erro ao criar tabela de tokens: {e}")

def adicionar_colunas_assinatura():
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        
        try:
            cursor.execute("ALTER TABLE jovens_rotas ADD COLUMN assinatura_path TEXT")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE jovens_rotas ADD COLUMN assinatura_data TEXT")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE jovens_rotas ADD COLUMN assinatura_ip TEXT")
        except sqlite3.OperationalError:
            pass
            
        conexao.commit()
        conexao.close()
    except Exception as e:
        logger.exception(f"Erro ao adicionar colunas de assinatura: {e}")

def criar_tabela_locais_trabalho():
    """Cria a tabela de locais de trabalho (unidades) e insere registro padrão"""
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locais_trabalho (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_unidade TEXT NOT NULL UNIQUE,
                cep TEXT NOT NULL,
                logradouro TEXT,
                numero TEXT,
                bairro TEXT,
                cidade_uf TEXT,
                coordenadas TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insere registro padrão se não existir
        cursor.execute("SELECT COUNT(*) FROM locais_trabalho WHERE nome_unidade = 'RENAPSI - SÃO PAULO-SP'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO locais_trabalho (nome_unidade, cep, logradouro, numero, bairro, cidade_uf, coordenadas)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'RENAPSI - SÃO PAULO-SP',
                '01333010',
                'RUA CINCINATO BRAGA',
                '388',
                'BELA VISTA',
                'SÃO PAULO - SP',
                '-23.56774139404297, -46.646541595458984'
            ))
        
        conexao.commit()
        conexao.close()
        logger.info("Tabela locais_trabalho criada/atualizada com sucesso")
    except Exception as e:
        logger.exception(f"Erro ao criar tabela de locais de trabalho: {e}")

def inicializar_banco_completo():
    atualizar_banco_geral()
    atualizar_banco_para_contestacoes()
    criar_tabela_tokens()
    adicionar_colunas_assinatura()
    criar_tabela_locais_trabalho()

def atualizar_consulta_com_assinatura(consulta_id: int, filepath: str, ip_address: str) -> bool:
    try:
        timestamp_atual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        
        cursor.execute('''
            UPDATE jovens_rotas 
            SET status_rota = 'Implantado',
                assinatura_path = ?,
                assinatura_data = ?,
                assinatura_ip = ?
            WHERE id = ?
        ''', (filepath, timestamp_atual, ip_address, consulta_id))
        
        if cursor.rowcount == 0:
            print(f"ERRO: Consulta com ID {consulta_id} não encontrada")
            conexao.close()
            return False
            
        conexao.commit()
        conexao.close()
        print(f"✅ Consulta {consulta_id} atualizada com sucesso: status='Implantado'")
        return True
    except Exception as e:
        print(f"❌ ERRO na atualização da assinatura: {str(e)}")
        return False

def obter_status_consulta(consulta_id: int) -> str:
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        cursor.execute("SELECT status_rota FROM jovens_rotas WHERE id = ?", (consulta_id,))
        resultado = cursor.fetchone()
        conexao.close()
        return resultado[0] if resultado else None
    except Exception as e:
        print(f"❌ ERRO ao obter status da consulta: {str(e)}")
        return None

def verificar_token_usado(token: str) -> bool:
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        cursor.execute("SELECT used FROM tokens_assinatura WHERE token = ?", (token,))
        resultado = cursor.fetchone()
        conexao.close()
        if not resultado:
            return False
        return resultado[0] == 1
    except Exception as e:
        print(f"❌ ERRO ao verificar token: {str(e)}")
        return False


def obter_status_visual(status_rota):
    """Retorna a máscara visual do status"""
    mapeamento = {
        'Otimizado': '🔵 Aguardando Aceite',
        'Implantado': '🟢 Assinado/Ativo',
        'Contestada': '🟡 Em Revisão',
        'Não Optante': '⚪ Não Optante'
    }
    return mapeamento.get(status_rota, status_rota)


# ─── FUNÇÕES PARA TRIAGEM DE FICHAS ──────────────────────────────────────────

def obter_fichas_cadastrais(filtro_nome="", filtro_status="Pendente"):
    """
    Busca fichas cadastrais com filtros de nome e status.
    
    Args:
        filtro_nome: Filtro por nome completo (LIKE)
        filtro_status: 'Pendente', 'Aprovado' ou 'Todos'
    
    Returns:
        DataFrame com as fichas encontradas
    """
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        
        # Constrói a query dinamicamente
        query = "SELECT * FROM fichas_cadastrais WHERE 1=1"
        params = []
        
        if filtro_nome.strip():
            query += " AND nome_completo LIKE ?"
            params.append(f"%{filtro_nome}%")
        
        if filtro_status != "Todos":
            query += " AND status_aprovacao = ?"
            params.append(filtro_status)
        
        query += " ORDER BY data_cadastro DESC"
        
        df = pd.read_sql_query(query, conexao, params=params)
        conexao.close()
        
        return df
    except Exception as e:
        logger.exception(f"Erro ao obter fichas cadastrais: {e}")
        return pd.DataFrame()


def aprovar_ficha_e_integrar(ficha_id):
    """
    Aprova uma ficha cadastral e integra o candidato à tabela jovens_rotas.
    Executa em uma única transação.
    
    Args:
        ficha_id: ID da ficha cadastral
    
    Returns:
        Tupla (sucesso: bool, mensagem: str)
    """
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        
        # Inicia transação
        cursor.execute("BEGIN TRANSACTION")
        
        # 1. Busca os dados da ficha
        cursor.execute("SELECT * FROM fichas_cadastrais WHERE id = ?", (ficha_id,))
        ficha = cursor.fetchone()
        
        if not ficha:
            conexao.rollback()
            conexao.close()
            return False, "Ficha não encontrada"
        
        # Mapeia os dados da ficha para as colunas
        ficha_dict = {
            'id': ficha[0],
            'nome_completo': ficha[1],
            'nome_social': ficha[2],
            'data_nascimento': ficha[3],
            'cpf': ficha[4],
            'rg': ficha[5],
            'identidade_genero': ficha[6],
            'raca': ficha[7],
            'estado_civil': ficha[8],
            'email_jovem': ficha[9],
            'email_responsavel': ficha[10],
            'endereco_completo': ficha[11],
            'cidade_estado': ficha[12],
            'cep': ficha[13],
            'tel_jovem': ficha[14],
            'tel_responsavel': ficha[15],
            'tamanho_uniforme': ficha[16],
            'nome_mae': ficha[17],
            'ocupacao_mae': ficha[18],
            'estado_civil_mae': ficha[19],
            'nome_pai': ficha[20],
            'ocupacao_pai': ficha[21],
            'estado_civil_pai': ficha[22],
            'nome_resp': ficha[23],
            'ocupacao_resp': ficha[24],
            'estado_civil_resp': ficha[25],
            'tem_dependentes': ficha[26],
            'path_comp_residencia': ficha[27],
            'path_rg': ficha[28],
            'path_conta_salario': ficha[29],
            'path_titulo': ficha[30],
            'path_reservista': ficha[31],
            'path_casamento': ficha[32],
            'path_cert_nasc_dep': ficha[33],
            'path_vacina_dep': ficha[34],
            'data_cadastro': ficha[35],
            'status_aprovacao': ficha[36]
        }
        
        # 2. UPDATE: Marca a ficha como Aprovada
        cursor.execute(
            "UPDATE fichas_cadastrais SET status_aprovacao = 'Aprovado' WHERE id = ?",
            (ficha_id,)
        )
        
        # 3. INSERT: Cria registro na tabela jovens_rotas
        cursor.execute('''
            INSERT INTO jovens_rotas (
                nome, cpf, cep_casa, cep_trabalho, email, celular, 
                matricula, status_rota, data_consulta
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ficha_dict['nome_completo'],  # nome
            ficha_dict['cpf'],             # cpf
            ficha_dict['cep'],             # cep_casa
            '',                            # cep_trabalho (vazio para edição posterior)
            ficha_dict['email_jovem'],     # email
            ficha_dict['tel_jovem'],       # celular
            '',                            # matricula (vazio)
            'Aguardando Rota',             # status_rota
            datetime.datetime.now().isoformat()  # data_consulta
        ))
        
        # Confirma a transação
        conexao.commit()
        conexao.close()
        
        logger.info(f"Ficha {ficha_id} aprovada e integrada com sucesso")
        return True, f"✅ {ficha_dict['nome_completo']} foi integrado(a) ao banco de dados da mobilidade com sucesso!"
        
    except Exception as e:
        try:
            conexao.rollback()
        except:
            pass
        conexao.close()
        logger.exception(f"Erro ao aprovar ficha: {e}")
        return False, f"❌ Erro ao aprovar ficha: {str(e)}"


def reprovar_ficha(ficha_id, motivo=""):
    """
    Marca uma ficha como reprovada.
    
    Args:
        ficha_id: ID da ficha cadastral
        motivo: Motivo da reprovação (opcional)
    
    Returns:
        Tupla (sucesso: bool, mensagem: str)
    """
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        
        cursor.execute(
            "UPDATE fichas_cadastrais SET status_aprovacao = 'Reprovado' WHERE id = ?",
            (ficha_id,)
        )
        
        conexao.commit()
        conexao.close()
        
        logger.info(f"Ficha {ficha_id} reprovada")
        return True, "✅ Ficha reprovada com sucesso"
        
    except Exception as e:
        conexao.close()
        logger.exception(f"Erro ao reprovar ficha: {e}")
        return False, f"❌ Erro ao reprovar ficha: {str(e)}"


# ─── FUNÇÕES PARA GERENCIAMENTO DE LOCAIS DE TRABALHO ──────────────────────────

def obter_locais_trabalho():
    """Retorna lista de todos os locais de trabalho cadastrados."""
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id, nome_unidade, cep, logradouro, numero, bairro, cidade_uf, coordenadas
            FROM locais_trabalho
            ORDER BY nome_unidade
        """)
        locais = []
        for row in cursor.fetchall():
            locais.append({
                'id': row[0],
                'nome_unidade': row[1],
                'cep': row[2],
                'logradouro': row[3],
                'numero': row[4],
                'bairro': row[5],
                'cidade_uf': row[6],
                'coordenadas': row[7]
            })
        conexao.close()
        return locais
    except Exception as e:
        logger.exception(f"Erro ao obter locais de trabalho: {e}")
        return []


def inserir_local_trabalho(nome_unidade, cep, logradouro, numero, bairro, cidade_uf, coordenadas=""):
    """Insere um novo local de trabalho no banco."""
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        cursor.execute("""
            INSERT INTO locais_trabalho (nome_unidade, cep, logradouro, numero, bairro, cidade_uf, coordenadas)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nome_unidade, cep, logradouro, numero, bairro, cidade_uf, coordenadas))
        conexao.commit()
        conexao.close()
        logger.info(f"Local de trabalho '{nome_unidade}' inserido com sucesso")
        return True
    except sqlite3.IntegrityError:
        logger.error(f"Local de trabalho '{nome_unidade}' já existe")
        return False
    except Exception as e:
        logger.exception(f"Erro ao inserir local de trabalho: {e}")
        return False


def obter_local_trabalho_por_id(local_id):
    """Retorna os dados de um local de trabalho específico."""
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id, nome_unidade, cep, logradouro, numero, bairro, cidade_uf, coordenadas
            FROM locais_trabalho
            WHERE id = ?
        """, (local_id,))
        row = cursor.fetchone()
        conexao.close()
        
        if row:
            return {
                'id': row[0],
                'nome_unidade': row[1],
                'cep': row[2],
                'logradouro': row[3],
                'numero': row[4],
                'bairro': row[5],
                'cidade_uf': row[6],
                'coordenadas': row[7]
            }
        return None
    except Exception as e:
        logger.exception(f"Erro ao obter local de trabalho: {e}")
        return None


def atualizar_local_trabalho(local_id, nome_unidade, cep, logradouro, numero, bairro, cidade_uf, coordenadas=""):
    """Atualiza os dados de um local de trabalho."""
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        cursor.execute("""
            UPDATE locais_trabalho
            SET nome_unidade = ?, cep = ?, logradouro = ?, numero = ?, bairro = ?, cidade_uf = ?, coordenadas = ?
            WHERE id = ?
        """, (nome_unidade, cep, logradouro, numero, bairro, cidade_uf, coordenadas, local_id))
        conexao.commit()
        sucesso = cursor.rowcount > 0
        conexao.close()
        if sucesso:
            logger.info(f"Local de trabalho ID {local_id} atualizado com sucesso")
        return sucesso
    except Exception as e:
        logger.exception(f"Erro ao atualizar local de trabalho: {e}")
        return False


def deletar_local_trabalho(local_id):
    """Deleta um local de trabalho do banco."""
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM locais_trabalho WHERE id = ?", (local_id,))
        conexao.commit()
        sucesso = cursor.rowcount > 0
        conexao.close()
        if sucesso:
            logger.info(f"Local de trabalho ID {local_id} deletado com sucesso")
        return sucesso
    except Exception as e:
        logger.exception(f"Erro ao deletar local de trabalho: {e}")
        return False
