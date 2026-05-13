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

def atualizar_esquema_banco():
    """Cria as colunas faltantes no banco de dados"""
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            
            try:
                cursor.execute("ALTER TABLE locais_trabalho ADD COLUMN tipo_local TEXT DEFAULT 'Trabalho'")
                logger.info("Coluna tipo_local adicionada em locais_trabalho")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE jovens_rotas ADD COLUMN cep_curso TEXT")
                logger.info("Coluna cep_curso adicionada em jovens_rotas")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE jovens_rotas ADD COLUMN status_curso TEXT DEFAULT 'Otimizado'")
                logger.info("Coluna status_curso adicionada em jovens_rotas")
            except sqlite3.OperationalError:
                pass

            cursor.execute("UPDATE locais_trabalho SET tipo_local = 'Trabalho' WHERE tipo_local IS NULL")
            cursor.execute("UPDATE jovens_rotas SET status_curso = 'Otimizado' WHERE status_curso IS NULL")
            conexao.commit()
        logger.info("Esquema do banco atualizado com sucesso")
    except Exception as e:
        logger.exception(f"Erro ao atualizar esquema do banco: {e}")

def carregar_dados():
    try:
        atualizar_esquema_banco()
        with sqlite3.connect(DATABASE_FILE) as conexao:
            df = pd.read_sql_query("SELECT * FROM jovens_rotas", conexao)
        logger.info(f"Carregados {len(df)} registros do banco local")
        return df
    except Exception as e:
        logger.exception(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def inserir_novo_jovem(nome, cpf, cep_casa, cep_trabalho, matricula):
    try:
        status_rota = "Otimizado"
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute('''
                INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota))
            conexao.commit()
        logger.info(f"Novo jovem inserido: {nome}")
        return True
    except Exception as e:
        logger.exception(f"Erro ao inserir novo jovem: {e}")
        return False

def cpf_ja_existe(cpf):
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT COUNT(*) FROM jovens_rotas WHERE cpf = ?", (cpf,))
            resultado = cursor.fetchone()[0]
        return resultado > 0
    except Exception as e:
        logger.exception(f"Erro ao verificar CPF: {e}")
        return False

def excluir_jovem(id_jovem):
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM jovens_rotas WHERE id = ?", (id_jovem,))
            conexao.commit()
    except Exception as e:
        logger.exception(f"Erro ao excluir jovem: {e}")

def atualizar_banco_geral():
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            
            colunas_novas = [
                ("data_consulta", "TEXT"), ("sla_segundos", "REAL"), ("matricula", "TEXT"),
                ("status_rota", "TEXT DEFAULT 'Otimizado'"), ("email", "TEXT"),
                ("celular", "TEXT"), ("numero_casa", "TEXT"), ("coordenadas", "TEXT"),
                ("modo_rota", "TEXT DEFAULT 'automatica'"),
                ("tipo_bilhete_manual", "TEXT"),
                ("valor_tarifa_manual", "REAL"),
                ("descricao_itinerario_manual", "TEXT"),
                ("assinatura_digital", "TEXT"),
                ("cep_curso", "TEXT"),
                ("status_curso", "TEXT DEFAULT 'Otimizado'")
            ]
            
            for coluna, tipo in colunas_novas:
                try:
                    cursor.execute(f"ALTER TABLE jovens_rotas ADD COLUMN {coluna} {tipo}")
                except sqlite3.OperationalError:
                    pass

            cursor.execute("UPDATE jovens_rotas SET status_rota = 'Otimizado' WHERE status_rota IS NULL")
            cursor.execute("UPDATE jovens_rotas SET modo_rota = 'automatica' WHERE modo_rota IS NULL")
            cursor.execute("UPDATE jovens_rotas SET status_curso = 'Otimizado' WHERE status_curso IS NULL")
            conexao.commit()
    except Exception as e:
        logger.exception(f"Erro na atualização geral do banco: {e}")

def atualizar_dados_funcionario(id_jovem, matricula, email, celular, cep, numero, coordenadas):
    try:
        id_jovem = int(id_jovem)
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT id FROM jovens_rotas WHERE id = ?", (id_jovem,))
            existe = cursor.fetchone()
            if not existe:
                logger.error(f"Registro com ID {id_jovem} não encontrado no banco")
                return False
            cursor.execute('''
                UPDATE jovens_rotas 
                SET matricula = ?, email = ?, celular = ?, 
                    cep_casa = ?, numero_casa = ?, coordenadas = ?
                WHERE id = ?
            ''', (matricula, email, celular, cep, numero, coordenadas, id_jovem))
            conexao.commit()
            sucesso = cursor.rowcount > 0
        return sucesso
    except Exception as e:
        logger.exception(f"ERRO na atualização: {str(e)}")
        return False

def salvar_rota_manual(id_jovem, tipo_bilhete, valor_tarifa, descricao_itinerario):
    """Salva os dados da rota manual no banco de dados"""
    try:
        id_jovem = int(id_jovem)
        with sqlite3.connect(DATABASE_FILE) as conexao:
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
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT COUNT(DISTINCT id) FROM jovens_rotas")
            total_consultas = cursor.fetchone()[0] or 0
            cursor.execute("SELECT AVG(sla_segundos) FROM jovens_rotas WHERE sla_segundos IS NOT NULL")
            sla_medio = cursor.fetchone()[0] or 0.0
            cursor.execute("SELECT COUNT(*) FROM contestacoes")
            total_contestacoes = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM jovens_rotas WHERE status_rota = 'Implantado'")
            total_implantados = cursor.fetchone()[0] or 0
        return total_consultas, sla_medio, total_contestacoes, total_implantados
    except Exception as e:
        logger.exception(f"Erro ao obter dados do dashboard: {e}")
        return 0, 0.0, 0, 0

def atualizar_banco_para_contestacoes():
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
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
            try:
                cursor.execute("ALTER TABLE contestacoes ADD COLUMN status TEXT DEFAULT 'Pendente'")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE contestacoes ADD COLUMN tratativa TEXT")
            except sqlite3.OperationalError:
                pass
            conexao.commit()
    except Exception as e:
        logger.exception(f"Erro ao atualizar banco de contestações: {e}")

def resolver_contestacao(id_contestacao, tratativa):
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute("UPDATE contestacoes SET status = 'Resolvido', tratativa = ? WHERE id = ?",
                           (tratativa, id_contestacao))
            cursor.execute("SELECT nome_jovem FROM contestacoes WHERE id = ?", (id_contestacao,))
            resultado = cursor.fetchone()
            if resultado:
                nome_jovem = resultado[0]
                cursor.execute("UPDATE jovens_rotas SET status_rota = 'Otimizado' WHERE nome = ?", (nome_jovem,))
            conexao.commit()
    except Exception as e:
        logger.exception(f"Erro ao resolver contestação: {e}")

def registrar_contestacao(nome, cid_res, cid_trab, motivo):
    try:
        data_atual = datetime.datetime.now().strftime("%d/%m/%Y às %Hh%Mm")
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute('''
                INSERT INTO contestacoes (nome_jovem, cidade_residencia, cidade_trabalho, motivo, data_geracao)
                VALUES (?, ?, ?, ?, ?)
            ''', (nome, cid_res, cid_trab, motivo, data_atual))
            conexao.commit()
    except Exception as e:
        logger.exception(f"Erro ao registrar contestação: {e}")

def criar_tabela_tokens():
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
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
    except Exception as e:
        logger.exception(f"Erro ao criar tabela de tokens: {e}")

def adicionar_colunas_assinatura():
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            for coluna in ("assinatura_path TEXT", "assinatura_data TEXT", "assinatura_ip TEXT"):
                try:
                    cursor.execute(f"ALTER TABLE jovens_rotas ADD COLUMN {coluna}")
                except sqlite3.OperationalError:
                    pass
            conexao.commit()
    except Exception as e:
        logger.exception(f"Erro ao adicionar colunas de assinatura: {e}")

def criar_tabela_locais_trabalho():
    """Cria a tabela de locais de trabalho (unidades) e insere registro padrão"""
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS locais_trabalho (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_unidade TEXT NOT NULL UNIQUE,
                    tipo_local TEXT DEFAULT 'Trabalho',
                    cep TEXT NOT NULL,
                    logradouro TEXT,
                    numero TEXT,
                    bairro TEXT,
                    cidade_uf TEXT,
                    coordenadas TEXT,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            try:
                cursor.execute("ALTER TABLE locais_trabalho ADD COLUMN tipo_local TEXT DEFAULT 'Trabalho'")
            except sqlite3.OperationalError:
                pass
            cursor.execute("UPDATE locais_trabalho SET tipo_local = 'Trabalho' WHERE tipo_local IS NULL")
            cursor.execute("SELECT COUNT(*) FROM locais_trabalho WHERE nome_unidade = 'RENAPSI - SÃO PAULO-SP'")
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO locais_trabalho (nome_unidade, tipo_local, cep, logradouro, numero, bairro, cidade_uf, coordenadas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'RENAPSI - SÃO PAULO-SP', 'Trabalho', '01333010',
                    'RUA CINCINATO BRAGA', '388', 'BELA VISTA',
                    'SÃO PAULO - SP', '-23.56774139404297, -46.646541595458984'
                ))
            conexao.commit()
        logger.info("Tabela locais_trabalho criada/atualizada com sucesso")
    except Exception as e:
        logger.exception(f"Erro ao criar tabela de locais de trabalho: {e}")

def criar_tabela_jovens_rotas():
    """Cria a tabela principal jovens_rotas se não existir."""
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            conexao.execute('''
                CREATE TABLE IF NOT EXISTS jovens_rotas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cpf TEXT,
                    cep_casa TEXT,
                    cep_trabalho TEXT,
                    matricula TEXT,
                    status_rota TEXT DEFAULT 'Otimizado',
                    email TEXT,
                    celular TEXT,
                    numero_casa TEXT,
                    coordenadas TEXT,
                    modo_rota TEXT DEFAULT 'automatica',
                    tipo_bilhete_manual TEXT,
                    valor_tarifa_manual REAL,
                    descricao_itinerario_manual TEXT,
                    assinatura_digital TEXT,
                    assinatura_path TEXT,
                    assinatura_data TEXT,
                    assinatura_ip TEXT,
                    ultima_carta_enviada TEXT,
                    observacoes TEXT,
                    data_consulta TEXT,
                    sla_segundos REAL,
                    cep_curso TEXT,
                    status_curso TEXT DEFAULT 'Otimizado',
                    local_trabalho_id INTEGER
                )
            ''')
            conexao.commit()
        logger.info("Tabela jovens_rotas criada/verificada com sucesso")
    except Exception as e:
        logger.exception(f"Erro ao criar tabela jovens_rotas: {e}")

def criar_tabela_fichas_cadastrais():
    """Cria a tabela fichas_cadastrais se não existir."""
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            conexao.execute('''
                CREATE TABLE IF NOT EXISTS fichas_cadastrais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cpf TEXT,
                    email TEXT,
                    celular TEXT,
                    cep_casa TEXT,
                    numero_casa TEXT,
                    cep_trabalho TEXT,
                    cep_curso TEXT,
                    matricula TEXT,
                    status_aprovacao TEXT DEFAULT 'Pendente',
                    data_envio TEXT,
                    observacoes TEXT
                )
            ''')
            conexao.commit()
        logger.info("Tabela fichas_cadastrais criada/verificada com sucesso")
    except Exception as e:
        logger.exception(f"Erro ao criar tabela fichas_cadastrais: {e}")

def inicializar_banco_completo():
    criar_tabela_jovens_rotas()
    criar_tabela_fichas_cadastrais()
    atualizar_esquema_banco()
    atualizar_banco_geral()
    atualizar_banco_para_contestacoes()
    criar_tabela_tokens()
    adicionar_colunas_assinatura()
    criar_tabela_locais_trabalho()
    criar_tabela_usuarios()
    seed_admin_padrao()
    criar_tabela_historico()
    criar_tabela_historico_aprovacoes()  # Nova tabela para histórico de triagem
    _colunas_extras = [
        ("ultima_carta_enviada", "TEXT"),
        ("observacoes", "TEXT"),
    ]
    try:
        with sqlite3.connect(DATABASE_FILE) as _c:
            for _col, _tipo in _colunas_extras:
                try:
                    _c.execute(f"ALTER TABLE jovens_rotas ADD COLUMN {_col} {_tipo}")
                except Exception:
                    pass
            _c.commit()
    except Exception:
        pass

def criar_tabela_historico_aprovacoes():
    """Cria tabela para histórico de aprovações/reprovações na triagem de fichas"""
    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS historico_aprovacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ficha_id INTEGER NOT NULL,
                    decisao TEXT NOT NULL,
                    usuario TEXT NOT NULL,
                    data_decisao TEXT NOT NULL,
                    comentario TEXT,
                    FOREIGN KEY (ficha_id) REFERENCES fichas_cadastrais(id)
                )
            ''')
            conn.commit()
            logger.info("Tabela historico_aprovacoes criada/verificada com sucesso")
    except Exception as e:
        logger.exception(f"Erro ao criar tabela historico_aprovacoes: {e}")

