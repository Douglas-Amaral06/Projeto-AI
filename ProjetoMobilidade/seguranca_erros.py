"""
Módulo de Tratamento Seguro de Erros para Streamlit.
Evita expor informações técnicas sensíveis ao usuário.
"""

import logging
import streamlit as st
from functools import wraps

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def executar_com_seguranca(funcao):
    """
    Decorator que executa uma função com tratamento seguro de erros.
    
    Erros técnicos são registrados em log, mas mensagens genéricas
    são mostradas ao usuário para não expor detalhes da infraestrutura.
    """
    @wraps(funcao)
    def wrapper(*args, **kwargs):
        try:
            return funcao(*args, **kwargs)
        except ValueError as e:
            # Erros de validação podem ser mostrados
            logger.warning(f"Erro de validação em {funcao.__name__}: {e}")
            st.error(f"❌ {str(e)}")
            return None
        except ConnectionError as e:
            logger.exception(f"Erro de conexão em {funcao.__name__}")
            st.error("❌ Erro ao conectar ao servidor. Tente novamente mais tarde.")
            return None
        except TimeoutError as e:
            logger.exception(f"Timeout em {funcao.__name__}")
            st.error("❌ Operação expirou. Tente novamente.")
            return None
        except Exception as e:
            # Erros genéricos não devem expor detalhes técnicos
            logger.exception(f"Erro inesperado em {funcao.__name__}: {e}")
            st.error("❌ Erro ao processar solicitação. Contate o administrador.")
            return None
    
    return wrapper


def mostrar_erro_seguro(titulo: str, mensagem_tecnica: str = None):
    """
    Mostra um erro de forma segura ao usuário.
    
    Args:
        titulo: Mensagem amigável para o usuário
        mensagem_tecnica: Mensagem técnica para logging (opcional)
    """
    if mensagem_tecnica:
        logger.error(f"[ERRO TÉCNICO] {mensagem_tecnica}")
    
    st.error(f"❌ {titulo}")


def mostrar_aviso_seguro(titulo: str, mensagem_tecnica: str = None):
    """
    Mostra um aviso de forma segura ao usuário.
    
    Args:
        titulo: Mensagem amigável para o usuário
        mensagem_tecnica: Mensagem técnica para logging (opcional)
    """
    if mensagem_tecnica:
        logger.warning(f"[AVISO TÉCNICO] {mensagem_tecnica}")
    
    st.warning(f"⚠️ {titulo}")


def validar_entrada(valor, tipo_esperado, nome_campo):
    """
    Valida entrada de usuário de forma segura.
    
    Args:
        valor: Valor a validar
        tipo_esperado: Tipo esperado (str, int, float, etc)
        nome_campo: Nome do campo para mensagem de erro
        
    Returns:
        True se válido, False caso contrário
    """
    try:
        if valor is None or valor == "":
            mostrar_erro_seguro(f"❌ {nome_campo} é obrigatório")
            return False
        
        if not isinstance(valor, tipo_esperado):
            mostrar_erro_seguro(f"❌ {nome_campo} deve ser do tipo {tipo_esperado.__name__}")
            return False
        
        return True
    except Exception as e:
        logger.exception(f"Erro ao validar {nome_campo}")
        mostrar_erro_seguro("❌ Erro ao validar entrada")
        return False


class GerenciadorErrosSeguro:
    """
    Gerenciador centralizado de erros para a aplicação.
    """
    
    @staticmethod
    def processar_erro_banco_dados(erro: Exception, operacao: str):
        """Processa erros de banco de dados de forma segura."""
        logger.exception(f"Erro de banco de dados em {operacao}: {erro}")
        mostrar_erro_seguro(
            "❌ Erro ao acessar banco de dados",
            f"Operação: {operacao}, Erro: {str(erro)}"
        )
    
    @staticmethod
    def processar_erro_api(erro: Exception, api_nome: str):
        """Processa erros de API de forma segura."""
        logger.exception(f"Erro de API ({api_nome}): {erro}")
        mostrar_erro_seguro(
            f"❌ Erro ao conectar com {api_nome}",
            f"API: {api_nome}, Erro: {str(erro)}"
        )
    
    @staticmethod
    def processar_erro_email(erro: Exception):
        """Processa erros de envio de e-mail de forma segura."""
        logger.exception(f"Erro ao enviar e-mail: {erro}")
        mostrar_erro_seguro(
            "❌ Erro ao enviar e-mail",
            f"Erro: {str(erro)}"
        )
    
    @staticmethod
    def processar_erro_arquivo(erro: Exception, arquivo: str):
        """Processa erros de arquivo de forma segura."""
        logger.exception(f"Erro ao processar arquivo {arquivo}: {erro}")
        mostrar_erro_seguro(
            "❌ Erro ao processar arquivo",
            f"Arquivo: {arquivo}, Erro: {str(erro)}"
        )
