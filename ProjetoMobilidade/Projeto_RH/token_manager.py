import os
"""
Módulo de gerenciamento de tokens de assinatura digital.

Este módulo fornece funcionalidades para:
- Gerar tokens criptograficamente seguros
- Validar tokens de assinatura
- Gerenciar ciclo de vida de tokens (expiração, uso)
- Limpar tokens expirados

Os tokens são usados para autenticar solicitações de assinatura digital
de Vale-Transporte através de links únicos enviados por email.
"""

import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Optional


def gerar_token(consulta_id: int) -> dict:
    """
    Gera token de assinatura único e seguro para uma consulta.
    
    Cria um token criptograficamente seguro usando secrets.token_urlsafe(32),
    calcula timestamps de criação e expiração (30 dias), e armazena no banco
    de dados com lógica de retry para colisões (máximo 3 tentativas).
    
    Args:
        consulta_id: ID da consulta na tabela jovens_rotas
        
    Returns:
        dict contendo:
            - token (str): Token gerado (43+ caracteres base64url)
            - url (str): URL completa para página de assinatura
            - created_at (str): Timestamp de criação (ISO 8601)
            - expires_at (str): Timestamp de expiração (ISO 8601)
            
    Raises:
        ValueError: Se consulta_id não existir no banco
        RuntimeError: Se não conseguir gerar token único após 3 tentativas
        
    Example:
        >>> resultado = gerar_token(123)
        >>> print(resultado['token'])
        'xK7j9mP2qR...'
        >>> print(resultado['url'])
        'http://localhost:8501/assinar?token=xK7j9mP2qR...'
    """
    # Validar que consulta_id existe
    conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
    cursor = conexao.cursor()
    
    cursor.execute("SELECT id FROM jovens_rotas WHERE id = ?", (consulta_id,))
    if not cursor.fetchone():
        conexao.close()
        raise ValueError(f"Consulta ID {consulta_id} não encontrada no banco de dados")
    
    # Calcular timestamps
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expires_at = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    
    # Tentar gerar token único com retry logic (máximo 3 tentativas)
    max_tentativas = 3
    token = None
    
    for tentativa in range(1, max_tentativas + 1):
        # Gerar token criptograficamente seguro
        token_candidato = secrets.token_urlsafe(32)
        
        try:
            # Tentar inserir no banco
            cursor.execute('''
                INSERT INTO tokens_assinatura 
                (token, consulta_id, created_at, expires_at, used)
                VALUES (?, ?, ?, ?, 0)
            ''', (token_candidato, consulta_id, created_at, expires_at))
            
            conexao.commit()
            token = token_candidato
            break  # Sucesso, sair do loop
            
        except sqlite3.IntegrityError:
            # Colisão de token (extremamente raro), tentar novamente
            if tentativa == max_tentativas:
                conexao.close()
                raise RuntimeError(
                    f"Não foi possível gerar token único após {max_tentativas} tentativas"
                )
            continue
    
    conexao.close()
    
    # Construir URL de assinatura
    url = f"http://localhost:8501/assinar?token={token}"
    
    return {
        "token": token,
        "url": url,
        "created_at": created_at,
        "expires_at": expires_at
    }