def atualizar_consulta_com_assinatura(consulta_id: int, filepath: str, ip_address: str, contexto: str = 'Trabalho') -> bool:
    try:
        timestamp_atual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if contexto == 'Trabalho':
            coluna_status = 'status_rota'
        elif contexto == 'Curso':
            coluna_status = 'status_curso'
        else:
            raise ValueError(f"Contexto inválido: {contexto}")
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute(f'''
                UPDATE jovens_rotas 
                SET {coluna_status} = 'Implantado',
                    assinatura_path = ?,
                    assinatura_data = ?,
                    assinatura_ip = ?
                WHERE id = ?
            ''', (filepath, timestamp_atual, ip_address, consulta_id))
            if cursor.rowcount == 0:
                print(f"ERRO: Consulta com ID {consulta_id} não encontrada")
                return False
            conexao.commit()
        print(f"✅ Consulta {consulta_id} atualizada: {coluna_status}='Implantado' (Contexto: {contexto})")
        return True
    except Exception as e:
        print(f"❌ ERRO na atualização da assinatura: {str(e)}")
        return False

def obter_status_consulta(consulta_id: int) -> str:
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT status_rota FROM jovens_rotas WHERE id = ?", (consulta_id,))
            resultado = cursor.fetchone()
        return resultado[0] if resultado else None
    except Exception as e:
        print(f"❌ ERRO ao obter status da consulta: {str(e)}")
        return None

