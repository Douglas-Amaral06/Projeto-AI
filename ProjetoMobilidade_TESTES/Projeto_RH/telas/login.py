"""Tela de login do sistema RENAPSI."""

import streamlit as st
from banco_dados import verificar_credenciais


def renderizar_login():
    """
    Exibe a tela de login e gerencia a sessão.
    Retorna True se o usuário está autenticado, False caso contrário.
    """
    # Já logado — não exibe a tela
    if st.session_state.get("usuario_logado"):
        return True

    # ── Layout centralizado ──────────────────────────────────────────────────
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer     {visibility: hidden;}
    header     {visibility: hidden;}

    .stApp {
        background: #FFFFFF !important;
    }

    /* Oculta a sidebar na tela de login */
    [data-testid="stSidebar"] {
        display: none !important;
    }

    .login-card {
        max-width: 420px;
        margin: 60px auto 0 auto;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 40px 36px 32px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    }

    .login-logo-area {
        text-align: center;
        margin-bottom: 28px;
    }

    .login-title {
        color: #444c9b !important;
        font-size: 22px !important;
        font-weight: 800 !important;
        margin: 12px 0 4px !important;
    }

    .login-subtitle {
        color: #64748B !important;
        font-size: 13px !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
    }

    /* Inputs */
    .stTextInput > div > div > input {
        background: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        color: #1E293B !important;
        font-size: 16px !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #f8ae28 !important;
        box-shadow: 0 0 0 2px rgba(248,174,40,0.15) !important;
    }

    /* Botão primário */
    .stButton > button[kind="primary"] {
        background: #f8ae28 !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        border-radius: 8px !important;
        width: 100% !important;
        padding: 12px !important;
        box-shadow: 0 2px 6px rgba(248,174,40,0.35) !important;
        transition: background 0.2s, transform 0.1s !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #e09a1f !important;
        transform: translateY(-1px) !important;
    }

    /* Labels */
    label, p, span, div {
        color: #333333 !important;
        font-size: 15px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Centraliza com colunas
    col_l, col_center, col_r = st.columns([1, 2, 1])

    with col_center:
        # Logo + título
        st.markdown("""
        <div class="login-logo-area">
            <svg viewBox="0 0 133.83 114" width="72" height="60">
              <defs><style>.s2-1{fill:#fff;} .s2-2{fill:#402fdd;}</style></defs>
              <g>
                <path class="s2-2" d="M57,0C25.52,0,0,25.52,0,57s25.52,57,57,57h19.83c31.48,0,57-25.52,57-57S108.31,0,76.83,0h-19.83Z"/>
                <path class="s2-1" d="M66.91,48.07c-9.15,0-16.59,7.48-16.59,16.66s7.44,16.66,16.59,16.66,16.59-7.48,16.59-16.66-7.44-16.66-16.59-16.66M66.91,88.58c-13.09,0-23.74-10.7-23.74-23.85s10.65-23.85,23.74-23.85,23.74,10.7,23.74,23.85-10.65,23.85-23.74,23.85"/>
                <polygon class="s2-1" points="90.66 88.58 83.5 87.55 83.5 29.11 90.66 30.14 90.66 88.58"/>
                <polygon class="s2-1" points="56.55 25.42 56.55 32.47 77.28 35.45 77.28 28.4 56.55 25.42"/>
              </g>
            </svg>
            <p class="login-title">RENAPSI Mobilidade</p>
            <p class="login-subtitle">Sistema de Mobilidade Urbana</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#E2E8F0;margin:0 0 24px;'>", unsafe_allow_html=True)

        with st.form("form_login", clear_on_submit=False):
            username = st.text_input("Usuário", placeholder="Digite seu usuário")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)

        if submitted:
            if not username.strip() or not password.strip():
                st.error("⚠️ Preencha usuário e senha.")
            else:
                usuario = verificar_credenciais(username, password)
                if usuario:
                    st.session_state["usuario_logado"] = True
                    st.session_state["usuario_dados"] = usuario
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos.")

        st.markdown("""
        <p style="color:#94A3B8;font-size:12px;text-align:center;margin-top:24px;">
            🔒 Acesso restrito a funcionários autorizados
        </p>
        """, unsafe_allow_html=True)

    return False