def validar_token(token: str) -> dict:
    """
    Valida token de assinatura e retorna dados da consulta associada.
    
    Verifica se o token existe, não expirou e não foi usado. Se válido,
    retorna os dados completos da consulta para exibição na página de assinatura.
    
    Args:
        token: Token a ser validado
        
    Returns:
        dict contendo:
            - valido (bool): True se token é válido
            - erro (str): Mensagem de erro se inválido (None se válido)
            - dados_consulta (dict): Dados da consulta se válido (None se inválido)
            
    Example:
        >>> resultado = validar_token("xK7j9mP2qR...")
        >>> if resultado['valido']:
        ...     print(resultado['dados_consulta']['nome'])
    """
    # Validar formato do token (deve ser string alfanumérica com pelo menos 32 caracteres)
    if not token or not isinstance(token, str):
        return {
            "valido": False,
            "erro": "invalido",
            "dados_consulta": None
        }
    
    # Verificar comprimento mínimo
    if len(token) < 32:
        return {
            "valido": False,
            "erro": "invalido",
            "dados_consulta": None
        }
    
    # Conectar ao banco de dados
    conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
    cursor = conexao.cursor()
    
    try:
        # Buscar token no banco
        cursor.execute('''
            SELECT consulta_id, expires_at, used
            FROM tokens_assinatura
            WHERE token = ?
        ''', (token,))
        
        resultado = cursor.fetchone()
        
        # Token não existe no banco
        if not resultado:
            conexao.close()
            return {
                "valido": False,
                "erro": "invalido",
                "dados_consulta": None
            }
        
        consulta_id, expires_at, used = resultado
        
        # Verificar se token já foi usado
        if used == 1:
            conexao.close()
            return {
                "valido": False,
                "erro": "usado",
                "dados_consulta": None
            }
        
        # Verificar se token expirou
        expires_at_dt = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        
        if now > expires_at_dt:
            conexao.close()
            return {
                "valido": False,
                "erro": "expirado",
                "dados_consulta": None
            }
        
        # Token é válido, carregar dados da consulta
        cursor.execute('''
            SELECT id, nome, cpf, cep_casa, cep_trabalho, matricula, 
                   status_rota, email, celular, numero_casa, coordenadas,
                   data_consulta, sla_segundos
            FROM jovens_rotas
            WHERE id = ?
        ''', (consulta_id,))
        
        consulta_row = cursor.fetchone()
        
        if not consulta_row:
            # Consulta não existe (inconsistência no banco)
            conexao.close()
            return {
                "valido": False,
                "erro": "invalido",
                "dados_consulta": None
            }
        
        # Construir dicionário com dados da consulta
        dados_consulta = {
            "id": consulta_row[0],
            "nome": consulta_row[1],
            "cpf": consulta_row[2],
            "cep_casa": consulta_row[3],
            "cep_trabalho": consulta_row[4],
            "matricula": consulta_row[5],
            "status_rota": consulta_row[6],
            "email": consulta_row[7],
            "celular": consulta_row[8],
            "numero_casa": consulta_row[9],
            "coordenadas": consulta_row[10],
            "data_consulta": consulta_row[11],
            "sla_segundos": consulta_row[12]
        }
        
        conexao.close()
        
        return {
            "valido": True,
            "erro": None,
            "dados_consulta": dados_consulta
        }
        
    except Exception as e:
        conexao.close()
        # Em caso de erro inesperado, retornar como inválido
        return {
            "valido": False,
            "erro": "invalido",
            "dados_consulta": None
        }


def marcar_token_usado(token: str, ip_cliente: Optional[str] = None) -> bool:
    """
    Marca token como usado após assinatura ou cancelamento.
    
    Atualiza o campo 'used' para 1 e registra timestamp e IP do cliente.
    Previne reutilização do mesmo link de assinatura.
    
    Args:
        token: Token a ser marcado como usado
        ip_cliente: Endereço IP do cliente (opcional)
        
    Returns:
        bool: True se token foi marcado com sucesso, False caso contrário
        
    Example:
        >>> sucesso = marcar_token_usado("xK7j9mP2qR...", "192.168.1.100")
        >>> print(sucesso)
        True
    """
    try:
        # Conectar ao banco de dados
        conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        cursor = conexao.cursor()
        
        # Registrar timestamp atual
        used_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Atualizar token: marcar como usado e registrar timestamp
        cursor.execute('''
            UPDATE tokens_assinatura 
            SET used = 1, used_at = ?
            WHERE token = ?
        ''', (used_at, token))
        
        # Verificar se alguma linha foi afetada
        linhas_afetadas = cursor.rowcount
        
        # Commit das mudanças
        conexao.commit()
        conexao.close()
        
        # Retornar True se token foi encontrado e atualizado, False caso contrário
        return linhas_afetadas > 0
        
    except Exception as e:
        # Em caso de erro, retornar False
        return False


def limpar_tokens_expirados() -> int:
    """
    Remove tokens expirados e não usados do banco.
    
    Executa limpeza periódica de tokens que expiraram e nunca foram usados,
    liberando espaço no banco de dados. Tokens usados são mantidos para
    auditoria mesmo após expiração.
    
    Returns:
        int: Número de tokens removidos
        
    Example:
        >>> removidos = limpar_tokens_expirados()
        >>> print(f"Removidos {removidos} tokens expirados")
    """
    try:
        # Conectar ao banco de dados
        conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        cursor = conexao.cursor()
        
        # Obter timestamp atual
        timestamp_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Contar quantos tokens serão deletados (para logging)
        cursor.execute('''
            SELECT COUNT(*) FROM tokens_assinatura
            WHERE used = 0 AND expires_at < ?
        ''', (timestamp_atual,))
        
        count = cursor.fetchone()[0]
        
        # Se não há tokens para limpar, retornar 0
        if count == 0:
            conexao.close()
            print(f"[INFO] Limpeza de tokens: Nenhum token expirado para remover")
            return 0
        
        # Executar DELETE apenas de tokens não usados e expirados
        cursor.execute('''
            DELETE FROM tokens_assinatura
            WHERE used = 0 AND expires_at < ?
        ''', (timestamp_atual,))
        
        # Commit das mudanças
        conexao.commit()
        conexao.close()
        
        # Registrar log da operação
        print(f"[INFO] Limpeza de tokens: {count} tokens expirados removidos (preservando tokens usados para auditoria)")
        
        # Retornar contagem de tokens removidos
        return count
        
    except Exception as e:
        # Em caso de erro, registrar e retornar 0
        print(f"[ERROR] Erro ao limpar tokens expirados: {e}")
        return 0