def verificar_token_usado(token: str) -> bool:
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT used FROM tokens_assinatura WHERE token = ?", (token,))
            resultado = cursor.fetchone()
        if not resultado:
            return False
        return resultado[0] == 1
    except Exception as e:
        print(f"❌ ERRO ao verificar token: {str(e)}")
        return False


def obter_status_visual(status_rota):
    """Retorna a máscara visual do status"""
    mapeamento = {
        'Otimizado': '🔵 Aguardando Assinar',
        'Implantado': '🟢 Assinado/Ativo',
        'Contestada': '🟡 Em Revisão',
        'Não Optante': '⚪ Não Optante'
    }
    return mapeamento.get(status_rota, status_rota)


# ─── FUNÇÕES PARA TRIAGEM DE FICHAS ──────────────────────────────────────────

def obter_fichas_cadastrais(filtro_nome="", filtro_status="Pendente"):
    try:
        query = "SELECT * FROM fichas_cadastrais WHERE 1=1"
        params = []
        if filtro_nome.strip():
            query += " AND nome_completo LIKE ?"
            params.append(f"%{filtro_nome}%")
        if filtro_status != "Todos":
            query += " AND status_aprovacao = ?"
            params.append(filtro_status)
        query += " ORDER BY data_cadastro DESC"
        with sqlite3.connect(DATABASE_FILE) as conexao:
            df = pd.read_sql_query(query, conexao, params=params)
        return df
    except Exception as e:
        logger.exception(f"Erro ao obter fichas cadastrais: {e}")
        return pd.DataFrame()


