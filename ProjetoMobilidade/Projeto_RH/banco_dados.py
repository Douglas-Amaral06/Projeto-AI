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

def inicializar_banco_completo():
    atualizar_banco_geral()
    atualizar_banco_para_contestacoes()
    criar_tabela_tokens()
    adicionar_colunas_assinatura()

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
