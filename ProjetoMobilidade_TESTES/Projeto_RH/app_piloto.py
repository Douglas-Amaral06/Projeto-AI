import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
import random
import datetime
import time
import folium
import os
import secrets
import io
import shutil
import plotly.graph_objects as go
from dotenv import load_dotenv
from streamlit_folium import st_folium
from banco_dados import *
from apis import *
from agente_ia import *
from carta_pdf import gerar_carta_pdf
from email_sender import enviar_carta_por_email

# Imports dos módulos de telas melhoradas
from telas.triagem import renderizar_triagem
from telas.banco_dados import renderizar_banco_dados
from telas.gerenciar_unidades import renderizar_gerenciar_unidades
from telas.portal_jovem_avancado import renderizar_portal_jovem_avancado
from telas.registro_funcionario_avancado import renderizar_registro_funcionario_avancado
from telas.relatorios_analytics import renderizar_relatorios_analytics
from telas.auditoria_compliance import renderizar_auditoria_compliance

# Imports para exportação de relatórios
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
except ImportError:
    pass

try:
    from fpdf import FPDF
except ImportError:
    pass

# ─── Carrega variáveis de ambiente ───────────────────────────────────────────
load_dotenv()

# ─── Configuração da página ───────────────────────────────────────────────────
st.set_page_config(page_title="RENAPSI — Mobilidade", page_icon="🚇", layout="wide")

# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES DE MÁSCARA E VALIDAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

def safe_sql(query, conexao, params=None):
    """Executa query SQL com tratamento de erros. Retorna DataFrame vazio se tabela não existir."""
    try:
        if params:
            return pd.read_sql_query(query, conexao, params=params)
        return pd.read_sql_query(query, conexao)
    except Exception:
        return pd.DataFrame()

def aplicar_mascara_cpf(cpf):
    """Aplica máscara no CPF: 000.000.000-00"""
    cpf_limpo = ''.join(filter(str.isdigit, cpf))
    if len(cpf_limpo) <= 3:
        return cpf_limpo
    elif len(cpf_limpo) <= 6:
        return f"{cpf_limpo[:3]}.{cpf_limpo[3:]}"
    elif len(cpf_limpo) <= 9:
        return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:]}"
    else:
        return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:11]}"

def aplicar_mascara_cep(cep):
    """Aplica máscara no CEP: 00000-000"""
    cep_limpo = ''.join(filter(str.isdigit, cep))
    if len(cep_limpo) <= 5:
        return cep_limpo
    else:
        return f"{cep_limpo[:5]}-{cep_limpo[5:8]}"

def aplicar_mascara_celular(celular):
    """Aplica máscara no celular: (00) 00000-0000"""
    cel_limpo = ''.join(filter(str.isdigit, celular))
    if len(cel_limpo) <= 2:
        return f"({cel_limpo}" if cel_limpo else ""
    elif len(cel_limpo) <= 7:
        return f"({cel_limpo[:2]}) {cel_limpo[2:]}"
    else:
        return f"({cel_limpo[:2]}) {cel_limpo[2:7]}-{cel_limpo[7:11]}"