def aprovar_ficha_e_integrar(ficha_id):
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("SELECT * FROM fichas_cadastrais WHERE id = ?", (ficha_id,))
            ficha = cursor.fetchone()
            if not ficha:
                conexao.rollback()
                return False, "Ficha não encontrada"
            ficha_dict = {
                'id': ficha[0], 'nome_completo': ficha[1], 'nome_social': ficha[2],
                'data_nascimento': ficha[3], 'cpf': ficha[4], 'rg': ficha[5],
                'identidade_genero': ficha[6], 'raca': ficha[7], 'estado_civil': ficha[8],
                'email_jovem': ficha[9], 'email_responsavel': ficha[10],
                'endereco_completo': ficha[11], 'cidade_estado': ficha[12], 'cep': ficha[13],
                'tel_jovem': ficha[14], 'tel_responsavel': ficha[15],
                'tamanho_uniforme': ficha[16], 'nome_mae': ficha[17],
                'ocupacao_mae': ficha[18], 'estado_civil_mae': ficha[19],
                'nome_pai': ficha[20], 'ocupacao_pai': ficha[21], 'estado_civil_pai': ficha[22],
                'nome_resp': ficha[23], 'ocupacao_resp': ficha[24], 'estado_civil_resp': ficha[25],
                'tem_dependentes': ficha[26], 'path_comp_residencia': ficha[27],
                'path_rg': ficha[28], 'path_conta_salario': ficha[29],
                'path_titulo': ficha[30], 'path_reservista': ficha[31],
                'path_casamento': ficha[32], 'path_cert_nasc_dep': ficha[33],
                'path_vacina_dep': ficha[34], 'data_cadastro': ficha[35],
                'status_aprovacao': ficha[36]
            }
            cursor.execute(
                "UPDATE fichas_cadastrais SET status_aprovacao = 'Aprovado' WHERE id = ?",
                (ficha_id,)
            )
            cursor.execute('''
                INSERT INTO jovens_rotas (
                    nome, cpf, cep_casa, cep_trabalho, email, celular,
                    matricula, status_rota, data_consulta
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ficha_dict['nome_completo'], ficha_dict['cpf'], ficha_dict['cep'],
                '', ficha_dict['email_jovem'], ficha_dict['tel_jovem'],
                '', 'Aguardando Rota', datetime.datetime.now().isoformat()
            ))
            conexao.commit()
        logger.info(f"Ficha {ficha_id} aprovada e integrada com sucesso")
        return True, f"✅ {ficha_dict['nome_completo']} foi integrado(a) ao banco de dados da mobilidade com sucesso!"
    except Exception as e:
        logger.exception(f"Erro ao aprovar ficha: {e}")
        return False, f"❌ Erro ao aprovar ficha: {str(e)}"


def reprovar_ficha(ficha_id, motivo=""):
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                "UPDATE fichas_cadastrais SET status_aprovacao = 'Reprovado' WHERE id = ?",
                (ficha_id,)
            )
            conexao.commit()
        logger.info(f"Ficha {ficha_id} reprovada")
        return True, "✅ Ficha reprovada com sucesso"
    except Exception as e:
        logger.exception(f"Erro ao reprovar ficha: {e}")
        return False, f"❌ Erro ao reprovar ficha: {str(e)}"


# ─── FUNÇÕES PARA GERENCIAMENTO DE LOCAIS DE TRABALHO ──────────────────────────

def obter_locais_trabalho(tipo_local=None):
    """Retorna lista de locais de trabalho filtrados por tipo."""
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            if tipo_local:
                cursor.execute("""
                    SELECT id, nome_unidade, tipo_local, cep, logradouro, numero, bairro, cidade_uf, coordenadas
                    FROM locais_trabalho WHERE tipo_local = ? ORDER BY nome_unidade
                """, (tipo_local,))
            else:
                cursor.execute("""
                    SELECT id, nome_unidade, tipo_local, cep, logradouro, numero, bairro, cidade_uf, coordenadas
                    FROM locais_trabalho ORDER BY nome_unidade
                """)
            locais = [
                {'id': r[0], 'nome_unidade': r[1], 'tipo_local': r[2], 'cep': r[3],
                 'logradouro': r[4], 'numero': r[5], 'bairro': r[6], 'cidade_uf': r[7],
                 'coordenadas': r[8]}
                for r in cursor.fetchall()
            ]
        return locais
    except Exception as e:
        logger.exception(f"Erro ao obter locais de trabalho: {e}")
        return []

def inserir_local_trabalho(nome_unidade, cep, logradouro, numero, bairro, cidade_uf, tipo_local='Trabalho', coordenadas=""):
    """Insere um novo local de trabalho no banco."""
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute("""
                INSERT INTO locais_trabalho (nome_unidade, tipo_local, cep, logradouro, numero, bairro, cidade_uf, coordenadas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nome_unidade, tipo_local, cep, logradouro, numero, bairro, cidade_uf, coordenadas))
            conexao.commit()
        logger.info(f"Local de trabalho '{nome_unidade}' ({tipo_local}) inserido com sucesso")
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
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute("""
                SELECT id, nome_unidade, cep, logradouro, numero, bairro, cidade_uf, coordenadas
                FROM locais_trabalho WHERE id = ?
            """, (local_id,))
            row = cursor.fetchone()
        if row:
            return {'id': row[0], 'nome_unidade': row[1], 'cep': row[2],
                    'logradouro': row[3], 'numero': row[4], 'bairro': row[5],
                    'cidade_uf': row[6], 'coordenadas': row[7]}
        return None
    except Exception as e:
        logger.exception(f"Erro ao obter local de trabalho: {e}")
        return None


def atualizar_local_trabalho(local_id, nome_unidade, cep, logradouro, numero, bairro, cidade_uf, tipo_local='Trabalho', coordenadas=""):
    """Atualiza os dados de um local de trabalho."""
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute("""
                UPDATE locais_trabalho
                SET nome_unidade = ?, tipo_local = ?, cep = ?, logradouro = ?, numero = ?, bairro = ?, cidade_uf = ?, coordenadas = ?
                WHERE id = ?
            """, (nome_unidade, tipo_local, cep, logradouro, numero, bairro, cidade_uf, coordenadas, local_id))
            conexao.commit()
            sucesso = cursor.rowcount > 0
        if sucesso:
            logger.info(f"Local de trabalho ID {local_id} atualizado com sucesso")
        return sucesso
    except Exception as e:
        logger.exception(f"Erro ao atualizar local de trabalho: {e}")
        return False


def deletar_local_trabalho(local_id):
    """Deleta um local de trabalho do banco."""
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM locais_trabalho WHERE id = ?", (local_id,))
            conexao.commit()
            sucesso = cursor.rowcount > 0
        if sucesso:
            logger.info(f"Local de trabalho ID {local_id} deletado com sucesso")
        return sucesso
    except Exception as e:
        logger.exception(f"Erro ao deletar local de trabalho: {e}")
        return False


def atualizar_status_rota(id_jovem, novo_status, contexto='Trabalho'):
    """Atualiza status da rota para o contexto especificado."""
    try:
        id_jovem = int(id_jovem)
        if contexto == 'Trabalho':
            coluna = 'status_rota'
        elif contexto == 'Curso':
            coluna = 'status_curso'
        else:
            raise ValueError(f"Contexto inválido: {contexto}")
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute(f"UPDATE jovens_rotas SET {coluna} = ? WHERE id = ?", (novo_status, id_jovem))
            conexao.commit()
            sucesso = cursor.rowcount > 0
        if sucesso:
            logger.info(f"Status {contexto} atualizado para {novo_status} (ID: {id_jovem})")
        return sucesso
    except Exception as e:
        logger.exception(f"Erro ao atualizar status: {e}")
        return False


# ─── AUTENTICAÇÃO DE USUÁRIOS ─────────────────────────────────────────────────

def criar_tabela_usuarios():
    """Cria a tabela de usuários do sistema se não existir."""
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            conexao.execute('''
                CREATE TABLE IF NOT EXISTS usuarios_sistema (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'funcionario',
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    criado_por TEXT,
                    deve_trocar_senha INTEGER DEFAULT 0
                )
            ''')
            # Adiciona coluna deve_trocar_senha se não existir (bancos antigos)
            try:
                conexao.execute("ALTER TABLE usuarios_sistema ADD COLUMN deve_trocar_senha INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            conexao.commit()
        logger.info("Tabela usuarios_sistema criada/verificada com sucesso")
    except Exception as e:
        logger.exception(f"Erro ao criar tabela de usuários: {e}")


def seed_admin_padrao():
    """
    Garante que o usuário admin padrão existe no banco.
    Só insere se ainda não existir — nunca sobrescreve.
    Marca deve_trocar_senha=1 para forçar troca na primeira entrada.
    """
    from werkzeug.security import generate_password_hash
    try:
        with sqlite3.connect(DATABASE_FILE) as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT COUNT(*) FROM usuarios_sistema WHERE username = ?", ("ADMIN_HGMC7",))
            if cursor.fetchone()[0] == 0:
                hash_senha = generate_password_hash("kUZ9TN>w:H>i2,+^TxwwMC", method="pbkdf2:sha256")
                cursor.execute(
                    "INSERT INTO usuarios_sistema (username, password_hash, role, criado_por, deve_trocar_senha) VALUES (?, ?, ?, ?, ?)",
                    ("ADMIN_HGMC7", hash_senha, "admin", "sistema", 1)
                )
                conexao.commit()
                logger.info("Admin padrão criado com sucesso")
    except Exception as e:
        logger.exception(f"Erro ao criar admin padrão: {e}")


def verificar_credenciais(username: str, password: str):
    """
    Verifica usuário e senha. Retorna dict com dados do usuário ou None.
    Inclui flag deve_trocar_senha para forçar troca na primeira entrada.
    """
    from werkzeug.security import check_password_hash
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, role, deve_trocar_senha FROM usuarios_sistema WHERE username = ?",
            (username.strip(),)
        )
        row = cursor.fetchone()
        conexao.close()
        if row and check_password_hash(row[2], password):
            return {
                "id": row[0], 
                "username": row[1], 
                "role": row[3],
                "deve_trocar_senha": row[4] if len(row) > 4 else 0
            }
        return None
    except Exception as e:
        logger.exception(f"Erro ao verificar credenciais: {e}")
        return None


def listar_usuarios():
    """Retorna todos os usuários (sem hash de senha) para o painel admin."""
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        df = pd.read_sql_query(
            "SELECT id, username, role, criado_em, criado_por FROM usuarios_sistema ORDER BY criado_em DESC",
            conexao
        )
        conexao.close()
        return df
    except Exception as e:
        logger.exception(f"Erro ao listar usuários: {e}")
        return pd.DataFrame()


def trocar_senha_usuario(user_id: int, nova_senha: str) -> tuple:
    """
    Troca a senha de um usuário e marca deve_trocar_senha=0.
    Retorna (sucesso: bool, mensagem: str).
    """
    from werkzeug.security import generate_password_hash
    if len(nova_senha) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres."
    try:
        hash_senha = generate_password_hash(nova_senha, method="pbkdf2:sha256")
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        cursor.execute(
            "UPDATE usuarios_sistema SET password_hash = ?, deve_trocar_senha = 0 WHERE id = ?",
            (hash_senha, user_id)
        )
        conexao.commit()
        conexao.close()
        logger.info(f"Senha trocada para user_id={user_id}")
        return True, "✅ Senha alterada com sucesso."
    except Exception as e:
        logger.exception(f"Erro ao trocar senha: {e}")
        return False, f"❌ Erro interno: {str(e)}"


def criar_usuario(username: str, password: str, role: str, criado_por: str) -> tuple:
    """
    Cria um novo usuário. Retorna (sucesso: bool, mensagem: str).
    """
    from werkzeug.security import generate_password_hash
    if not username.strip() or not password.strip():
        return False, "Usuário e senha são obrigatórios."
    try:
        hash_senha = generate_password_hash(password, method="pbkdf2:sha256")
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO usuarios_sistema (username, password_hash, role, criado_por) VALUES (?, ?, ?, ?)",
            (username.strip(), hash_senha, role, criado_por)
        )
        conexao.commit()
        conexao.close()
        logger.info(f"Usuário '{username}' criado por '{criado_por}'")
        return True, f"✅ Usuário '{username}' criado com sucesso."
    except sqlite3.IntegrityError:
        return False, f"❌ O usuário '{username}' já existe."
    except Exception as e:
        logger.exception(f"Erro ao criar usuário: {e}")
        return False, f"❌ Erro interno: {str(e)}"


def excluir_usuario(user_id: int, solicitante_username: str) -> tuple:
    """Remove um usuário. Não permite auto-exclusão do admin."""
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        cursor.execute("SELECT username, role FROM usuarios_sistema WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            conexao.close()
            return False, "Usuário não encontrado."
        if row[0] == solicitante_username:
            conexao.close()
            return False, "Você não pode excluir sua própria conta."
        cursor.execute("DELETE FROM usuarios_sistema WHERE id = ?", (user_id,))
        conexao.commit()
        conexao.close()
        return True, f"✅ Usuário '{row[0]}' removido."
    except Exception as e:
        logger.exception(f"Erro ao excluir usuário: {e}")
        return False, f"❌ Erro interno: {str(e)}"


# ─── HISTÓRICO DE ALTERAÇÕES (AUDITORIA LGPD) ────────────────────────────────

def criar_tabela_historico():
    """Cria a tabela de histórico de alterações se não existir."""
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        conexao.execute('''
            CREATE TABLE IF NOT EXISTS historico_alteracoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL,
                acao TEXT NOT NULL,
                tabela TEXT NOT NULL,
                registro_id INTEGER,
                campo TEXT,
                valor_anterior TEXT,
                valor_novo TEXT,
                timestamp TEXT NOT NULL
            )
        ''')
        conexao.commit()
        conexao.close()
    except Exception as e:
        logger.exception(f"Erro ao criar tabela historico_alteracoes: {e}")


def registrar_historico(usuario: str, acao: str, tabela: str,
                        registro_id: int = None, campo: str = None,
                        valor_anterior: str = None, valor_novo: str = None):
    """
    Registra uma entrada no histórico de auditoria.

    Args:
        usuario: username do usuário logado
        acao: descrição da ação (ex: 'Edição de dados', 'Contestação registrada')
        tabela: nome da tabela afetada
        registro_id: ID do registro alterado
        campo: campo específico alterado (opcional)
        valor_anterior: valor antes da alteração (opcional)
        valor_novo: valor após a alteração (opcional)
    """
    try:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conexao = sqlite3.connect(DATABASE_FILE)
        conexao.execute('''
            INSERT INTO historico_alteracoes
                (usuario, acao, tabela, registro_id, campo, valor_anterior, valor_novo, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (usuario, acao, tabela, registro_id, campo, valor_anterior, valor_novo, ts))
        conexao.commit()
        conexao.close()
    except Exception as e:
        logger.exception(f"Erro ao registrar histórico: {e}")


