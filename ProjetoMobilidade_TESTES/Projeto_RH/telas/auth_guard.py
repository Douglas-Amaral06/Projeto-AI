"""
Módulo de proteção de autenticação para telas secundárias.
Importar e chamar exigir_login() no início de cada função renderizar_*().
"""
import streamlit as st


def exigir_login():
    """
    Verifica se o usuário está autenticado.
    Se não estiver, exibe mensagem e para a execução com st.stop().
    
    Uso:
        from telas.auth_guard import exigir_login
        
        def renderizar_minha_tela():
            exigir_login()
            # ... resto da tela
    """
    if not st.session_state.get("usuario_logado"):
        st.error("🔒 Acesso negado. Faça login para continuar.")
        st.info("Por favor, acesse o sistema pelo endereço principal.")
        st.stop()


def exigir_admin():
    """
    Verifica se o usuário está autenticado E tem perfil de admin.
    Se não estiver, exibe mensagem e para a execução com st.stop().
    
    Uso:
        from telas.auth_guard import exigir_admin
        
        def renderizar_tela_admin():
            exigir_admin()
            # ... resto da tela
    """
    exigir_login()
    usuario = st.session_state.get("usuario_dados", {})
    if usuario.get("role") != "admin":
        st.error("🚫 Acesso restrito a administradores.")
        st.stop()


def usuario_atual():
    """Retorna os dados do usuário logado ou dict vazio."""
    return st.session_state.get("usuario_dados", {})


def role_atual():
    """Retorna o perfil do usuário logado ('admin' ou 'funcionario')."""
    return usuario_atual().get("role", "funcionario")


def is_admin():
    """Retorna True se o usuário logado for admin."""
    return role_atual() == "admin"