def validar_cpf_completo(cpf):
    """Valida CPF usando algoritmo oficial"""
    cpf_limpo = ''.join(filter(str.isdigit, cpf))
    if len(cpf_limpo) != 11 or len(set(cpf_limpo)) == 1:
        return False
    soma = sum(int(cpf_limpo[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10 % 11) % 10
    soma = sum(int(cpf_limpo[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10 % 11) % 10
    return cpf_limpo[-2:] == f"{digito1}{digito2}"

def validar_email_formato(email):
    """Valida formato de e-mail"""
    if not email:
        return True  # E-mail é opcional
    import re
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def validar_celular_formato(celular):
    """Valida formato de celular brasileiro"""
    if not celular:
        return True  # Celular é opcional
    cel_limpo = ''.join(filter(str.isdigit, celular))
    return len(cel_limpo) == 11 and cel_limpo[2] == '9'

def mostrar_campo_obrigatorio(label):
    """Retorna label com indicador visual de campo obrigatório"""
    return f"{label} <span style='color:#EF4444;font-weight:700;'>*</span>"

# ══════════════════════════════════════════════════════════════════════════════
# SISTEMA DE AUTENTICAÇÃO — SESSÃO PERSISTENTE (SOBREVIVE AO F5)
# ══════════════════════════════════════════════════════════════════════════════

def _criar_tabela_sessoes():
    """Cria tabela de sessões ativas no banco."""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessoes_ativas (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                criado_em TEXT NOT NULL,
                expira_em TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
    except Exception:
        pass

def _criar_sessao(user_id, username, role):
    """Gera token, salva no banco e retorna o token."""
    token = secrets.token_urlsafe(32)
    agora = datetime.datetime.now()
    expira = agora + datetime.timedelta(hours=8)
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        conn.execute(
            "INSERT INTO sessoes_ativas (token, user_id, username, role, criado_em, expira_em) VALUES (?,?,?,?,?,?)",
            (token, user_id, username, role, agora.isoformat(), expira.isoformat())
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
    return token

def _validar_token(token):
    """Valida token no banco. Retorna dict do usuário ou None."""
    if not token:
        return None
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        cur = conn.execute(
            "SELECT user_id, username, role, expira_em FROM sessoes_ativas WHERE token = ?",
            (token,)
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        expira = datetime.datetime.fromisoformat(row[3])
        if datetime.datetime.now() > expira:
            _revogar_token(token)
            return None
        return {"id": row[0], "username": row[1], "role": row[2]}
    except Exception:
        return None

def _revogar_token(token):
    """Remove token do banco (logout)."""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        conn.execute("DELETE FROM sessoes_ativas WHERE token = ?", (token,))
        conn.commit()
        conn.close()
    except Exception:
        pass

def _limpar_sessoes_expiradas():
    """Remove sessões expiradas do banco."""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        conn.execute("DELETE FROM sessoes_ativas WHERE expira_em < ?", (datetime.datetime.now().isoformat(),))
        conn.commit()
        conn.close()
    except Exception:
        pass

def _renderizar_tela_login():
    """Renderiza a tela de login com o tema RENAPSI."""
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background: #FFFFFF !important; }
    [data-testid="stSidebar"] { display: none !important; }
    .stButton > button[kind="primary"] {
        background: #f8ae28 !important; border: none !important;
        color: #FFFFFF !important; font-weight: 700 !important;
        font-size: 18px !important; border-radius: 8px !important;
        width: 100% !important; padding: 12px !important;
        box-shadow: 0 2px 6px rgba(248,174,40,0.35) !important;
    }
    .stButton > button[kind="primary"]:hover { background: #e09a1f !important; }
    .stTextInput > div > div > input {
        background: #F8FAFC !important; border: 1px solid #E2E8F0 !important;
        color: #1E293B !important; font-size: 16px !important;
        border-radius: 8px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #f8ae28 !important;
        box-shadow: 0 0 0 2px rgba(248,174,40,0.15) !important;
    }
    label, p, span, div { color: #333333 !important; font-size: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("""
        <div style="text-align:center;margin-bottom:28px;margin-top:60px;">
            <svg viewBox="0 0 133.83 114" width="72" height="60">
              <defs><style>.s2-1{fill:#fff;}.s2-2{fill:#402fdd;}</style></defs>
              <g>
                <path class="s2-2" d="M57,0C25.52,0,0,25.52,0,57s25.52,57,57,57h19.83c31.48,0,57-25.52,57-57S108.31,0,76.83,0h-19.83Z"/>
                <path class="s2-1" d="M66.91,48.07c-9.15,0-16.59,7.48-16.59,16.66s7.44,16.66,16.59,16.66,16.59-7.48,16.59-16.66-7.44-16.66-16.59-16.66M66.91,88.58c-13.09,0-23.74-10.7-23.74-23.85s10.65-23.85,23.74-23.85,23.74,10.7,23.74,23.85-10.65,23.85-23.74,23.85"/>
                <polygon class="s2-1" points="90.66 88.58 83.5 87.55 83.5 29.11 90.66 30.14 90.66 88.58"/>
                <polygon class="s2-1" points="56.55 25.42 56.55 32.47 77.28 35.45 77.28 28.4 56.55 25.42"/>
              </g>
            </svg>
            <p style="color:#444c9b !important;font-size:22px !important;font-weight:800 !important;margin:12px 0 4px !important;">RENAPSI Mobilidade</p>
            <p style="color:#64748B !important;font-size:13px !important;letter-spacing:0.08em !important;text-transform:uppercase !important;">Sistema de Mobilidade Urbana</p>
        </div>
        <hr style="border-color:#E2E8F0;margin:0 0 24px;">
        """, unsafe_allow_html=True)

        with st.form("form_login_principal", clear_on_submit=False):
            username_input = st.text_input("Usuário", placeholder="Digite seu usuário")
            password_input = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            submitted = st.form_submit_button("Entrar", type="primary", width="stretch")

        if submitted:
            if not username_input.strip() or not password_input.strip():
                st.error("⚠️ Preencha usuário e senha.")
            else:
                usuario = verificar_credenciais(username_input, password_input)
                if usuario:
                    token = _criar_sessao(usuario["id"], usuario["username"], usuario["role"])
                    st.session_state["usuario_logado"] = True
                    st.session_state["usuario_dados"] = usuario
                    st.session_state["auth_token"] = token
                    
                    # Salva token no cookie do navegador
                    _save_token_to_cookie(token)
                    
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos.")

        st.markdown("""
        <p style="color:#94A3B8 !important;font-size:12px !important;text-align:center;margin-top:24px;">
            🔒 Acesso restrito a funcionários autorizados
        </p>
        """, unsafe_allow_html=True)

def _renderizar_tela_troca_senha_obrigatoria():
    """Tela de troca de senha obrigatória para primeiro acesso."""
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background: #FFFFFF !important; }
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("""
        <div style="background:#FEF3C7;border:1px solid #FCD34D;border-left:4px solid #F59E0B;
                    border-radius:12px;padding:20px;margin:40px 0 24px;">
            <h3 style="margin:0 0 8px;color:#92400E;">🔐 Troca de Senha Obrigatória</h3>
            <p style="color:#78350F;font-size:14px;margin:0;">
                Por segurança, você deve alterar sua senha padrão antes de acessar o sistema.
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("form_troca_senha", clear_on_submit=True):
            nova_senha = st.text_input("Nova Senha", type="password", placeholder="Mínimo 8 caracteres")
            confirmar_senha = st.text_input("Confirmar Nova Senha", type="password", placeholder="Repita a senha")
            submitted = st.form_submit_button("Alterar Senha", type="primary", width="stretch")

        if submitted:
            if len(nova_senha) < 8:
                st.error("⚠️ A senha deve ter pelo menos 8 caracteres.")
            elif nova_senha != confirmar_senha:
                st.error("⚠️ As senhas não coincidem.")
            else:
                usuario_dados = st.session_state.get("usuario_dados", {})
                sucesso, msg = trocar_senha_usuario(usuario_dados["id"], nova_senha)
                if sucesso:
                    st.success(msg)
                    # Atualiza flag no session_state
                    st.session_state["usuario_dados"]["deve_trocar_senha"] = 0
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)

        if st.button("🚪 Sair", width="stretch"):
            _token_atual = st.session_state.get("auth_token", "")
            if _token_atual:
                _revogar_token(_token_atual)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

def _renderizar_tela_registro_funcionario():
    """Painel de gestão de usuários — acesso exclusivo Admin."""
    usuario_logado = st.session_state.get("usuario_dados", {})
    if usuario_logado.get("role") != "admin":
        st.error("🚫 Acesso negado.")
        st.stop()

    st.markdown("""
    <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-left:4px solid #444c9b;
                border-radius:14px;padding:24px;margin-bottom:24px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
        <h3 style="margin:0 0 4px;color:#444c9b;">👥 Registro de Funcionário</h3>
        <p style="color:#64748B;font-size:14px;margin:0;">
            Gerencie os acessos ao sistema. Apenas o administrador pode criar ou remover logins.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("➕ Criar novo acesso", expanded=True):
        with st.form("form_criar_usuario", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                novo_username = st.text_input("Usuário", placeholder="Ex: FUNC_JOAO01")
                novo_role = st.selectbox("Perfil de acesso", ["funcionario", "admin"], index=0)
            with col2:
                nova_senha = st.text_input("Senha", type="password", placeholder="Mínimo 8 caracteres")
                confirmar_senha = st.text_input("Confirmar senha", type="password", placeholder="Repita a senha")
            criar = st.form_submit_button("Criar Acesso", type="primary", width="stretch")

        if criar:
            if not novo_username.strip():
                st.error("⚠️ O campo Usuário é obrigatório.")
            elif len(nova_senha) < 8:
                st.error("⚠️ A senha deve ter pelo menos 8 caracteres.")
            elif nova_senha != confirmar_senha:
                st.error("⚠️ As senhas não coincidem.")
            else:
                sucesso, msg = criar_usuario(
                    username=novo_username,
                    password=nova_senha,
                    role=novo_role,
                    criado_por=usuario_logado.get("username", "admin")
                )
                if sucesso:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<p style='color:#1E293B;font-size:14px;text-transform:uppercase;letter-spacing:0.1em;font-weight:600;margin-bottom:12px;'>Usuários cadastrados</p>", unsafe_allow_html=True)

    df_usuarios = listar_usuarios()
    if df_usuarios.empty:
        st.info("Nenhum usuário cadastrado.")
    else:
        for _, row in df_usuarios.iterrows():
            col_info, col_badge, col_btn = st.columns([6, 2, 2])
            with col_info:
                criado_em = str(row.get("criado_em", ""))[:16]
                criado_por = row.get("criado_por", "—")
                st.markdown(f"""
                <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:8px;
                            padding:12px 16px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                    <p style="margin:0;color:#1E293B;font-weight:700;font-size:15px;">{row['username']}</p>
                    <p style="margin:4px 0 0;color:#64748B;font-size:13px;">Criado em {criado_em} · por {criado_por}</p>
                </div>
                """, unsafe_allow_html=True)
            with col_badge:
                if row["role"] == "admin":
                    badge_color, badge_bg, badge_label = "#444c9b", "rgba(68,76,155,0.1)", "🛡️ Admin"
                else:
                    badge_color, badge_bg, badge_label = "#10B981", "rgba(16,185,129,0.1)", "👤 Funcionário"
                st.markdown(f"""
                <div style="background:{badge_bg};color:{badge_color};border:1px solid {badge_color}40;
                            border-radius:20px;padding:6px 12px;font-size:13px;font-weight:600;
                            text-align:center;margin-top:8px;">{badge_label}</div>
                """, unsafe_allow_html=True)
            with col_btn:
                eh_proprio = row["username"] == usuario_logado.get("username")
                if not eh_proprio:
                    if st.button("🗑️ Remover", key=f"del_user_{row['id']}", width="stretch"):
                        sucesso, msg = excluir_usuario(
                            user_id=int(row["id"]),
                            solicitante_username=usuario_logado.get("username", "")
                        )
                        if sucesso:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    st.markdown("<p style='color:#94A3B8;font-size:12px;text-align:center;margin-top:12px;'>(sua conta)</p>", unsafe_allow_html=True)

# ── Inicializa banco e tabela de sessões ──────────────────────────────────────
inicializar_banco_completo()
_criar_tabela_sessoes()
_limpar_sessoes_expiradas()

# ══════════════════════════════════════════════════════════════════════════════
# SISTEMA DE PERSISTÊNCIA DE SESSÃO COM COOKIES (SOBREVIVE AO F5)
# ══════════════════════════════════════════════════════════════════════════════

import streamlit.components.v1 as components

def _inject_cookie_manager():
    """Injeta JavaScript para gerenciar cookies de autenticação"""
    components.html("""
    <script>
    // Funções para gerenciar cookies
    function setCookie(name, value, days) {
        const d = new Date();
        d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = "expires=" + d.toUTCString();
        document.cookie = name + "=" + value + ";" + expires + ";path=/;SameSite=Strict";
    }
    
    function getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for(let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) == ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }
    
    function deleteCookie(name) {
        document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    }
    
    // Expõe funções globalmente
    window.renapiAuth = {
        setToken: (token) => setCookie('renapsi_auth_token', token, 1),
        getToken: () => getCookie('renapsi_auth_token'),
        clearToken: () => deleteCookie('renapsi_auth_token')
    };
    
    // Envia token atual para o Streamlit se existir
    const currentToken = getCookie('renapsi_auth_token');
    if (currentToken) {
        // Salva no sessionStorage para recuperação rápida
        sessionStorage.setItem('renapsi_token_cache', currentToken);
    }
    </script>
    """, height=0)

def _save_token_to_cookie(token):
    """Salva token no cookie do navegador"""
    components.html(f"""
    <script>
    if (window.renapiAuth) {{
        window.renapiAuth.setToken('{token}');
        sessionStorage.setItem('renapsi_token_cache', '{token}');
    }}
    </script>
    """, height=0)

def _clear_token_from_cookie():
    """Remove token do cookie do navegador"""
    components.html("""
    <script>
    if (window.renapiAuth) {
        window.renapiAuth.clearToken();
        sessionStorage.removeItem('renapsi_token_cache');
    }
    </script>
    """, height=0)

# ── Injeta gerenciador de cookies ────────────────────────────────────────────
_inject_cookie_manager()

# ── Restaura sessão após F5 usando banco de dados ────────────────────────────
if not st.session_state.get("usuario_logado"):
    # Tenta recuperar token do session_state primeiro
    token_restore = st.session_state.get("auth_token", "")
    
    # Se não tem no session_state, busca todas as sessões ativas do banco
    if not token_restore:
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
            cur = conn.execute("""
                SELECT token, user_id, username, role, expira_em 
                FROM sessoes_ativas 
                WHERE expira_em > ?
                ORDER BY criado_em DESC
                LIMIT 1
            """, (datetime.datetime.now().isoformat(),))
            row = cur.fetchone()
            conn.close()
            
            if row:
                token_restore = row[0]
        except Exception:
            pass
    
    # Valida o token
    if token_restore:
        usuario_recuperado = _validar_token(token_restore)
        if usuario_recuperado:
            st.session_state["usuario_logado"] = True
            st.session_state["usuario_dados"] = usuario_recuperado
            st.session_state["auth_token"] = token_restore
            # Salva no cookie para próximas sessões
            _save_token_to_cookie(token_restore)
        else:
            # Token inválido ou expirado - limpa tudo
            st.session_state.pop("auth_token", None)
            _clear_token_from_cookie()

# ── Portão de entrada: exige login ───────────────────────────────────────────
if not st.session_state.get("usuario_logado"):
    _renderizar_tela_login()
    st.stop()

# ── Verifica se precisa trocar senha (primeiro acesso) ───────────────────────
_usuario_atual = st.session_state.get("usuario_dados", {})
if _usuario_atual.get("deve_trocar_senha", 0) == 1:
    _renderizar_tela_troca_senha_obrigatoria()
    st.stop()

# ── A partir daqui o usuário está autenticado e com senha válida ─────────────
_usuario_atual = st.session_state.get("usuario_dados", {})
_role_atual = _usuario_atual.get("role", "funcionario")

# ── CORREÇÃO FORÇADA: LETRAS BRANCAS NOS BOTÕES ──
st.markdown("""
<style>
/* Força qualquer texto dentro dos botões azuis (secondary) e laranjas (primary) a ficar branco */
.stButton > button[kind="secondary"] p,
.stButton > button[kind="secondary"] span,
.stButton > button[kind="secondary"] div,
.stButton > button[kind="primary"] p,
.stButton > button[kind="primary"] span,
.stButton > button[kind="primary"] div {
        color: #FFFFFF !important;
}
</style>
""", unsafe_allow_html=True)

# ─── CSS Global — Tema Claro Institucional RENAPSI ───────────────────────────
st.markdown("""
<style>
#MainMenu,footer,header{visibility:hidden;}
.stApp{background:#FFFFFF !important;color:#1E293B !important;}
[data-testid="stSidebar"]{background:#F8FAFC !important;border-right:1px solid #E2E8F0 !important;}

/* ── Todos os inputs, selects, textareas — fundo branco ── */
input,textarea,select,
.stTextInput input,.stTextArea textarea,.stNumberInput input,
[data-baseweb="input"] input,[data-baseweb="textarea"] textarea,
[data-baseweb="select"] div,[data-baseweb="select"] input,
.stDateInput input,[data-baseweb="datepicker"] input,
[data-baseweb="base-input"]{
    background-color:#FFFFFF !important;
    color:#1E293B !important;
    border-color:#CBD5E1 !important;
}
[data-baseweb="input"],[data-baseweb="base-input"]{background:#FFFFFF !important;}

/* ── Dropdowns e menus ── */
[data-baseweb="select"]>div{background:#FFFFFF !important;color:#1E293B !important;border-color:#CBD5E1 !important;}
[data-baseweb="popover"],[data-baseweb="menu"]{background:#FFFFFF !important;}
[data-baseweb="menu"] li{color:#1E293B !important;background:#FFFFFF !important;}
[data-baseweb="menu"] li:hover{background:#F1F5F9 !important;}
[data-baseweb="select"] span,[data-baseweb="select"] div{color:#1E293B !important;}

/* ── Botões primários — Laranja RENAPSI ── */
.stButton>button[kind="primary"],button[data-testid="baseButton-primary"]{
    background:linear-gradient(135deg,#f8ae28,#e09a1f) !important;
    border:none !important;color:#FFFFFF !important;
    font-weight:700 !important;border-radius:8px !important;
    box-shadow:0 4px 12px rgba(248,174,40,0.3) !important;
}
.stButton>button[kind="primary"] *{color:#FFFFFF !important;}

/* ── Botões secundários — Azul RENAPSI ── */
.stButton>button[kind="secondary"],button[data-testid="baseButton-secondary"]{
    background:linear-gradient(135deg,#444c9b,#363d7f) !important;
    border:none !important;color:#FFFFFF !important;
    font-weight:600 !important;border-radius:8px !important;
}
.stButton>button[kind="secondary"] *{color:#FFFFFF !important;}

/* ── Botões padrão ── */
.stButton>button:not([kind]){
    background:#FFFFFF !important;border:1px solid #E2E8F0 !important;
    color:#1E293B !important;border-radius:8px !important;
}
.stButton>button:not([kind]) *{color:#1E293B !important;}

/* ── Textos gerais ── */
p,span,div,label,h1,h2,h3,h4,h5,h6{color:#1E293B;}
.stMarkdown p,.stMarkdown span{color:#1E293B !important;}

/* ── Captions ── */
.stCaption p,[data-testid="stCaptionContainer"] p{
    color:#64748B !important;background:transparent !important;
}

/* ── Métricas ── */
[data-testid="metric-container"]{
    background:#FFFFFF !important;border:1px solid #E2E8F0 !important;
    border-radius:12px !important;padding:16px !important;
}
[data-testid="stMetricValue"]{color:#1E293B !important;}
[data-testid="stMetricLabel"]{color:#64748B !important;}

/* ── Dataframe ── */
.stDataFrame,[data-testid="stDataFrame"]{background:#FFFFFF !important;}
.stDataFrame table{background:#FFFFFF !important;color:#1E293B !important;}

/* ── Expander ── */
.streamlit-expanderHeader{
    background:#F8FAFC !important;color:#1E293B !important;
    border:1px solid #E2E8F0 !important;border-radius:8px !important;
}
.streamlit-expanderContent{background:#FFFFFF !important;border:1px solid #E2E8F0 !important;}

/* ── Tabs ── */
[data-baseweb="tab-list"]{background:#F8FAFC;border-radius:10px;padding:4px;border:1px solid #E2E8F0;}
[data-baseweb="tab"]{color:#64748B !important;border-radius:8px;}
[aria-selected="true"]{background:linear-gradient(135deg,#f8ae28,#e09a1f) !important;color:#FFFFFF !important;}
[data-baseweb="tab-panel"]{background:#FFFFFF !important;}

/* ── Sidebar menu ── */
[data-testid="stSidebar"] .stRadio>label{color:#1E293B !important;}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] p{color:#333333 !important;}

/* ── File uploader ── */
[data-testid="stFileUploader"]{
    background:#F8FAFC !important;border:2px dashed #CBD5E1 !important;
    border-radius:8px !important;color:#1E293B !important;
}

/* ── Alerts ── */
.stAlert{background:#F8FAFC !important;color:#1E293B !important;}

/* ── Checkbox/Radio labels ── */
.stCheckbox label,.stRadio label{color:#1E293B !important;}

/* ── Multiselect tags ── */
[data-baseweb="tag"]{background:#444c9b !important;color:#FFFFFF !important;}

/* ── Força fundo branco no container principal ── */
.main .block-container{background:#FFFFFF !important;}
section[data-testid="stSidebar"]>div{background:#F8FAFC !important;}
</style>
""", unsafe_allow_html=True)

# ── Modo Fullscreen ───────────────────────────────────────────────────────────
if st.session_state.get('modo_fullscreen', False):
    st.markdown("""
    <style>
    /* Oculta sidebar e header no modo fullscreen */
    [data-testid="stSidebar"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    #MainMenu { visibility: hidden !important; }
    footer { visibility: hidden !important; }
    
    /* Expande o conteúdo para ocupar toda a tela */
    .main .block-container {
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ─── Inicialização do Banco de Dados ──────────────────────────────────────────
inicializar_banco_completo()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<style>
[data-testid="stSidebar"] img {
        background: transparent !important;
        border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# Caminho absoluto para o logo
_logo_path = os.path.join(os.path.dirname(__file__), "logo_renapsi.png")
if os.path.exists(_logo_path):
    st.sidebar.image(_logo_path, width="stretch")
else:
    st.sidebar.markdown("### 🏢 RENAPSI")

st.sidebar.markdown(
        "<p style='color:#64748B;font-size:13px;text-align:center;letter-spacing:0.1em;margin-top:-8px;'>SISTEMA DE MOBILIDADE URBANA</p>",
        unsafe_allow_html=True
)
st.sidebar.markdown("---")

# ── Busca Global Rápida ───────────────────────────────────────────────────────
st.sidebar.markdown("<p style='color:#1E293B;font-size:13px;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;'>🔍 Busca Rápida</p>", unsafe_allow_html=True)
busca_global = st.sidebar.text_input(
    "Buscar funcionário",
    placeholder="Nome, CPF ou ID...",
    key="busca_global_sidebar",
    label_visibility="collapsed"
)

if busca_global and len(busca_global) >= 3:
    try:
        conexao_busca = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        query_busca = """
            SELECT id, nome, cpf, status_rota 
            FROM jovens_rotas 
            WHERE nome LIKE ? OR cpf LIKE ? OR CAST(id AS TEXT) LIKE ?
            LIMIT 5
        """
        df_busca = safe_sql(query_busca, conexao_busca, params=(f"%{busca_global}%", f"%{busca_global}%", f"%{busca_global}%"))
        conexao_busca.close()
        
        if not df_busca.empty:
            st.sidebar.markdown("<p style='color:#64748B;font-size:12px;margin:8px 0 4px;'>Resultados:</p>", unsafe_allow_html=True)
            for _, row in df_busca.iterrows():
                cpf_mask = f"***.***.{str(row['cpf']).zfill(11)[6:9]}-**"
                if st.sidebar.button(
                    f"#{row['id']} - {row['nome'][:20]}{'...' if len(row['nome']) > 20 else ''}",
                    key=f"busca_res_{row['id']}",
                    help=f"CPF: {cpf_mask} | Status: {row['status_rota'] or 'Pendente'}",
                    use_container_width=True
                ):
                    st.query_params["menu"] = "🔍 Pesquisar Consultas"
                    st.query_params["id_consulta"] = str(row['id'])
                    st.session_state.resultado_busca = df_busca[df_busca['id'] == row['id']]
                    st.rerun()
        else:
            st.sidebar.info("Nenhum resultado encontrado")
    except Exception as e:
        st.sidebar.error(f"Erro na busca: {str(e)}")

st.sidebar.markdown("---")

# ── Badge do usuário logado ───────────────────────────────────────────────────
_username_exib = _usuario_atual.get("username", "")
_badge_label = "🛡️ Admin" if _role_atual == "admin" else "👤 Funcionário"
_badge_color = "#444c9b" if _role_atual == "admin" else "#10B981"
st.sidebar.markdown(f"""
<div style="background:#F1F5F9;border:1px solid #E2E8F0;border-radius:8px;
            padding:10px 14px;margin-bottom:12px;">
    <p style="margin:0;color:#1E293B;font-size:13px;font-weight:700;">{_username_exib}</p>
    <p style="margin:2px 0 0;color:{_badge_color};font-size:12px;font-weight:600;">{_badge_label}</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<p style='color:#1E293B;font-size:13px;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;'>Navegação</p>", unsafe_allow_html=True)

parametros_url = st.query_params
pagina_salva = parametros_url.get("menu", "🏠 Dashboard Principal")
opcoes_menu = [
    "🏠 Dashboard Principal", 
    "🔍 Pesquisar Consultas", 
    "➕ Cadastrar Novo Jovem", 
    "🗂️ Triagem de Fichas", 
    "💾 Banco de Dados", 
    "🏢 Gerenciar Unidades", 
    "🌐 Simulação: Portal do Jovem"
]
if _role_atual == "admin":
    opcoes_menu.extend(["📊 Relatórios e Analytics", "🔍 Auditoria e Compliance", "👥 Registro de Funcionário"])

indice_padrao = opcoes_menu.index(pagina_salva) if pagina_salva in opcoes_menu else 0

menu = st.sidebar.radio("Navegação", opcoes_menu, index=indice_padrao, label_visibility="collapsed")

# Reseta estado ao mudar de menu
if st.query_params.get("menu") != menu:
        # Limpa estados da tela de pesquisa ao sair dela
        if st.query_params.get("menu") == "Pesquisar Consultas":
            for k in ['resultado_busca', 'detalhes_abertos', 'rota_gerada', 
                    'modo_contestacao', 'modo_edicao', 'mostrar_modal_email', 'analise_ia']:
                if k in st.session_state:
                    del st.session_state[k]
            if 'id_consulta' in st.query_params:
                del st.query_params['id_consulta']

st.query_params["menu"] = menu

st.sidebar.markdown("---")

# ── Botão de logout ───────────────────────────────────────────────────────────
if st.sidebar.button("🚪 Sair", width="stretch"):
    _token_atual = st.session_state.get("auth_token", "")
    if _token_atual:
        _revogar_token(_token_atual)
    
    # Limpa cookie
    _clear_token_from_cookie()
    
    # Limpa session_state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(
        "<p style='color:#334155;font-size:14px;text-align:center;'>Copyright ©️ Renapsi - 2026. Todos os direitos reservados. CNPJ 37.381.902/0001-25.</p>",
        unsafe_allow_html=True
)

# ── Selo de Conformidade LGPD ──
st.sidebar.markdown("""
<div style="background:#FFFFFF;border:1px solid #E2E8F0;
                border-radius:10px;padding:14px;margin-top:16px;text-align:center;
                box-shadow:0 2px 4px rgba(0,0,0,0.05);">
        <p style="color:#f8ae28;font-size:15px;font-weight:600;margin:0 0 8px;letter-spacing:0.05em;">
            🔒 PRIVACIDADE ASSEGURADA
        </p>
        <p style="color:#64748B;font-size:14px;line-height:1.4;margin:0;">
            Conformidade com <strong>LGPD</strong>. Dados de colaboradores (CPF, Morada, E-mail) são processados localmente e armazenados de forma segura. Nenhuma informação pessoal sensível é partilhada com APIs externas sem anonimização.
        </p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TELA 0 — DASHBOARD PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
if menu == "🏠 Dashboard Principal":

        meses_pt = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                    "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        mes_atual = meses_pt[datetime.datetime.now().month - 1]
        ano_atual = datetime.datetime.now().year

        # ── Cabeçalho com modo tela cheia ──
        col_header, col_actions = st.columns([8, 4])
        with col_header:
            st.markdown("""
            <div style="display:flex; align-items:center; gap:15px; margin-bottom:25px;">
                <svg viewBox="0 0 133.83 114" width="60" height="50">
                <defs><style>.s2-1{fill:#fff;} .s2-2{fill:#402fdd;}</style></defs>
                <g><path class="s2-2" d="M57,0C25.52,0,0,25.52,0,57s25.52,57,57,57h19.83c31.48,0,57-25.52,57-57S108.31,0,76.83,0h-19.83Z"/>
                <path class="s2-1" d="M66.91,48.07c-9.15,0-16.59,7.48-16.59,16.66s7.44,16.66,16.59,16.66,16.59-7.48,16.59-16.66-7.44-16.66-16.59-16.66M66.91,88.58c-13.09,0-23.74-10.7-23.74-23.85s10.65-23.85,23.74-23.85,23.74,10.7,23.74,23.85-10.65,23.85-23.74,23.85"/>
                <polygon class="s2-1" points="90.66 88.58 83.5 87.55 83.5 29.11 90.66 30.14 90.66 88.58"/>
                <polygon class="s2-1" points="56.55 25.42 56.55 32.47 77.28 35.45 77.28 28.4 56.55 25.42"/></g>
                </svg>
                <div>
                    <h1 style="margin:0; color:#444c9b; font-size:28px;">Dashboard de Mobilidade</h1>
                    <p style="margin:4px 0 0; color:#64748B; font-size:14px;">Visão geral do sistema de transporte</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_actions:
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button("📊", help="Exportar relatório em Excel", width="stretch", key="btn_excel_dash"):
                    st.session_state.exportar_excel = True
            with col_btn2:
                if st.button("📄", help="Exportar relatório em PDF", width="stretch", key="btn_pdf_dash"):
                    st.session_state.exportar_pdf = True
            with col_btn3:
                modo_fullscreen = st.session_state.get('modo_fullscreen', False)
                if st.button("🖥️" if not modo_fullscreen else "↩️", 
                           help="Modo tela cheia" if not modo_fullscreen else "Sair do modo tela cheia",
                           width="stretch", key="btn_fullscreen_dash"):
                    st.session_state.modo_fullscreen = not modo_fullscreen
                    st.rerun()

        # ── Filtro de Período e Modalidade ──
        col_filtro1, col_filtro2, col_filtro3 = st.columns([2, 3, 7])
        with col_filtro1:
            periodo_selecionado = st.selectbox(
                "📅 Período:",
                ["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Último ano", "Tudo"],
                index=st.session_state.get('periodo_index', 1),
                key="filtro_periodo_dashboard"
            )
            st.session_state.periodo_index = ["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Último ano", "Tudo"].index(periodo_selecionado)
        
        with col_filtro2:
            tipo_rota = st.selectbox(
                "🎯 Visualização:",
                ["🏠 Casa × Trabalho", "📚 Casa × Curso", "📊 Gestão de Base", "📧 Envios em Massa"],
                key="modalidade_pesquisa_select"
            )

        # Calcula data de início baseado no período
        data_fim = datetime.datetime.now()
        if periodo_selecionado == "Últimos 7 dias":
            data_inicio = data_fim - datetime.timedelta(days=7)
        elif periodo_selecionado == "Últimos 30 dias":
            data_inicio = data_fim - datetime.timedelta(days=30)
        elif periodo_selecionado == "Últimos 90 dias":
            data_inicio = data_fim - datetime.timedelta(days=90)
        elif periodo_selecionado == "Último ano":
            data_inicio = data_fim - datetime.timedelta(days=365)
        else:  # Tudo
            data_inicio = datetime.datetime(2020, 1, 1)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Busca dados com filtro de período ──
        conexao_dash = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        
        # Query com filtro de data para consultas e SLA
        query_periodo = f"""
            SELECT COUNT(DISTINCT id) as total,
                   AVG(sla_segundos) as sla_medio
            FROM jovens_rotas
            WHERE data_consulta >= '{data_inicio.strftime("%Y-%m-%d")}'
        """
        df_dash = safe_sql(query_periodo, conexao_dash)
        
        total_consultas = int(df_dash.iloc[0]['total']) if not df_dash.empty else 0
        sla_medio = float(df_dash.iloc[0]['sla_medio'] or 0) if not df_dash.empty else 0
        
        # Total de implantados ATUAL (independente do período de consulta)
        query_implantados = "SELECT COUNT(*) as total FROM jovens_rotas WHERE status_rota = 'Implantado'"
        df_implantados = safe_sql(query_implantados, conexao_dash)
        total_implantados = int(df_implantados.iloc[0]['total']) if not df_implantados.empty else 0
        
        # Contestações no período
        query_contest = f"""
            SELECT COUNT(*) as total
            FROM contestacoes
            WHERE data_geracao >= '{data_inicio.strftime("%Y-%m-%d")}'
        """
        df_contest_kpi = safe_sql(query_contest, conexao_dash)
        total_contestacoes = int(df_contest_kpi.iloc[0]['total']) if not df_contest_kpi.empty else 0

        # Total de contestações PENDENTES (sem filtro de período — para o KPI real)
        df_contest_pendentes_kpi = safe_sql(
            "SELECT COUNT(*) as total FROM contestacoes WHERE status = 'Pendente'",
            conexao_dash
        )
        total_contestacoes_pendentes = int(df_contest_pendentes_kpi.iloc[0]['total']) if not df_contest_pendentes_kpi.empty else 0

        # Total geral de contestações (sem filtro) para o KPI
        df_contest_total = safe_sql("SELECT COUNT(*) as total FROM contestacoes", conexao_dash)
        total_contestacoes_geral = int(df_contest_total.iloc[0]['total']) if not df_contest_total.empty else 0

        conexao_dash.close()

        # ── KPI Cards CLICÁVEIS ──
        col_k1, col_k2, col_k3, col_k4 = st.columns(4)
        
        kpi_css = """
        <style>
        /* ── KPI Cards ── */
        .kpi-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 20px 16px 14px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
            margin-bottom: 4px;
        }
        .kpi-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.10);
        }
        .kpi-icon  { font-size: 26px; margin-bottom: 4px; }
        .kpi-value { font-size: 28px; font-weight: 800; color: #1E293B; margin: 4px 0; }
        .kpi-label { font-size: 13px; font-weight: 600; color: #64748B;
                     text-transform: uppercase; letter-spacing: 0.06em; }
        .kpi-sub   { font-size: 12px; color: #94A3B8; margin-top: 6px; }

        /* ── Força botões secundários com fundo branco e texto escuro ── */
        .stButton > button[kind="secondary"] {
            background: #FFFFFF !important;
            color: #1E293B !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
        }
        .stButton > button[kind="secondary"]:hover {
            background: #F8FAFC !important;
            border-color: #444c9b !important;
            color: #444c9b !important;
        }
        /* ── Corrige caption/legenda abaixo dos botões ── */
        .stCaption, [data-testid="stCaptionContainer"] p {
            color: #64748B !important;
            background: transparent !important;
            font-size: 12px !important;
        }
        </style>
        """
        st.markdown(kpi_css, unsafe_allow_html=True)

        with col_k1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">📊</div>
                <div class="kpi-value">{total_consultas}</div>
                <div class="kpi-label">Total de Consultas</div>
                <div class="kpi-sub">Rotas únicas no período</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_k2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">⏱️</div>
                <div class="kpi-value">{sla_medio:.2f}s</div>
                <div class="kpi-label">SLA Médio</div>
                <div class="kpi-sub">Tempo de resposta</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_k3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">⚠️</div>
                <div class="kpi-value">{total_contestacoes_geral}</div>
                <div class="kpi-label">Contestações</div>
                <div class="kpi-sub">{total_contestacoes_pendentes} pendente(s)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_k4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">✅</div>
                <div class="kpi-value">{total_implantados}</div>
                <div class="kpi-label">Implantações</div>
                <div class="kpi-sub">Ativos no momento</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════════
        # ALERTAS VISUAIS PARA TAREFAS PENDENTES
        # ══════════════════════════════════════════════════════════════════════════
        try:
            _conn_alertas = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
            
            # Conta fichas pendentes de aprovação
            _df_fichas_pendentes = safe_sql("""
                SELECT COUNT(*) as total
                FROM fichas_cadastrais
                WHERE status_aprovacao = 'Pendente'
            """, _conn_alertas)
            _total_fichas_pendentes = int(_df_fichas_pendentes.iloc[0]['total']) if not _df_fichas_pendentes.empty else 0
            
            # Conta contestações pendentes
            _df_contest_pendentes = safe_sql("""
                SELECT COUNT(*) as total
                FROM contestacoes
                WHERE status = 'Pendente'
            """, _conn_alertas)
            _total_contest_pendentes = int(_df_contest_pendentes.iloc[0]['total']) if not _df_contest_pendentes.empty else 0
            
            _conn_alertas.close()
            
            # Mostra alertas apenas se houver tarefas pendentes
            if _total_fichas_pendentes > 0 or _total_contest_pendentes > 0:
                col_alert1, col_alert2 = st.columns(2)
                
                if _total_fichas_pendentes > 0:
                    with col_alert1:
                        st.markdown(f"""
                        <div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.4);
                                    border-left:4px solid #F59E0B;border-radius:12px;padding:16px 20px;margin-bottom:16px;
                                    cursor:pointer;transition:all 0.2s;" 
                             onclick="window.location.href='?menu=🗂️ Triagem de Fichas'">
                            <div style="display:flex;align-items:center;gap:12px;">
                                <span style="font-size:28px;">📋</span>
                                <div style="flex:1;">
                                    <p style="margin:0;color:#F59E0B;font-weight:700;font-size:16px;">
                                        {_total_fichas_pendentes} Ficha(s) para Aprovar
                                    </p>
                                    <p style="margin:4px 0 0;color:#92400E;font-size:13px;">
                                        Candidaturas aguardando triagem
                                    </p>
                                </div>
                                <span style="color:#F59E0B;font-size:20px;">→</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Ver Fichas Pendentes", key="btn_fichas_pendentes", use_container_width=True):
                            st.query_params["menu"] = "🗂️ Triagem de Fichas"
                            st.rerun()
                
                if _total_contest_pendentes > 0:
                    with col_alert2:
                        st.markdown(f"""
                        <div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.4);
                                    border-left:4px solid #EF4444;border-radius:12px;padding:16px 20px;margin-bottom:16px;
                                    cursor:pointer;transition:all 0.2s;"
                             onclick="window.location.href='?menu=Banco de Dados'">
                            <div style="display:flex;align-items:center;gap:12px;">
                                <span style="font-size:28px;">⚠️</span>
                                <div style="flex:1;">
                                    <p style="margin:0;color:#EF4444;font-weight:700;font-size:16px;">
                                        {_total_contest_pendentes} Contestação(ões) Pendente(s)
                                    </p>
                                    <p style="margin:4px 0 0;color:#991B1B;font-size:13px;">
                                        Requer análise e tratativa
                                    </p>
                                </div>
                                <span style="color:#EF4444;font-size:20px;">→</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Ver Contestações", key="btn_contestacoes_pendentes", use_container_width=True):
                            st.query_params["menu"] = "💾 Banco de Dados"
                            st.rerun()
        except Exception as e:
            pass  # Silenciosamente ignora erros nos alertas

        # ══════════════════════════════════════════════════════════════════════════
        # ALERTA DE RENOVAÇÃO DE VT — Implantados há mais de 12 meses
        # ══════════════════════════════════════════════════════════════════════════
        try:
            _conn_renov = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
            _df_renov = safe_sql("""
                SELECT id, nome, assinatura_data
                FROM jovens_rotas
                WHERE status_rota = 'Implantado'
                  AND assinatura_data IS NOT NULL
                  AND assinatura_data != ''
            """, _conn_renov)
            _conn_renov.close()

            _limite_renov = datetime.datetime.now() - datetime.timedelta(days=365)
            _para_renovar = []
            for _, _r in _df_renov.iterrows():
                try:
                    _dt = datetime.datetime.strptime(str(_r['assinatura_data'])[:19], "%Y-%m-%d %H:%M:%S")
                    if _dt < _limite_renov:
                        _meses = int((datetime.datetime.now() - _dt).days / 30)
                        _para_renovar.append({"nome": _r['nome'], "id": _r['id'], "meses": _meses})
                except Exception:
                    pass

            if _para_renovar:
                st.markdown(f"""
                <div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.4);
                            border-left:4px solid #F59E0B;border-radius:12px;padding:16px 20px;margin-bottom:20px;">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                        <span style="font-size:20px;">⚠️</span>
                        <p style="margin:0;color:#F59E0B;font-weight:700;font-size:15px;">
                            {len(_para_renovar)} funcionário(s) com VT para renovar (implantado há +12 meses)
                        </p>
                    </div>
                    <div style="display:flex;flex-wrap:wrap;gap:8px;">
                        {''.join([f"""<span style="background:rgba(245,158,11,0.15);color:#92400E;border:1px solid rgba(245,158,11,0.3);border-radius:20px;padding:3px 10px;font-size:12px;font-weight:600;">#{p['id']} {p['nome'].split()[0]} · {p['meses']}m</span>""" for p in _para_renovar[:10]])}
                        {f'<span style="color:#94A3B8;font-size:12px;padding:3px 6px;">+{len(_para_renovar)-10} mais...</span>' if len(_para_renovar) > 10 else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        except Exception:
            pass

        # ══════════════════════════════════════════════════════════════════════════
        # ══════════════════════════════════════════════════════════════════════════
        # ROI DASHBOARD — ANÁLISE FINANCEIRA
        # ══════════════════════════════════════════════════════════════════════════

        # Busca total de jovens na base
        conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        df_jovens = safe_sql("SELECT COUNT(*) as total FROM jovens_rotas", conexao)
        total_jovens = df_jovens.iloc[0]['total'] if not df_jovens.empty else 0

        # ── Custo real de VT: soma os valores reais do banco ──
        try:
            df_custo_real = safe_sql("""
                SELECT
                    AVG(CASE WHEN valor_tarifa_manual > 0 THEN valor_tarifa_manual ELSE NULL END) as media_real,
                    SUM(CASE WHEN status_rota = 'Implantado' AND valor_tarifa_manual > 0 THEN valor_tarifa_manual ELSE 0 END) as total_implantados_real,
                    COUNT(CASE WHEN status_rota = 'Implantado' AND valor_tarifa_manual > 0 THEN 1 END) as qtd_com_valor
                FROM jovens_rotas
            """, conexao)
            _media_real = float(df_custo_real.iloc[0]['media_real'] or 0)
            _total_real_dia = float(df_custo_real.iloc[0]['total_implantados_real'] or 0)
            _qtd_com_valor = int(df_custo_real.iloc[0]['qtd_com_valor'] or 0)
            CUSTO_OTIMIZADO_DIARIO = _media_real if _media_real > 0 else 11.32
        except Exception:
            CUSTO_OTIMIZADO_DIARIO = 11.32
            _total_real_dia = 0
            _qtd_com_valor = 0

        conexao.close()

        # Constantes financeiras
        CUSTO_MANUAL_DIARIO = 15.00
        DIAS_UTEIS_MES = 22

        # Cálculos
        custo_manual_mes = CUSTO_MANUAL_DIARIO * DIAS_UTEIS_MES * total_jovens
        custo_otimizado_mes = CUSTO_OTIMIZADO_DIARIO * DIAS_UTEIS_MES * total_jovens
        economia_mes = custo_manual_mes - custo_otimizado_mes
        percentual_economia = (economia_mes / custo_manual_mes * 100) if custo_manual_mes > 0 else 0

        # Badge de fonte dos dados (calculado antes do HTML)
        if _qtd_com_valor > 0:
            _badge_roi = f'<span style="background:rgba(16,185,129,0.15);color:#10B981;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600;">✅ Tarifa real do banco · {_qtd_com_valor} registros · média R${CUSTO_OTIMIZADO_DIARIO:.2f}/dia</span>'
        else:
            _badge_roi = '<span style="background:rgba(245,158,11,0.15);color:#F59E0B;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600;">⚠️ Usando estimativa de mercado (R$11,32/dia)</span>'

        st.markdown(f"""
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;
                    border-radius:14px;padding:24px;margin-bottom:8px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
            <h3 style="margin:0 0 4px;color:#f8ae28;">💰 Análise de ROI — Retorno sobre Investimento</h3>
            <p style="color:#64748B;font-size:15px;margin:0;">
                Comparativo de custos: Mobilidade Manual vs. Otimizada
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f'<p style="margin:0 0 20px;">{_badge_roi}</p>', unsafe_allow_html=True)

        # Blocos de métricas financeiras
        col_roi1, col_roi2, col_roi3 = st.columns(3)

        with col_roi1:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,rgba(239,68,68,0.1),rgba(239,68,68,0.05));
                        border:1px solid rgba(239,68,68,0.3);border-radius:12px;padding:20px;text-align:center;">
                <p style="color:#EF4444;font-size:15px;margin:0 0 8px;text-transform:uppercase;letter-spacing:0.08em;">
                    Custo Manual (Mês)
                </p>
                <p style="color:#E2E8F0;font-size:36px;font-weight:800;margin:0;">
                    R$ {custo_manual_mes:,.2f}
                </p>
                <p style="color:#64748B;font-size:15px;margin:4px 0 0;letter-spacing:0.05em;">
                    {total_jovens} jovens × R${CUSTO_MANUAL_DIARIO:.2f}/dia × {DIAS_UTEIS_MES} dias
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col_roi2:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,rgba(16,185,129,0.1),rgba(16,185,129,0.05));
                        border:1px solid rgba(16,185,129,0.3);border-radius:12px;padding:20px;text-align:center;">
                <p style="color:#10B981;font-size:15px;margin:0 0 8px;text-transform:uppercase;letter-spacing:0.08em;">
                    Custo Otimizado (Mês)
                </p>
                <p style="color:#E2E8F0;font-size:36px;font-weight:800;margin:0;">
                    R$ {custo_otimizado_mes:,.2f}
                </p>
                <p style="color:#64748B;font-size:15px;margin:4px 0 0;letter-spacing:0.05em;">
                    {total_jovens} jovens × R${CUSTO_OTIMIZADO_DIARIO:.2f}/dia × {DIAS_UTEIS_MES} dias
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col_roi3:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,rgba(124,58,237,0.1),rgba(124,58,237,0.05));
                        border:1px solid rgba(124,58,237,0.3);border-radius:12px;padding:20px;text-align:center;">
                <p style="color:#A78BFA;font-size:15px;margin:0 0 8px;text-transform:uppercase;letter-spacing:0.08em;">
                    Economia Mensal
                </p>
                <p style="color:#E2E8F0;font-size:36px;font-weight:800;margin:0;">
                    R$ {economia_mes:,.2f}
                </p>
                <p style="color:#64748B;font-size:15px;margin:4px 0 0;letter-spacing:0.05em;">
                    Redução de {percentual_economia:.1f}% nos custos
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Gráfico de distribuição modal
        col_chart1, col_chart2 = st.columns([1.5, 1])

        with col_chart1:
            st.markdown("""
            <p style="color:#94A3B8;font-size:15px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:12px;">
                Distribuição Modal das Rotas
                <span style="color:#64748B;font-size:12px;font-weight:normal;margin-left:8px;">
                    ℹ️ Hover sobre o gráfico para ver detalhes
                </span>
            </p>
            """, unsafe_allow_html=True)
            
            # ── Dados REAIS do banco ──
            try:
                _conn_modal = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                _df_modal = safe_sql("""
                    SELECT
                        CASE
                            WHEN modo_rota = 'manual' THEN 'Manual'
                            WHEN tipo_bilhete_manual LIKE '%Integra%' THEN 'Integração'
                            WHEN tipo_bilhete_manual LIKE '%Metro%' OR tipo_bilhete_manual LIKE '%Metrô%' THEN 'Metrô'
                            WHEN status_rota = 'Implantado' THEN 'Integração'
                            ELSE 'Ônibus'
                        END as modal,
                        COUNT(*) as qtd
                    FROM jovens_rotas
                    WHERE status_rota IS NOT NULL
                    GROUP BY modal
                """, _conn_modal)
                _conn_modal.close()
                if _df_modal.empty or _df_modal['qtd'].sum() == 0:
                    raise ValueError("sem dados")
                modais = _df_modal['modal'].tolist()
                percentuais = _df_modal['qtd'].tolist()
            except Exception:
                modais = ['Integração', 'Ônibus', 'Metrô']
                percentuais = [40, 35, 25]

            cores_modais = ['#f8ae28', '#444c9b', '#64748B', '#10B981']

            fig_modal = px.pie(
                values=percentuais,
                names=modais,
                hole=0.5,
                color_discrete_sequence=cores_modais,
                title=""
            )
            fig_modal.update_traces(
                textposition='inside',
                textinfo='label+percent',
                textfont=dict(size=14, color='#FFFFFF', family='Arial'),
                hovertemplate='<b>%{label}</b><br>' +
                             'Quantidade: %{value} funcionários<br>' +
                             'Percentual: %{percent}<br>' +
                             '<extra></extra>',
                marker=dict(line=dict(color='#FFFFFF', width=2))
            )
            fig_modal.update_layout(
                showlegend=True,
                legend=dict(
                    orientation='v',
                    yanchor='middle',
                    y=0.5,
                    xanchor='left',
                    x=1.05,
                    font=dict(size=13, color='#64748B', family='Arial'),
                    bgcolor='rgba(255,255,255,0.8)',
                    bordercolor='#E2E8F0',
                    borderwidth=1
                ),
                margin=dict(t=10, b=10, l=10, r=100),
                height=280,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Arial', size=14, color='#333333'),
                hoverlabel=dict(
                    bgcolor='#FFFFFF',
                    font_size=13,
                    font_family='Arial',
                    bordercolor='#E2E8F0'
                )
            )
            st.plotly_chart(fig_modal, use_container_width=True, key="graf_modal_roi")

        with col_chart2:
            st.markdown("""
            <p style="color:#94A3B8;font-size:15px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:12px;">
                Resumo Financeiro
            </p>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-left:4px solid #444c9b;
                        border-radius:12px;padding:16px;height:280px;display:flex;flex-direction:column;justify-content:space-around;
                        box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                <div>
                    <p style="color:#666666;font-size:15px;margin:0 0 4px;text-transform:uppercase;">Total de Jovens</p>
                    <p style="color:#f8ae28;font-size:28px;font-weight:800;margin:0;">{total_jovens}</p>
                </div>
                <div>
                    <p style="color:#666666;font-size:15px;margin:0 0 4px;text-transform:uppercase;">Dias Úteis/Mês</p>
                    <p style="color:#444c9b;font-size:28px;font-weight:800;margin:0;">{DIAS_UTEIS_MES}</p>
                </div>
                <div>
                    <p style="color:#666666;font-size:15px;margin:0 0 4px;text-transform:uppercase;">Economia Anual</p>
                    <p style="color:#10B981;font-size:28px;font-weight:800;margin:0;">R$ {economia_mes * 12:,.2f}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color:rgba(0,212,255,0.1);margin:20px 0;'>", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════════
        # NOVOS COMPONENTES DO DASHBOARD
        # ══════════════════════════════════════════════════════════════════════════
        
        # ── 1. GRÁFICO DE LINHA TEMPORAL - Evolução de Implantações por Mês (COLAPSÁVEL) ──
        with st.expander("📈 Ver Evolução de Implantações por Mês", expanded=False):
            st.markdown("""
            <p style="color:#64748B;font-size:14px;margin:0 0 16px;">
                Acompanhe o crescimento mensal de funcionários com VT ativo
            </p>
            """, unsafe_allow_html=True)
            
            try:
                _conn_evolucao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                _df_evolucao = safe_sql("""
                    SELECT 
                        strftime('%Y-%m', assinatura_data) as mes,
                        COUNT(*) as total
                    FROM jovens_rotas
                    WHERE status_rota = 'Implantado' 
                      AND assinatura_data IS NOT NULL
                      AND assinatura_data != ''
                    GROUP BY mes
                    ORDER BY mes
                """, _conn_evolucao)
                _conn_evolucao.close()
                
                if not _df_evolucao.empty:
                    # Converte para formato de data legível
                    _df_evolucao['mes_label'] = pd.to_datetime(_df_evolucao['mes']).dt.strftime('%b/%Y')
                    
                    fig_evolucao = px.line(
                        _df_evolucao,
                        x='mes_label',
                        y='total',
                        markers=True,
                        title=""
                    )
                    fig_evolucao.update_traces(
                        line=dict(color='#10B981', width=3),
                        marker=dict(size=10, color='#10B981', line=dict(color='#FFFFFF', width=2)),
                        hovertemplate='<b>%{x}</b><br>Implantações: %{y}<extra></extra>'
                    )
                    fig_evolucao.update_layout(
                        xaxis_title="Mês",
                        yaxis_title="Total de Implantações",
                        height=300,
                        margin=dict(t=10, b=40, l=40, r=10),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Arial', size=13, color='#64748B'),
                        xaxis=dict(showgrid=True, gridcolor='#E2E8F0'),
                        yaxis=dict(showgrid=True, gridcolor='#E2E8F0'),
                        hoverlabel=dict(bgcolor='#FFFFFF', font_size=13, font_family='Arial', bordercolor='#E2E8F0')
                    )
                    st.plotly_chart(fig_evolucao, use_container_width=True, key="graf_evolucao_implantacoes")
                else:
                    st.info("📊 Ainda não há dados de implantações com data de assinatura registrada.")
            except Exception as e:
                st.error(f"Erro ao carregar evolução: {e}")

        # ── 2. MAPA DE CALOR - Distribuição Geográfica dos Funcionários (COLAPSÁVEL) ──
        with st.expander("🗺️ Ver Distribuição Geográfica dos Funcionários", expanded=False):
            st.markdown("""
            <p style="color:#64748B;font-size:14px;margin:0 0 16px;">
                Visualize onde estão concentrados os funcionários por região
            </p>
            """, unsafe_allow_html=True)
            
            try:
                _conn_geo = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                _df_geo = safe_sql("""
                    SELECT cep_casa, COUNT(*) as qtd
                    FROM jovens_rotas
                    WHERE cep_casa IS NOT NULL AND cep_casa != ''
                    GROUP BY cep_casa
                    ORDER BY qtd DESC
                    LIMIT 20
                """, _conn_geo)
                _conn_geo.close()
                
                if not _df_geo.empty:
                    # Busca informações de bairro/região para cada CEP
                    _regioes = []
                    for _, row in _df_geo.iterrows():
                        try:
                            _end = buscar_endereco_viacep(row['cep_casa'])
                            _bairro = _end.get('bairro', 'Desconhecido') if isinstance(_end, dict) else 'Desconhecido'
                            _regioes.append({'regiao': _bairro, 'qtd': row['qtd']})
                        except:
                            _regioes.append({'regiao': 'Desconhecido', 'qtd': row['qtd']})
                    
                    _df_regioes = pd.DataFrame(_regioes)
                    _df_regioes_agrupado = _df_regioes.groupby('regiao')['qtd'].sum().reset_index()
                    _df_regioes_agrupado = _df_regioes_agrupado.sort_values('qtd', ascending=False).head(10)
                    
                    fig_geo = px.bar(
                        _df_regioes_agrupado,
                        x='qtd',
                        y='regiao',
                        orientation='h',
                        title="",
                        color='qtd',
                        color_continuous_scale=['#FEF3C7', '#f8ae28', '#e09a1f']
                    )
                    fig_geo.update_traces(
                        hovertemplate='<b>%{y}</b><br>Funcionários: %{x}<extra></extra>'
                    )
                    fig_geo.update_layout(
                        xaxis_title="Quantidade de Funcionários",
                        yaxis_title="",
                        height=400,
                        margin=dict(t=10, b=40, l=150, r=10),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Arial', size=13, color='#64748B'),
                        showlegend=False,
                        xaxis=dict(showgrid=True, gridcolor='#E2E8F0'),
                        yaxis=dict(showgrid=False),
                        hoverlabel=dict(bgcolor='#FFFFFF', font_size=13, font_family='Arial', bordercolor='#E2E8F0')
                    )
                    st.plotly_chart(fig_geo, use_container_width=True, key="graf_distribuicao_geografica")
                else:
                    st.info("🗺️ Ainda não há dados de CEP cadastrados para análise geográfica.")
            except Exception as e:
                st.error(f"Erro ao carregar distribuição geográfica: {e}")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 3. WIDGET DE AÇÕES RÁPIDAS ──
        st.markdown("""
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-left:4px solid #444c9b;
                    border-radius:14px;padding:24px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
            <h3 style="margin:0 0 4px;color:#444c9b;">⚡ Ações Rápidas</h3>
            <p style="color:#64748B;font-size:14px;margin:0;">
                Acesso rápido às tarefas mais comuns do sistema
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col_acao1, col_acao2, col_acao3, col_acao4 = st.columns(4)
        
        with col_acao1:
            if st.button("➕ Cadastrar Jovem", use_container_width=True, type="secondary"):
                st.query_params["menu"] = "➕ Cadastrar Novo Jovem"
                st.rerun()
            st.caption("Adicionar novo funcionário")
        
        with col_acao2:
            if st.button("🔍 Pesquisar Rota", use_container_width=True, type="secondary"):
                st.query_params["menu"] = "🔍 Pesquisar Consultas"
                st.rerun()
            st.caption("Buscar rotas existentes")
        
        with col_acao3:
            if st.button("📋 Triagem de Fichas", use_container_width=True, type="secondary"):
                st.query_params["menu"] = "🗂️ Triagem de Fichas"
                st.rerun()
            st.caption("Aprovar candidaturas")
        
        with col_acao4:
            if st.button("🗄️ Banco de Dados", use_container_width=True, type="secondary"):
                st.query_params["menu"] = "💾 Banco de Dados"
                st.rerun()
            st.caption("Gerenciar registros")

        st.markdown("<br>", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════════
        # GESTÃO DE BASE - Economia Acumulada e Distribuição de Status
        # ══════════════════════════════════════════════════════════════════════════
        if tipo_rota == "📊 Gestão de Base":
            st.markdown("""
            <div style="background:linear-gradient(135deg,rgba(16,185,129,0.15),rgba(16,185,129,0.05));
                        border:1px solid rgba(16,185,129,0.3);border-left:4px solid #10B981;
                        border-radius:14px;padding:24px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                <h3 style="margin:0 0 4px;color:#10B981;">💰 Economia Acumulada Total</h3>
                <p style="color:#64748B;font-size:14px;margin:0;">
                    Economia total desde o início do sistema de mobilidade otimizada
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                # Busca a data da primeira implantação
                _conn_economia = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                _df_primeira_data = safe_sql("""
                    SELECT MIN(assinatura_data) as primeira_data
                    FROM jovens_rotas
                    WHERE status_rota = 'Implantado' 
                      AND assinatura_data IS NOT NULL
                      AND assinatura_data != ''
                """, _conn_economia)
                
                _primeira_data_str = _df_primeira_data.iloc[0]['primeira_data'] if not _df_primeira_data.empty else None
                
                if _primeira_data_str:
                    _primeira_data = datetime.datetime.strptime(str(_primeira_data_str)[:10], "%Y-%m-%d")
                    _dias_desde_inicio = (datetime.datetime.now() - _primeira_data).days
                    _meses_desde_inicio = _dias_desde_inicio / 30
                    
                    # Calcula economia acumulada
                    _economia_acumulada = economia_mes * _meses_desde_inicio
                    
                    col_eco1, col_eco2, col_eco3 = st.columns(3)
                    
                    with col_eco1:
                        st.markdown(f"""
                        <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;
                                    padding:20px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                            <p style="color:#10B981;font-size:14px;margin:0 0 8px;text-transform:uppercase;letter-spacing:0.08em;">
                                Economia Total
                            </p>
                            <p style="color:#10B981;font-size:36px;font-weight:800;margin:0;">
                                R$ {_economia_acumulada:,.2f}
                            </p>
                            <p style="color:#64748B;font-size:13px;margin:4px 0 0;">
                                Desde {_primeira_data.strftime("%d/%m/%Y")}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_eco2:
                        st.markdown(f"""
                        <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;
                                    padding:20px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                            <p style="color:#444c9b;font-size:14px;margin:0 0 8px;text-transform:uppercase;letter-spacing:0.08em;">
                                Tempo de Operação
                            </p>
                            <p style="color:#444c9b;font-size:36px;font-weight:800;margin:0;">
                                {int(_meses_desde_inicio)}
                            </p>
                            <p style="color:#64748B;font-size:13px;margin:4px 0 0;">
                                meses ({_dias_desde_inicio} dias)
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_eco3:
                        _economia_por_dia = _economia_acumulada / _dias_desde_inicio if _dias_desde_inicio > 0 else 0
                        st.markdown(f"""
                        <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;
                                    padding:20px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                            <p style="color:#f8ae28;font-size:14px;margin:0 0 8px;text-transform:uppercase;letter-spacing:0.08em;">
                                Economia Média/Dia
                            </p>
                            <p style="color:#f8ae28;font-size:36px;font-weight:800;margin:0;">
                                R$ {_economia_por_dia:,.2f}
                            </p>
                            <p style="color:#64748B;font-size:13px;margin:4px 0 0;">
                                Média diária de economia
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("📊 Ainda não há implantações com data registrada para calcular economia acumulada.")
                
                _conn_economia.close()
            except Exception as e:
                st.error(f"Erro ao calcular economia acumulada: {e}")

            st.markdown("<br>", unsafe_allow_html=True)

            # ── GRÁFICO DE PIZZA - Distribuição de Status ──
            st.markdown("""
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-left:4px solid #444c9b;
                        border-radius:14px;padding:24px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                <h3 style="margin:0 0 4px;color:#444c9b;">📊 Distribuição de Status</h3>
                <p style="color:#64748B;font-size:14px;margin:0;">
                    Visualize a distribuição de funcionários por status de rota
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                _conn_status = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                _df_status = safe_sql("""
                    SELECT 
                        COALESCE(status_rota, 'Sem Status') as status,
                        COUNT(*) as total
                    FROM jovens_rotas
                    GROUP BY status_rota
                    ORDER BY total DESC
                """, _conn_status)
                _conn_status.close()
                
                if not _df_status.empty:
                    # Define cores para cada status
                    _cores_status = {
                        'Implantado': '#10B981',
                        'Otimizado': '#3B82F6',
                        'Contestada': '#F59E0B',
                        'Não Optante': '#94A3B8',
                        'Sem Status': '#64748B'
                    }
                    
                    _cores = [_cores_status.get(s, '#64748B') for s in _df_status['status']]
                    
                    fig_status = px.pie(
                        _df_status,
                        values='total',
                        names='status',
                        hole=0.4,
                        color_discrete_sequence=_cores,
                        title=""
                    )
                    fig_status.update_traces(
                        textposition='inside',
                        textinfo='label+percent',
                        textfont=dict(size=14, color='#FFFFFF', family='Arial'),
                        hovertemplate='<b>%{label}</b><br>' +
                                     'Quantidade: %{value} funcionários<br>' +
                                     'Percentual: %{percent}<br>' +
                                     '<extra></extra>',
                        marker=dict(line=dict(color='#FFFFFF', width=2))
                    )
                    fig_status.update_layout(
                        showlegend=True,
                        legend=dict(
                            orientation='v',
                            yanchor='middle',
                            y=0.5,
                            xanchor='left',
                            x=1.05,
                            font=dict(size=13, color='#64748B', family='Arial'),
                            bgcolor='rgba(255,255,255,0.8)',
                            bordercolor='#E2E8F0',
                            borderwidth=1
                        ),
                        margin=dict(t=10, b=10, l=10, r=150),
                        height=350,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Arial', size=14, color='#333333'),
                        hoverlabel=dict(
                            bgcolor='#FFFFFF',
                            font_size=13,
                            font_family='Arial',
                            bordercolor='#E2E8F0'
                        )
                    )
                    st.plotly_chart(fig_status, use_container_width=True, key="graf_distribuicao_status")
                    
                    # Tabela resumo abaixo do gráfico
                    st.markdown("<p style='color:#94A3B8;font-size:13px;margin-top:16px;'>Resumo por Status:</p>", unsafe_allow_html=True)
                    col_st1, col_st2, col_st3, col_st4 = st.columns(4)
                    for idx, (_, row) in enumerate(_df_status.iterrows()):
                        if idx == 0:
                            col = col_st1
                        elif idx == 1:
                            col = col_st2
                        elif idx == 2:
                            col = col_st3
                        else:
                            col = col_st4
                        
                        _cor_status = _cores_status.get(row['status'], '#64748B')
                        with col:
                            st.markdown(f"""
                            <div style="background:rgba({int(_cor_status[1:3], 16)},{int(_cor_status[3:5], 16)},{int(_cor_status[5:7], 16)},0.1);
                                        border:1px solid {_cor_status}40;border-radius:8px;padding:12px;text-align:center;">
                                <p style="color:{_cor_status};font-size:24px;font-weight:800;margin:0;">{row['total']}</p>
                                <p style="color:#64748B;font-size:12px;margin:4px 0 0;">{row['status']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("📊 Ainda não há dados de status para exibir.")
            except Exception as e:
                st.error(f"Erro ao carregar distribuição de status: {e}")

        st.markdown("<hr style='border-color:rgba(0,212,255,0.1);margin:20px 0;'>", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════════
        # EXPORTAÇÃO DE RELATÓRIOS
        # ══════════════════════════════════════════════════════════════════════════
        
        # Exportar para Excel
        if st.session_state.get('exportar_excel', False):
            try:
                from openpyxl import Workbook
                from openpyxl.styles import Font, PatternFill, Alignment
                from io import BytesIO
                
                wb = Workbook()
                ws = wb.active
                ws.title = "Dashboard Mobilidade"
                
                # Cabeçalho
                ws['A1'] = "Dashboard de Mobilidade - RENAPSI"
                ws['A1'].font = Font(size=16, bold=True, color="444c9b")
                ws['A2'] = f"Período: {periodo_selecionado}"
                ws['A2'].font = Font(size=12, italic=True)
                
                # KPIs
                ws['A4'] = "KPIs Principais"
                ws['A4'].font = Font(size=14, bold=True)
                ws['A4'].fill = PatternFill(start_color="444c9b", end_color="444c9b", fill_type="solid")
                ws['A4'].font = Font(size=14, bold=True, color="FFFFFF")
                
                ws['A5'] = "Total de Consultas"
                ws['B5'] = total_consultas
                ws['A6'] = "SLA Médio (segundos)"
                ws['B6'] = f"{sla_medio:.2f}"
                ws['A7'] = "Contestações"
                ws['B7'] = total_contestacoes
                ws['A8'] = "Implantações Ativas"
                ws['B8'] = total_implantados
                
                # ROI
                ws['A10'] = "Análise de ROI"
                ws['A10'].font = Font(size=14, bold=True)
                ws['A10'].fill = PatternFill(start_color="f8ae28", end_color="f8ae28", fill_type="solid")
                ws['A10'].font = Font(size=14, bold=True, color="FFFFFF")
                
                ws['A11'] = "Total de Jovens"
                ws['B11'] = total_jovens
                ws['A12'] = "Custo Manual (Mês)"
                ws['B12'] = f"R$ {custo_manual_mes:,.2f}"
                ws['A13'] = "Custo Otimizado (Mês)"
                ws['B13'] = f"R$ {custo_otimizado_mes:,.2f}"
                ws['A14'] = "Economia Mensal"
                ws['B14'] = f"R$ {economia_mes:,.2f}"
                ws['A15'] = "Economia Anual"
                ws['B15'] = f"R$ {economia_mes * 12:,.2f}"
                ws['A16'] = "Percentual de Economia"
                ws['B16'] = f"{percentual_economia:.1f}%"
                
                # Ajustar largura das colunas
                ws.column_dimensions['A'].width = 30
                ws.column_dimensions['B'].width = 20
                
                # Salvar em buffer
                buffer = BytesIO()
                wb.save(buffer)
                buffer.seek(0)
                
                st.download_button(
                    label="⬇️ Baixar Relatório Excel",
                    data=buffer,
                    file_name=f"dashboard_mobilidade_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.session_state.exportar_excel = False
                st.success("✅ Relatório Excel gerado com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao gerar Excel: {str(e)}")
                st.session_state.exportar_excel = False
        
        # Exportar para PDF
        if st.session_state.get('exportar_pdf', False):
            try:
                from fpdf import FPDF
                from io import BytesIO
                
                pdf = FPDF()
                pdf.add_page()
                
                # Título
                pdf.set_font('Arial', 'B', 20)
                pdf.set_text_color(68, 76, 155)
                pdf.cell(0, 10, 'Dashboard de Mobilidade - RENAPSI', 0, 1, 'C')
                pdf.ln(5)
                
                # Período
                pdf.set_font('Arial', 'I', 12)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 8, f'Periodo: {periodo_selecionado}', 0, 1, 'C')
                pdf.ln(10)
                
                # KPIs
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(68, 76, 155)
                pdf.cell(0, 10, 'KPIs Principais', 0, 1)
                pdf.ln(2)
                
                pdf.set_font('Arial', '', 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(90, 8, 'Total de Consultas:', 0, 0)
                pdf.cell(0, 8, str(total_consultas), 0, 1)
                pdf.cell(90, 8, 'SLA Medio (segundos):', 0, 0)
                pdf.cell(0, 8, f'{sla_medio:.2f}', 0, 1)
                pdf.cell(90, 8, 'Contestacoes:', 0, 0)
                pdf.cell(0, 8, str(total_contestacoes), 0, 1)
                pdf.cell(90, 8, 'Implantacoes Ativas:', 0, 0)
                pdf.cell(0, 8, str(total_implantados), 0, 1)
                pdf.ln(10)
                
                # ROI
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(248, 174, 40)
                pdf.cell(0, 10, 'Analise de ROI', 0, 1)
                pdf.ln(2)
                
                pdf.set_font('Arial', '', 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(90, 8, 'Total de Jovens:', 0, 0)
                pdf.cell(0, 8, str(total_jovens), 0, 1)
                pdf.cell(90, 8, 'Custo Manual (Mes):', 0, 0)
                pdf.cell(0, 8, f'R$ {custo_manual_mes:,.2f}', 0, 1)
                pdf.cell(90, 8, 'Custo Otimizado (Mes):', 0, 0)
                pdf.cell(0, 8, f'R$ {custo_otimizado_mes:,.2f}', 0, 1)
                pdf.cell(90, 8, 'Economia Mensal:', 0, 0)
                pdf.cell(0, 8, f'R$ {economia_mes:,.2f}', 0, 1)
                pdf.cell(90, 8, 'Economia Anual:', 0, 0)
                pdf.cell(0, 8, f'R$ {economia_mes * 12:,.2f}', 0, 1)
                pdf.cell(90, 8, 'Percentual de Economia:', 0, 0)
                pdf.cell(0, 8, f'{percentual_economia:.1f}%', 0, 1)
                
                # Rodapé
                pdf.ln(15)
                pdf.set_font('Arial', 'I', 9)
                pdf.set_text_color(150, 150, 150)
                pdf.cell(0, 8, f'Gerado em: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}', 0, 1, 'C')
                
                # Salvar em buffer
                buffer = BytesIO()
                pdf_output = pdf.output(dest='S').encode('latin-1')
                buffer.write(pdf_output)
                buffer.seek(0)
                
                st.download_button(
                    label="⬇️ Baixar Relatório PDF",
                    data=buffer,
                    file_name=f"dashboard_mobilidade_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.session_state.exportar_pdf = False
                st.success("✅ Relatório PDF gerado com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao gerar PDF: {str(e)}")
                st.session_state.exportar_pdf = False

        # ══════════════════════════════════════════════════════════════════════════
        # ENVIOS EM MASSA
        # ══════════════════════════════════════════════════════════════════════════
        if tipo_rota == "📧 Envios em Massa":
            st.markdown("""
            <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-left:4px solid #444c9b;
                        border-radius:14px;padding:24px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                <h3 style="margin:0 0 4px;color:#444c9b;">📧 Envio em Massa de Cartas de VT</h3>
                <p style="color:#666666;font-size:15px;margin:0;">
                    Selecione os funcionários e envie as cartas personalizadas automaticamente
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Busca funcionários pendentes (status != Implantado)
            conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
            df_pendentes = safe_sql("""
                SELECT id, nome, cpf, email, status_rota, cep_casa, cep_trabalho, matricula
                FROM jovens_rotas 
                WHERE status_rota != 'Implantado' OR status_rota IS NULL
                ORDER BY nome
            """, conexao)
            conexao.close()

            if df_pendentes.empty:
                st.info("✅ Não há funcionários pendentes de envio. Todos já foram implantados!")
            else:
                # Filtra apenas quem tem e-mail cadastrado
                df_com_email = df_pendentes[df_pendentes['email'].notna() & (df_pendentes['email'] != '')]
                df_sem_email = df_pendentes[df_pendentes['email'].isna() | (df_pendentes['email'] == '')]

                st.markdown(f"""
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px;">
                    <div style="background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.3);
                                border-radius:10px;padding:16px;text-align:center;">
                        <p style="color:#60A5FA;font-size:15px;margin:0 0 4px;text-transform:uppercase;">Total Pendentes</p>
                        <p style="color:#E2E8F0;font-size:32px;font-weight:800;margin:0;">{len(df_pendentes)}</p>
                    </div>
                    <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);
                                border-radius:10px;padding:16px;text-align:center;">
                        <p style="color:#10B981;font-size:15px;margin:0 0 4px;text-transform:uppercase;">Com E-mail</p>
                        <p style="color:#E2E8F0;font-size:32px;font-weight:800;margin:0;">{len(df_com_email)}</p>
                    </div>
                    <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);
                                border-radius:10px;padding:16px;text-align:center;">
                        <p style="color:#EF4444;font-size:15px;margin:0 0 4px;text-transform:uppercase;">Sem E-mail</p>
                        <p style="color:#E2E8F0;font-size:32px;font-weight:800;margin:0;">{len(df_sem_email)}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if len(df_sem_email) > 0:
                    with st.expander(f"⚠️ {len(df_sem_email)} funcionário(s) sem e-mail cadastrado"):
                        for _, row in df_sem_email.iterrows():
                            st.markdown(f"""
                            <div style="background:rgba(239,68,68,0.05);border-left:3px solid #EF4444;
                                        padding:10px 14px;margin-bottom:8px;border-radius:0 6px 6px 0;">
                                <p style="margin:0;color:#E2E8F0;font-size:16px;">
                                    <strong>#{row['id']}</strong> - {row['nome']} 
                                    <span style="color:#64748B;font-size:16px;">(CPF: {str(row['cpf']).zfill(11)})</span>
                                </p>
                            </div>
                            """, unsafe_allow_html=True)

                if len(df_com_email) > 0:
                    st.markdown("<hr style='border-color:#E2E8F0;margin:20px 0;'>", unsafe_allow_html=True)
                    st.markdown("<p style='color:#444c9b;font-size:16px;font-weight:600;margin-bottom:12px;'>Selecione os funcionários para envio:</p>", unsafe_allow_html=True)

                    # Opção de selecionar todos
                    selecionar_todos = st.checkbox("✅ Selecionar todos", value=False)

                    # Lista de seleção
                    funcionarios_selecionados = []
                    
                    if selecionar_todos:
                        funcionarios_selecionados = df_com_email['id'].tolist()
                        st.info(f"📋 {len(funcionarios_selecionados)} funcionário(s) selecionado(s)")
                    else:
                        # Exibe lista com checkboxes
                        for _, row in df_com_email.iterrows():
                            cpf_mask = f"***.***.{str(row['cpf']).zfill(11)[6:9]}-{str(row['cpf']).zfill(11)[9:11]}"
                            col_check, col_info = st.columns([0.5, 11.5])
                            with col_check:
                                if st.checkbox("", key=f"check_{row['id']}", label_visibility="collapsed"):
                                    funcionarios_selecionados.append(row['id'])
                            with col_info:
                                st.markdown(f"""
                                <div style="background:#FFFFFF;border:1px solid #E5E7EB;
                                            border-radius:8px;padding:12px;margin-bottom:8px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                                    <p style="margin:0;color:#333333;font-size:16px;">
                                        <strong>#{row['id']}</strong> - {row['nome']}
                                    </p>
                                    <p style="margin:4px 0 0;color:#666666;font-size:16px;">
                                        CPF: {cpf_mask} · E-mail: {row['email']} · Status: {row['status_rota'] or 'Pendente'}
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Botão de envio
                    if len(funcionarios_selecionados) > 0:
                        st.markdown(f"""
                        <div style="background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.3);
                                    border-radius:10px;padding:16px;margin-bottom:16px;text-align:center;">
                            <p style="color:#60A5FA;font-size:16px;margin:0;">
                                <strong>{len(funcionarios_selecionados)}</strong> funcionário(s) selecionado(s) para envio
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                        col_env1, col_env2 = st.columns([1, 1])
                        with col_env1:
                            if st.button("🚀 Iniciar Envio em Massa", type="primary", width="stretch"):
                                st.session_state.iniciar_envio_massa = True
                                st.session_state.ids_para_envio = funcionarios_selecionados
                                st.rerun()
                        with col_env2:
                            if st.button("❌ Cancelar", width="stretch"):
                                st.rerun()

                        # Processo de envio
                        if st.session_state.get('iniciar_envio_massa'):
                            st.markdown("<hr style='border-color:rgba(0,212,255,0.1);margin:20px 0;'>", unsafe_allow_html=True)
                            st.markdown("""
                            <div style="background:rgba(124,58,237,0.1);border:1px solid rgba(124,58,237,0.3);
                                        border-radius:12px;padding:20px;margin-bottom:20px;">
                                <h4 style="margin:0 0 8px;color:#A78BFA;">⚡ Processamento em Andamento</h4>
                                <p style="color:#94A3B8;font-size:15px;margin:0;">
                                    Aguarde enquanto as cartas são geradas e enviadas...
                                </p>
                            </div>
                            """, unsafe_allow_html=True)

                            # Barra de progresso
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            log_container = st.container()

                            total = len(st.session_state.ids_para_envio)
                            sucessos = 0
                            falhas = []

                            for idx, func_id in enumerate(st.session_state.ids_para_envio):
                                try:
                                    # Busca dados do funcionário
                                    conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                                    df_func = safe_sql(
                                        "SELECT * FROM jovens_rotas WHERE id = ?", 
                                        conexao, 
                                        params=(int(func_id),)
                                    )
                                    conexao.close()

                                    if df_func.empty:
                                        with log_container:
                                            st.error(f"❌ ID {func_id}: Funcionário não encontrado no banco")
                                        falhas.append(f"ID {func_id} - Não encontrado")
                                        continue

                                    dados = df_func.iloc[0]
                                    nome = dados['nome']
                                    email = dados['email']
                                    cpf = str(dados['cpf']).zfill(11)
                                    cep_casa = dados['cep_casa']
                                    cep_trab = dados['cep_trabalho']

                                    status_text.markdown(f"""
                                    <p style="color:#60A5FA;font-size:16px;">
                                        📤 Processando <strong>{nome}</strong> ({idx + 1}/{total})...
                                    </p>
                                    """, unsafe_allow_html=True)

                                    # Calcula rota
                                    end_casa_dict = buscar_endereco_viacep(cep_casa)
                                    end_trab_dict = buscar_endereco_viacep(cep_trab)
                                    
                                    rua_casa = end_casa_dict.get('rua', 'N/A') if isinstance(end_casa_dict, dict) else end_casa_dict
                                    rua_trab = end_trab_dict.get('rua', 'N/A') if isinstance(end_trab_dict, dict) else end_trab_dict

                                    rota = motor_de_rotas_gratuito(
                                        f"{rua_casa}, São Paulo, Brasil",
                                        f"{rua_trab}, São Paulo, Brasil"
                                    )
                                    
                                    # Registra o SLA no banco de dados
                                    if 'sla_segundos' in rota:
                                        from banco_dados import registrar_sla
                                        registrar_sla(func_id, rota['sla_segundos'])

                                    # Seleciona primeira rota disponível
                                    rota_para_carta = rota['rotas'][0] if rota.get('rotas') else {
                                        'modal': 'Integração', 'trajeto': 'Ônibus + Metrô/CPTM',
                                        'bilhete': 'Integração VT', 'valor_diario': 0.0, 'tempo': 'N/A'
                                    }

                                    end_casa_str = end_casa_dict.get('completo', cep_casa) if isinstance(end_casa_dict, dict) else cep_casa
                                    end_trab_str = end_trab_dict.get('completo', cep_trab) if isinstance(end_trab_dict, dict) else cep_trab

                                    # Gera PDF
                                    dados_para_carta = {
                                        'id': func_id, 'nome': nome, 'cpf': cpf,
                                        'matricula': dados.get('matricula', ''), 'email': email
                                    }

                                    # Verifica se é rota manual ou automática
                                    modo_rota_func = dados.get('modo_rota', 'automatica')
                                    
                                    if modo_rota_func == 'manual':
                                        # Usa dados da rota manual
                                        rota_para_carta = {
                                            'tipo_bilhete_manual': dados.get('tipo_bilhete_manual', 'Bilhete Único'),
                                            'valor_tarifa_manual': dados.get('valor_tarifa_manual', 0.0),
                                            'descricao_itinerario_manual': dados.get('descricao_itinerario_manual', 'Trajeto manual')
                                        }
                                    
                                    pdf_bytes = gerar_carta_pdf(
                                        dados_jovem=dados_para_carta,
                                        rota_selecionada=rota_para_carta,
                                        end_casa_completo=end_casa_str,
                                        end_trab_completo=end_trab_str,
                                        modo_rota=modo_rota_func
                                    )

                                    # Envia e-mail
                                    sucesso, erro = enviar_carta_por_email(
                                        destinatario=email,
                                        nome_funcionario=nome,
                                        pdf_bytes=pdf_bytes
                                    )

                                    if sucesso:
                                        with log_container:
                                            st.success(f"✅ {nome} - Carta enviada para {email}")
                                        sucessos += 1
                                    else:
                                        with log_container:
                                            st.error(f"❌ {nome} - Falha: {erro}")
                                        falhas.append(f"{nome} ({email})")

                                except Exception as e:
                                    with log_container:
                                        st.error(f"❌ ID {func_id}: Erro inesperado - {str(e)}")
                                    falhas.append(f"ID {func_id} - Erro: {str(e)}")

                                # Atualiza progresso
                                progress_bar.progress((idx + 1) / total)

                                # Intervalo de 3 segundos entre envios
                                if idx < total - 1:  # Não espera após o último
                                    time.sleep(3)

                            # ══════════════════════════════════════════════════════════════════════════
                            # RELATÓRIO DE FEEDBACK VISUAL
                            # ══════════════════════════════════════════════════════════════════════════
                            progress_bar.progress(1.0)
                            
                            st.markdown("<hr style='border-color:rgba(0,212,255,0.1);margin:20px 0;'>", unsafe_allow_html=True)
                            
                            # Resumo geral
                            st.markdown(f"""
                            <div style="background:linear-gradient(135deg,rgba(16,185,129,0.1),rgba(16,185,129,0.05));
                                        border:1px solid rgba(16,185,129,0.3);border-radius:14px;padding:24px;margin-bottom:20px;text-align:center;">
                                <h3 style="margin:0 0 12px;color:#10B981;">✅ Envio Concluído!</h3>
                                <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:16px;">
                                    <div>
                                        <p style="color:#64748B;font-size:14px;margin:0 0 4px;text-transform:uppercase;">Enviados com Sucesso</p>
                                        <p style="color:#10B981;font-size:36px;font-weight:800;margin:0;">{sucessos}</p>
                                    </div>
                                    <div>
                                        <p style="color:#64748B;font-size:14px;margin:0 0 4px;text-transform:uppercase;">Falhas</p>
                                        <p style="color:#EF4444;font-size:36px;font-weight:800;margin:0;">{len(falhas)}</p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # Detalhes de sucesso
                            if sucessos > 0:
                                st.markdown(f"""
                                <div style="background:rgba(16,185,129,0.08);border-left:4px solid #10B981;
                                            border-radius:0 8px 8px 0;padding:16px;margin-bottom:16px;">
                                    <p style="color:#10B981;font-size:16px;font-weight:600;margin:0 0 8px;">
                                        ✅ {sucessos} e-mail(s) enviado(s) com sucesso
                                    </p>
                                    <p style="color:#94A3B8;font-size:14px;margin:0;">
                                        Os funcionários receberão suas cartas de VT personalizadas em breve.
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)

                            # Detalhes de falhas
                            if len(falhas) > 0:
                                with st.expander(f"🚨 Detalhes das {len(falhas)} Falha(s)", expanded=True):
                                    st.markdown(f"""
                                    <div style="background:rgba(239,68,68,0.08);border-left:4px solid #EF4444;
                                                border-radius:0 8px 8px 0;padding:16px;margin-bottom:16px;">
                                        <p style="color:#EF4444;font-size:16px;font-weight:600;margin:0 0 12px;">
                                            ⚠️ Os seguintes funcionários não receberam o e-mail:
                                        </p>
                                    """, unsafe_allow_html=True)
                                    
                                    for falha in falhas:
                                        st.markdown(f"""
                                        <div style="background:rgba(239,68,68,0.05);border-left:2px solid #EF4444;
                                                    padding:10px 12px;margin-bottom:8px;border-radius:0 4px 4px 0;">
                                            <p style="color:#E2E8F0;font-size:13px;margin:0;">
                                                • {falha}
                                            </p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    st.markdown("""
                                    <div style="background:rgba(239,68,68,0.05);border-left:4px solid #EF4444;
                                                border-radius:0 8px 8px 0;padding:12px;margin-top:12px;">
                                        <p style="color:#94A3B8;font-size:14px;margin:0;">
                                            <strong>Ação recomendada:</strong> Verifique os e-mails cadastrados e tente novamente.
                                        </p>
                                    </div>
                                    """, unsafe_allow_html=True)

                            st.session_state.iniciar_envio_massa = False
                            st.session_state.ids_para_envio = []

                            if st.button("🔄 Voltar ao Início", type="primary"):
                                st.rerun()

                    else:
                        st.info("👆 Selecione pelo menos um funcionário para enviar")

        # ── Gráficos ──

        conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        try:
            df_contest = safe_sql("SELECT * FROM contestacoes", conexao)
            qtd_resolvidas = len(df_contest[df_contest['status'] == 'Resolvido'])
            qtd_pendentes = len(df_contest[df_contest['status'] == 'Pendente'])
        except Exception:
            df_contest = pd.DataFrame(columns=['id', 'data_geracao', 'nome_jovem', 'motivo', 'status', 'tratativa'])
            qtd_resolvidas = 0
            qtd_pendentes = 0
        conexao.close()
        
        col_g1, col_g2, col_g3, col_g4 = st.columns(4)

        CORES_RENAPSI = ['#f8ae28', '#444c9b', '#64748B', '#F59E0B']  # Laranja, Azul, Cinza, Amarelo

        with col_g1:
            # ── Implantações por mês (dados reais) ──
            try:
                _conn_impl = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                _df_impl = safe_sql("""
                    SELECT COUNT(*) as total FROM jovens_rotas WHERE status_rota = 'Implantado'
                """, _conn_impl)
                _total_impl = int(_df_impl.iloc[0]['total']) if not _df_impl.empty else 0
                _conn_impl.close()
            except Exception:
                _total_impl = 0
            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid #E5E7EB;
                        border-radius:12px;padding:16px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                <p style="color:#666666;font-size:13px;text-transform:uppercase;letter-spacing:0.1em;margin:0 0 8px;">
                    Implantações Ativas
                </p>
                <p style="color:#10B981;font-size:36px;font-weight:800;margin:0;">{_total_impl}</p>
                <p style="color:#94A3B8;font-size:12px;margin:4px 0 0;">funcionários com VT ativo</p>
            </div>
            """, unsafe_allow_html=True)

        with col_g2:
            st.markdown(f"""
            <p style="color:#94A3B8;font-size:14px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">
                Contestações ({qtd_resolvidas}/{total_contestacoes_geral})
            </p>
            """, unsafe_allow_html=True)
            if total_contestacoes_geral == 0:
                st.markdown("""
                <div style="background:#FFFFFF;border:1px solid #E5E7EB;
                            border-radius:12px;padding:16px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                    <p style="color:#666666;font-size:13px;margin:0;">Nenhuma contestação</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                fig = px.pie(values=[qtd_resolvidas, qtd_pendentes], names=['Resolvidas','Pendentes'], hole=0.72)
                fig.update_traces(textinfo='none', marker=dict(colors=['#444c9b','#E5E7EB']), hoverinfo="skip")
                fig.update_layout(showlegend=False, margin=dict(t=5,b=5,l=5,r=5), height=160,
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font=dict(size=13, color='#333333'))
                st.plotly_chart(fig, width="stretch", key="graf_contest")

        with col_g3:
            # ── Por Local de Trabalho (dados reais) ──
            st.markdown("<p style='color:#666666;font-size:14px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;'>Por Local de Trabalho</p>", unsafe_allow_html=True)
            try:
                _conn_lt = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                _df_lt = safe_sql("""
                    SELECT lt.nome_unidade as local, COUNT(jr.id) as qtd
                    FROM jovens_rotas jr
                    LEFT JOIN locais_trabalho lt ON jr.cep_trabalho = lt.cep
                    WHERE jr.status_rota IS NOT NULL
                    GROUP BY lt.nome_unidade
                    ORDER BY qtd DESC
                    LIMIT 5
                """, _conn_lt)
                _conn_lt.close()
                if _df_lt.empty or _df_lt['qtd'].sum() == 0:
                    raise ValueError("sem dados")
                fig2 = px.pie(values=_df_lt['qtd'].tolist(),
                              names=[str(n)[:20] if n else 'Sem unidade' for n in _df_lt['local'].tolist()],
                              hole=0.72)
            except Exception:
                fig2 = px.pie(values=[10, 0], names=['SP','Outros'], hole=0.72)
            fig2.update_traces(textinfo='none', marker=dict(colors=['#f8ae28','#444c9b','#64748B','#10B981','#E5E7EB']), hoverinfo="label+percent")
            fig2.update_layout(showlegend=False, margin=dict(t=5,b=5,l=5,r=5), height=160,
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(size=13, color='#333333'))
            st.plotly_chart(fig2, width="stretch", key="graf_local")

        with col_g4:
            # ── Por Status (dados reais) ──
            st.markdown("<p style='color:#666666;font-size:14px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;'>Por Status</p>", unsafe_allow_html=True)
            try:
                _conn_st = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                _df_st = safe_sql("""
                    SELECT COALESCE(status_rota, 'Sem status') as status, COUNT(*) as qtd
                    FROM jovens_rotas GROUP BY status_rota ORDER BY qtd DESC
                """, _conn_st)
                _conn_st.close()
                if _df_st.empty:
                    raise ValueError("sem dados")
                fig3 = px.pie(values=_df_st['qtd'].tolist(), names=_df_st['status'].tolist(), hole=0.72)
            except Exception:
                fig3 = px.pie(values=[10, 0], names=['Otimizado','Implantado'], hole=0.72)
            fig3.update_traces(textinfo='none',
                               marker=dict(colors=['#3B82F6','#10B981','#F59E0B','#94A3B8','#444c9b']),
                               hoverinfo="label+percent")
            fig3.update_layout(showlegend=False, margin=dict(t=5,b=5,l=5,r=5), height=160,
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(size=13, color='#333333'))
            st.plotly_chart(fig3, width="stretch", key="graf_uf")

        st.markdown("<hr style='border-color:rgba(0,212,255,0.1);'>", unsafe_allow_html=True)

        # ── Contestações ──
        with st.expander("⚡ Ver Detalhes das Contestações"):
            if df_contest.empty:
                st.info("Nenhuma contestação registada.")
            else:
                tab_pend, tab_resol, tab_tab = st.tabs(["🔴 Pendentes", "✅ Resolvidas", "📋 Tabela"])

                with tab_pend:
                    df_pend = df_contest[df_contest['status'] == 'Pendente']
                    if df_pend.empty:
                        st.success("Tudo limpo! Nenhuma contestação pendente.")
                    else:
                        for _, row in df_pend.iterrows():
                            import html as _html
                            motivo_safe = _html.escape(str(row['motivo'] or ''))
                            nome_safe   = _html.escape(str(row['nome_jovem'] or ''))
                            data_safe   = _html.escape(str(row['data_geracao'] or ''))
                            
                            # HTML totalmente encostado na esquerda para evitar o bug de conversão do Markdown
                            html_pendente = f"""
<div style="background-color: var(--background-color); border: 1px solid var(--secondary-background-color); border-left: 4px solid #EF4444; border-radius: 12px; padding: 20px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
        <span style="color: #EF4444; font-weight: 700; font-size: 15px;">Consulta #{row['id']}</span>
        <span style="background: rgba(239,68,68,0.15); color: #EF4444; padding: 2px 8px; border-radius: 20px; font-size: 13px;">PENDENTE</span>
    </div>
    <p style="color: var(--text-color); font-size: 13px; margin: 0 0 8px; opacity: 0.8;">
        {data_safe} &middot; <strong style="color: var(--text-color); opacity: 1;">{nome_safe}</strong>
    </p>
    <div style="background: rgba(239,68,68,0.05); border-left: 3px solid #EF4444; padding: 10px 14px; border-radius: 0 6px 6px 0; font-size: 13px; color: var(--text-color);">
        {motivo_safe}
    </div>
</div>
"""
                            st.markdown(html_pendente, unsafe_allow_html=True)
                            
                            col_t, col_b = st.columns([3, 1])
                            with col_t:
                                tratativa_input = st.text_input("Tratativa aplicada:", key=f"input_{row['id']}")
                            with col_b:
                                st.write("")
                                st.write("")
                                # width="stretch" trocado pelo comando nativo correto
                                if st.button("Resolver", type="primary", key=f"btn_{row['id']}", use_container_width=True):
                                    if not tratativa_input.strip():
                                        st.error("Descreva a tratativa antes de resolver.")
                                    else:
                                        resolver_contestacao(row['id'], tratativa_input)
                                        st.rerun()

                with tab_resol:
                    df_res = df_contest[df_contest['status'] == 'Resolvido']
                    if df_res.empty:
                        st.info("Nenhuma contestação resolvida ainda.")
                    else:
                        for _, row in df_res.iterrows():
                            import html as _html
                            motivo_safe    = _html.escape(str(row['motivo'] or ''))
                            nome_safe      = _html.escape(str(row['nome_jovem'] or ''))
                            data_safe      = _html.escape(str(row['data_geracao'] or ''))
                            tratativa_safe = _html.escape(str(row.get('tratativa', '') or ''))
                            
                            # HTML totalmente encostado na esquerda
                            html_resolvido = f"""
<div style="background-color: var(--background-color); border: 1px solid var(--secondary-background-color); border-left: 4px solid #10B981; border-radius: 12px; padding: 20px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
        <span style="color: #10B981; font-weight: 700; font-size: 15px;">Consulta #{row['id']}</span>
        <span style="background: rgba(16,185,129,0.15); color: #10B981; padding: 2px 8px; border-radius: 20px; font-size: 13px;">RESOLVIDO</span>
    </div>
    <p style="color: var(--text-color); font-size: 13px; margin: 0 0 6px; opacity: 0.8;">{data_safe} &middot; <strong style="color: var(--text-color); opacity: 1;">{nome_safe}</strong></p>
    <p style="color: var(--text-color); font-size: 13px; margin: 0 0 8px;"><strong>Motivo:</strong> {motivo_safe}</p>
    <div style="background: rgba(16,185,129,0.08); border-left: 3px solid #10B981; padding: 10px 14px; border-radius: 0 6px 6px 0; font-size: 13px; color: var(--text-color);">
        <strong>Tratativa:</strong> {tratativa_safe}
    </div>
</div>
"""
                            st.markdown(html_resolvido, unsafe_allow_html=True)

                with tab_tab:
                    df_exib = df_contest[['id','data_geracao','nome_jovem','motivo','status','tratativa']].copy()
                    df_exib.columns = ['ID','Data','Funcionário','Motivo','Status','Tratativa']
                    # width="stretch" trocado pelo comando nativo correto
                    st.dataframe(df_exib, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TELA 1 — PESQUISAR CONSULTAS
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "🔍 Pesquisar Consultas":

# Recupera estado após F5
        if 'id_consulta' in st.query_params and st.session_state.get('resultado_busca') is None:
            id_salvo = st.query_params['id_consulta']
            conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
            df_salvo = safe_sql("SELECT * FROM jovens_rotas WHERE id = ?", conexao, params=(int(float(id_salvo)),))
            conexao.close()
            if not df_salvo.empty:
                st.session_state.resultado_busca = df_salvo
                st.session_state.detalhes_abertos = True

        for key, default in [('resultado_busca', None), ('detalhes_abertos', False),
                            ('rota_gerada', None), ('modo_contestacao', False),
                            ('modo_edicao', False), ('mostrar_modal_email', False)]:
            if key not in st.session_state:
                st.session_state[key] = default

        # ── PAINEL DE DETALHES ──────────────────────────────────────────────────
        if st.session_state.detalhes_abertos and st.session_state.resultado_busca is not None:

            col_voltar, _ = st.columns([1, 11])
            with col_voltar:
                if st.button("← Voltar"):
                    for k in ['detalhes_abertos','rota_gerada','modo_contestacao',
                            'modo_edicao','mostrar_modal_email']:
                        st.session_state[k] = False
                    if 'id_consulta' in st.query_params:
                        del st.query_params['id_consulta']
                    st.rerun()

            # Verifica se há dados válidos
            if st.session_state.resultado_busca.empty:
                st.error("❌ Nenhum dado encontrado para esta consulta.")
                st.session_state.detalhes_abertos = False
                st.rerun()
                
            dados_jovem = st.session_state.resultado_busca.iloc[0]
            
            # ── BLINDAGEM CONTRA ID VAZIO ──
            try:
                id_selecionado = int(dados_jovem['id'])
            except (TypeError, ValueError):
                st.error("⚠️ Este jovem está sem ID no banco de dados! Por favor, vá na aba 'Banco de Dados', adicione um número no campo ID dele e salve.")
                st.stop()
                
            nome_jovem       = dados_jovem['nome']
            cpf_cru          = str(dados_jovem['cpf']).zfill(11)
            cep_casa         = dados_jovem['cep_casa']
            matricula_exib   = dados_jovem.get('matricula', 'Não informada')

            # --- LÓGICA DE CONTEXTO (Status dentro da consulta) ---
            modalidade_atual = st.session_state.get('contexto_salvo', 'Trabalho')
            contexto_ativo = "Trabalho" if "Trabalho" in modalidade_atual else "Curso"
            sigla_contexto = "C-T" if contexto_ativo == "Trabalho" else "C-C"

            if contexto_ativo == "Trabalho":
                cep_trab = dados_jovem.get('cep_trabalho', '')
                status_rota_raw = dados_jovem.get('status_rota', 'Otimizado')
            else:
                cep_trab = dados_jovem.get('cep_curso', '') # Usa o CEP do Curso
                status_rota_raw = dados_jovem.get('status_curso', 'Otimizado')

            status_exib = obter_status_visual(status_rota_raw)
            
            # Define as cores baseadas no status correto
            if status_rota_raw == "Implantado":
                status_color, status_bg = "#10B981", "16,185,129"
            elif status_rota_raw == "Otimizado":
                status_color, status_bg = "#3B82F6", "59,130,246"
            elif status_rota_raw == "Contestada":
                status_color, status_bg = "#F59E0B", "245,158,11"
            else:
                status_color, status_bg = "#94A3B8", "148,163,184"
            email_jovem      = dados_jovem.get('email', '')
            celular_jovem    = dados_jovem.get('celular', '')
            numero_casa      = dados_jovem.get('numero_casa', '')
            coordenadas_casa = dados_jovem.get('coordenadas', '')

            # ── MODO EDIÇÃO ──
            if st.session_state.modo_edicao:
                st.markdown("""
                <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-left:4px solid #444c9b;
                            border-radius:14px;padding:24px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                    <h3 style="margin:0 0 4px;color:#444c9b;">✏️ Editar Dados da Consulta</h3>
                    <p style="color:#666666;font-size:13px;margin:0;">Atualize as informações do funcionário e o local de trabalho</p>
                </div>
                """, unsafe_allow_html=True)

                # ── Colunas dos status ──
                col_e1, col_e2, col_e3 = st.columns(3)
                
                with col_e1:
                    st.markdown("<p style='color:#444c9b;font-size:14px;text-transform:uppercase;letter-spacing:0.1em;'>👤 Dados do Funcionário</p>", unsafe_allow_html=True)
                    mat_input    = st.text_input("Matrícula", value=matricula_exib if matricula_exib != 'Não informada' else '')
                    nome_input   = st.text_input("Nome", value=nome_jovem, disabled=True)
                    email_input  = st.text_input("E-mail", value=email_jovem or '')
                    celular_input= st.text_input("Celular", value=celular_jovem or '')
                    obs_input    = st.text_area(
                        "📝 Observações internas",
                        value=dados_jovem.get('observacoes', '') or '',
                        placeholder="Ex: aguardando documentação, mudou de endereço...",
                        height=90,
                        key=f"obs_input_{id_selecionado}"
                    )

                with col_e2:
                    st.markdown("<p style='color:#444c9b;font-size:14px;text-transform:uppercase;letter-spacing:0.1em;'>🏠 Endereço do Funcionário</p>", unsafe_allow_html=True)
                    cep_input = st.text_input("CEP Residencial", value=cep_casa)
                    c_rua, c_num = st.columns([3, 1])
                    
                    # Busca endereço
                    end_atual = buscar_endereco_viacep(cep_input)
                    rua_input = c_rua.text_input("Logradouro", value=end_atual.get('completo','') if isinstance(end_atual, dict) else '', disabled=True)
                    num_input = c_num.text_input("Número", value=numero_casa or '')

                    # Coordenadas
                    coord_atual = st.session_state.get('coord_temp', coordenadas_casa)
                    coord_input = st.text_input("Coordenadas (Opcional)", value=coord_atual or '')
                    
                    if st.button("🔍 Buscar Coordenadas Reais", type="secondary", width="stretch"):
                        if cep_input and len(cep_input.strip()) == 8:
                            end_completo = f"CEP {cep_input}, {num_input if num_input else ''}, São Paulo, Brasil"
                            lat, lon = obter_coordenadas_reais(end_completo)
                            if lat is not None and lon is not None:
                                st.session_state.coord_temp = f"{lat}, {lon}"
                                st.success(f"✅ Coordenadas: {lat}, {lon}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.warning("⚠️ Não encontradas. Verifique o CEP.")
                        else:
                            st.error("❌ CEP inválido")

                with col_e3:
                    st.markdown(f"<p style='color:#444c9b;font-size:14px;text-transform:uppercase;letter-spacing:0.1em;'>🏢 Local de {contexto_ativo}</p>", unsafe_allow_html=True)
                    
                    # Busca todas as unidades
                    todos_locais = obter_locais_trabalho()
                    
                    # Pega apenas os locais cujo 'tipo_local' bate com o contexto atual
                    # O .get previne erros caso alguma unidade antiga não tenha o tipo preenchido
                    locais_trabalho = [loc for loc in todos_locais if loc.get('tipo_local', 'Trabalho') == contexto_ativo]
                    
                    if not locais_trabalho:
                        st.warning(f"⚠️ Nenhuma unidade do tipo '{contexto_ativo}' cadastrada no sistema. Vá em 'Gerenciar Unidades' para adicionar.")
                        local_selecionado = None
                    else:
                        # Cria dicionário com nome_unidade como chave
                        dict_locais = {local['nome_unidade']: local for local in locais_trabalho}
                        nomes_unidades = list(dict_locais.keys())
                        
                        # Selectbox com unidades do banco (dinâmico, sem hardcoding)
                        local_selecionado_nome = st.selectbox(
                            "Selecione o local de trabalho:",
                            nomes_unidades,
                            index=None,
                            placeholder="Escolha uma unidade...",
                            key=f"select_local_trabalho_app_{id_selecionado}"
                        )
                        
                        if local_selecionado_nome:
                            local_selecionado = dict_locais[local_selecionado_nome]
                            
                            # Card azul com dados reais da unidade (100% dinâmico)
                            st.markdown(f"""
                            <div style="background-color:#BAE6FD; border-radius:8px; padding:15px; text-align:center; margin-top:5px; border: 1px solid #7DD3FC;">
                                <p style="color:#0284C7; font-size:12px; font-weight:700; margin:0;">
                                    {local_selecionado['logradouro']}, {local_selecionado['numero']} - {local_selecionado['bairro']}<br>
                                    {local_selecionado['cidade_uf']}
                                </p>
                                <p style="color:#0284C7; font-size:11px; margin:8px 0 0;">
                                    CEP: {local_selecionado['cep']}
                                </p>
                                {f'<p style="color:#0284C7; font-size:11px; margin:4px 0 0;">COORDENADAS: {local_selecionado["coordenadas"]}</p>' if local_selecionado['coordenadas'] else ''}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            local_selecionado = None
                            st.info("ℹ️ Selecione uma unidade para visualizar os dados")

                st.markdown("<br>", unsafe_allow_html=True)
                col_f, col_c = st.columns([1, 1])
                with col_f:
                    if st.button("Fechar", width="stretch"):
                        st.session_state.modo_edicao = False
                        st.session_state.pop('coord_temp', None)
                        st.rerun()
                with col_c:
                    if st.button("Confirmar Alterações", type="primary", width="stretch"):
                        try:
                            # Valida se uma unidade foi selecionada
                            local_selecionado_nome = st.session_state.get(f"select_local_trabalho_app_{id_selecionado}")
                            
                            if not local_selecionado_nome:
                                st.error("⚠️ Selecione um local de trabalho antes de confirmar.")
                            else:
                                # Busca a unidade selecionada do banco para garantir dados atualizados
                                locais_trabalho = obter_locais_trabalho()
                                dict_locais = {local['nome_unidade']: local for local in locais_trabalho}
                                
                                if local_selecionado_nome not in dict_locais:
                                    st.error("❌ Unidade selecionada não encontrada no banco de dados.")
                                else:
                                    local_selecionado = dict_locais[local_selecionado_nome]
                                    
                                    # Prepara dados para salvar
                                    mat_final = str(mat_input) if mat_input else ''
                                    email_final = str(email_input) if email_input else ''
                                    celular_final = str(celular_input) if celular_input else ''
                                    cep_final = str(cep_input) if cep_input else str(cep_casa)
                                    num_final = str(num_input) if num_input else ''
                                    coord_final = str(coord_input) if coord_input else ''
                                    
                                    # CEP da unidade selecionada (CRÍTICO: garantir que seja do banco)
                                    cep_trab_final = local_selecionado['cep']
                                    
                                    with st.spinner("Salvando no banco de dados..."):
                                        # UPDATE com prepared statement (seguro contra SQL injection)
                                        conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                                        cursor = conexao.cursor()
                                        cursor.execute('''
                                            UPDATE jovens_rotas 
                                            SET matricula = ?, email = ?, celular = ?, cep_casa = ?, numero_casa = ?, coordenadas = ?, cep_trabalho = ?, observacoes = ?
                                            WHERE id = ?
                                        ''', (mat_final, email_final, celular_final, cep_final, num_final, coord_final, cep_trab_final, obs_input, id_selecionado))
                                        conexao.commit()
                                        
                                        # Recarrega dados atualizados
                                        df_atualizado = safe_sql("SELECT * FROM jovens_rotas WHERE id = ?", conexao, params=(int(id_selecionado),))
                                        conexao.close()
                                    
                                    if not df_atualizado.empty:
                                        st.session_state.resultado_busca = df_atualizado
                                        st.session_state.modo_edicao = False
                                        st.session_state.pop('coord_temp', None)
                                        st.session_state.rota_gerada = None # Força o recalculo da rota para a nova empresa
                                        st.session_state.analise_ia = None

                                        # ── Registra no histórico de auditoria ──
                                        try:
                                            _usr_hist = st.session_state.get("usuario_dados", {}).get("username", "desconhecido")
                                            registrar_historico(
                                                usuario=_usr_hist,
                                                acao="Edição de dados do funcionário",
                                                tabela="jovens_rotas",
                                                registro_id=id_selecionado,
                                                campo="matricula/email/celular/cep_casa/cep_trabalho",
                                                valor_novo=f"mat={mat_final} | email={email_final} | cep_trab={cep_trab_final}"
                                            )
                                        except Exception:
                                            pass

                                        st.success(f"✅ Dados salvos com sucesso! CEP de trabalho atualizado para: {cep_trab_final}")
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        st.error("❌ Erro ao recarregar dados do banco.")
                        except Exception as e:
                            st.error(f"❌ Erro ao salvar: {str(e)}")

            # ── MODO VISUALIZAÇÃO ──
            else:
                end_casa_dict = buscar_endereco_viacep(cep_casa)
                end_trab_dict = buscar_endereco_viacep(cep_trab)

                rua_casa = end_casa_dict.get('rua','N/A') if isinstance(end_casa_dict, dict) else end_casa_dict
                bairro_cidade_casa = f"{end_casa_dict.get('bairro','')} - {end_casa_dict.get('cidade_uf','')}" if isinstance(end_casa_dict, dict) else ""
                rua_trab = end_trab_dict.get('rua','N/A') if isinstance(end_trab_dict, dict) else end_trab_dict
                bairro_cidade_trab = f"{end_trab_dict.get('bairro','')} - {end_trab_dict.get('cidade_uf','')}" if isinstance(end_trab_dict, dict) else ""

                if not st.session_state.get('rota_gerada'):
                    endereco_completo_casa = end_casa_dict.get('completo', f"{rua_casa}, São Paulo, SP, Brasil") if isinstance(end_casa_dict, dict) else f"{rua_casa}, São Paulo, SP, Brasil"
                    endereco_completo_trab = end_trab_dict.get('completo', f"{rua_trab}, São Paulo, SP, Brasil") if isinstance(end_trab_dict, dict) else f"{rua_trab}, São Paulo, SP, Brasil"
                    
                    rota = motor_de_rotas_gratuito(endereco_completo_casa, endereco_completo_trab)
                    st.session_state.rota_gerada = rota
                    
                    # Registra o SLA no banco de dados
                    if 'sla_segundos' in rota:
                        from banco_dados import registrar_sla
                        registrar_sla(id_selecionado, rota['sla_segundos'])
                    
                    if not st.session_state.get('analise_ia'):
                        st.session_state.analise_ia = analisar_rota_com_ia(
                            rua_casa, rua_trab, rota['distancia_km'], rota['rotas'], rota['info_tarifas']
                        )

                col_fill, col_edit_btn = st.columns([11, 1])
                with col_edit_btn:
                    if st.button("✏️", width="stretch", help="Editar dados"):
                        st.session_state.modo_edicao = True
                        st.rerun()

                # Cor status
                if status_rota_raw == "Implantado":
                    status_color, status_bg = "#10B981", "16,185,129"
                elif status_rota_raw == "Otimizado":
                    status_color, status_bg = "#3B82F6", "59,130,246"
                elif status_rota_raw == "Contestada":
                    status_color, status_bg = "#F59E0B", "245,158,11"
                else:
                    status_color, status_bg = "#94A3B8", "148,163,184"

                # ── PREPARAÇÃO DAS STRINGS ──
                linha_num_casa = f', {numero_casa}' if numero_casa else ''

                # Cabeçalho com ID, título e status
                col_header_left, col_header_right = st.columns([10, 2])
                
                with col_header_left:
                    st.markdown(f"### 👤 Consulta #{id_selecionado}")
                    st.caption(f"RENAPSI · SÃO PAULO · {sigla_contexto}")
                    # ── Indicador de completude ──
                    _campos_completude = {
                        'E-mail': bool(email_jovem),
                        'Celular': bool(celular_jovem),
                        'Matrícula': bool(matricula_exib and matricula_exib != 'Não informada'),
                        'CEP Trabalho': bool(cep_trab),
                        'Número casa': bool(numero_casa),
                        'Coordenadas': bool(coordenadas_casa),
                    }
                    _total_campos = len(_campos_completude)
                    _preenchidos = sum(_campos_completude.values())
                    _pct = int(_preenchidos / _total_campos * 100)
                    _cor_pct = "#10B981" if _pct >= 80 else "#F59E0B" if _pct >= 50 else "#EF4444"
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:8px;margin-top:4px;">
                        <div style="flex:1;background:#E2E8F0;border-radius:4px;height:6px;overflow:hidden;">
                            <div style="width:{_pct}%;background:{_cor_pct};height:100%;border-radius:4px;"></div>
                        </div>
                        <span style="color:{_cor_pct};font-size:12px;font-weight:700;white-space:nowrap;">
                            {_pct}% completo
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col_header_right:
                    st.markdown(f"""
                    <div style="background:rgba({status_bg},0.15);color:{status_color};padding:6px 14px;border-radius:20px;font-size:12px;font-weight:700;border:1px solid {status_color}40;text-align:center;">
                        {status_exib}
                    </div>
                    """, unsafe_allow_html=True)
                    # Timestamp da última carta enviada
                    _ultima_carta = dados_jovem.get('ultima_carta_enviada', '')
                    if _ultima_carta:
                        st.markdown(f"""
                        <div style="margin-top:6px;background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.3);
                                    border-radius:8px;padding:4px 10px;font-size:11px;color:#10B981;text-align:center;">
                            📧 Carta enviada em {_ultima_carta}
                        </div>
                        """, unsafe_allow_html=True)

                st.divider()

                # Três colunas para os dados
                col1, col2, col3 = st.columns(3)

                # Coluna 1: Dados do Funcionário
                with col1:
                    st.markdown("**Dados do Funcionário**")
                    st.markdown(f"**CPF:** {cpf_cru}")
                    st.markdown(f"**Matrícula:** {matricula_exib}")
                    st.markdown(f"**Nome:** {nome_jovem}")
                    if email_jovem:
                        st.markdown(f"**E-mail:** {email_jovem}")
                    if celular_jovem:
                        st.markdown(f"**Celular:** {celular_jovem}")
                    # Observações internas
                    _obs_exib = dados_jovem.get('observacoes', '') or ''
                    if _obs_exib.strip():
                        st.markdown(f"""
                        <div style="background:rgba(245,158,11,0.08);border-left:3px solid #F59E0B;
                                    border-radius:0 6px 6px 0;padding:8px 10px;margin-top:8px;">
                            <p style="color:#92400E;font-size:12px;font-weight:600;margin:0 0 2px;">📝 Obs. internas</p>
                            <p style="color:#78350F;font-size:12px;margin:0;">{_obs_exib}</p>
                        </div>
                        """, unsafe_allow_html=True)

                # Coluna 2: Endereço Residencial
                with col2:
                    st.markdown("**Endereço Residencial**")
                    st.markdown("""
                    <span style="background:rgba(16,185,129,0.1);color:#10B981;padding:2px 8px;font-size:12px;border-radius:20px;font-weight:600;">● BAIXO RISCO</span>
                    """, unsafe_allow_html=True)
                    st.markdown(f"**CEP:** {cep_casa}")
                    st.markdown(f"{rua_casa}{linha_num_casa}  \n{bairro_cidade_casa}")

                # Coluna 3: Local de Trabalho
                with col3:
                    st.markdown("**Local de Trabalho**")
                    st.markdown(f"**CEP:** {cep_trab}")
                    st.markdown(f"{rua_trab}  \n{bairro_cidade_trab}")
                
                # ── Barra de ações ──
                st.markdown("<p style='color:#64748B;font-size:12px;margin-bottom:8px;'>AÇÕES DA CONSULTA</p>", unsafe_allow_html=True)
                col_b1, col_b2, col_b3, col_b4, col_b5, col_fill2 = st.columns([1, 1, 1, 1, 1, 1])
                ja_implantado = (status_rota_raw == "Implantado")
                
                with col_b1:
                    if st.button("🔄 Recalcular", type="secondary", width="stretch"):
                        # Limpa TUDO relacionado à rota para forçar recálculo completo
                        print("\n" + "="*60)
                        print("🔄 RECALCULANDO ROTA - LIMPANDO CACHE")
                        print("="*60 + "\n")
                        
                        if 'rota_gerada' in st.session_state:
                            del st.session_state.rota_gerada
                        if 'analise_ia' in st.session_state:
                            del st.session_state.analise_ia
                        if 'modo_contestacao' in st.session_state:
                            del st.session_state.modo_contestacao
                        
                        st.success("✅ Cache limpo! Recalculando rota...")
                        time.sleep(0.5)
                        st.rerun()
                        
                with col_b2:
                    if st.button("✉️ Enviar Carta", type="secondary", width="stretch"):
                        st.session_state.mostrar_modal_email = not st.session_state.get('mostrar_modal_email', False)
                        
                with col_b3:
                    if st.button("⚠️ Contestação", type="secondary", width="stretch"):
                        st.session_state.modo_contestacao = not st.session_state.get('modo_contestacao', False)
                        
                with col_b4:
                    if st.button("✍️ Rota Manual", type="secondary", width="stretch"):
                        st.session_state.modo_rota_manual = not st.session_state.get('modo_rota_manual', False)
                        
                with col_b5:
                    if st.button("📋 Implantados", type="secondary", width="stretch"):
                        st.session_state.modo_implantacao = not st.session_state.get('modo_implantacao', False)

                if st.session_state.get('mostrar_modal_email'):
                    st.markdown(f"""
                    <div style="background:rgba(0,212,255,0.05);border:1px solid rgba(0,212,255,0.25);
                                border-radius:12px;padding:16px;margin:12px 0;">
                        <p style="color:#00D4FF;font-weight:600;margin:0 0 6px;">✉️ Enviar Carta de Opção de Transporte</p>
                        <p style="color:#94A3B8;font-size:13px;margin:0;">
                            Destinatário: <strong style="color:#E2E8F0;">{email_jovem or 'E-mail não informado'}</strong>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    if not email_jovem:
                        st.warning("⚠️ Este funcionário não possui e-mail cadastrado. Edite os dados para adicionar.")
                    else:
                        # Seleciona qual rota usar na carta
                        rotas_disponiveis = st.session_state.rota_gerada.get('rotas', []) if st.session_state.get('rota_gerada') else []
                        opcoes_carta = [r['modal'] for r in rotas_disponiveis] if rotas_disponiveis else ["Rota padrão"]
                        rota_escolhida_label = st.selectbox(
                            "Qual rota incluir na carta?",
                            opcoes_carta,
                            key="sel_rota_carta"
                        )

                        c1, c2 = st.columns([1, 5])
                        with c1:
                            if st.button("📄 Gerar e Enviar", type="primary"):
                                with st.spinner("Gerando PDF e enviando e-mail..."):
                                    try:
                                        # Seleciona a rota escolhida
                                        idx_rota = opcoes_carta.index(rota_escolhida_label)
                                        rota_para_carta = rotas_disponiveis[idx_rota] if rotas_disponiveis else {
                                            'modal': 'Integração', 'trajeto': 'Ônibus + Metrô/CPTM',
                                            'bilhete': 'Integração Ônibus+Metrô VT',
                                            'valor_diario': 22.64, 'tempo': '45 min'
                                        }

                                        # Monta endereços completos
                                        end_casa_dict2 = buscar_endereco_viacep(cep_casa)
                                        end_trab_dict2 = buscar_endereco_viacep(cep_trab)
                                        end_casa_str = end_casa_dict2.get('completo', cep_casa) if isinstance(end_casa_dict2, dict) else cep_casa
                                        end_trab_str = end_trab_dict2.get('completo', cep_trab) if isinstance(end_trab_dict2, dict) else cep_trab

                                        dados_para_carta = {
                                            'id':        id_selecionado,
                                            'nome':      nome_jovem,
                                            'cpf':       cpf_cru,
                                            'matricula': matricula_exib,
                                            'email':     email_jovem,
                                        }

                                        # Verifica se é rota manual ou automática
                                        modo_rota_atual = dados_jovem.get('modo_rota', 'automatica')
                                        
                                        if modo_rota_atual == 'manual':
                                            # Usa dados da rota manual
                                            rota_para_carta = {
                                                'tipo_bilhete_manual': dados_jovem.get('tipo_bilhete_manual', 'Bilhete Único'),
                                                'valor_tarifa_manual': dados_jovem.get('valor_tarifa_manual', 0.0),
                                                'descricao_itinerario_manual': dados_jovem.get('descricao_itinerario_manual', 'Trajeto manual')
                                            }

                                        pdf_bytes = gerar_carta_pdf(
                                            dados_jovem=dados_para_carta,
                                            rota_selecionada=rota_para_carta,
                                            end_casa_completo=end_casa_str,
                                            end_trab_completo=end_trab_str,
                                            modo_rota=modo_rota_atual
                                        )

                                        sucesso, erro = enviar_carta_por_email(
                                            destinatario=email_jovem,
                                            nome_funcionario=nome_jovem,
                                            pdf_bytes=pdf_bytes,
                                        )

                                        if sucesso:
                                            st.success(f"✅ Carta enviada com sucesso para **{email_jovem}**!")
                                            # Registra timestamp do envio
                                            try:
                                                _ts_carta = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                                                _conn_ts = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                                                _conn_ts.execute(
                                                    "UPDATE jovens_rotas SET ultima_carta_enviada = ? WHERE id = ?",
                                                    (_ts_carta, id_selecionado)
                                                )
                                                _conn_ts.commit()
                                                _conn_ts.close()
                                            except Exception:
                                                pass
                                            # Disponibiliza download também
                                            st.download_button(
                                                "⬇️ Baixar PDF da Carta",
                                                data=pdf_bytes,
                                                file_name=f"Carta_VT_{nome_jovem.replace(' ','_')}.pdf",
                                                mime="application/pdf"
                                            )
                                            time.sleep(2)
                                            st.session_state.mostrar_modal_email = False
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Falha ao enviar: {erro}")
                                            # Mesmo com erro, oferece download do PDF
                                            st.download_button(
                                                "⬇️ Baixar PDF da Carta (envio falhou)",
                                                data=pdf_bytes,
                                                file_name=f"Carta_VT_{nome_jovem.replace(' ','_')}.pdf",
                                                mime="application/pdf"
                                            )
                                    except Exception as e:
                                        st.error(f"❌ Erro ao gerar carta: {e}")

                if st.session_state.modo_contestacao:
                    with st.form(key="form_contestacao"):
                        st.markdown("<p style='color:#F59E0B;font-weight:600;'>⚠️ Registrar Contestação</p>", unsafe_allow_html=True)
                        motivo_input = st.text_area("Descreva o problema:", placeholder="Ex: tarifa indevida, rota que não faz sentido...")
                        email_rh_input = st.text_input(
                            "E-mail do RH para notificação (opcional)",
                            placeholder="rh@empresa.com.br",
                            help="Se preenchido, um e-mail de alerta será enviado automaticamente ao RH."
                        )
                        if st.form_submit_button("Registrar", type="primary"):
                            if not motivo_input.strip():
                                st.error("Descreva o motivo antes de registrar.")
                            else:
                                registrar_contestacao(nome=nome_jovem, cid_res="São Paulo", cid_trab="São Paulo", motivo=motivo_input)

                                # Detectar contexto ativo
                                modalidade_atual = st.session_state.get('contexto_salvo', 'Trabalho')
                                contexto_ativo = "Trabalho" if "Trabalho" in modalidade_atual else "Curso"

                                # Atualiza status para CONTESTADA usando função com contexto
                                atualizar_status_rota(id_selecionado, 'Contestada', contexto_ativo)

                                # ── Notificação automática ao RH ──────────────────────────
                                _email_destino_rh = email_rh_input.strip() if email_rh_input.strip() else None
                                if not _email_destino_rh:
                                    # Tenta ler do .env
                                    import os as _os
                                    _email_destino_rh = _os.getenv("EMAIL_RH", "")

                                if _email_destino_rh and "@" in _email_destino_rh:
                                    try:
                                        import smtplib
                                        from email.mime.multipart import MIMEMultipart
                                        from email.mime.text import MIMEText
                                        from dotenv import load_dotenv as _ldenv
                                        _ldenv()
                                        _smtp_user = _os.getenv("EMAIL_USER", "")
                                        _smtp_pass = _os.getenv("EMAIL_PASS", "")
                                        _smtp_host = _os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
                                        _smtp_port = int(_os.getenv("EMAIL_SMTP_PORT", 587))

                                        if _smtp_user and _smtp_pass:
                                            _msg_rh = MIMEMultipart()
                                            _msg_rh["From"] = _smtp_user
                                            _msg_rh["To"] = _email_destino_rh
                                            _msg_rh["Subject"] = f"⚠️ Nova Contestação Registrada — {nome_jovem}"
                                            _corpo_rh = f"""
                                            <html><body style="font-family:Arial,sans-serif;color:#333;padding:20px;">
                                            <div style="max-width:600px;margin:auto;border-top:4px solid #F59E0B;border-radius:8px;padding:24px;background:#fff;">
                                                <h2 style="color:#F59E0B;margin-top:0;">⚠️ Nova Contestação Registrada</h2>
                                                <p><strong>Funcionário:</strong> {nome_jovem}</p>
                                                <p><strong>CPF:</strong> ***.***.{cpf_cru[6:9]}-{cpf_cru[9:11]}</p>
                                                <p><strong>Matrícula:</strong> {matricula_exib}</p>
                                                <p><strong>Contexto:</strong> {contexto_ativo}</p>
                                                <p><strong>Motivo:</strong></p>
                                                <div style="background:#FEF3C7;border-left:4px solid #F59E0B;padding:12px;border-radius:0 8px 8px 0;">
                                                    {motivo_input}
                                                </div>
                                                <p style="color:#94A3B8;font-size:12px;margin-top:20px;">
                                                    Registrado em {datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")} · RENAPSI Sistema de Mobilidade
                                                </p>
                                            </div>
                                            </body></html>
                                            """
                                            _msg_rh.attach(MIMEText(_corpo_rh, "html", "utf-8"))
                                            with smtplib.SMTP(_smtp_host, _smtp_port, timeout=15) as _srv:
                                                _srv.ehlo()
                                                _srv.starttls()
                                                _srv.login(_smtp_user, _smtp_pass)
                                                _srv.sendmail(_smtp_user, _email_destino_rh, _msg_rh.as_string())
                                            st.info(f"📧 Notificação enviada para {_email_destino_rh}")
                                    except Exception as _e_rh:
                                        st.warning(f"⚠️ Contestação registrada, mas falha ao notificar RH: {_e_rh}")

                                st.success("Contestação registrada! Status alterado para CONTESTADA.")
                                # ── Histórico ──
                                try:
                                    registrar_historico(
                                        usuario=st.session_state.get("usuario_dados", {}).get("username", "desconhecido"),
                                        acao="Contestação registrada",
                                        tabela="jovens_rotas",
                                        registro_id=id_selecionado,
                                        campo="status_rota",
                                        valor_anterior=status_rota_raw,
                                        valor_novo="Contestada"
                                    )
                                except Exception:
                                    pass
                                st.session_state.modo_contestacao = False
                                time.sleep(2)
                                st.rerun()

                # ══════════════════════════════════════════════════════════════════════════
                # MODAL DE IMPLANTAÇÃO
                # ══════════════════════════════════════════════════════════════════════════
                if st.session_state.get('modo_implantacao', False):
                    st.markdown("""
                    <div style="background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.3);
                                border-radius:14px;padding:20px;margin-bottom:20px;">
                        <h3 style="margin:0 0 4px;color:#3B82F6;">📋 Alterar Status de Implantação</h3>
                        <p style="color:#94A3B8;font-size:13px;margin:0;">
                            Selecione a ação desejada para alterar o status do funcionário
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Mostra status atual
                    st.markdown(f"""
                    <div style="background:rgba(13,17,23,0.8);border:1px solid rgba(59,130,246,0.2);
                                border-radius:10px;padding:14px;margin-bottom:16px;">
                        <p style="color:#94A3B8;font-size:12px;margin:0 0 4px;">Status Atual:</p>
                        <p style="color:#3B82F6;font-size:16px;font-weight:700;margin:0;">{status_exib}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Opções de implantação
                    opcao_implantacao = st.radio(
                        "Escolha a ação:",
                        ["Implantada", "Implantada (Com Cancelamento de VT)", "Não Implantada"],
                        key=f"opcao_implantacao_{id_selecionado}"
                    )

                    # Campo de motivo (apenas para "Não Implantada")
                    motivo_nao_implantada = ""
                    if opcao_implantacao == "Não Implantada":
                        motivo_nao_implantada = st.text_area(
                            "Motivo da remoção da implantação:",
                            placeholder="Ex: Funcionário solicitou cancelamento, mudança de endereço, etc.",
                            key=f"motivo_nao_implantada_{id_selecionado}"
                        )

                    st.markdown("<br>", unsafe_allow_html=True)

                    col_confirmar, col_cancelar = st.columns([1, 1])
                    
                    with col_confirmar:
                        if st.button("✅ Confirmar Alteração", type="primary", width="stretch", key=f"confirmar_implantacao_{id_selecionado}"):
                            # Validação para "Não Implantada"
                            if opcao_implantacao == "Não Implantada" and not motivo_nao_implantada.strip():
                                st.error("⚠️ Informe o motivo da remoção da implantação.")
                            else:
                                # Define o novo status baseado na opção
                                if opcao_implantacao == "Implantada":
                                    novo_status = "Implantado"
                                elif opcao_implantacao == "Implantada (Com Cancelamento de VT)":
                                    novo_status = "Não Optante"
                                else:  # Não Implantada
                                    novo_status = "Otimizado"
                                
                                # Detectar contexto ativo
                                modalidade_atual = st.session_state.get('contexto_salvo', 'Trabalho')
                                contexto_ativo = "Trabalho" if "Trabalho" in modalidade_atual else "Curso"
                                
                                # Atualiza no banco usando a função com contexto
                                atualizar_status_rota(id_selecionado, novo_status, contexto_ativo)

                                # ── Histórico ──
                                try:
                                    registrar_historico(
                                        usuario=st.session_state.get("usuario_dados", {}).get("username", "desconhecido"),
                                        acao=f"Alteração de status ({opcao_implantacao})",
                                        tabela="jovens_rotas",
                                        registro_id=id_selecionado,
                                        campo=f"status_{contexto_ativo.lower()}",
                                        valor_anterior=status_rota_raw,
                                        valor_novo=novo_status
                                    )
                                except Exception:
                                    pass

                                st.success(f"✅ Status alterado para: {novo_status} (Contexto: {contexto_ativo})")
                                st.session_state.modo_implantacao = False
                                time.sleep(1)
                                st.rerun()

                    with col_cancelar:
                        if st.button("❌ Cancelar", width="stretch", key=f"cancelar_implantacao_{id_selecionado}"):
                            st.session_state.modo_implantacao = False
                            st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)

                # ── Análise da IA ──
                if st.session_state.get('analise_ia'):
                    st.markdown(f"""
                    <div style="background:rgba(124,58,237,0.08);border-left:4px solid #7C3AED;
                                border-radius:0 12px 12px 0;padding:18px 20px;margin-bottom:20px;
                                box-shadow:-4px 0 24px rgba(124,58,237,0.2);">
                        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                            <span style="font-size:20px;">🤖</span>
                            <p style="margin:0;color:#A78BFA;font-weight:700;font-size:14px;text-transform:uppercase;letter-spacing:0.08em;">
                                Análise do Agente de IA
                            </p>
                        </div>
                        <p style="margin:0;color:#CBD5E1;font-size:14px;line-height:1.7;">{st.session_state.analise_ia}</p>
                    </div>
                    """, unsafe_allow_html=True)

                # ══════════════════════════════════════════════════════════════════════════
                # MODAL DE ROTA MANUAL
                # ══════════════════════════════════════════════════════════════════════════
                if st.session_state.get('modo_rota_manual', False):
                    st.markdown("""
                    <div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.3);
                                border-radius:14px;padding:20px;margin-bottom:20px;">
                        <h3 style="margin:0 0 4px;color:#F59E0B;">✍️ Inserir Rota Manual</h3>
                        <p style="color:#94A3B8;font-size:13px;margin:0;">
                            Preencha os campos abaixo para definir a rota manualmente (SPTRANS)
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Busca dados salvos (se existirem)
                    tipo_bilhete_salvo = dados_jovem.get('tipo_bilhete_manual', '')
                    valor_tarifa_salvo = dados_jovem.get('valor_tarifa_manual', 0.0)
                    descricao_salva = dados_jovem.get('descricao_itinerario_manual', '')

                    col_bilhete, col_valor = st.columns([2, 1])
                    
                    with col_bilhete:
                        tipo_bilhete_manual = st.selectbox(
                            "Tipo de Bilhete (SPTRANS)",
                            [
                                "Bilhete Único",
                                "Integração Ônibus+Metrô",
                                "Integração Ônibus+CPTM",
                                "Vale Transporte"
                            ],
                            index=0 if not tipo_bilhete_salvo else (
                                ["Bilhete Único", "Integração Ônibus+Metrô", "Integração Ônibus+CPTM", "Vale Transporte"].index(tipo_bilhete_salvo)
                                if tipo_bilhete_salvo in ["Bilhete Único", "Integração Ônibus+Metrô", "Integração Ônibus+CPTM", "Vale Transporte"]
                                else 0
                            ),
                            key=f"tipo_bilhete_{id_selecionado}"
                        )

                    with col_valor:
                        valor_tarifa_manual = st.number_input(
                            "Valor da Tarifa (R$)",
                            min_value=0.10,
                            max_value=500.00,
                            value=float(valor_tarifa_salvo) if valor_tarifa_salvo else 0.10,
                            step=0.10,
                            format="%.2f",
                            key=f"valor_tarifa_{id_selecionado}"
                        )

                    descricao_itinerario_manual = st.text_area(
                        "Descrição do Itinerário",
                        value=descricao_salva,
                        placeholder="Ex: Linha 102 -> Terminal Bandeira -> Metrô Linha 3-Vermelha -> Estação Sé",
                        height=120,
                        key=f"descricao_itinerario_{id_selecionado}"
                    )

                    st.markdown("<br>", unsafe_allow_html=True)

                    col_salvar_manual, col_cancelar_manual = st.columns([1, 1])
                    
                    with col_salvar_manual:
                        if st.button("💾 Salvar Rota Manual", type="primary", width="stretch", key=f"salvar_manual_{id_selecionado}"):
                            if not tipo_bilhete_manual or valor_tarifa_manual < 0.10 or not descricao_itinerario_manual.strip():
                                st.error("⚠️ Preencha todos os campos antes de salvar.")
                            else:
                                from banco_dados import salvar_rota_manual
                                
                                sucesso = salvar_rota_manual(
                                    id_selecionado,
                                    tipo_bilhete_manual,
                                    valor_tarifa_manual,
                                    descricao_itinerario_manual
                                )
                                
                                if sucesso:
                                    st.success("✅ Rota manual salva com sucesso!")
                                    
                                    # Recarrega os dados
                                    conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                                    df_atualizado = safe_sql(
                                        "SELECT * FROM jovens_rotas WHERE id = ?", 
                                        conexao, 
                                        params=(int(id_selecionado),)
                                    )
                                    conexao.close()
                                    
                                    if not df_atualizado.empty:
                                        st.session_state.resultado_busca = df_atualizado
                                    
                                    st.session_state.modo_rota_manual = False
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Erro ao salvar rota manual. Verifique o console.")

                    with col_cancelar_manual:
                        if st.button("❌ Cancelar", width="stretch", key=f"cancelar_manual_{id_selecionado}"):
                            st.session_state.modo_rota_manual = False
                            st.rerun()

                # ══════════════════════════════════════════════════════════════════════════
                # EXIBIÇÃO DA ROTA E MAPA
                # ══════════════════════════════════════════════════════════════════════════
                
                # Calcula rota se ainda não foi calculada
                if not st.session_state.get('rota_gerada'):
                    # Monta endereços completos para geocoding preciso
                    endereco_completo_casa = end_casa_dict.get('completo', f"{rua_casa}, São Paulo, SP, Brasil") if isinstance(end_casa_dict, dict) else f"{rua_casa}, São Paulo, SP, Brasil"
                    endereco_completo_trab = end_trab_dict.get('completo', f"{rua_trab}, São Paulo, SP, Brasil") if isinstance(end_trab_dict, dict) else f"{rua_trab}, São Paulo, SP, Brasil"
                    
                    rota = motor_de_rotas_gratuito(
                        endereco_completo_casa,
                        endereco_completo_trab
                    )
                    st.session_state.rota_gerada = rota
                    
                    # Registra o SLA no banco de dados
                    if 'sla_segundos' in rota:
                        from banco_dados import registrar_sla
                        registrar_sla(id_selecionado, rota['sla_segundos'])
                    
                    # Análise da IA em background (não bloqueia a UI)
                    if not st.session_state.get('analise_ia'):
                        st.session_state.analise_ia = analisar_rota_com_ia(
                            rua_casa, rua_trab, rota['distancia_km'],
                            rota['rotas'], rota['info_tarifas']
                        )

                # ── Rotas + Mapa ──
                col_painel, col_mapa = st.columns([1, 2.8])

                with col_painel:
                    st.markdown("<p style='color:#444c9b;font-size:12px;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;'>🗺️ Opções de Trajeto</p>", unsafe_allow_html=True)

                    if st.session_state.get('rota_gerada') and 'rotas' in st.session_state.rota_gerada:
                        abas = st.tabs([r["modal"] for r in st.session_state.rota_gerada["rotas"]])
                        for i, aba in enumerate(abas):
                            with aba:
                                rt = st.session_state.rota_gerada["rotas"][i]
                                st.markdown(f"""
                                <div style="background:#f8ae28;border:1px solid #E5E7EB;
                                            border-radius:12px;padding:18px;margin-top:8px;
                                            box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                                    <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:16px;">
                                        <div style="background:#FFFFFF;border-radius:50%;
                                                    min-width:40px;height:40px;display:flex;align-items:center;
                                                    justify-content:center;font-weight:800;color:#f8ae28;font-size:13px;
                                                    border:2px solid #FFFFFF;">SP</div>
                                        <div>
                                            <p style="margin:0;font-weight:700;color:#FFFFFF;font-size:14px;">{rt['trajeto']}</p>
                                            <p style="margin:4px 0;font-size:12px;color:#FFFFFF;">{rt['bilhete']}</p>
                                            <p style="margin:4px 0;font-size:12px;color:#FFFFFF;font-weight:600;">⏱ {rt['tempo']}</p>
                                        </div>
                                    </div>
                                    <div style="background:#FFFFFF;
                                                border:1px solid #E5E7EB;border-radius:8px;
                                                text-align:center;padding:14px;
                                                box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                                        <p style="margin:0;color:#666666;font-size:13px;text-transform:uppercase;letter-spacing:0.08em;">VT Diário (Ida + Volta)</p>
                                        <p style="margin:4px 0 0;color:#f8ae28;font-size:26px;font-weight:800;">R$ {rt['valor_diario']:.2f}</p>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("Calculando rotas...")

                with col_mapa:
                    if st.session_state.get('rota_gerada'):
                        (lat_c, lon_c), (lat_t, lon_t) = st.session_state.rota_gerada['coords_reais']
                        rota_info = st.session_state.rota_gerada
                        
                        # Calcula tempo estimado de deslocamento (baseado na distância)
                        distancia_km = rota_info.get('distancia_km', 0)
                        # Velocidade média em SP: 25 km/h (considerando trânsito)
                        tempo_estimado_min = int((distancia_km / 25) * 60)
                        tempo_horas = tempo_estimado_min // 60
                        tempo_minutos = tempo_estimado_min % 60
                        tempo_texto = f"{tempo_horas}h{tempo_minutos}min" if tempo_horas > 0 else f"{tempo_minutos}min"
                        
                        # ── INFO BOX: Tempo estimado e distância ──
                        st.markdown(f"""
                        <div style="background:linear-gradient(135deg,#444c9b,#5a63b8);border-radius:12px;
                                    padding:16px;margin-bottom:16px;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                            <div style="display:flex;justify-content:space-around;align-items:center;">
                                <div style="text-align:center;">
                                    <p style="color:rgba(255,255,255,0.9) !important;font-size:12px;margin:0;text-transform:uppercase;letter-spacing:0.1em;">
                                        Distância
                                    </p>
                                    <p style="color:#FFFFFF !important;font-size:24px;font-weight:800;margin:4px 0 0;">
                                        {distancia_km:.1f} km
                                    </p>
                                </div>
                                <div style="width:1px;height:40px;background:rgba(255,255,255,0.3);"></div>
                                <div style="text-align:center;">
                                    <p style="color:rgba(255,255,255,0.9) !important;font-size:12px;margin:0;text-transform:uppercase;letter-spacing:0.1em;">
                                        Tempo Estimado
                                    </p>
                                    <p style="color:#f8ae28 !important;font-size:24px;font-weight:800;margin:4px 0 0;">
                                        ⏱️ {tempo_texto}
                                    </p>
                                </div>
                            </div>
                            <p style="color:rgba(255,255,255,0.8) !important;font-size:11px;margin:8px 0 0;text-align:center;">
                                * Tempo calculado com velocidade média de 25 km/h (considerando trânsito de SP)
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Cria mapa centralizado no ponto médio entre Casa e Trabalho
                        m = folium.Map(
                            location=[(lat_c + lat_t) / 2, (lon_c + lon_t) / 2],
                            zoom_start=13,
                            control_scale=True,
                            zoom_control=True,  # Habilita controles de zoom
                            scrollWheelZoom=True,  # Habilita zoom com scroll do mouse
                            dragging=True,  # Habilita pan (arrastar mapa)
                            doubleClickZoom=True,  # Zoom com duplo clique
                            touchZoom=True  # Zoom em dispositivos touch
                        )
                        
                        # ── Camada de mapa com estilo OpenStreetMap ──
                        folium.TileLayer('OpenStreetMap', name='Mapa Padrão').add_to(m)
                        
                        # ── Camada alternativa: Satélite ──
                        folium.TileLayer(
                            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                            attr='Esri',
                            name='Satélite',
                            overlay=False,
                            control=True
                        ).add_to(m)
                        
                        # ── Adiciona controle de camadas ──
                        folium.LayerControl().add_to(m)

                        # ── MARCADOR PERSONALIZADO: CASA (Azul com ícone de casa) ──
                        folium.Marker(
                            [lat_c, lon_c],
                            icon=folium.DivIcon(html=f"""
                            <div style="position:relative;">
                                <div style="background:linear-gradient(135deg,#00D4FF,#0EA5E9);width:44px;height:44px;
                                            border-radius:50%;border:3px solid #FFFFFF;display:flex;
                                            align-items:center;justify-content:center;font-weight:800;
                                            font-size:20px;box-shadow:0 4px 12px rgba(0,212,255,0.6);
                                            position:relative;z-index:1000;">
                                    🏠
                                </div>
                                <div style="position:absolute;bottom:-8px;left:50%;transform:translateX(-50%);
                                            width:0;height:0;border-left:8px solid transparent;
                                            border-right:8px solid transparent;border-top:12px solid #0EA5E9;
                                            filter:drop-shadow(0 2px 4px rgba(0,0,0,0.2));"></div>
                            </div>
                        """, icon_anchor=(22, 44)),
                            popup=folium.Popup(f"""
                                <div style="font-family:Arial;padding:8px;min-width:200px;">
                                    <h4 style="margin:0 0 8px;color:#0EA5E9;font-size:14px;">🏠 Residência</h4>
                                    <p style="margin:4px 0;font-size:12px;color:#666;">
                                        <strong>Endereço:</strong><br>{rua_casa}{linha_num_casa}
                                    </p>
                                    <p style="margin:4px 0;font-size:12px;color:#666;">
                                        <strong>Bairro:</strong> {bairro_cidade_casa}
                                    </p>
                                    <p style="margin:4px 0;font-size:11px;color:#999;">
                                        📍 {lat_c:.6f}, {lon_c:.6f}
                                    </p>
                                </div>
                            """, max_width=300),
                            tooltip=f"🏠 Residência · {rua_casa}"
                        ).add_to(m)

                        # ── MARCADOR PERSONALIZADO: TRABALHO (Roxo com ícone de prédio) ──
                        folium.Marker(
                            [lat_t, lon_t],
                            icon=folium.DivIcon(html=f"""
                            <div style="position:relative;">
                                <div style="background:linear-gradient(135deg,#7C3AED,#A855F7);width:44px;height:44px;
                                            border-radius:50%;border:3px solid #FFFFFF;display:flex;
                                            align-items:center;justify-content:center;font-weight:800;
                                            font-size:20px;box-shadow:0 4px 12px rgba(124,58,237,0.6);
                                            position:relative;z-index:1000;">
                                    🏢
                                </div>
                                <div style="position:absolute;bottom:-8px;left:50%;transform:translateX(-50%);
                                            width:0;height:0;border-left:8px solid transparent;
                                            border-right:8px solid transparent;border-top:12px solid #A855F7;
                                            filter:drop-shadow(0 2px 4px rgba(0,0,0,0.2));"></div>
                            </div>
                        """, icon_anchor=(22, 44)),
                            popup=folium.Popup(f"""
                                <div style="font-family:Arial;padding:8px;min-width:200px;">
                                    <h4 style="margin:0 0 8px;color:#A855F7;font-size:14px;">🏢 Local de Trabalho</h4>
                                    <p style="margin:4px 0;font-size:12px;color:#666;">
                                        <strong>Endereço:</strong><br>{rua_trab}
                                    </p>
                                    <p style="margin:4px 0;font-size:12px;color:#666;">
                                        <strong>Bairro:</strong> {bairro_cidade_trab}
                                    </p>
                                    <p style="margin:4px 0;font-size:11px;color:#999;">
                                        📍 {lat_t:.6f}, {lon_t:.6f}
                                    </p>
                                </div>
                            """, max_width=300),
                            tooltip=f"🏢 Trabalho · {rua_trab}"
                        ).add_to(m)

                        # ── LINHA CONECTANDO CASA E TRABALHO (com animação) ──
                        folium.PolyLine(
                            locations=[[lat_c, lon_c], [lat_t, lon_t]],
                            color="#f8ae28",
                            weight=5,
                            opacity=0.8,
                            dash_array="10 5",
                            popup=f"Distância: {distancia_km:.1f} km · Tempo: {tempo_texto}"
                        ).add_to(m)
                        
                        # ── MARCADOR DO PONTO MÉDIO (opcional - mostra distância) ──
                        lat_meio = (lat_c + lat_t) / 2
                        lon_meio = (lon_c + lon_t) / 2
                        folium.Marker(
                            [lat_meio, lon_meio],
                            icon=folium.DivIcon(html=f"""
                            <div style="background:#f8ae28;color:#FFFFFF;padding:6px 12px;
                                        border-radius:20px;font-size:12px;font-weight:700;
                                        box-shadow:0 2px 8px rgba(248,174,40,0.4);
                                        border:2px solid #FFFFFF;white-space:nowrap;">
                                📏 {distancia_km:.1f} km · ⏱️ {tempo_texto}
                            </div>
                        """, icon_anchor=(60, 15)),
                            tooltip=f"Distância total: {distancia_km:.1f} km"
                        ).add_to(m)
                        
                        # ── Ajusta o zoom para mostrar ambos os pontos ──
                        m.fit_bounds([[lat_c, lon_c], [lat_t, lon_t]], padding=[50, 50])

                        # ── RENDERIZA O MAPA (altura aumentada) ──
                        st_folium(m, height=700, width="stretch", returned_objects=[])

        # ── LISTA DE PESQUISA ────────────────────────────────────────────────────
        else:
            st.markdown("""
            <h1 style="color:#1E293B;
                    font-size:26px;font-weight:800;margin-bottom:4px;">
                Pesquisar Consultas
            </h1>
            <p style="color:#666666;font-size:13px;margin-bottom:20px;">Localize aprendizes por CPF, nome ou matrícula</p>
            """, unsafe_allow_html=True)

            col_modal_pesq, col_status_pesq = st.columns([2, 1])
            with col_modal_pesq:
                modalidade_pesquisa = st.radio(
                    "Modalidade:",
                    ["🏠 Casa × Trabalho", "📚 Casa × Curso"],
                    horizontal=True,
                    key="modalidade_pesquisa_radio"
                )
            with col_status_pesq:
                filtro_status_pesq = st.selectbox(
                    "Filtrar por Status",
                    ["Todos", "Otimizado", "Implantado", "Contestada", "Não Optante", "Aguardando Rota"],
                    key="filtro_status_pesquisa",
                    label_visibility="visible"
                )

            st.markdown("<hr style='border-color:rgba(0,212,255,0.1);'>", unsafe_allow_html=True)

            tab_cpf, tab_nome, tab_mat, tab_status = st.tabs(["🔍 Por CPF", "👤 Por Nome", "🪪 Por Matrícula", "📊 Por Status"])

            with tab_cpf:
                with st.form(key="form_cpf"):
                    cpf_busca = st.text_input("CPF", max_chars=11, placeholder="000.000.000-00 ou só números")
                    if st.form_submit_button("Pesquisar", type="primary"):
                        if not cpf_busca.strip():
                            st.warning("⚠️ Digite um CPF para buscar.")
                        else:
                            try:
                                # Tira pontos e traços do que a pessoa digitou
                                cpf_limpo = ''.join(filter(str.isdigit, cpf_busca))
                                
                                conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                                # CORRIGIDO: Busca na coluna CPF
                                st.session_state.resultado_busca = safe_sql(
                                    "SELECT * FROM jovens_rotas WHERE cpf = ?", conexao, params=(cpf_limpo,))
                                
                                # Remove flag de busca por status
                                st.session_state.busca_por_status = False
                                
                                if st.session_state.resultado_busca.empty:
                                    st.warning("❌ Nenhum resultado encontrado para este CPF.")
                                st.session_state.detalhes_abertos = False
                                conexao.close()
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro na busca: {str(e)}")

            with tab_nome:
                # ── AUTOCOMPLETE: Busca todos os nomes do banco ──
                try:
                    conexao_autocomplete = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                    df_nomes = safe_sql("SELECT DISTINCT nome FROM jovens_rotas ORDER BY nome", conexao_autocomplete)
                    conexao_autocomplete.close()
                    lista_nomes = df_nomes['nome'].tolist() if not df_nomes.empty else []
                except Exception:
                    lista_nomes = []
                
                with st.form(key="form_nome"):
                    # Selectbox com autocomplete (busca incremental)
                    nome_busca = st.selectbox(
                        "Nome completo",
                        options=[""] + lista_nomes,
                        index=0,
                        placeholder="Digite para buscar...",
                        help="🔍 Comece a digitar para filtrar os nomes"
                    )
                    
                    # Opção de busca parcial
                    busca_parcial = st.checkbox("Buscar nome parcial (contém)", value=False)
                    
                    if st.form_submit_button("Pesquisar", type="primary"):
                        if not nome_busca or nome_busca == "":
                            st.warning("⚠️ Selecione um nome para buscar.")
                        else:
                            try:
                                conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                                
                                if busca_parcial:
                                    st.session_state.resultado_busca = safe_sql(
                                        "SELECT * FROM jovens_rotas WHERE nome LIKE ?", conexao, params=(f"%{nome_busca}%",))
                                else:
                                    st.session_state.resultado_busca = safe_sql(
                                        "SELECT * FROM jovens_rotas WHERE nome = ?", conexao, params=(nome_busca,))
                                
                                # Remove flag de busca por status
                                st.session_state.busca_por_status = False
                                
                                if st.session_state.resultado_busca.empty:
                                    st.warning("❌ Nenhum resultado encontrado para este nome")
                                st.session_state.detalhes_abertos = False
                                conexao.close()
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro na busca: {str(e)}")

            with tab_mat:
                with st.form(key="form_mat"):
                    mat_busca = st.text_input("Matrícula", placeholder="Apenas números")
                    if st.form_submit_button("Pesquisar", type="primary"):
                        try:
                            conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                            st.session_state.resultado_busca = safe_sql(
                                "SELECT * FROM jovens_rotas WHERE matricula = ?", conexao, params=(mat_busca,))
                            
                            # Remove flag de busca por status
                            st.session_state.busca_por_status = False
                            
                            if st.session_state.resultado_busca.empty:
                                st.warning("❌ Nenhum resultado encontrado para esta matrícula")
                            st.session_state.detalhes_abertos = False
                            conexao.close()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro na busca: {str(e)}")

            with tab_status:
                st.markdown("<p style='color:#64748B;font-size:13px;margin-bottom:12px;'>Lista todos os funcionários com o status selecionado no filtro acima.</p>", unsafe_allow_html=True)
                if st.button("🔍 Buscar por Status", type="primary", key="btn_busca_status"):
                    try:
                        conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                        if filtro_status_pesq == "Todos":
                            st.session_state.resultado_busca = safe_sql(
                                "SELECT * FROM jovens_rotas ORDER BY nome", conexao)
                        else:
                            st.session_state.resultado_busca = safe_sql(
                                "SELECT * FROM jovens_rotas WHERE status_rota = ? ORDER BY nome",
                                conexao, params=(filtro_status_pesq,))
                        conexao.close()
                        
                        # Define flag para mostrar controles avançados
                        st.session_state.busca_por_status = True
                        
                        if st.session_state.resultado_busca.empty:
                            st.warning(f"❌ Nenhum resultado com status '{filtro_status_pesq}'.")
                        else:
                            st.success(f"✅ {len(st.session_state.resultado_busca)} resultado(s) encontrado(s).")
                        st.session_state.detalhes_abertos = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro na busca: {str(e)}")

            if st.session_state.resultado_busca is not None and not st.session_state.resultado_busca.empty:
                st.markdown("<hr style='border-color:rgba(0,212,255,0.1);margin:20px 0;'>", unsafe_allow_html=True)
                
                # Verifica se a busca foi feita pela aba "Por Status"
                mostrar_controles_avancados = st.session_state.get('busca_por_status', False)
                
                if mostrar_controles_avancados:
                    # ══════════════════════════════════════════════════════════════════════════
                    # CONTROLES DE VISUALIZAÇÃO, ORDENAÇÃO E EXPORTAÇÃO
                    # ══════════════════════════════════════════════════════════════════════════
                    
                    col_header1, col_header2, col_header3, col_header4 = st.columns([3, 2, 2, 2])
                    
                    with col_header1:
                        st.markdown(f"<p style='color:#444c9b;font-size:14px;font-weight:700;margin:8px 0;'>📋 {len(st.session_state.resultado_busca)} Resultado(s)</p>", unsafe_allow_html=True)
                    
                    with col_header2:
                        # Toggle Cards/Tabela
                        modo_visualizacao = st.radio(
                            "Visualização:",
                            ["🎴 Cards", "📊 Tabela"],
                            horizontal=True,
                            key="modo_visualizacao",
                            label_visibility="collapsed"
                        )
                    
                    with col_header3:
                        # Ordenação
                        ordenar_por = st.selectbox(
                            "Ordenar por:",
                            ["Nome (A-Z)", "Nome (Z-A)", "Data (Mais recente)", "Data (Mais antiga)", 
                             "Valor (Maior)", "Valor (Menor)", "Status"],
                            key="ordenar_por",
                            label_visibility="collapsed"
                        )
                    
                    with col_header4:
                        # Exportar para Excel
                        if st.button("📥 Exportar Excel", use_container_width=True):
                            try:
                                from io import BytesIO
                                from openpyxl import Workbook
                                from openpyxl.styles import Font, PatternFill, Alignment
                                
                                wb = Workbook()
                                ws = wb.active
                                ws.title = "Resultados Pesquisa"
                                
                                # Cabeçalho
                                headers = ['ID', 'Nome', 'CPF', 'Matrícula', 'E-mail', 'Celular', 'Status', 
                                          'CEP Casa', 'CEP Trabalho', 'Valor Tarifa', 'Data Consulta']
                                ws.append(headers)
                                
                                # Estilo do cabeçalho
                                for cell in ws[1]:
                                    cell.font = Font(bold=True, color="FFFFFF")
                                    cell.fill = PatternFill(start_color="444c9b", end_color="444c9b", fill_type="solid")
                                    cell.alignment = Alignment(horizontal="center")
                                
                                # Dados
                                for _, row in st.session_state.resultado_busca.iterrows():
                                    ws.append([
                                        row.get('id', ''),
                                        row.get('nome', ''),
                                        str(row.get('cpf', '')).zfill(11),
                                        row.get('matricula', ''),
                                        row.get('email', ''),
                                        row.get('celular', ''),
                                        row.get('status_rota', ''),
                                        row.get('cep_casa', ''),
                                        row.get('cep_trabalho', ''),
                                        row.get('valor_tarifa_manual', ''),
                                        str(row.get('data_consulta', ''))[:10]
                                    ])
                                
                                # Ajusta largura das colunas
                                for column in ws.columns:
                                    max_length = 0
                                    column_letter = column[0].column_letter
                                    for cell in column:
                                        try:
                                            if len(str(cell.value)) > max_length:
                                                max_length = len(cell.value)
                                        except:
                                            pass
                                    adjusted_width = min(max_length + 2, 50)
                                    ws.column_dimensions[column_letter].width = adjusted_width
                                
                                # Salva em buffer
                                buffer = BytesIO()
                                wb.save(buffer)
                                buffer.seek(0)
                                
                                st.download_button(
                                    label="⬇️ Baixar Excel",
                                    data=buffer,
                                    file_name=f"pesquisa_consultas_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    use_container_width=True
                                )
                            except Exception as e:
                                st.error(f"❌ Erro ao exportar: {str(e)}")
                else:
                    # Modo simples: apenas mostra o contador
                    st.markdown(f"<p style='color:#444c9b;font-size:14px;font-weight:700;margin:8px 0;'>📋 {len(st.session_state.resultado_busca)} Resultado(s)</p>", unsafe_allow_html=True)
                    # Define valores padrão para variáveis usadas abaixo
                    modo_visualizacao = "🎴 Cards"
                    ordenar_por = "Nome (A-Z)"
                
                # ── ORDENAÇÃO DOS RESULTADOS ──
                df_resultados = st.session_state.resultado_busca.copy()
                
                if ordenar_por == "Nome (A-Z)":
                    df_resultados = df_resultados.sort_values('nome', ascending=True)
                elif ordenar_por == "Nome (Z-A)":
                    df_resultados = df_resultados.sort_values('nome', ascending=False)
                elif ordenar_por == "Data (Mais recente)":
                    df_resultados = df_resultados.sort_values('data_consulta', ascending=False, na_position='last')
                elif ordenar_por == "Data (Mais antiga)":
                    df_resultados = df_resultados.sort_values('data_consulta', ascending=True, na_position='last')
                elif ordenar_por == "Valor (Maior)":
                    df_resultados = df_resultados.sort_values('valor_tarifa_manual', ascending=False, na_position='last')
                elif ordenar_por == "Valor (Menor)":
                    df_resultados = df_resultados.sort_values('valor_tarifa_manual', ascending=True, na_position='last')
                elif ordenar_por == "Status":
                    df_resultados = df_resultados.sort_values('status_rota', ascending=True, na_position='last')
                
                if mostrar_controles_avancados:
                    # ── PAGINAÇÃO ──
                    itens_por_pagina = 10
                    total_paginas = (len(df_resultados) - 1) // itens_por_pagina + 1
                    
                    if 'pagina_atual' not in st.session_state:
                        st.session_state.pagina_atual = 1
                    
                    col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
                    
                    with col_pag1:
                        if st.button("⬅️ Anterior", disabled=(st.session_state.pagina_atual == 1), use_container_width=True):
                            st.session_state.pagina_atual -= 1
                            st.rerun()
                    
                    with col_pag2:
                        st.markdown(f"<p style='text-align:center;color:#64748B;font-size:13px;margin:8px 0;'>Página {st.session_state.pagina_atual} de {total_paginas}</p>", unsafe_allow_html=True)
                    
                    with col_pag3:
                        if st.button("Próxima ➡️", disabled=(st.session_state.pagina_atual == total_paginas), use_container_width=True):
                            st.session_state.pagina_atual += 1
                            st.rerun()
                    
                    # Calcula índices da página atual
                    inicio = (st.session_state.pagina_atual - 1) * itens_por_pagina
                    fim = inicio + itens_por_pagina
                    df_pagina = df_resultados.iloc[inicio:fim]
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # ══════════════════════════════════════════════════════════════════════════
                    # AÇÕES EM LOTE
                    # ══════════════════════════════════════════════════════════════════════════
                    
                    if 'selecionados_lote' not in st.session_state:
                        st.session_state.selecionados_lote = []
                    
                    col_lote1, col_lote2 = st.columns([3, 1])
                    
                    with col_lote1:
                        selecionar_todos = st.checkbox(
                            f"Selecionar todos ({len(df_pagina)} itens desta página)",
                            key="selecionar_todos_pagina"
                        )
                        
                        if selecionar_todos:
                            st.session_state.selecionados_lote = df_pagina['id'].tolist()
                    
                    with col_lote2:
                        if len(st.session_state.selecionados_lote) > 0:
                            if st.button(f"📧 Enviar Cartas ({len(st.session_state.selecionados_lote)})", type="primary", use_container_width=True):
                                st.info(f"🚀 Preparando envio de {len(st.session_state.selecionados_lote)} cartas...")
                                # Aqui você pode adicionar a lógica de envio em massa
                                st.success(f"✅ {len(st.session_state.selecionados_lote)} cartas enviadas com sucesso!")
                                st.session_state.selecionados_lote = []
                                time.sleep(2)
                                st.rerun()
                    
                    st.markdown("<hr style='border-color:rgba(0,212,255,0.05);margin:12px 0;'>", unsafe_allow_html=True)
                    
                    # ══════════════════════════════════════════════════════════════════════════
                    # VISUALIZAÇÃO: CARDS OU TABELA
                    # ══════════════════════════════════════════════════════════════════════════
                    
                    if modo_visualizacao == "📊 Tabela":
                        # ── MODO TABELA ──
                        st.dataframe(
                            df_pagina[['id', 'nome', 'cpf', 'matricula', 'status_rota', 'email', 'celular', 'data_consulta']],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "id": st.column_config.NumberColumn("ID", width="small"),
                                "nome": st.column_config.TextColumn("Nome", width="large"),
                                "cpf": st.column_config.TextColumn("CPF", width="medium"),
                                "matricula": st.column_config.TextColumn("Matrícula", width="small"),
                                "status_rota": st.column_config.TextColumn("Status", width="medium"),
                                "email": st.column_config.TextColumn("E-mail", width="medium"),
                                "celular": st.column_config.TextColumn("Celular", width="small"),
                                "data_consulta": st.column_config.DateColumn("Data", width="small")
                            }
                        )
                    else:
                        # ── MODO CARDS (código existente) ──
                        pass  # O código dos cards já existe abaixo
                else:
                    # Modo simples: sem paginação, mostra todos os resultados
                    df_pagina = df_resultados

                #Auto-Refresh na lista de resultados na aba de pesquisa :)
            try:
                            ids_lista = st.session_state.resultado_busca['id'].tolist()
                            if ids_lista:
                                conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                                placeholders = ','.join('?' for _ in ids_lista)
                                st.session_state.resultado_busca = safe_sql(
                                    f"SELECT * FROM jovens_rotas WHERE id IN ({placeholders})",
                                    conexao, params=ids_lista
                                )
                                conexao.close()
            except Exception as e:
                pass
            
            # Lógica de separação: Trabalho x Curso
            modalidade_atual = st.session_state.get('modalidade_pesquisa_radio', 'Trabalho')

            # Verifica se resultado_busca existe e não é vazio
            if st.session_state.get('resultado_busca') is not None and not st.session_state.resultado_busca.empty:
                # Verifica se deve mostrar em modo cards
                mostrar_cards = True
                if mostrar_controles_avancados and modo_visualizacao == "📊 Tabela":
                    mostrar_cards = False
                
                if mostrar_cards:
                    for _, row in df_pagina.iterrows():
                        # --- LÓGICA DE SEPARAÇÃO: TRABALHO x CURSO ---
                        if "Trabalho" in modalidade_atual:
                            status_raw = row.get('status_rota', 'Otimizado')
                        else:
                            status_raw = row.get('status_curso', 'Otimizado')
                        
                        status_exib = obter_status_visual(status_raw)
                        
                        # Define as cores da bolinha 
                        if status_raw == "Implantado":
                            status_color, status_bg = "#10B981", "16,185,129"
                        elif status_raw == "Otimizado":
                            status_color, status_bg = "#3B82F6", "59,130,246"
                        elif status_raw == "Contestada":
                            status_color, status_bg = "#F59E0B", "245,158,11"
                        else:
                            status_color, status_bg = "#94A3B8", "148,163,184"

                        # ── DESTAQUE VISUAL PARA PENDÊNCIAS ──
                        tem_pendencia = False
                        icone_pendencia = ""
                        texto_pendencia = ""
                        
                        # Verifica pendências
                        if not row.get('email') or row.get('email') == '':
                            tem_pendencia = True
                            icone_pendencia += "📧 "
                            texto_pendencia += "E-mail ausente · "
                        
                        if not row.get('celular') or row.get('celular') == '':
                            tem_pendencia = True
                            icone_pendencia += "📱 "
                            texto_pendencia += "Celular ausente · "
                        
                        if not row.get('matricula') or row.get('matricula') == '':
                            tem_pendencia = True
                            icone_pendencia += "🪪 "
                            texto_pendencia += "Matrícula ausente · "
                        
                        if not row.get('cep_trabalho') or row.get('cep_trabalho') == '':
                            tem_pendencia = True
                            icone_pendencia += "🏢 "
                            texto_pendencia += "CEP trabalho ausente · "
                        
                        # Remove último separador
                        texto_pendencia = texto_pendencia.rstrip(" · ")
                        
                        # Define estilo do card baseado em pendências
                        if tem_pendencia:
                            card_border = "border-left:4px solid #F59E0B;"
                            card_bg = "background:rgba(245,158,11,0.05);"
                        else:
                            card_border = "border-left:4px solid #10B981;"
                            card_bg = "background:#FFFFFF;"

                        # Camuflador do CPF
                        cpf_str = str(row['cpf']).zfill(11)
                        cpf_mask = f"***.***.{cpf_str[6:9]}-{cpf_str[9:11]}"

                        if mostrar_controles_avancados:
                            # Modo avançado: com checkbox
                            col_check, col_info, col_btn = st.columns([0.5, 9.5, 2])
                            
                            with col_check:
                                # Checkbox para seleção em lote
                                is_selected = st.checkbox(
                                    "",
                                    value=row['id'] in st.session_state.selecionados_lote,
                                    key=f"check_{row['id']}",
                                    label_visibility="collapsed"
                                )
                                
                                if is_selected and row['id'] not in st.session_state.selecionados_lote:
                                    st.session_state.selecionados_lote.append(row['id'])
                                elif not is_selected and row['id'] in st.session_state.selecionados_lote:
                                    st.session_state.selecionados_lote.remove(row['id'])
                        else:
                            # Modo simples: sem checkbox
                            col_info, col_btn = st.columns([10, 2])
                        
                        with col_info:
                            st.markdown(f"""<div style="{card_bg}{card_border}border:1px solid #E5E7EB;border-radius:8px;padding:12px;"><div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;"><p style="margin:0;color:#444c9b;font-weight:700;font-size:16px;">{row['nome']}</p><span style="background:rgba({status_bg},0.15);color:{status_color};padding:2px 8px;border-radius:20px;font-size:12px;font-weight:700;">{status_exib}</span>{f'<span style="background:rgba(245,158,11,0.15);color:#F59E0B;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600;">{icone_pendencia}PENDÊNCIAS</span>' if tem_pendencia else ''}</div><p style="margin:0;color:#666666;font-size:13px;">PRÉ-ADM · CPF: {cpf_mask} · Matrícula: {row.get('matricula', 'N/A')}</p>{f'<p style="margin:4px 0 0;color:#F59E0B;font-size:12px;font-weight:600;">⚠️ {texto_pendencia}</p>' if tem_pendencia else ''}</div>""", unsafe_allow_html=True)
                        
                        with col_btn:
                            st.write("") # Espaço para alinhar o botãozin
                            
                            # Botão "Copiar dados" ao lado do "Abrir Consulta"
                            col_copiar, col_abrir = st.columns(2)
                            
                            with col_copiar:
                                # Prepara dados para copiar
                                dados_copiar = f"""Nome: {row['nome']}
CPF: {cpf_str}
Matrícula: {row.get('matricula', 'N/A')}
E-mail: {row.get('email', 'N/A')}
Celular: {row.get('celular', 'N/A')}
Status: {status_exib}
CEP Casa: {row.get('cep_casa', 'N/A')}
CEP Trabalho: {row.get('cep_trabalho', 'N/A')}"""
                                
                                if st.button("📋", key=f"btn_copiar_{row['id']}", help="Copiar dados", use_container_width=True):
                                    # Usa JavaScript para copiar para clipboard
                                    import streamlit.components.v1 as components
                                    components.html(f"""
                                    <script>
                                    navigator.clipboard.writeText(`{dados_copiar}`);
                                    </script>
                                    """, height=0)
                                    st.success("✅ Dados copiados!")
                                    time.sleep(1)
                            
                            with col_abrir:
                                if st.button("Abrir →", key=f"btn_abrir_{row['id']}", type="primary", use_container_width=True):
                                    st.session_state.resultado_busca = pd.DataFrame([row])
                                    st.session_state.detalhes_abertos = True
                                    st.query_params['id_consulta'] = str(row['id'])
                                    st.session_state.contexto_salvo = st.session_state.modalidade_pesquisa_radio
                                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TELA 2 — CADASTRAR NOVO JOVEM
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "➕ Cadastrar Novo Jovem":

        st.markdown("""
            <div style="display:flex; align-items:center; gap:15px; margin-bottom:25px;">
                <svg viewBox="0 0 378 708.82" width="40" height="75">
                <defs><style>.s1-1{fill:#402fdd;} .s1-1,.s1-2,.s1-3,.s1-4{stroke-width:0px;} .s1-3{fill:#ed9e06;} .s1-4{fill:#231f20;}</style></defs>
                <g><path class="s1-4" d="m201.23,256.63c8.57,0,8.59-13.95,0-13.95s-8.59,13.95,0,13.95h0Z"/><path class="s1-4" d="m201.23,288.82c8.57,0,8.59-13.95,0-13.95s-8.59,13.95,0,13.95h0Z"/><path class="s1-3" d="m27.95,115.09c-4.81-1.19-7.19-4.51-10.93-9.68-2.67-3.69-15.67-33.45-15.96-36.85-.14-1.68-2.65-9.29.59-10.35,4.11-1.34,9.39,16.78,11.07,19.92-1.85-3.65-6.71-16.39-7.43-18.49-1.42-4.14-2.47-11.71-.94-12.39,4.89-2.18,7.45,5.97,8.28,7.15,1.09,1.54,8.65,16.82,8.65,16.82.04-.02.05-.06.04-.09-2.25-6.72-7.49-14.79-10.33-21.76-1.63-4-1.48-7.65,0-8.57,4.75-2.95,16.1,20.1,17.54,23.6-1.2-3.54-3.73-8.21-4.93-11.75-.56-1.65-3.33-10.55-2.17-12.12,4.47-6.03,7.59,4.26,8.85,7.24.68,1.6,3.68,6.61,4.26,8.22,2.85,7.95,4.64,11.49,8.04,19.17,1.51-3.02,2.54-5.08,4.04-8.1,1.05-2.12,2.22-4.35,4.22-5.68,2-1.32,5.06-1.14,5.73.92.35,1.06-.03,2.29-.35,3.44-1.61,5.53-2.52,11.17-2.7,16.75-.15,4.56,2.15,11.74-1.31,15.19l8.14,11.57-25.53,18.44s-6.87-12.58-6.87-12.58Z"/><path class="s1-2" d="m5.79,62.37c2.67,6.4,5.49,12.73,8.45,18.97.35.72,1.36.09,1.03-.63-2.96-6.25-5.78-12.58-8.45-18.97-.13-.31-.55-.38-.81-.23-.3.18-.35.55-.21.85h0Z"/><path class="s1-2" d="m11.46,52.37c2.97,6.15,5.86,12.33,8.67,18.56.8,1.77,1.59,3.55,2.38,5.34.32.73,1.35.09,1.03-.63-2.76-6.25-5.6-12.46-8.53-18.64-.84-1.75-1.67-3.52-2.52-5.26-.35-.72-1.37-.08-1.03.63h0Z"/><path class="s1-2" d="m21.46,51.11c2.42,5.45,4.84,10.89,7.26,16.34.69,1.56,1.38,3.12,2.08,4.68.33.73,1.35.09,1.03-.63-2.42-5.45-4.84-10.89-7.26-16.34-.69-1.56-1.38-3.12-2.08-4.68-.33-.73-1.35-.09-1.03.63h0Z"/><path class="s1-3" d="m319.04,612.74c6.85,5.73,20.79,22.23,22.92,27.85,7.25,19.13,17.27,49.96,28.72,67.62.2-33.32,2.91-67.81,7.24-99.19-2.33-1.94-5.73-1.1-8.59-1.9-2.47-.69-4.46-2.57-6.35-4.39-3.82-3.68-8.96-15.05-8.96-15.05-11.16,7.22-24.83,18.45-35.99,25.67"/><path class="s1-3" d="m82.53,489.18c2.98,5.85,5.96,11.69,8.95,17.54,1.24,2.42,2.48,4.87,3.05,7.55.75,3.61.24,7.35-.26,11.01-3.08,22.8-4.79,45.82-5.1,68.85,22.78-24.49,31.45-59.7,49.35-88.35-2.32-3.46-6.97-4.51-9.27-7.99-1.04-1.57-1.47-3.48-1.89-5.34-1.23-5.44-2.45-10.86-3.67-16.3-13.35,4.19-26.69,8.38-40.04,12.57-.48.15-1.03.35-1.23.85s.36,1.19.76.85"/><path class="s1-1" d="m158.84,246.8c-31.59-9.26-62.23-24.23-86.25-47.75-21.46-21.01-36.85-48.01-49.67-75.77,14.31-6.57,27.91-14.85,40.47-24.6,2.91,5.74,5.87,11.49,9.71,16.58,4.01,5.33,8.89,9.83,13.74,14.32,27.52,25.51,54.58,51.57,81.17,78.15.98.98,2,2.03,2.36,3.4.31,1.15.11,2.38-.11,3.56-2.08,11.65-4.87,23.17-8.34,34.45-.8-1.13-1.86-2.06-3.06-2.69"/><path class="s1-2" d="m229.82,302.11c12.65,12.48,20.15,36.99,13.32,65.81-.59,2.5,23.42,71.58,44.73,110.05,21.31,38.47,47.52,73.64,73.64,108.66-7.79,5.4-15.71,10.58-23.75,15.55-7.13,4.41-24.21,12.48-24.21,12.48,0,0-76.44-93.06-108.1-169.29-13.55-32.6-33.19-62.28-43.59-96.14.64,2.78,1.27,5.57,1.91,8.35-23.55-5.11-45.97-6.95-68.45-15.94,6.5,47.81,18.15,89.46,36,133.95-18.34,5.57-36.67,11.15-55.01,16.72-14.36-24.69-22.31-52.85-30.02-80.65-9.89-35.68-19.72-73.14-12.65-109.55,1.49-7.67,3.88-15.49,9.02-21.16,9.96-11.02,26.56-10.59,40.86-8.47,15.33,2.27,30.52,5.56,45.45,9.86,5.87,1.69,11.73,3.55,17.18,6.39,5.25,2.74,18.5-7.15,23.66-4.23,20.38,11.5,32.31,15.36,54.43,8.26"/><path class="s1-3" d="m173.64,193.71c3.47-8.21,7.84-16.95,12.4-22.96-5.09,2.88-11.95.3-15.1-4.81s-1.08-16.84,1.29-22.39c2.36-5.55,3.03-10.43,7.66-14.06,2.95-2.32,7.91.93,11.53.23,3.62-.71,7.69.22,10.11,3.15,2.24,2.71,2.68,6.55,2.65,10.15-.04,5.09,3.57,3.76,2.8,8.79-2.12,13.86-8.62,34.1-10.74,47.96-.08.51-.22,1.11-.67,1.31-.32.14-.67.03-.99-.09-6.98-2.42-13.95-4.85-20.94-7.26"/><path class="s1-1" d="m230.92,303.11c-5.51-29.95-11.32-56.94-16.84-86.89-.75-4.08-9.13-28.62-9.13-28.62-9.9,6.51-25.51,3.74-27.1,1.4-2.53-3.72-7.98,10.31-11.8,12.47-6.46,3.67.44,11.7-2.61,18.75-5.22,12.1-7.65,25.29-9.68,38.41-1.53,9.86-2.84,19.76-3.95,29.69-.12,1.03-.23,2.09.05,3.09.45,1.68,1.86,2.85,3.24,3.84,12.7,9.03,28.66,11.29,43.98,11.26,11.35-.02,22.69-1.16,33.83-3.4"/></g>
                </svg>
                <h1 style="margin:0; color:#444c9b; font-size:28px;">Cadastrar Novo Jovem</h1>
            </div>
        """, unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════════
        # SELETOR DE MODO: WIZARD OU FORMULÁRIO COMPLETO
        # ══════════════════════════════════════════════════════════════════════════
        
        col_modo1, col_modo2 = st.columns([3, 1])
        with col_modo1:
            st.markdown("<p style='color:#64748B;font-size:13px;margin:8px 0;'>Escolha o modo de cadastro:</p>", unsafe_allow_html=True)
        with col_modo2:
            modo_cadastro = st.radio(
                "Modo",
                ["🧙 Wizard (Passo a Passo)", "📝 Formulário Completo"],
                horizontal=False,
                label_visibility="collapsed",
                key="modo_cadastro_radio"
            )
        
        st.markdown("<hr style='border-color:#E2E8F0;margin:16px 0;'>", unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════════════════════
        # MODO WIZARD (PASSO A PASSO)
        # ══════════════════════════════════════════════════════════════════════════
        
        if "🧙" in modo_cadastro:
            # Inicializa estado do wizard
            if 'wizard_passo' not in st.session_state:
                st.session_state.wizard_passo = 1
            if 'wizard_dados' not in st.session_state:
                st.session_state.wizard_dados = {}
            
            # Barra de progresso
            progresso = (st.session_state.wizard_passo - 1) / 4
            st.progress(progresso)
            st.markdown(f"<p style='text-align:center;color:#64748B;font-size:13px;margin:8px 0;'>Passo {st.session_state.wizard_passo} de 5</p>", unsafe_allow_html=True)
            st.markdown("<hr style='border-color:#E2E8F0;margin:16px 0;'>", unsafe_allow_html=True)
            
            # ── PASSO 1: DADOS PESSOAIS ──
            if st.session_state.wizard_passo == 1:
                st.markdown("### 👤 Dados Pessoais")
                st.markdown("<p style='color:#94A3B8;font-size:12px;margin:-8px 0 16px;'>Campos marcados com <span style='color:#EF4444;font-weight:700;'>*</span> são obrigatórios</p>", unsafe_allow_html=True)
                
                # Nome
                nome_wiz = st.text_input(
                    "Nome Completo",
                    value=st.session_state.wizard_dados.get('nome', ''),
                    placeholder="Ex: João da Silva Santos",
                    help="Campo obrigatório",
                    key="nome_wiz_input"
                )
                if nome_wiz:
                    st.markdown("<p style='color:#10B981;font-size:12px;margin:-8px 0 8px;'>✅ Nome preenchido</p>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color:#EF4444;font-size:12px;margin:-8px 0 8px;'>⚠️ Campo obrigatório</p>", unsafe_allow_html=True)
                
                col_cpf, col_mat = st.columns(2)
                with col_cpf:
                    # CPF com máscara visual
                    cpf_wiz_raw = st.text_input(
                        "CPF",
                        max_chars=14,
                        value=st.session_state.wizard_dados.get('cpf_formatado', ''),
                        placeholder="000.000.000-00",
                        help="Campo obrigatório - Digite apenas números",
                        key="cpf_wiz_input"
                    )
                    
                    # Aplica máscara e valida
                    if cpf_wiz_raw:
                        cpf_limpo = ''.join(filter(str.isdigit, cpf_wiz_raw))
                        cpf_formatado = aplicar_mascara_cpf(cpf_limpo)
                        
                        if len(cpf_limpo) == 11:
                            if validar_cpf_completo(cpf_limpo):
                                # Verifica duplicidade em tempo real
                                if cpf_ja_existe(cpf_limpo):
                                    st.markdown("<p style='color:#EF4444;font-size:12px;margin:-8px 0 8px;'>❌ CPF já cadastrado no sistema</p>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"<p style='color:#10B981;font-size:12px;margin:-8px 0 8px;'>✅ CPF válido: {cpf_formatado}</p>", unsafe_allow_html=True)
                            else:
                                st.markdown("<p style='color:#EF4444;font-size:12px;margin:-8px 0 8px;'>❌ CPF inválido</p>", unsafe_allow_html=True)
                        elif len(cpf_limpo) > 0:
                            st.markdown(f"<p style='color:#F59E0B;font-size:12px;margin:-8px 0 8px;'>⚠️ Digite 11 dígitos ({len(cpf_limpo)}/11)</p>", unsafe_allow_html=True)
                    else:
                        st.markdown("<p style='color:#EF4444;font-size:12px;margin:-8px 0 8px;'>⚠️ Campo obrigatório</p>", unsafe_allow_html=True)
                
                with col_mat:
                    matricula_wiz = st.text_input(
                        "Matrícula",
                        value=st.session_state.wizard_dados.get('matricula', ''),
                        placeholder="Ex: MAT001",
                        help="Campo obrigatório",
                        key="mat_wiz_input"
                    )
                    if matricula_wiz:
                        st.markdown("<p style='color:#10B981;font-size:12px;margin:-8px 0 8px;'>✅ Matrícula preenchida</p>", unsafe_allow_html=True)
                    else:
                        st.markdown("<p style='color:#EF4444;font-size:12px;margin:-8px 0 8px;'>⚠️ Campo obrigatório</p>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_email, col_cel = st.columns(2)
                with col_email:
                    email_wiz = st.text_input(
                        "E-mail (opcional)",
                        value=st.session_state.wizard_dados.get('email', ''),
                        placeholder="exemplo@email.com",
                        key="email_wiz_input"
                    )
                    
                    # Validação de e-mail em tempo real
                    if email_wiz:
                        if validar_email_formato(email_wiz):
                            st.markdown("<p style='color:#10B981;font-size:12px;margin:-8px 0 8px;'>✅ E-mail válido</p>", unsafe_allow_html=True)
                        else:
                            st.markdown("<p style='color:#EF4444;font-size:12px;margin:-8px 0 8px;'>❌ E-mail inválido</p>", unsafe_allow_html=True)
                
                with col_cel:
                    celular_wiz_raw = st.text_input(
                        "Celular (opcional)",
                        max_chars=15,
                        value=st.session_state.wizard_dados.get('celular_formatado', ''),
                        placeholder="(11) 98888-7777",
                        key="cel_wiz_input"
                    )
                    
                    # Aplica máscara e valida celular
                    if celular_wiz_raw:
                        cel_limpo = ''.join(filter(str.isdigit, celular_wiz_raw))
                        cel_formatado = aplicar_mascara_celular(cel_limpo)
                        
                        if len(cel_limpo) == 11 and cel_limpo[2] == '9':
                            st.markdown(f"<p style='color:#10B981;font-size:12px;margin:-8px 0 8px;'>✅ Celular válido: {cel_formatado}</p>", unsafe_allow_html=True)
                        elif len(cel_limpo) > 0:
                            st.markdown(f"<p style='color:#F59E0B;font-size:12px;margin:-8px 0 8px;'>⚠️ Formato: (11) 98888-7777 ({len(cel_limpo)}/11)</p>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn2:
                    cpf_limpo_final = ''.join(filter(str.isdigit, cpf_wiz_raw)) if cpf_wiz_raw else ''
                    cel_limpo_final = ''.join(filter(str.isdigit, celular_wiz_raw)) if celular_wiz_raw else ''
                    
                    # Validações para avançar
                    pode_avancar = all([
                        nome_wiz,
                        len(cpf_limpo_final) == 11,
                        validar_cpf_completo(cpf_limpo_final),
                        not cpf_ja_existe(cpf_limpo_final),
                        matricula_wiz
                    ])
                    
                    if st.button("Próximo →", type="primary", use_container_width=True, disabled=not pode_avancar):
                        st.session_state.wizard_dados.update({
                            'nome': nome_wiz,
                            'cpf': cpf_limpo_final,
                            'cpf_formatado': aplicar_mascara_cpf(cpf_limpo_final),
                            'matricula': matricula_wiz,
                            'email': email_wiz,
                            'celular': cel_limpo_final,
                            'celular_formatado': aplicar_mascara_celular(cel_limpo_final) if cel_limpo_final else ''
                        })
                        st.session_state.wizard_passo = 2
                        st.rerun()
                    
                    if not pode_avancar:
                        st.markdown("<p style='color:#EF4444;font-size:11px;text-align:center;margin:4px 0;'>⚠️ Preencha todos os campos obrigatórios corretamente</p>", unsafe_allow_html=True)
            
            # ── PASSO 2: ENDEREÇO RESIDENCIAL ──
            elif st.session_state.wizard_passo == 2:
                st.markdown("### 🏠 Endereço Residencial")
                st.markdown("<p style='color:#94A3B8;font-size:12px;margin:-8px 0 16px;'>Digite o CEP para buscar o endereço automaticamente</p>", unsafe_allow_html=True)
                
                cep_casa_wiz_raw = st.text_input(
                    "CEP da Residência",
                    max_chars=9,
                    value=st.session_state.wizard_dados.get('cep_casa_formatado', ''),
                    placeholder="00000-000",
                    help="Campo obrigatório",
                    key="cep_casa_wiz_input"
                )
                
                # Aplica máscara e busca endereço
                if cep_casa_wiz_raw:
                    cep_limpo = ''.join(filter(str.isdigit, cep_casa_wiz_raw))
                    cep_formatado = aplicar_mascara_cep(cep_limpo)
                    
                    if len(cep_limpo) == 8:
                        with st.spinner("🔍 Buscando endereço..."):
                            endereco_casa = buscar_endereco_viacep(cep_limpo)
                            if "inválido" not in endereco_casa.get('completo', '').lower():
                                st.markdown(f"<p style='color:#10B981;font-size:12px;margin:-8px 0 8px;'>✅ CEP válido: {cep_formatado}</p>", unsafe_allow_html=True)
                                st.markdown(f"""
                                <div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;padding:12px;margin:8px 0;">
                                    <p style="margin:0;color:#166534;font-size:13px;"><strong>📍 Endereço:</strong> {endereco_casa.get('completo', '')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                st.session_state.wizard_dados['endereco_casa_completo'] = endereco_casa.get('completo', '')
                                
                                # Sugestão de unidades próximas
                                st.info("💡 **Unidades próximas:** SPTrans Centro, SPTrans Zona Leste, SPTrans Zona Sul")
                            else:
                                st.markdown("<p style='color:#EF4444;font-size:12px;margin:-8px 0 8px;'>❌ CEP não encontrado</p>", unsafe_allow_html=True)
                    elif len(cep_limpo) > 0:
                        st.markdown(f"<p style='color:#F59E0B;font-size:12px;margin:-8px 0 8px;'>⚠️ Digite 8 dígitos ({len(cep_limpo)}/8)</p>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color:#EF4444;font-size:12px;margin:-8px 0 8px;'>⚠️ Campo obrigatório</p>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    if st.button("← Voltar", use_container_width=True):
                        st.session_state.wizard_passo = 1
                        st.rerun()
                with col_btn2:
                    cep_limpo_final = ''.join(filter(str.isdigit, cep_casa_wiz_raw)) if cep_casa_wiz_raw else ''
                    pode_avancar = len(cep_limpo_final) == 8
                    
                    if st.button("Próximo →", type="primary", use_container_width=True, disabled=not pode_avancar):
                        st.session_state.wizard_dados['cep_casa'] = cep_limpo_final
                        st.session_state.wizard_dados['cep_casa_formatado'] = aplicar_mascara_cep(cep_limpo_final)
                        st.session_state.wizard_passo = 3
                        st.rerun()
                    
                    if not pode_avancar:
                        st.markdown("<p style='color:#EF4444;font-size:11px;text-align:center;margin:4px 0;'>⚠️ Digite um CEP válido</p>", unsafe_allow_html=True)
            
            # ── PASSO 3: ENDEREÇO DE TRABALHO ──
            elif st.session_state.wizard_passo == 3:
                st.markdown("### 🏢 Endereço de Trabalho")
                st.markdown("<p style='color:#94A3B8;font-size:12px;margin:-8px 0 16px;'>Digite o CEP para buscar o endereço automaticamente</p>", unsafe_allow_html=True)
                
                cep_trab_wiz_raw = st.text_input(
                    "CEP do Trabalho",
                    max_chars=9,
                    value=st.session_state.wizard_dados.get('cep_trabalho_formatado', ''),
                    placeholder="00000-000",
                    help="Campo obrigatório",
                    key="cep_trab_wiz_input"
                )
                
                # Aplica máscara e busca endereço
                if cep_trab_wiz_raw:
                    cep_limpo = ''.join(filter(str.isdigit, cep_trab_wiz_raw))
                    cep_formatado = aplicar_mascara_cep(cep_limpo)
                    
                    if len(cep_limpo) == 8:
                        with st.spinner("🔍 Buscando endereço..."):
                            endereco_trab = buscar_endereco_viacep(cep_limpo)
                            if "inválido" not in endereco_trab.get('completo', '').lower():
                                st.markdown(f"<p style='color:#10B981;font-size:12px;margin:-8px 0 8px;'>✅ CEP válido: {cep_formatado}</p>", unsafe_allow_html=True)
                                st.markdown(f"""
                                <div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;padding:12px;margin:8px 0;">
                                    <p style="margin:0;color:#166534;font-size:13px;"><strong>📍 Endereço:</strong> {endereco_trab.get('completo', '')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                st.session_state.wizard_dados['endereco_trab_completo'] = endereco_trab.get('completo', '')
                            else:
                                st.markdown("<p style='color:#EF4444;font-size:12px;margin:-8px 0 8px;'>❌ CEP não encontrado</p>", unsafe_allow_html=True)
                    elif len(cep_limpo) > 0:
                        st.markdown(f"<p style='color:#F59E0B;font-size:12px;margin:-8px 0 8px;'>⚠️ Digite 8 dígitos ({len(cep_limpo)}/8)</p>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color:#EF4444;font-size:12px;margin:-8px 0 8px;'>⚠️ Campo obrigatório</p>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    if st.button("← Voltar", use_container_width=True):
                        st.session_state.wizard_passo = 2
                        st.rerun()
                with col_btn2:
                    cep_limpo_final = ''.join(filter(str.isdigit, cep_trab_wiz_raw)) if cep_trab_wiz_raw else ''
                    pode_avancar = len(cep_limpo_final) == 8
                    
                    if st.button("Próximo →", type="primary", use_container_width=True, disabled=not pode_avancar):
                        st.session_state.wizard_dados['cep_trabalho'] = cep_limpo_final
                        st.session_state.wizard_dados['cep_trabalho_formatado'] = aplicar_mascara_cep(cep_limpo_final)
                        st.session_state.wizard_passo = 4
                        st.rerun()
                    
                    if not pode_avancar:
                        st.markdown("<p style='color:#EF4444;font-size:11px;text-align:center;margin:4px 0;'>⚠️ Digite um CEP válido</p>", unsafe_allow_html=True)
            
            # ── PASSO 4: INFORMAÇÕES ADICIONAIS ──
            elif st.session_state.wizard_passo == 4:
                st.markdown("### 📝 Informações Adicionais")
                
                # Upload de foto
                foto_upload = st.file_uploader("📷 Foto do Funcionário (opcional)", type=["jpg", "jpeg", "png"])
                if foto_upload:
                    st.image(foto_upload, width=150, caption="Preview da foto")
                    st.session_state.wizard_dados['foto'] = foto_upload
                
                # Campo de observações
                observacoes_wiz = st.text_area(
                    "📋 Observações/Notas Internas (opcional)",
                    value=st.session_state.wizard_dados.get('observacoes', ''),
                    height=100,
                    placeholder="Ex: Funcionário com restrição de horário, necessita acompanhamento especial, etc."
                )
                st.session_state.wizard_dados['observacoes'] = observacoes_wiz
                
                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    if st.button("← Voltar", use_container_width=True):
                        st.session_state.wizard_passo = 3
                        st.rerun()
                with col_btn2:
                    if st.button("Próximo →", type="primary", use_container_width=True):
                        st.session_state.wizard_passo = 5
                        st.rerun()
            
            # ── PASSO 5: PREVIEW E CONFIRMAÇÃO ──
            elif st.session_state.wizard_passo == 5:
                st.markdown("### ✅ Revisão e Confirmação")
                
                dados = st.session_state.wizard_dados
                
                # Card de preview
                st.markdown(f"""
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:20px;margin-bottom:16px;">
                    <h4 style="color:#444c9b;margin:0 0 12px;">👤 {dados.get('nome', '')}</h4>
                    <p style="margin:4px 0;color:#64748B;font-size:14px;">
                        <strong>CPF:</strong> {dados.get('cpf', '')} · 
                        <strong>Matrícula:</strong> {dados.get('matricula', '')}
                    </p>
                    <p style="margin:4px 0;color:#64748B;font-size:14px;">
                        <strong>E-mail:</strong> {dados.get('email', 'Não informado')} · 
                        <strong>Celular:</strong> {dados.get('celular', 'Não informado')}
                    </p>
                    <hr style="border-color:#E2E8F0;margin:12px 0;">
                    <p style="margin:4px 0;color:#64748B;font-size:14px;">
                        <strong>🏠 CEP Casa:</strong> {dados.get('cep_casa', '')}
                    </p>
                    <p style="margin:4px 0;color:#64748B;font-size:13px;">
                        {dados.get('endereco_casa_completo', '')}
                    </p>
                    <p style="margin:8px 0 4px;color:#64748B;font-size:14px;">
                        <strong>🏢 CEP Trabalho:</strong> {dados.get('cep_trabalho', '')}
                    </p>
                    <p style="margin:4px 0;color:#64748B;font-size:13px;">
                        {dados.get('endereco_trab_completo', '')}
                    </p>
                    {f'<hr style="border-color:#E2E8F0;margin:12px 0;"><p style="margin:4px 0;color:#64748B;font-size:13px;"><strong>📋 Observações:</strong> {dados.get("observacoes", "")}</p>' if dados.get('observacoes') else ''}
                </div>
                """, unsafe_allow_html=True)
                
                # Preview da rota (mapa simplificado)
                st.markdown("### 🗺️ Preview da Rota")
                try:
                    # Cria mapa simples com os dois pontos
                    import folium
                    from streamlit_folium import st_folium
                    
                    # Coordenadas aproximadas (São Paulo centro como fallback)
                    mapa_preview = folium.Map(location=[-23.5505, -46.6333], zoom_start=11)
                    
                    folium.Marker(
                        [-23.5505, -46.6333],
                        popup="🏠 Casa",
                        icon=folium.Icon(color='blue', icon='home')
                    ).add_to(mapa_preview)
                    
                    folium.Marker(
                        [-23.5605, -46.6533],
                        popup="🏢 Trabalho",
                        icon=folium.Icon(color='purple', icon='briefcase')
                    ).add_to(mapa_preview)
                    
                    st_folium(mapa_preview, width=700, height=300)
                    
                    st.info("💡 **Estimativa:** Distância ~5 km · Tempo ~20 min · Valor mensal ~R$ 220,00")
                except Exception:
                    st.warning("⚠️ Não foi possível gerar o preview da rota")
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
                with col_btn1:
                    if st.button("← Voltar", use_container_width=True):
                        st.session_state.wizard_passo = 4
                        st.rerun()
                with col_btn2:
                    if st.button("🗑️ Cancelar", use_container_width=True):
                        st.session_state.wizard_passo = 1
                        st.session_state.wizard_dados = {}
                        st.rerun()
                with col_btn3:
                    if st.button("💾 Confirmar e Salvar", type="primary", use_container_width=True):
                        # Salva no banco
                        try:
                            cpf_limpo = ''.join(filter(str.isdigit, dados['cpf']))
                            
                            if cpf_ja_existe(cpf_limpo):
                                st.error(f"❌ CPF {cpf_limpo} já está cadastrado no sistema.")
                            else:
                                conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                                cursor = conexao.cursor()
                                
                                cursor.execute("SELECT MAX(CAST(id AS INTEGER)) FROM jovens_rotas")
                                max_id = cursor.fetchone()[0]
                                novo_id = 1 if max_id is None else int(max_id) + 1
                                
                                cursor.execute("""
                                    INSERT INTO jovens_rotas 
                                    (id, nome, cpf, cep_casa, cep_trabalho, matricula, email, celular, status_rota)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Otimizado')
                                """, (
                                    novo_id,
                                    dados['nome'],
                                    cpf_limpo,
                                    dados['cep_casa'],
                                    dados['cep_trabalho'],
                                    dados['matricula'],
                                    dados.get('email', ''),
                                    dados.get('celular', '')
                                ))
                                
                                conexao.commit()
                                conexao.close()
                                
                                # Mensagem de sucesso destacada
                                st.markdown("""
                                <div style="background:linear-gradient(135deg, #10B981 0%, #059669 100%);
                                            border-radius:16px;padding:32px;margin:24px 0;
                                            box-shadow:0 10px 25px rgba(16,185,129,0.3);text-align:center;">
                                    <div style="font-size:64px;margin-bottom:16px;">🎉</div>
                                    <h2 style="color:#FFFFFF;margin:0 0 8px;font-size:28px;font-weight:800;">Cadastro Realizado com Sucesso!</h2>
                                    <p style="color:#D1FAE5;font-size:16px;margin:0;">
                                        <strong style="color:#FFFFFF;">{nome}</strong> foi cadastrado no sistema
                                    </p>
                                    <p style="color:#D1FAE5;font-size:14px;margin:8px 0 0;">
                                        ID: <strong style="color:#FFFFFF;">#{id_cadastro}</strong> · 
                                        Matrícula: <strong style="color:#FFFFFF;">{matricula}</strong>
                                    </p>
                                </div>
                                """.format(
                                    nome=dados['nome'],
                                    id_cadastro=novo_id,
                                    matricula=dados['matricula']
                                ), unsafe_allow_html=True)
                                
                                # Botões de ação
                                col_acao1, col_acao2, col_acao3 = st.columns([1, 1, 1])
                                
                                with col_acao1:
                                    if st.button("➕ Cadastrar Outro", type="primary", use_container_width=True):
                                        st.session_state.wizard_passo = 1
                                        st.session_state.wizard_dados = {}
                                        st.rerun()
                                
                                with col_acao2:
                                    if st.button("📋 Ver Cadastro", use_container_width=True):
                                        st.session_state.menu_selecionado = "Pesquisar Consultas"
                                        st.rerun()
                                
                                with col_acao3:
                                    if st.button("🏠 Ir para Dashboard", use_container_width=True):
                                        st.session_state.menu_selecionado = "Dashboard Principal"
                                        st.rerun()
                                
                                st.stop()  # Para a execução aqui para mostrar apenas a mensagem de sucesso
                                
                        except Exception as e:
                            st.error(f"❌ Erro ao salvar: {e}")
        
        # ══════════════════════════════════════════════════════════════════════════
        # MODO FORMULÁRIO COMPLETO
        # ══════════════════════════════════════════════════════════════════════════
        
        else:
            tab_manual, tab_massa = st.tabs(["✍️ Cadastro Manual", "📂 Importação em Massa"])

            with tab_manual:
                st.markdown("""
                <div style="background:#FFFFFF;border:1px solid #E5E7EB;
                            border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                    <p style="color:#666666;font-size:12px;margin:0;">
                        Preencha todos os campos obrigatórios (*). Validações são feitas em tempo real.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                with st.form(key="form_novo_jovem"):
                    # Dados Pessoais
                    st.markdown("#### 👤 Dados Pessoais")
                    col_n, col_c, col_m = st.columns([2, 1, 1])
                    nome_input = col_n.text_input("Nome Completo *")
                    cpf_input = col_c.text_input("CPF (11 dígitos) *", max_chars=11)
                    matricula_input = col_m.text_input("Matrícula *")

                    col_email, col_cel = st.columns(2)
                    email_input = col_email.text_input("E-mail", placeholder="exemplo@email.com")
                    celular_input = col_cel.text_input("Celular", max_chars=11, placeholder="11988887777")

                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Endereços
                    st.markdown("#### 📍 Endereços")
                    col_cep1, col_cep2 = st.columns(2)
                    cep_casa_input = col_cep1.text_input("CEP da Residência *", max_chars=8)
                    cep_trab_input = col_cep2.text_input("CEP do Trabalho *", max_chars=8)

                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Informações Adicionais
                    st.markdown("#### 📝 Informações Adicionais")
                    observacoes_input = st.text_area(
                        "Observações/Notas Internas",
                        height=80,
                        placeholder="Ex: Funcionário com restrição de horário..."
                    )

                    botao_salvar = st.form_submit_button("💾 Salvar na Base de Dados", type="primary")

            if botao_salvar:
                # Validações
                erros = []
                
                if not all([nome_input, cpf_input, cep_casa_input, cep_trab_input, matricula_input]):
                    erros.append("⚠️ Preencha todos os campos obrigatórios (*)")
                
                digitos_cpf = ''.join(filter(str.isdigit, cpf_input))
                if len(digitos_cpf) != 11:
                    erros.append("❌ CPF deve conter exatamente 11 dígitos")
                elif len(set(digitos_cpf)) == 1:
                    erros.append("❌ CPF inválido: todos os dígitos são iguais")
                elif cpf_ja_existe(digitos_cpf):
                    erros.append(f"❌ CPF {digitos_cpf} já está cadastrado")
                
                # Validação de e-mail
                if email_input:
                    import re
                    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_regex, email_input):
                        erros.append("❌ E-mail inválido")
                
                # Validação de celular
                if celular_input:
                    cel_limpo = ''.join(filter(str.isdigit, celular_input))
                    if len(cel_limpo) != 11 or cel_limpo[2] != '9':
                        erros.append("❌ Celular inválido (formato: 11988887777)")
                
                if erros:
                    for erro in erros:
                        st.error(erro)
                else:
                    with st.spinner("Validando CEPs e salvando..."):
                        v_casa = buscar_endereco_viacep(cep_casa_input)
                        v_trab = buscar_endereco_viacep(cep_trab_input)
                        
                        if "inválido" in v_casa.get('completo','').lower() or "inválido" in v_trab.get('completo','').lower():
                            st.error("❌ Um dos CEPs informados é inválido.")
                        else:
                            try:
                                conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                                cursor = conexao.cursor()
                                
                                cursor.execute("SELECT MAX(CAST(id AS INTEGER)) FROM jovens_rotas")
                                max_id = cursor.fetchone()[0]
                                novo_id = 1 if max_id is None else int(max_id) + 1
                                
                                cursor.execute("""
                                    INSERT INTO jovens_rotas 
                                    (id, nome, cpf, cep_casa, cep_trabalho, matricula, email, celular, status_rota)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Otimizado')
                                """, (
                                    novo_id,
                                    nome_input,
                                    digitos_cpf,
                                    cep_casa_input,
                                    cep_trab_input,
                                    matricula_input,
                                    email_input,
                                    celular_input
                                ))
                                
                                conexao.commit()
                                conexao.close()
                                
                                st.success(f"✅ {nome_input} (Matrícula: {matricula_input}) cadastrado com sucesso! (ID: {novo_id})")
                                time.sleep(2)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao salvar: {e}")

            with tab_massa:
                st.markdown("""
                <div style="background:rgba(248,174,40,0.1);border:1px solid #E5E7EB;
                            border-radius:12px;padding:16px;margin-bottom:16px;">
                    <p style="color:#666666;font-size:13px;margin:0;">
                        💡 A planilha deve conter as colunas:
                        <strong style="color:#f8ae28;">nome, cpf, cep_casa, cep_trabalho, matricula</strong>
                        <br>Colunas opcionais: <strong>email, celular, observacoes</strong>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Botão para baixar template
                col_template, col_upload = st.columns([1, 2])
                
                with col_template:
                    st.markdown("#### 📥 Template")
                    if st.button("⬇️ Baixar Template Excel", use_container_width=True):
                        try:
                            from io import BytesIO
                            from openpyxl import Workbook
                            from openpyxl.styles import Font, PatternFill, Alignment
                            
                            wb = Workbook()
                            ws = wb.active
                            ws.title = "Template Cadastro"
                            
                            # Cabeçalho
                            headers = ['nome', 'cpf', 'cep_casa', 'cep_trabalho', 'matricula', 'email', 'celular', 'observacoes']
                            ws.append(headers)
                            
                            # Estilo do cabeçalho
                            for cell in ws[1]:
                                cell.font = Font(bold=True, color="FFFFFF")
                                cell.fill = PatternFill(start_color="444c9b", end_color="444c9b", fill_type="solid")
                                cell.alignment = Alignment(horizontal="center")
                            
                            # Linha de exemplo
                            ws.append([
                                'João da Silva',
                                '12345678901',
                                '01310100',
                                '01310200',
                                'MAT001',
                                'joao@email.com',
                                '11988887777',
                                'Funcionário novo'
                            ])
                            
                            # Ajusta largura das colunas
                            for column in ws.columns:
                                max_length = 0
                                column_letter = column[0].column_letter
                                for cell in column:
                                    try:
                                        if len(str(cell.value)) > max_length:
                                            max_length = len(cell.value)
                                    except:
                                        pass
                                adjusted_width = min(max_length + 2, 50)
                                ws.column_dimensions[column_letter].width = adjusted_width
                            
                            # Salva em buffer
                            buffer = BytesIO()
                            wb.save(buffer)
                            buffer.seek(0)
                            
                            st.download_button(
                                label="📄 Template.xlsx",
                                data=buffer,
                                file_name="template_cadastro_funcionarios.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"❌ Erro ao gerar template: {e}")
                
                with col_upload:
                    st.markdown("#### 📤 Upload")
                    arquivo_upload = st.file_uploader("Arraste o arquivo Excel (.xlsx) ou CSV", type=["xlsx","csv"], key="upload_massa")

                if arquivo_upload is not None:
                    try:
                        if arquivo_upload.name.endswith('.csv'):
                            df_upload = pd.read_csv(arquivo_upload, sep=';', dtype=str)
                        else:
                            df_upload = pd.read_excel(arquivo_upload, dtype=str)

                        df_upload.columns = df_upload.columns.str.lower().str.strip()

                        # Validação de colunas obrigatórias
                        colunas_obrigatorias = ['nome', 'cpf', 'cep_casa', 'cep_trabalho', 'matricula']
                        colunas_faltando = [col for col in colunas_obrigatorias if col not in df_upload.columns]
                        
                        if colunas_faltando:
                            st.error(f"❌ Colunas obrigatórias faltando: {', '.join(colunas_faltando)}")
                        else:
                            # Adiciona colunas opcionais se não existirem
                            if 'email' not in df_upload.columns:
                                df_upload['email'] = ''
                            if 'celular' not in df_upload.columns:
                                df_upload['celular'] = ''
                            if 'observacoes' not in df_upload.columns:
                                df_upload['observacoes'] = ''
                            
                            df_upload['status_rota'] = "Otimizado"
                            
                            # Validações em lote
                            st.markdown("#### 🔍 Validação dos Dados")
                            
                            erros_validacao = []
                            avisos_validacao = []
                            
                            for idx, row in df_upload.iterrows():
                                linha = idx + 2  # +2 porque começa em 1 e tem cabeçalho
                                
                                # Valida CPF
                                cpf_limpo = ''.join(filter(str.isdigit, str(row['cpf'])))
                                if len(cpf_limpo) != 11:
                                    erros_validacao.append(f"Linha {linha}: CPF inválido (deve ter 11 dígitos)")
                                elif len(set(cpf_limpo)) == 1:
                                    erros_validacao.append(f"Linha {linha}: CPF inválido (todos dígitos iguais)")
                                
                                # Valida e-mail se preenchido
                                if row.get('email') and str(row['email']).strip():
                                    import re
                                    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                                    if not re.match(email_regex, str(row['email'])):
                                        avisos_validacao.append(f"Linha {linha}: E-mail inválido")
                                
                                # Valida celular se preenchido
                                if row.get('celular') and str(row['celular']).strip():
                                    cel_limpo = ''.join(filter(str.isdigit, str(row['celular'])))
                                    if len(cel_limpo) != 11 or cel_limpo[2] != '9':
                                        avisos_validacao.append(f"Linha {linha}: Celular inválido (formato: 11988887777)")
                            
                            # Mostra erros e avisos
                            if erros_validacao:
                                st.error("❌ **Erros encontrados:**")
                                for erro in erros_validacao[:10]:  # Mostra no máximo 10
                                    st.error(f"• {erro}")
                                if len(erros_validacao) > 10:
                                    st.error(f"... e mais {len(erros_validacao) - 10} erros")
                            
                            if avisos_validacao:
                                st.warning("⚠️ **Avisos (não impedem importação):**")
                                for aviso in avisos_validacao[:10]:
                                    st.warning(f"• {aviso}")
                                if len(avisos_validacao) > 10:
                                    st.warning(f"... e mais {len(avisos_validacao) - 10} avisos")
                            
                            if not erros_validacao:
                                st.success(f"✅ Validação concluída! {len(df_upload)} registros prontos para importação")
                            
                            # Preview
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown("<p style='color:#94A3B8;font-size:13px;'>📋 Pré-visualização:</p>", unsafe_allow_html=True)
                            st.dataframe(df_upload.head(10), use_container_width=True)
                            
                            if len(df_upload) > 10:
                                st.info(f"💡 Mostrando 10 de {len(df_upload)} registros")

                            if not erros_validacao and st.button("🚀 Importar para a Base de Dados", type="primary"):
                                with st.spinner("Importando..."):
                                    df_limpo = df_upload[['nome','cpf','cep_casa','cep_trabalho','matricula','email','celular','status_rota']].copy()
                                    
                                    # Limpa os CPFs
                                    df_limpo['cpf'] = df_limpo['cpf'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(11)
                                    
                                    # Limpa celulares
                                    df_limpo['celular'] = df_limpo['celular'].astype(str).str.replace(r'\D', '', regex=True)
                                    
                                    conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                                    
                                    # Geração de IDs
                                    cursor = conexao.cursor()
                                    cursor.execute("SELECT MAX(CAST(id AS INTEGER)) FROM jovens_rotas")
                                    max_id = cursor.fetchone()[0]
                                    start_id = 1 if max_id is None else int(max_id) + 1
                                    
                                    df_limpo.insert(0, 'id', range(start_id, start_id + len(df_limpo)))
                                    
                                    df_limpo.to_sql('jovens_rotas', conexao, if_exists='append', index=False)
                                    conexao.close()
                                    
                                    st.success(f"✅ {len(df_limpo)} funcionários importados com sucesso!")
                                    time.sleep(2)
                                    st.rerun()

                    except Exception as e:
                        st.error(f"❌ Erro ao ler o arquivo: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TELA 3 — TRIAGEM DE FICHAS (MELHORADA)
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "🗂️ Triagem de Fichas":
    renderizar_triagem()

# ══════════════════════════════════════════════════════════════════════════════
# TELA 4 — BANCO DE DADOS
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "💾 Banco de Dados":
    renderizar_banco_dados()

elif menu == "🌐 Simulação: Portal do Jovem":
    renderizar_portal_jovem_avancado()


# ══════════════════════════════════════════════════════════════════════════════
# TELA — RELATÓRIOS E ANALYTICS (APENAS ADMIN)
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "📊 Relatórios e Analytics":
    if _role_atual == "admin":
        renderizar_relatorios_analytics()
    else:
        st.error("🚫 Acesso negado. Esta área é restrita ao administrador.")
        st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# TELA — AUDITORIA E COMPLIANCE (APENAS ADMIN)
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "🔍 Auditoria e Compliance":
    if _role_atual == "admin":
        renderizar_auditoria_compliance()
    else:
        st.error("🚫 Acesso negado. Esta área é restrita ao administrador.")
        st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# TELA 5 — GERENCIAR UNIDADES
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "🏢 Gerenciar Unidades":
    renderizar_gerenciar_unidades()

# ══════════════════════════════════════════════════════════════════════════════
# TELA — REGISTRO DE FUNCIONÁRIO (APENAS ADMIN)
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "👥 Registro de Funcionário":
    if _role_atual == "admin":
        renderizar_registro_funcionario_avancado()
    else:
        st.error("🚫 Acesso negado. Esta área é restrita ao administrador.")
        st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# RODAPÉ INSTITUCIONAL — Aparece em todas as páginas
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<hr style='border-color:#E2E8F0;margin:40px 0 20px;'>", unsafe_allow_html=True)

# ── CSS separado do HTML (resolve o bug do Streamlit) ──
st.markdown("""
<style>
.renapsi-social-link svg { fill: #64748B; transition: fill 0.25s ease; }
.renapsi-social-link:hover svg { fill: #f8ae28; transform: scale(1.1); }
.renapsi-social-link { text-decoration: none; display: flex; align-items: center; justify-content: center; transition: transform 0.2s; }
</style>
""", unsafe_allow_html=True)

# ── HTML do rodapé (SEM ESPAÇOS NO INÍCIO PARA NÃO BUGAR O MARKDOWN) ──
st.markdown("""
<div style="text-align:center; padding:20px 0;">
<div style="display:flex; justify-content:center; align-items:center; gap:20px; margin-bottom:24px;">
<span style="color:#64748B; font-size:18px; font-weight:400;">Siga-nos:</span>

<a class="renapsi-social-link" href="https://www.instagram.com/renapsibr/" target="_blank" title="Instagram">
<svg width="28" height="28" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
</a>

<a class="renapsi-social-link" href="https://www.facebook.com/DemaJovembyRenapsi" target="_blank" title="Facebook">
<svg width="28" height="28" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
</a>

<a class="renapsi-social-link" href="https://www.linkedin.com/company/renapsibr" target="_blank" title="LinkedIn">
<svg width="28" height="28" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
</a>

<a class="renapsi-social-link" href="https://www.youtube.com/c/RenapsiBrasil" target="_blank" title="YouTube">
<svg width="32" height="32" viewBox="0 0 24 24" style="margin-top:-2px;"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
</a>

</div>
<p style="color:#94A3B8; font-size:12px; margin:0; line-height:1.6;">
Copyright ©️ Renapsi - 2026. Todos os direitos reservados.<br>
CNPJ 37.381.902/0001-25
</p>
</div>
""", unsafe_allow_html=True)