def obter_historico(registro_id: int = None, usuario: str = None, limite: int = 100):
    """
    Retorna o histórico de alterações filtrado.

    Args:
        registro_id: filtra por ID do registro (opcional)
        usuario: filtra por usuário (opcional)
        limite: máximo de registros retornados
    """
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        query = "SELECT * FROM historico_alteracoes WHERE 1=1"
        params = []
        if registro_id is not None:
            query += " AND registro_id = ?"
            params.append(registro_id)
        if usuario:
            query += " AND usuario = ?"
            params.append(usuario)
        query += f" ORDER BY timestamp DESC LIMIT {int(limite)}"
        df = pd.read_sql_query(query, conexao, params=params)
        conexao.close()
        return df
    except Exception as e:
        logger.exception(f"Erro ao obter histórico: {e}")
        return pd.DataFrame()


def registrar_sla(consulta_id: int, tempo_segundos: float):
    """
    Registra o tempo de processamento (SLA) de uma consulta/roteirização.
    
    Args:
        consulta_id: ID da consulta na tabela jovens_rotas
        tempo_segundos: Tempo de processamento em segundos
    """
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        
        # Atualiza o SLA e a data da consulta
        data_consulta = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE jovens_rotas 
            SET sla_segundos = ?, data_consulta = ?
            WHERE id = ?
        """, (tempo_segundos, data_consulta, consulta_id))
        
        conexao.commit()
        conexao.close()
        logger.info(f"SLA registrado: ID={consulta_id}, Tempo={tempo_segundos:.2f}s")
        return True
    except Exception as e:
        logger.exception(f"Erro ao registrar SLA: {e}")
        return False
