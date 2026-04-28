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
from dotenv import load_dotenv
from streamlit_folium import st_folium
from banco_dados import *
from apis import *
from agente_ia import *
from carta_pdf import gerar_carta_pdf
from email_sender import enviar_carta_por_email

# ─── Carrega variáveis de ambiente ───────────────────────────────────────────
load_dotenv()

# ─── Configuração da página ───────────────────────────────────────────────────
st.set_page_config(page_title="RENAPSI — Mobilidade", page_icon="🚇", layout="wide")

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
/* ── Reset ── */
#MainMenu {visibility: hidden;}
footer     {visibility: hidden;}
header     {visibility: hidden;}

/* ── Fundo principal — Branco puro ── */
.stApp {
        background: #FFFFFF !important;
        font-size: 18px !important;
}

/* ── Sidebar — Branco/Cinza gelo ── */
[data-testid="stSidebar"] {
        background: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
}
[data-testid="stSidebar"] .stRadio > label {
        color: #1E293B !important;
        font-size: 20px !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] .stMarkdown p {
        color: #333333 !important;
        font-size: 19px !important;
}
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
        color: #64748B;
        font-size: 20px !important;
        transition: color 0.2s;
}
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p:hover {
        color: #f8ae28;
}

/* ── KPI cards — Fundo branco com sombra suave ── */
div[data-testid="metric-container"] {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
}
div[data-testid="metric-container"] [data-testid="stMetricLabel"] {
        color: #64748B !important;
        font-size: 19px !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #f8ae28 !important;
        font-size: 2.6rem !important;
        font-weight: 700;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
        background: #f8ae28 !important;
        color: #FFFFFF !important;
        padding: 4px 8px !important;
        border-radius: 6px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] svg {
        display: none !important;
}

/* ── Headings — Cinza escuro ── */
h1, h2, h3 { color: #1E293B !important; font-size: 1.5em !important; }
h4          { color: #333333 !important; font-size: 1.3em !important; }

/* ── Texto geral — Cinza escuro para contraste ── */
p, span, div, label, input, textarea, select {
        color: #333333 !important;
        font-size: 19px !important;
}

/* ── Botões primários — Laranja RENAPSI ── */
.stButton > button[kind="primary"],
button[data-testid="baseButton-primary"] {
        background: #f8ae28 !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 20px !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 4px rgba(248,174,40,0.3) !important;
        transition: background 0.2s, transform 0.1s !important;
}
.stButton > button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover {
        background: #e09a1f !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(248,174,40,0.4) !important;
}

/* ── Botões secundários — Azul RENAPSI ── */
.stButton > button[kind="secondary"],
button[data-testid="baseButton-secondary"] {
        background: #444c9b !important;
        border: none !important;
        color: #FFFFFF !important;
        font-size: 20px !important;
        border-radius: 8px !important;
        transition: background 0.2s, box-shadow 0.2s !important;
}
.stButton > button[kind="secondary"]:hover {
        background: #363d7f !important;
        box-shadow: 0 2px 6px rgba(68,76,155,0.3) !important;
}

/* ── Botões padrão (sem type) — Tema claro ── */
.stButton > button:not([kind]),
button[data-testid="baseButton-minimal"] {
        background: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        color: #333333 !important;
        font-size: 20px !important;
        border-radius: 8px !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stButton > button:not([kind]):hover,
button[data-testid="baseButton-minimal"]:hover {
        border-color: #CBD5E1 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        background: #F8FAFC !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
        background: #F8FAFC;
        border-radius: 10px;
        padding: 4px;
        border: 1px solid #E2E8F0;
}
.stTabs [data-baseweb="tab"] {
        color: #64748B !important;
        font-size: 20px !important;
        border-radius: 8px;
}
.stTabs [aria-selected="true"] {
        background: #f8ae28 !important;
        color: #FFFFFF !important;
        border-bottom: 2px solid #f8ae28 !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        color: #333333 !important;
        font-size: 19px !important;
        border-radius: 8px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
        border-color: #f8ae28 !important;
        box-shadow: 0 0 0 2px rgba(248,174,40,0.1) !important;
}

/* ── Dataframe ── */
.stDataFrame {
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        font-size: 19px !important;
}

/* ── Expander ── */
[data-testid="stExpander"] details summary {
        background-color: #444c9b !important;
        border-radius: 8px !important;
        border: none !important;
}
/* Evita que fique preto ao clicar (estado de foco/hover) */
[data-testid="stExpander"] details summary:hover,
[data-testid="stExpander"] details summary:focus,
[data-testid="stExpander"] details summary:active {
        background-color: #363d7f !important;
        outline: none !important;
}
/* Força o texto e o ícone da setinha a ficarem brancos */
[data-testid="stExpander"] details summary p,
[data-testid="stExpander"] details summary svg {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 18px !important;
}
/* Garante que o conteúdo que abre embaixo continue com fundo branco */
[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
}
}

/* ── Divider ── */
hr { border-color: #E2E8F0 !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #f8ae28 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #F8FAFC; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }
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
st.sidebar.image("logo_renapsi.png", use_container_width=True)
st.sidebar.markdown(
        "<p style='color:#64748B;font-size:13px;text-align:center;letter-spacing:0.1em;margin-top:-8px;'>SISTEMA DE MOBILIDADE URBANA</p>",
        unsafe_allow_html=True
)
st.sidebar.markdown("---")
st.sidebar.markdown("<p style='color:#1E293B;font-size:13px;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;'>Navegação</p>", unsafe_allow_html=True)

parametros_url = st.query_params
pagina_salva = parametros_url.get("menu", "Dashboard Principal")
opcoes_menu = ["Dashboard Principal", "Pesquisar Consultas", "Cadastrar Novo Jovem", "🗂️ Triagem de Fichas", "Banco de Dados", "🏢 Gerenciar Unidades", "Simulação: Portal do Jovem"]
indice_padrao = opcoes_menu.index(pagina_salva) if pagina_salva in opcoes_menu else 0

menu = st.sidebar.radio("", opcoes_menu, index=indice_padrao)

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
if menu == "Dashboard Principal":

        meses_pt = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                    "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        mes_atual = meses_pt[datetime.datetime.now().month - 1]
        ano_atual = datetime.datetime.now().year

        # ── Cabeçalho ──
        col_header, col_img = st.columns([10, 2])
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
                <h1 style="margin:0; color:#444c9b; font-size:32px;">Dashboard de Mobilidade</h1>
            </div>
            """, unsafe_allow_html=True)
        
        with col_img:
            try:
                st.image("forma_grafica.png", width=100)
            except:
                pass  # Imagem decorativa opcional

        tipo_rota = st.radio(
            "Modalidade:",
            ["🏠 Casa × Trabalho", "📚 Casa × Curso", "📊 Gestão de Base", "📧 Envios em Massa"],
            horizontal=True,
            key="modalidade_pesquisa_radio"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        total_consultas, sla_medio, total_contestacoes, total_implantados = obter_dados_dashboard()

        # ── KPI Cards ──
        col_k1, col_k2, col_k3, col_k4 = st.columns(4)
        with col_k1:
            st.metric("Total de Consultas", f"{total_consultas}", "Rotas únicas")
        with col_k2:
            st.metric("SLA Médio", f"{sla_medio:.2f}s", "Tempo de resposta")
        with col_k3:
            st.metric("Contestações", f"{total_contestacoes}", "Total histórico")
        with col_k4:
            st.metric("Implantações", f"{total_implantados}", "Ativos no momento")

        st.markdown("<br>", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════════
        # ROI DASHBOARD — ANÁLISE FINANCEIRA
        # ══════════════════════════════════════════════════════════════════════════
        st.markdown("""
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;
                    border-radius:14px;padding:24px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
            <h3 style="margin:0 0 4px;color:#f8ae28;">💰 Análise de ROI — Retorno sobre Investimento</h3>
            <p style="color:#64748B;font-size:15px;margin:0;">
                Comparativo de custos: Mobilidade Manual vs. Otimizada
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Busca total de jovens na base
        conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        df_jovens = pd.read_sql_query("SELECT COUNT(*) as total FROM jovens_rotas", conexao)
        total_jovens = df_jovens.iloc[0]['total'] if not df_jovens.empty else 0
        conexao.close()

        # Constantes financeiras
        CUSTO_MANUAL_DIARIO = 15.00  # R$ por dia
        CUSTO_OTIMIZADO_DIARIO = 11.32  # R$ por dia
        DIAS_UTEIS_MES = 22  # Dias úteis em um mês

        # Cálculos
        custo_manual_mes = CUSTO_MANUAL_DIARIO * DIAS_UTEIS_MES * total_jovens
        custo_otimizado_mes = CUSTO_OTIMIZADO_DIARIO * DIAS_UTEIS_MES * total_jovens
        economia_mes = custo_manual_mes - custo_otimizado_mes
        percentual_economia = (economia_mes / custo_manual_mes * 100) if custo_manual_mes > 0 else 0

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
            </p>
            """, unsafe_allow_html=True)
            
            # Dados de distribuição modal
            modais = ['Integração', 'Ônibus', 'Metrô']
            percentuais = [40, 35, 25]
            cores_modais = ['#f8ae28', '#444c9b', '#64748B']  # Laranja, Azul, Cinza RENAPSI

            fig_modal = px.pie(
                values=percentuais,
                names=modais,
                hole=0.5,
                color_discrete_sequence=cores_modais
            )
            fig_modal.update_traces(
                textposition='inside',
                textinfo='label+percent',
                textfont=dict(size=14, color='#FFFFFF'),
                hovertemplate='<b>%{label}</b><br>%{value}%<extra></extra>'
            )
            fig_modal.update_layout(
                showlegend=True,
                legend=dict(
                    orientation='v',
                    yanchor='middle',
                    y=0.5,
                    xanchor='left',
                    x=1.05,
                    font=dict(size=13, color='#64748B')
                ),
                margin=dict(t=10, b=10, l=10, r=100),
                height=280,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Arial', size=14, color='#333333')
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
            df_pendentes = pd.read_sql_query("""
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
                            if st.button("🚀 Iniciar Envio em Massa", type="primary", use_container_width=True):
                                st.session_state.iniciar_envio_massa = True
                                st.session_state.ids_para_envio = funcionarios_selecionados
                                st.rerun()
                        with col_env2:
                            if st.button("❌ Cancelar", use_container_width=True):
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
                                    df_func = pd.read_sql_query(
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
            df_contest = pd.read_sql_query("SELECT * FROM contestacoes", conexao)
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
            st.markdown("""
            <div style="background:#FFFFFF;border:1px solid #E5E7EB;
                        border-radius:12px;padding:16px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                <p style="color:#666666;font-size:13px;text-transform:uppercase;letter-spacing:0.1em;margin:0 0 8px;">
                    Implantações
                </p>
                <p style="color:#666666;font-size:13px;margin:0;">Nenhuma no período</p>
            </div>
            """, unsafe_allow_html=True)

        with col_g2:
            st.markdown(f"""
            <p style="color:#94A3B8;font-size:14px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">
                Contestações ({qtd_resolvidas}/{total_contestacoes})
            </p>
            """, unsafe_allow_html=True)
            if total_contestacoes == 0:
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
                st.plotly_chart(fig, use_container_width=True, key="graf_contest")

        with col_g3:
            st.markdown("<p style='color:#666666;font-size:14px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;'>Por Local de Trabalho</p>", unsafe_allow_html=True)
            fig2 = px.pie(values=[10, 0], names=['SP','Outros'], hole=0.72)
            fig2.update_traces(textinfo='none', marker=dict(colors=['#f8ae28','#E5E7EB']), hoverinfo="skip")
            fig2.update_layout(showlegend=False, margin=dict(t=5,b=5,l=5,r=5), height=160,
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(size=13, color='#333333'))
            st.plotly_chart(fig2, use_container_width=True, key="graf_local")

        with col_g4:
            st.markdown("<p style='color:#666666;font-size:14px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;'>Por UF</p>", unsafe_allow_html=True)
            fig3 = px.pie(values=[10, 0], names=['SP','Outros'], hole=0.72)
            fig3.update_traces(textinfo='none', marker=dict(colors=['#444c9b','#E5E7EB']), hoverinfo="skip")
            fig3.update_layout(showlegend=False, margin=dict(t=5,b=5,l=5,r=5), height=160,
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(size=13, color='#333333'))
            st.plotly_chart(fig3, use_container_width=True, key="graf_uf")

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
                            st.markdown(f"""
                            <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-left:4px solid #EF4444;
                                        border-radius:12px;padding:20px;margin-bottom:12px;
                                        box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                                <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                                    <span style="color:#EF4444;font-weight:700;font-size:15px;">Consulta #{row['id']}</span>
                                    <span style="background:rgba(239,68,68,0.15);color:#EF4444;padding:2px 8px;
                                                border-radius:20px;font-size:13px;">PENDENTE</span>
                                </div>
                                <p style="color:#666666;font-size:13px;margin:0 0 8px;">
                                    {row['data_geracao']} · <strong style="color:#333333;">{row['nome_jovem']}</strong>
                                </p>
                                <div style="background:rgba(239,68,68,0.05);border-left:3px solid #EF4444;
                                            padding:10px 14px;border-radius:0 6px 6px 0;font-size:13px;color:#333333;">
                                    {row['motivo']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            col_t, col_b = st.columns([3, 1])
                            with col_t:
                                tratativa_input = st.text_input("Tratativa aplicada:", key=f"input_{row['id']}")
                            with col_b:
                                st.write("")
                                st.write("")
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
                            st.markdown(f"""
                            <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-left:4px solid #10B981;
                                        border-radius:12px;padding:20px;margin-bottom:12px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                                <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                                    <span style="color:#10B981;font-weight:700;font-size:15px;">Consulta #{row['id']}</span>
                                    <span style="background:rgba(16,185,129,0.15);color:#10B981;padding:2px 8px;
                                                border-radius:20px;font-size:13px;">RESOLVIDO</span>
                                </div>
                                <p style="color:#666666;font-size:13px;margin:0 0 6px;">{row['data_geracao']} · <strong style="color:#333333;">{row['nome_jovem']}</strong></p>
                                <p style="color:#666666;font-size:13px;margin:0 0 8px;"><strong>Motivo:</strong> {row['motivo']}</p>
                                <div style="background:rgba(16,185,129,0.08);border-left:3px solid #10B981;
                                            padding:10px 14px;border-radius:0 6px 6px 0;font-size:13px;color:#333333;">
                                    <strong>Tratativa:</strong> {row.get('tratativa','')}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                with tab_tab:
                    df_exib = df_contest[['id','data_geracao','nome_jovem','motivo','status','tratativa']].copy()
                    df_exib.columns = ['ID','Data','Funcionário','Motivo','Status','Tratativa']
                    st.dataframe(df_exib, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TELA 1 — PESQUISAR CONSULTAS
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "Pesquisar Consultas":

# Recupera estado após F5
        if 'id_consulta' in st.query_params and st.session_state.get('resultado_busca') is None:
            id_salvo = st.query_params['id_consulta']
            conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
            df_salvo = pd.read_sql_query("SELECT * FROM jovens_rotas WHERE id = ?", conexao, params=(int(float(id_salvo)),))
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
                    
                    if st.button("🔍 Buscar Coordenadas Reais", type="secondary", use_container_width=True):
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
                    if st.button("Fechar", use_container_width=True):
                        st.session_state.modo_edicao = False
                        st.session_state.pop('coord_temp', None)
                        st.rerun()
                with col_c:
                    if st.button("Confirmar Alterações", type="primary", use_container_width=True):
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
                                            SET matricula = ?, email = ?, celular = ?, cep_casa = ?, numero_casa = ?, coordenadas = ?, cep_trabalho = ?
                                            WHERE id = ?
                                        ''', (mat_final, email_final, celular_final, cep_final, num_final, coord_final, cep_trab_final, id_selecionado))
                                        conexao.commit()
                                        
                                        # Recarrega dados atualizados
                                        df_atualizado = pd.read_sql_query("SELECT * FROM jovens_rotas WHERE id = ?", conexao, params=(int(id_selecionado),))
                                        conexao.close()
                                    
                                    if not df_atualizado.empty:
                                        st.session_state.resultado_busca = df_atualizado
                                        st.session_state.modo_edicao = False
                                        st.session_state.pop('coord_temp', None)
                                        st.session_state.rota_gerada = None # Força o recalculo da rota para a nova empresa
                                        st.session_state.analise_ia = None
                                        
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
                    
                    if not st.session_state.get('analise_ia'):
                        st.session_state.analise_ia = analisar_rota_com_ia(
                            rua_casa, rua_trab, rota['distancia_km'], rota['rotas'], rota['info_tarifas']
                        )

                col_fill, col_edit_btn = st.columns([11, 1])
                with col_edit_btn:
                    if st.button("✏️", use_container_width=True, help="Editar dados"):
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
                    
                with col_header_right:
                    st.markdown(f"""
                    <div style="background:rgba({status_bg},0.15);color:{status_color};padding:6px 14px;border-radius:20px;font-size:12px;font-weight:700;border:1px solid {status_color}40;text-align:center;">
                        {status_exib}
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
                    if st.button("🔄 Recalcular", type="secondary", use_container_width=True):
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
                    if st.button("✉️ Enviar Carta", type="secondary", use_container_width=True):
                        st.session_state.mostrar_modal_email = not st.session_state.get('mostrar_modal_email', False)
                        
                with col_b3:
                    if st.button("⚠️ Contestação", type="secondary", use_container_width=True):
                        st.session_state.modo_contestacao = not st.session_state.get('modo_contestacao', False)
                        
                with col_b4:
                    if st.button("✍️ Rota Manual", type="secondary", use_container_width=True):
                        st.session_state.modo_rota_manual = not st.session_state.get('modo_rota_manual', False)
                        
                with col_b5:
                    if st.button("📋 Implantados", type="secondary", use_container_width=True):
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
                                
                                st.success("Contestação registrada! Status alterado para CONTESTADA.")
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
                        if st.button("✅ Confirmar Alteração", type="primary", use_container_width=True, key=f"confirmar_implantacao_{id_selecionado}"):
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
                                
                                st.success(f"✅ Status alterado para: {novo_status} (Contexto: {contexto_ativo})")
                                st.session_state.modo_implantacao = False
                                time.sleep(1)
                                st.rerun()

                    with col_cancelar:
                        if st.button("❌ Cancelar", use_container_width=True, key=f"cancelar_implantacao_{id_selecionado}"):
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
                        if st.button("💾 Salvar Rota Manual", type="primary", use_container_width=True, key=f"salvar_manual_{id_selecionado}"):
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
                                    df_atualizado = pd.read_sql_query(
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
                        if st.button("❌ Cancelar", use_container_width=True, key=f"cancelar_manual_{id_selecionado}"):
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
                        
                        # Cria mapa centralizado no ponto médio entre Casa e Trabalho
                        m = folium.Map(
                            location=[(lat_c + lat_t) / 2, (lon_c + lon_t) / 2],
                            zoom_start=13, 
                            control_scale=True
                        )
                        
                        # ── MUDANÇA 1: Estilo Colorido e Detalhado (OpenStreetMap) ──
                        folium.TileLayer('OpenStreetMap').add_to(m)

                        # Marcador C (CASA) - Azul
                        folium.Marker(
                            [lat_c, lon_c],
                            icon=folium.DivIcon(html="""
                            <div style="background:linear-gradient(135deg,#00D4FF,#0EA5E9);width:36px;height:36px;
                                        border-radius:50%;border:2px solid rgba(255,255,255,0.8);display:flex;
                                        align-items:center;justify-content:center;font-weight:800;color:#0A0E1A;
                                        font-size:16px;box-shadow:0 0 12px rgba(0,212,255,0.8);">C</div>
                        """, icon_anchor=(18, 18)), 
                            tooltip="🏠 Residência"
                        ).add_to(m)

                        # Marcador T (TRABALHO) - Roxo
                        folium.Marker(
                            [lat_t, lon_t],
                            icon=folium.DivIcon(html="""
                            <div style="background:linear-gradient(135deg,#7C3AED,#A855F7);width:36px;height:36px;
                                        border-radius:50%;border:2px solid rgba(255,255,255,0.8);display:flex;
                                        align-items:center;justify-content:center;font-weight:800;color:white;
                                        font-size:16px;box-shadow:0 0 12px rgba(124,58,237,0.8);">T</div>
                        """, icon_anchor=(18, 18)), 
                            tooltip="🏢 Trabalho"
                        ).add_to(m)

                        # Linha conectando Casa e Trabalho
                        folium.PolyLine(
                            locations=[[lat_c, lon_c], [lat_t, lon_t]],
                            color="#00D4FF", 
                            weight=4, 
                            opacity=0.8,
                            dash_array="8 8"
                        ).add_to(m)

                        # ── MUDANÇA 2: Altura aumentada para 700 pixels ──
                        st_folium(m, height=700, use_container_width=True)

        # ── LISTA DE PESQUISA ────────────────────────────────────────────────────
        else:
            st.markdown("""
            <h1 style="color:#1E293B;
                    font-size:26px;font-weight:800;margin-bottom:4px;">
                Pesquisar Consultas
            </h1>
            <p style="color:#666666;font-size:13px;margin-bottom:20px;">Localize aprendizes por CPF, nome ou matrícula</p>
            """, unsafe_allow_html=True)

            modalidade_pesquisa = st.radio(
                "Modalidade:",
                ["🏠 Casa × Trabalho", "📚 Casa × Curso"],
                horizontal=True,
                key="modalidade_pesquisa_radio"
            )

            st.markdown("<hr style='border-color:rgba(0,212,255,0.1);'>", unsafe_allow_html=True)

            tab_cpf, tab_nome, tab_mat = st.tabs(["🔍 Por CPF", "👤 Por Nome", "🪪 Por Matrícula"])

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
                                st.session_state.resultado_busca = pd.read_sql_query(
                                    "SELECT * FROM jovens_rotas WHERE cpf = ?", conexao, params=(cpf_limpo,))
                                
                                if st.session_state.resultado_busca.empty:
                                    st.warning("❌ Nenhum resultado encontrado para este CPF.")
                                st.session_state.detalhes_abertos = False
                                conexao.close()
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro na busca: {str(e)}")

            with tab_nome:
                with st.form(key="form_nome"):
                    nome_busca = st.text_input("Nome completo", placeholder="Digite o nome...")
                    if st.form_submit_button("Pesquisar", type="primary"):
                        try:
                            conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                            st.session_state.resultado_busca = pd.read_sql_query(
                                "SELECT * FROM jovens_rotas WHERE nome LIKE ?", conexao, params=(f"%{nome_busca}%",))
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
                            st.session_state.resultado_busca = pd.read_sql_query(
                                "SELECT * FROM jovens_rotas WHERE matricula = ?", conexao, params=(mat_busca,))
                            if st.session_state.resultado_busca.empty:
                                st.warning("❌ Nenhum resultado encontrado para esta matrícula")
                            st.session_state.detalhes_abertos = False
                            conexao.close()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro na busca: {str(e)}")

            if st.session_state.resultado_busca is not None and not st.session_state.resultado_busca.empty:
                st.markdown("<hr style='border-color:rgba(0,212,255,0.1);margin:20px 0;'>", unsafe_allow_html=True)
                st.markdown("<p style='color:#444c9b;font-size:12px;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;'>📋 Resultados da Busca</p>", unsafe_allow_html=True)

                #Auto-Refresh na lista de resultados na aba de pesquisa :)
            try:
                            ids_lista = st.session_state.resultado_busca['id'].tolist()
                            if ids_lista:
                                conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                                placeholders = ','.join('?' for _ in ids_lista)
                                st.session_state.resultado_busca = pd.read_sql_query(
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
                for _, row in st.session_state.resultado_busca.iterrows():
                    
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

                # Camuflador do CPF
                cpf_str = str(row['cpf']).zfill(11)
                cpf_mask = f"***.***.{cpf_str[6:9]}-{cpf_str[9:11]}"

                col_info, col_btn = st.columns([10, 2])
                with col_info:
                    st.markdown(f"""
                        <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:8px;padding:12px;">
                            <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
                                <p style="margin:0;color:#444c9b;font-weight:700;font-size:16px;">
                                    {row['nome']}
                                </p>
                                <span style="background:rgba({status_bg},0.15);color:{status_color};padding:2px 8px;border-radius:20px;font-size:12px;font-weight:700;">
                                    {status_exib}
                                </span>
                            </div>
                            <p style="margin:0;color:#666666;font-size:13px;">
                                PRÉ-ADM · CPF: {cpf_mask} · Matrícula: {row.get('matricula', 'N/A')}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_btn:
                        st.write("") # Espaço para alinhar o botãozin
                        if st.button("Abrir Consulta →", key=f"btn_abrir_{row['id']}", type="primary", use_container_width=True):
                            st.session_state.resultado_busca = pd.DataFrame([row])
                            st.session_state.detalhes_abertos = True
                            st.query_params['id_consulta'] = str(row['id'])
                            st.session_state.contexto_salvo = st.session_state.modalidade_pesquisa_radio
                            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TELA 2 — CADASTRAR NOVO JOVEM
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "Cadastrar Novo Jovem":

        st.markdown("""
            <div style="display:flex; align-items:center; gap:15px; margin-bottom:25px;">
                <svg viewBox="0 0 378 708.82" width="40" height="75">
                <defs><style>.s1-1{fill:#402fdd;} .s1-1,.s1-2,.s1-3,.s1-4{stroke-width:0px;} .s1-3{fill:#ed9e06;} .s1-4{fill:#231f20;}</style></defs>
                <g><path class="s1-4" d="m201.23,256.63c8.57,0,8.59-13.95,0-13.95s-8.59,13.95,0,13.95h0Z"/><path class="s1-4" d="m201.23,288.82c8.57,0,8.59-13.95,0-13.95s-8.59,13.95,0,13.95h0Z"/><path class="s1-3" d="m27.95,115.09c-4.81-1.19-7.19-4.51-10.93-9.68-2.67-3.69-15.67-33.45-15.96-36.85-.14-1.68-2.65-9.29.59-10.35,4.11-1.34,9.39,16.78,11.07,19.92-1.85-3.65-6.71-16.39-7.43-18.49-1.42-4.14-2.47-11.71-.94-12.39,4.89-2.18,7.45,5.97,8.28,7.15,1.09,1.54,8.65,16.82,8.65,16.82.04-.02.05-.06.04-.09-2.25-6.72-7.49-14.79-10.33-21.76-1.63-4-1.48-7.65,0-8.57,4.75-2.95,16.1,20.1,17.54,23.6-1.2-3.54-3.73-8.21-4.93-11.75-.56-1.65-3.33-10.55-2.17-12.12,4.47-6.03,7.59,4.26,8.85,7.24.68,1.6,3.68,6.61,4.26,8.22,2.85,7.95,4.64,11.49,8.04,19.17,1.51-3.02,2.54-5.08,4.04-8.1,1.05-2.12,2.22-4.35,4.22-5.68,2-1.32,5.06-1.14,5.73.92.35,1.06-.03,2.29-.35,3.44-1.61,5.53-2.52,11.17-2.7,16.75-.15,4.56,2.15,11.74-1.31,15.19l8.14,11.57-25.53,18.44s-6.87-12.58-6.87-12.58Z"/><path class="s1-2" d="m5.79,62.37c2.67,6.4,5.49,12.73,8.45,18.97.35.72,1.36.09,1.03-.63-2.96-6.25-5.78-12.58-8.45-18.97-.13-.31-.55-.38-.81-.23-.3.18-.35.55-.21.85h0Z"/><path class="s1-2" d="m11.46,52.37c2.97,6.15,5.86,12.33,8.67,18.56.8,1.77,1.59,3.55,2.38,5.34.32.73,1.35.09,1.03-.63-2.76-6.25-5.6-12.46-8.53-18.64-.84-1.75-1.67-3.52-2.52-5.26-.35-.72-1.37-.08-1.03.63h0Z"/><path class="s1-2" d="m21.46,51.11c2.42,5.45,4.84,10.89,7.26,16.34.69,1.56,1.38,3.12,2.08,4.68.33.73,1.35.09,1.03-.63-2.42-5.45-4.84-10.89-7.26-16.34-.69-1.56-1.38-3.12-2.08-4.68-.33-.73-1.35-.09-1.03.63h0Z"/><path class="s1-3" d="m319.04,612.74c6.85,5.73,20.79,22.23,22.92,27.85,7.25,19.13,17.27,49.96,28.72,67.62.2-33.32,2.91-67.81,7.24-99.19-2.33-1.94-5.73-1.1-8.59-1.9-2.47-.69-4.46-2.57-6.35-4.39-3.82-3.68-8.96-15.05-8.96-15.05-11.16,7.22-24.83,18.45-35.99,25.67"/><path class="s1-3" d="m82.53,489.18c2.98,5.85,5.96,11.69,8.95,17.54,1.24,2.42,2.48,4.87,3.05,7.55.75,3.61.24,7.35-.26,11.01-3.08,22.8-4.79,45.82-5.1,68.85,22.78-24.49,31.45-59.7,49.35-88.35-2.32-3.46-6.97-4.51-9.27-7.99-1.04-1.57-1.47-3.48-1.89-5.34-1.23-5.44-2.45-10.86-3.67-16.3-13.35,4.19-26.69,8.38-40.04,12.57-.48.15-1.03.35-1.23.85s.36,1.19.76.85"/><path class="s1-1" d="m158.84,246.8c-31.59-9.26-62.23-24.23-86.25-47.75-21.46-21.01-36.85-48.01-49.67-75.77,14.31-6.57,27.91-14.85,40.47-24.6,2.91,5.74,5.87,11.49,9.71,16.58,4.01,5.33,8.89,9.83,13.74,14.32,27.52,25.51,54.58,51.57,81.17,78.15.98.98,2,2.03,2.36,3.4.31,1.15.11,2.38-.11,3.56-2.08,11.65-4.87,23.17-8.34,34.45-.8-1.13-1.86-2.06-3.06-2.69"/><path class="s1-2" d="m229.82,302.11c12.65,12.48,20.15,36.99,13.32,65.81-.59,2.5,23.42,71.58,44.73,110.05,21.31,38.47,47.52,73.64,73.64,108.66-7.79,5.4-15.71,10.58-23.75,15.55-7.13,4.41-24.21,12.48-24.21,12.48,0,0-76.44-93.06-108.1-169.29-13.55-32.6-33.19-62.28-43.59-96.14.64,2.78,1.27,5.57,1.91,8.35-23.55-5.11-45.97-6.95-68.45-15.94,6.5,47.81,18.15,89.46,36,133.95-18.34,5.57-36.67,11.15-55.01,16.72-14.36-24.69-22.31-52.85-30.02-80.65-9.89-35.68-19.72-73.14-12.65-109.55,1.49-7.67,3.88-15.49,9.02-21.16,9.96-11.02,26.56-10.59,40.86-8.47,15.33,2.27,30.52,5.56,45.45,9.86,5.87,1.69,11.73,3.55,17.18,6.39,5.25,2.74,18.5-7.15,23.66-4.23,20.38,11.5,32.31,15.36,54.43,8.26"/><path class="s1-3" d="m173.64,193.71c3.47-8.21,7.84-16.95,12.4-22.96-5.09,2.88-11.95.3-15.1-4.81s-1.08-16.84,1.29-22.39c2.36-5.55,3.03-10.43,7.66-14.06,2.95-2.32,7.91.93,11.53.23,3.62-.71,7.69.22,10.11,3.15,2.24,2.71,2.68,6.55,2.65,10.15-.04,5.09,3.57,3.76,2.8,8.79-2.12,13.86-8.62,34.1-10.74,47.96-.08.51-.22,1.11-.67,1.31-.32.14-.67.03-.99-.09-6.98-2.42-13.95-4.85-20.94-7.26"/><path class="s1-1" d="m230.92,303.11c-5.51-29.95-11.32-56.94-16.84-86.89-.75-4.08-9.13-28.62-9.13-28.62-9.9,6.51-25.51,3.74-27.1,1.4-2.53-3.72-7.98,10.31-11.8,12.47-6.46,3.67.44,11.7-2.61,18.75-5.22,12.1-7.65,25.29-9.68,38.41-1.53,9.86-2.84,19.76-3.95,29.69-.12,1.03-.23,2.09.05,3.09.45,1.68,1.86,2.85,3.24,3.84,12.7,9.03,28.66,11.29,43.98,11.26,11.35-.02,22.69-1.16,33.83-3.4"/></g>
                </svg>
                <h1 style="margin:0; color:#444c9b; font-size:28px;">Cadastrar Novo Jovem</h1>
            </div>
        """, unsafe_allow_html=True)

        tab_manual, tab_massa = st.tabs(["✍️ Cadastro Manual", "📂 Importação em Massa"])

        with tab_manual:
            st.markdown("""
            <div style="background:#FFFFFF;border:1px solid #E5E7EB;
                        border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                <p style="color:#666666;font-size:12px;margin:0;">
                    Preencha todos os campos. O CPF deve conter 11 dígitos numéricos.
                </p>
            </div>
            """, unsafe_allow_html=True)

            with st.form(key="form_novo_jovem"):
                col_n, col_c, col_m = st.columns([2, 1, 1])
                nome_input      = col_n.text_input("Nome Completo")
                cpf_input       = col_c.text_input("CPF (11 dígitos)", max_chars=11)
                matricula_input = col_m.text_input("Matrícula")

                col_cep1, col_cep2 = st.columns(2)
                cep_casa_input = col_cep1.text_input("CEP da Residência", max_chars=8)
                cep_trab_input = col_cep2.text_input("CEP do Trabalho", max_chars=8)

                botao_salvar = st.form_submit_button("💾 Salvar na Base de Dados", type="primary")

        if botao_salvar:
            if not all([nome_input, cpf_input, cep_casa_input, cep_trab_input, matricula_input]):
                st.error("⚠️ Preencha todos os campos antes de salvar.")
            else:
                digitos_cpf = ''.join(filter(str.isdigit, cpf_input))
                if len(digitos_cpf) != 11:
                    st.error("❌ CPF deve conter exatamente 11 dígitos numéricos.")
                elif len(set(digitos_cpf)) == 1:
                    st.error("❌ CPF inválido: todos os dígitos são iguais.")
                elif cpf_ja_existe(digitos_cpf):
                    st.error(f"❌ CPF {digitos_cpf} já está cadastrado no sistema.")
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
                                
                                # ── GERAÇÃO PERFEITA DE ID (MANUAL) ──
                                cursor.execute("SELECT MAX(CAST(id AS INTEGER)) FROM jovens_rotas")
                                max_id = cursor.fetchone()[0]
                                novo_id = 1 if max_id is None else int(max_id) + 1
                                
                                cursor.execute("""
                                    INSERT INTO jovens_rotas (id, nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
                                    VALUES (?, ?, ?, ?, ?, ?, 'Otimizado')
                                """, (novo_id, nome_input, digitos_cpf, cep_casa_input, cep_trab_input, matricula_input))
                                
                                conexao.commit()
                                conexao.close()
                                st.success(f"✅ {nome_input} (Matrícula: {matricula_input}) cadastrado com sucesso! (ID: {novo_id})")
                            except Exception as e:
                                st.error(f"❌ Erro ao salvar: {e}")

        with tab_massa:
            st.markdown("""
            <div style="background:rgba(248,174,40,0.1);border:1px solid #E5E7EB;
                        border-radius:12px;padding:16px;margin-bottom:16px;">
                <p style="color:#666666;font-size:13px;margin:0;">
                    💡 A planilha deve conter as colunas:
                    <strong style="color:#f8ae28;">nome, cpf, cep_casa, cep_trabalho, matricula</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)

            arquivo_upload = st.file_uploader("Arraste o arquivo Excel (.xlsx) ou CSV", type=["xlsx","csv"])

            if arquivo_upload is not None:
                try:
                    if arquivo_upload.name.endswith('.csv'):
                        df_upload = pd.read_csv(arquivo_upload, sep=';', dtype=str)
                    else:
                        df_upload = pd.read_excel(arquivo_upload, dtype=str)

                    df_upload.columns = df_upload.columns.str.lower().str.strip()

                    if 'matricula' not in df_upload.columns:
                        st.error("❌ O arquivo precisa ter a coluna 'matricula'.")
                    else:
                        df_upload['status_rota'] = "Otimizado"
                        st.markdown("<p style='color:#94A3B8;font-size:13px;'>Pré-visualização:</p>", unsafe_allow_html=True)
                        st.dataframe(df_upload.head(), use_container_width=True)

                        if st.button("🚀 Importar para a Base de Dados", type="primary"):
                            with st.spinner("Importando..."):
                                df_limpo = df_upload[['nome','cpf','cep_casa','cep_trabalho','matricula','status_rota']].copy()
                                
                                # Limpa os CPFs do Excel
                                df_limpo['cpf'] = df_limpo['cpf'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(11)
                                
                                conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                                
                                # ── GERAÇÃO PERFEITA DE ID (EM MASSA) ──
                                cursor = conexao.cursor()
                                cursor.execute("SELECT MAX(CAST(id AS INTEGER)) FROM jovens_rotas")
                                max_id = cursor.fetchone()[0]
                                start_id = 1 if max_id is None else int(max_id) + 1
                                
                                df_limpo.insert(0, 'id', range(start_id, start_id + len(df_limpo)))
                                
                                df_limpo.to_sql('jovens_rotas', conexao, if_exists='append', index=False)
                                conexao.close()
                                
                                st.success(f"✅ {len(df_limpo)} aprendizes importados com sucesso!")
                                time.sleep(2)
                                st.rerun()

                except Exception as e:
                    st.error(f"❌ Erro ao ler o arquivo: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TELA 3 — TRIAGEM DE FICHAS
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "🗂️ Triagem de Fichas":

        st.markdown("""
        <div style="display:flex; align-items:center; gap:15px; margin-bottom:25px;">
            <svg viewBox="0 0 24 24" width="50" height="50" fill="none" stroke="#444c9b" stroke-width="2">
                <path d="M9 11l3 3L22 4"></path>
                <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <h1 style="margin:0; color:#444c9b; font-size:28px;">Triagem de Fichas Cadastrais</h1>
        </div>
        <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-left:4px solid #444c9b;
                    border-radius:14px;padding:20px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
            <p style="color:#666666;font-size:14px;margin:0;">
                Analise as candidaturas do portal do jovem, revise os documentos e integre os aprovados ao sistema de mobilidade.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ── FILTROS E PESQUISA ──
        col_pesquisa, col_status = st.columns([2, 1])
        
        with col_pesquisa:
            filtro_nome = st.text_input("🔍 Pesquisar por Nome ou CPF", placeholder="Digite o nome ou CPF...")
        
        with col_status:
            filtro_status = st.selectbox("Status", ["Pendente", "Aprovado", "Reprovado", "Todos"], index=0)

        st.markdown("<hr style='border-color:#E2E8F0;margin:20px 0;'>", unsafe_allow_html=True)

        # ── BUSCA FICHAS DIRETAMENTE NO BANCO ──
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DB_PATH = os.path.join(BASE_DIR, '..', 'mobilidade_renapsi.db')
        
        try:
            conexao = sqlite3.connect(DB_PATH)
            query = "SELECT * FROM fichas_cadastrais WHERE 1=1"
            params = []
            
            if filtro_status != "Todos":
                query += " AND status_aprovacao = ?"
                params.append(filtro_status)
                
            if filtro_nome:
                query += " AND (nome_completo LIKE ? OR cpf LIKE ?)"
                params.extend([f"%{filtro_nome}%", f"%{filtro_nome}%"])
                
            df_fichas = pd.read_sql_query(query, conexao, params=params)
            conexao.close()
        except Exception as e:
            st.error(f"Erro ao carregar banco de dados: {e}")
            df_fichas = pd.DataFrame()

        if df_fichas.empty:
            st.info("📭 Nenhuma ficha encontrada com os filtros selecionados.")
        else:
            st.markdown(f"""
            <div style="background:rgba(68,76,155,0.1);border:1px solid rgba(68,76,155,0.3);
                        border-radius:10px;padding:12px;margin-bottom:16px;text-align:center;">
                <p style="color:#444c9b;font-size:14px;margin:0;text-transform:uppercase;font-weight:600;">
                    📋 {len(df_fichas)} ficha(s) encontrada(s)
                </p>
            </div>
            """, unsafe_allow_html=True)

            # ── EXIBIÇÃO DE FICHAS (Apenas 1 Loop For) ──
            for idx, (_, ficha) in enumerate(df_fichas.iterrows()):
                ficha_id = ficha['id']
                nome_completo = ficha['nome_completo']
                cpf_raw = str(ficha['cpf']).zfill(11)
                cpf_mask = f"***.***.{cpf_raw[6:9]}-{cpf_raw[9:11]}"
                status_aprovacao = ficha['status_aprovacao']
                
                if status_aprovacao == "Aprovado": emoji_status = "✅"
                elif status_aprovacao == "Reprovado": emoji_status = "❌"
                else: emoji_status = "⏳"

                with st.expander(f"📋 {nome_completo} | Status: {emoji_status} {status_aprovacao} | CPF: {cpf_mask}", expanded=False):
                    # 4 Colunas corretas
                    col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.5, 1])

                    with col1:
                        st.markdown("""<p style="color:#444c9b;font-size:14px;text-transform:uppercase;font-weight:600;">👤 Pessoais</p>""", unsafe_allow_html=True)
                        st.write(f"**Nome Social:** {ficha.get('nome_social', 'N/A')}")
                        st.write(f"**Data de Nasc.:** {ficha.get('data_nascimento', 'N/A')}")
                        st.write(f"**Gênero:** {ficha.get('identidade_genero', 'N/A')}")
                        st.write(f"**Raça:** {ficha.get('raca', 'N/A')}")
                        st.write(f"**Uniforme:** {ficha.get('tamanho_uniforme', 'N/A')}")

                    with col2:
                        st.markdown("""<p style="color:#444c9b;font-size:14px;text-transform:uppercase;font-weight:600;">🏠 Contato/Endereço</p>""", unsafe_allow_html=True)
                        st.write(f"**CEP:** {ficha.get('cep', 'N/A')}")
                        st.write(f"**Endereço:** {ficha.get('endereco_completo', 'N/A')}")
                        st.write(f"**Cidade:** {ficha.get('cidade_estado', 'N/A')}")
                        
                        # ── MÁGICA DO WHATSAPP ──
                        telefone_original = str(ficha.get('tel_jovem', 'N/A'))
                        if telefone_original != 'N/A' and telefone_original.strip():
                            # Limpa tudo que não for número (tira parênteses, traços, espaços)
                            telefone_limpo = ''.join(filter(str.isdigit, telefone_original))
                            
                            # Adiciona o código do Brasil (55) se o jovem não tiver colocado
                            if telefone_limpo and not telefone_limpo.startswith('55'):
                                telefone_limpo = '55' + telefone_limpo
                                
                            link_wpp = f"https://wa.me/{telefone_limpo}"
                            
                            st.markdown(f"""
                                <p style='margin:2px 0; font-size:15px;'>
                                    <strong>Telefone:</strong> {telefone_original} 
                                    <a href='{link_wpp}' target='_blank' style='text-decoration:none; background-color:#25D366; color:white; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:bold; margin-left:8px; display:inline-flex; align-items:center; gap:4px;'>
                                        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                                            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51a12.8 12.8 0 0 0-.57-.01c-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/>
                                        </svg>
                                        Conversar
                                    </a>
                                </p>
                            """, unsafe_allow_html=True)
                        else:
                            st.write(f"**Telefone:** {telefone_original}")
                            
                        st.write(f"**E-mail:** {ficha.get('email_jovem', 'N/A')}")

                    with col3:
                        st.markdown("""<p style="color:#444c9b;font-size:14px;text-transform:uppercase;font-weight:600;">👨‍👩‍👧 Família</p>""", unsafe_allow_html=True)
                        st.write(f"**Mãe:** {ficha.get('nome_mae', 'N/A')} ({ficha.get('ocupacao_mae', 'N/A')} - {ficha.get('estado_civil_mae', 'N/A')})")
                        st.write(f"**Pai:** {ficha.get('nome_pai', 'N/A')} ({ficha.get('ocupacao_pai', 'N/A')} - {ficha.get('estado_civil_pai', 'N/A')})")
                        if ficha.get('nome_resp'):
                            st.write(f"**Resp. Legal:** {ficha.get('nome_resp')}")
                        st.write(f"**Dependentes:** {ficha.get('tem_dependentes', 'N/A')}")

                    with col4:
                        st.markdown("""<p style="color:#444c9b;font-size:14px;text-transform:uppercase;font-weight:600;">📄 Documentos</p>""", unsafe_allow_html=True)
                        
                        documentos = [
                            ('path_comp_residencia', '🏠 Comp. Residência'),
                            ('path_rg', '🪪 RG'),
                            ('path_conta_salario', '🏦 Conta Salário'),
                            ('path_titulo', '🗳️ Título Eleitor'),
                            ('path_reservista', '⚔️ Reservista'),
                            ('path_casamento', '💍 Certidão Casamento'),
                            ('path_cert_nasc_dep', '👶 Cert. Nasc. Dependente'),
                            ('path_vacina_dep', '💉 Vacina Dependente'),
                        ]
                        
                        for campo_path, label_doc in documentos:
                            caminho_arquivo = ficha.get(campo_path, '')
                            if caminho_arquivo and os.path.exists(caminho_arquivo):
                                with open(caminho_arquivo, 'rb') as f:
                                    arquivo_bytes = f.read()
                                st.download_button(
                                    label=f"⬇️ {label_doc}",
                                    data=arquivo_bytes,
                                    file_name=os.path.basename(caminho_arquivo),
                                    mime="application/octet-stream",
                                    key=f"dl_{ficha_id}_{campo_path}",
                                    use_container_width=True
                                )

                    st.markdown("<hr style='border-color:#E2E8F0;margin:20px 0;'>", unsafe_allow_html=True)

                    # ── BOTÕES DE AÇÃO ──
                    col_reprovar, col_aprovar = st.columns([1, 1])

                    with col_reprovar:
                        if st.button("❌ Reprovar", key=f"reprovar_{ficha_id}", use_container_width=True, type="secondary"):
                            conn = sqlite3.connect(DB_PATH)
                            conn.execute("UPDATE fichas_cadastrais SET status_aprovacao = 'Reprovado' WHERE id = ?", (ficha_id,))
                            conn.commit()
                            conn.close()
                            st.success("Ficha Reprovada.")
                            time.sleep(1)
                            st.rerun()

                    with col_aprovar:
                        if st.button("✅ Aprovar e Enviar p/ Mobilidade", key=f"aprovar_{ficha_id}", use_container_width=True, type="primary"):
                            try:
                                conn = sqlite3.connect(DB_PATH)
                                conn.execute("UPDATE fichas_cadastrais SET status_aprovacao = 'Aprovado' WHERE id = ?", (ficha_id,))
                                
                                cursor = conn.cursor()
                                cursor.execute("SELECT id FROM jovens_rotas WHERE cpf = ?", (cpf_raw,))
                                if cursor.fetchone():
                                    st.warning("⚠️ Jovem já existe no painel de mobilidade!")
                                else:
                                    # ── MÁGICA DO ID: Descobre qual o último ID e soma +1 ──
                                    cursor.execute("SELECT MAX(CAST(id AS INTEGER)) FROM jovens_rotas")
                                    max_id = cursor.fetchone()[0]
                                    novo_id = 1 if max_id is None else int(max_id) + 1

                                    conn.execute("""
                                        INSERT INTO jovens_rotas (id, nome, cpf, email, celular, cep_casa, numero_casa, status_rota)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, 'Aguardando Rota')
                                    """, (
                                        novo_id,
                                        nome_completo, 
                                        cpf_raw, 
                                        ficha.get('email_jovem', ''), 
                                        ficha.get('tel_jovem', ''), 
                                        ficha.get('cep', ''), 
                                        ficha.get('endereco_completo', '')
                                    ))
                                    st.success("✅ Jovem aprovado e adicionado à fila de roteirização!")
                                
                                conn.commit()
                                conn.close()
                                time.sleep(2)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao aprovar: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TELA 4 — BANCO DE DADOS
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "Banco de Dados":

        st.markdown("""
            <div style="display:flex; align-items:center; gap:15px; margin-bottom:25px;">
                <svg viewBox="0 0 603.93 431.92" width="60" height="43">
                <defs><style>.s3-1{fill:#d42c4d;} .s3-2{fill:#231f20;} .s3-3{fill:#ed9e06;}</style></defs>
                <g><path class="s3-3" d="M435.68,157.79c-14.38-13.19-35.99-16.6-54.92-11.83-18.92,4.77-35.34,16.81-48.67,31.06-22.83,24.4-38.08,58.56-31.1,91.24s41.76,59.61,73.83,50.23c-13.59,34.44-34.7,71.48-44.18,107.27,49.38,8.4,110.4,2.36,157.74-14-10.43-37.73-15.84-76.84-16.05-115.99-.14-27,2.16-54.26-2.74-80.81s-18.44-53.16-42.24-65.9"/><path d="M448.44,195.49c3.25,14.92,2.29,30.77-2.74,45.38,24.3-11.58,39.67-13.09,35.83-64.93-1.92-25.93-26.05-47.54-52.56-51.27-31.6-4.44-61.47,14.21-90.58,27.74-5.8,2.69-11.99,5.27-18.34,4.82s-12.77-4.95-13.01-11.13c-7.66,14.57-5.11,33.44,6.12,45.24,12.56,13.21,33.12,16.48,51.74,14.33s36.44-8.86,54.83-12.6c10.15-2.06,22.05-2.74,29.27,4.28"/><path class="s3-1" d="M358.23,359.33c-4.64,13.39,8.14,26.63,19.7,34.37,15.91,10.66,35.24,9.55,48.17,6.46,18.81-4.49,22.49-4.98,40.76-20.32,3.34-2.8,9.91-14.32,9.91-14.32,4.25-1.19,60.85-5.94,84.69,6.58,22.31,11.71,40.19,32.29,41.96,57.43,0,0,1.15-4.8,0,0-53.9,1.88-321.41,2.58-392.45,1.31,0,0,.21-17.77,20.37-35.66,29.63-26.3,59.03-36.46,92.57-36.3,12.86.06,25.49.19,34.32.45"/><path class="s3-3" d="M453.18,232.1c1.2-3.27,4.31-5.52,7.58-6.72,8.78-3.2,19.3.38,25.03,7.76,5.73,7.38,6.74,17.87,3.4,26.6-3.09,8.08-10.02,14.86-18.48,16.68-8.46,1.82-18.12-2.01-22.14-9.66"/><path class="s3-3" d="M131.58,119.01c-2-12.26.63-24.74,3.25-36.88,2.09-9.66,4.17-19.31,6.26-28.97,1.67-7.72,3.63-15.97,9.5-21.26s16.97-5.29,20.27,1.89c-13.34,25.91-24.15,53.12-32.23,81.12-2.92-.02-5.83-.04-8.75-.07"/><path class="s3-3" d="M115.62,76.65c-.77-14.86,5.31-29.14,11.73-42.56,2.52-5.26,5.2-10.62,9.51-14.56,4.3-3.94,10.62-6.22,16.1-4.22.66.24,1.32.55,1.79,1.07,1.22,1.34.79,3.43.3,5.17-7.8,27.6-13.85,55.7-18.09,84.06-12.99-10.5-23.97-23.47-32.18-38.01.98-.55,2.41.17,2.56,1.28"/><path class="s3-3" d="M124.86,177.55c11.67-14.04,20-54.48,14.64-71.93s-16.28-32.57-27.01-47.33c-6.55-9.01-13.1-18.02-19.65-27.03-7.64-10.51-18.7-25.49-27.33-29.46-10.43,9.26-7.36,21.07-4.14,28.51,3.22,7.45,8.81,13.56,13.37,20.27,6.06,8.92,10.36,19.04,12.56,29.6,1.62,7.79,2.04,16.23-1.43,23.38-3.47,7.16-11.78,12.41-19.43,10.25-7.92-2.24-12.06-11-13.54-19.1s-1.4-16.73-5.26-24c-5.55-10.43-19.43-15.51-30.4-11.12,11.9,26.61,5.29,58.12,14.19,85.88,5.09,15.89,15.32,30.08,28.78,39.94,3.27,2.4,6.76,4.56,10.57,5.94,16.69,6.05,35.78-3.76,52.77,1.41,3.89-12.36-2.57-2.85,1.32-15.21"/><path class="s3-1" d="M2.36,172.23c35.28-.27,102.3-4.07,137.58-3.28-2.52,66.19,7.33,132.83,28.91,195.45,8.61,24.98,19.61,41.59,30.86,66.44-55.56-1.58-99.86,2.9-148.45.18C14.93,352.15-7.59,258.49,2.36,172.23"/><path class="s3-2" d="M154.01,15.81c-4.83,13.22-9.01,26.67-12.12,40.4-3.09,13.64-5.11,27.48-6.48,41.39-.21,2.11,3.1,2.1,3.3,0,2.73-27.79,8.9-54.68,18.48-80.91.73-2-2.46-2.86-3.18-.88h0Z"/><path class="s3-2" d="M66.11,2.85c16.58,18.05,31.82,37.3,45.55,57.61,6.73,9.95,13.25,20.12,19.08,30.62,2.99,5.38,5.55,10.97,6.9,17,1.36,6.05,1.58,12.3,1.26,18.48-.74,14.24-3.97,28.38-8.93,41.73-.74,1.99,2.45,2.85,3.18.88,4.53-12.18,7.48-24.91,8.7-37.84,1.17-12.47.12-24.7-5.27-36.13-5.25-11.13-12.27-21.62-19.03-31.87-6.79-10.29-13.97-20.33-21.51-30.09-8.72-11.29-17.92-22.21-27.57-32.72-1.44-1.57-3.77.77-2.33,2.33h-.03Z"/><path class="s3-2" d="M58.79,8.1c1.8,5.68,4.92,11.7,10.71,14.14,4.95,2.09,10.85,1.09,14.16-3.3,1.28-1.7-1.59-3.34-2.85-1.67-2.54,3.38-7.7,3.34-11.1,1.4-4.15-2.38-6.35-7.08-7.74-11.45-.64-2.02-3.83-1.16-3.18.88h0Z"/></g>
                </svg>
                <h1 style="margin:0; color:#444c9b; font-size:28px;">Banco de Dados</h1>
            </div>
        """, unsafe_allow_html=True)

        # ── CAMINHOS ABSOLUTOS CORRIGIDOS ──
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DB_PATH = os.path.join(BASE_DIR, '..', 'mobilidade_renapsi.db')
        BACKUP_PATH = os.path.join(BASE_DIR, '..', 'mobilidade_renapsi_backup.db')

        # Carrega dados do banco
        try:
            conexao = sqlite3.connect(DB_PATH)
            df_banco = pd.read_sql_query("SELECT * FROM jovens_rotas", conexao)
            conexao.close()
        except Exception as e:
            st.error(f"Erro ao carregar banco de dados: {e}")
            df_banco = pd.DataFrame()

        # Tabs para diferentes operações
        tab_visualizar, tab_adicionar_coluna, tab_excluir, tab_backup = st.tabs([
            "📊 Visualizar & Editar",
            "➕ Adicionar Coluna",
            "🚨 Excluir Registro",
            "💾 Backup"
        ])

        # ── TAB 1: VISUALIZAR E EDITAR ──
        with tab_visualizar:
            st.markdown("""
            <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-left:4px solid #444c9b;
                        border-radius:14px;padding:20px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                <h3 style="margin:0 0 4px;color:#444c9b;">📊 Tabela de Jovens</h3>
                <p style="color:#666666;font-size:13px;margin:0;">
                    Edite os dados diretamente na tabela. Clique em qualquer célula para modificar.
                </p>
            </div>
            """, unsafe_allow_html=True)

            df_editado = st.data_editor(
                df_banco,
                use_container_width=True,
                num_rows="dynamic",
                key="editor_banco",
                hide_index=False
            )

            st.markdown("<br>", unsafe_allow_html=True)

            col_save, col_info = st.columns([1, 4])
            with col_save:
                if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                    try:
                        df_editado['cpf'] = df_editado['cpf'].astype(str).str.zfill(11)
                        
                        conexao = sqlite3.connect(DB_PATH)
                        df_editado.to_sql('jovens_rotas', conexao, if_exists='replace', index=False)
                        conexao.close()

                        import shutil
                        shutil.copy(DB_PATH, BACKUP_PATH)

                        st.success("✅ Alterações salvas com sucesso! Backup criado automaticamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar: {str(e)}")

            with col_info:
                st.markdown(f"""
                <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);
                            border-radius:10px;padding:12px;text-align:center;">
                    <p style="color:#10B981;font-size:12px;margin:0;text-transform:uppercase;">
                        Total de Registros: <strong>{len(df_editado)}</strong>
                    </p>
                </div>
                """, unsafe_allow_html=True)

        # ── TAB 2: ADICIONAR COLUNA ──
        with tab_adicionar_coluna:
            st.markdown("""
            <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-left:4px solid #444c9b;
                        border-radius:14px;padding:20px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                <h3 style="margin:0 0 4px;color:#444c9b;">➕ Adicionar Nova Coluna</h3>
                <p style="color:#666666;font-size:13px;margin:0;">
                    Expanda a estrutura da tabela com novas colunas.
                </p>
            </div>
            """, unsafe_allow_html=True)

            col_nome, col_tipo = st.columns(2)
            with col_nome:
                nome_coluna = st.text_input("Nome da coluna", placeholder="ex: telefone_secundario")
            with col_tipo:
                tipo_coluna = st.selectbox("Tipo de dados", ["TEXT", "INTEGER", "REAL", "BLOB"])

            if st.button("➕ Adicionar Coluna", type="primary", use_container_width=True):
                if not nome_coluna.strip():
                    st.error("❌ Digite um nome para a coluna")
                else:
                    import re
                    SQL_KEYWORDS = {
                        "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
                        "TABLE", "DATABASE", "INDEX", "VIEW", "TRIGGER", "PROCEDURE",
                        "FUNCTION", "WHERE", "FROM", "JOIN", "LEFT", "RIGHT", "INNER",
                        "OUTER", "ON", "AND", "OR", "NOT", "IN", "EXISTS", "BETWEEN",
                        "LIKE", "IS", "NULL", "TRUE", "FALSE", "ORDER", "BY", "GROUP",
                        "HAVING", "LIMIT", "OFFSET", "UNION", "INTERSECT", "EXCEPT",
                        "CASE", "WHEN", "THEN", "ELSE", "END", "CAST", "AS", "DISTINCT",
                        "ALL", "ANY", "SOME", "CONSTRAINT", "PRIMARY", "KEY", "FOREIGN",
                        "UNIQUE", "CHECK", "DEFAULT", "COLLATE", "PRAGMA", "VACUUM",
                        "ANALYZE", "EXPLAIN", "PLAN", "QUERY", "TRANSACTION", "BEGIN",
                        "COMMIT", "ROLLBACK", "SAVEPOINT", "RELEASE", "ATTACH", "DETACH"
                    }
                    
                    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', nome_coluna):
                        st.error("❌ Nome da coluna inválido. Use apenas letras, números e underscore (_).")
                    elif len(nome_coluna) > 64:
                        st.error("❌ Nome da coluna muito longo (máximo 64 caracteres).")
                    elif nome_coluna.upper() in SQL_KEYWORDS:
                        st.error(f"❌ '{nome_coluna}' é uma palavra-chave SQL reservada. Escolha outro nome.")
                    else:
                        try:
                            conexao = sqlite3.connect(DB_PATH)
                            cursor = conexao.cursor()
                            cursor.execute(f"ALTER TABLE jovens_rotas ADD COLUMN {nome_coluna} {tipo_coluna}")
                            conexao.commit()
                            conexao.close()
                            st.success(f"✅ Coluna '{nome_coluna}' adicionada com sucesso!")
                            st.rerun()
                        except sqlite3.OperationalError as e:
                            if "already exists" in str(e):
                                st.error(f"❌ Coluna '{nome_coluna}' já existe na tabela.")
                            else:
                                st.error(f"❌ Erro ao adicionar coluna: {str(e)}")
                        except Exception as e:
                            st.error(f"❌ Erro inesperado: {str(e)}")

        # ── TAB 3: EXCLUIR REGISTRO ──
        with tab_excluir:
            st.markdown("""
            <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-left:4px solid #EF4444;
                        border-radius:14px;padding:20px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                <h3 style="margin:0 0 4px;color:#EF4444;">🚨 Excluir Registro</h3>
                <p style="color:#666666;font-size:13px;margin:0;">
                    ⚠️ Esta ação é irreversível. Certifique-se antes de confirmar.
                </p>
            </div>
            """, unsafe_allow_html=True)

            col_id, col_btn = st.columns([2, 1])
            with col_id:
                id_excluir = st.number_input("ID do registro a excluir", min_value=1, step=1)
            with col_btn:
                st.write("")
                st.write("")
                if st.button("🚨 Excluir", type="secondary", use_container_width=True):
                    try:
                        conexao = sqlite3.connect(DB_PATH)
                        cursor = conexao.cursor()
                        cursor.execute("DELETE FROM jovens_rotas WHERE id = ?", (id_excluir,))
                        conexao.commit()
                        conexao.close()
                        
                        import shutil
                        shutil.copy(DB_PATH, BACKUP_PATH)
                        
                        st.success(f"✅ Registro #{id_excluir} excluído com sucesso! Backup criado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao excluir: {str(e)}")

        # ── TAB 4: BACKUP ──
        with tab_backup:
            st.markdown("""
            <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-left:4px solid #444c9b;
                        border-radius:14px;padding:20px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                <h3 style="margin:0 0 4px;color:#444c9b;">💾 Gerenciamento de Backup</h3>
                <p style="color:#666666;font-size:13px;margin:0;">
                    Crie e gerencie cópias de segurança do banco de dados.
                </p>
            </div>
            """, unsafe_allow_html=True)

            col_b1, col_b2 = st.columns(2)

            with col_b1:
                if st.button("💾 Criar Backup Agora", type="primary", use_container_width=True):
                    try:
                        import shutil
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        backup_name = os.path.join(BASE_DIR, '..', f"mobilidade_renapsi_backup_{timestamp}.db")
                        shutil.copy(DB_PATH, backup_name)
                        st.success(f"✅ Backup criado na raiz: mobilidade_renapsi_backup_{timestamp}.db")
                    except Exception as e:
                        st.error(f"❌ Erro ao criar backup: {str(e)}")

            with col_b2:
                if st.button("📥 Restaurar Último Backup Padrão", type="secondary", use_container_width=True):
                    try:
                        import shutil
                        if os.path.exists(BACKUP_PATH):
                            shutil.copy(BACKUP_PATH, DB_PATH)
                            st.success("✅ Banco restaurado do backup!")
                            st.rerun()
                        else:
                            st.warning("⚠️ Nenhum backup padrão disponível")
                    except Exception as e:
                        st.error(f"❌ Erro ao restaurar: {str(e)}")

            st.markdown("<hr style='border-color:rgba(0,212,255,0.1);margin:20px 0;'>", unsafe_allow_html=True)

            st.markdown("""
            <div style="background:#FFFFFF;border:1px solid #E5E7EB;
                        border-radius:10px;padding:16px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                <p style="color:#666666;font-size:12px;margin:0;">
                    <strong>ℹ️ Informações:</strong><br>
                    • Backups automáticos são criados ao salvar alterações ou excluir registros<br>
                    • O arquivo de backup padrão fica na raiz do projeto (mobilidade_renapsi_backup.db)<br>
                    • Restaurar substitui o banco atual pelo backup padrão
                </p>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TELA 4 — SIMULAÇÃO: PORTAL DO JOVEM
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "Simulação: Portal do Jovem":

        st.markdown("""
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
            <div>
                <h1 style="margin:0;font-size:28px;color:#1E293B;font-weight:800;">
                    Portal do Jovem - Aceite de Rota
                </h1>
                <p style="margin:0;color:#666666;font-size:13px;letter-spacing:0.05em;">
                    Simulação da visão que o jovem teria ao receber o link de aceite
                </p>
            </div>
        </div>
        <hr style="border-color:#E2E8F0;margin-bottom:20px;">
        """, unsafe_allow_html=True)

        # Busca jovens com status Otimizado
        with sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db')) as conexao:
            df_otimizados = pd.read_sql_query(
                "SELECT id, nome, cep_casa, cep_trabalho FROM jovens_rotas WHERE status_rota = 'Otimizado'",
                conexao
            )

        if df_otimizados.empty:
            st.info("📭 Não há jovens com status 'Otimizado' para simular o aceite.")
        else:
            # Selectbox para escolher o jovem
            opcoes_jovens = [f"{row['id']} - {row['nome']}" for _, row in df_otimizados.iterrows()]
            jovem_selecionado = st.selectbox(
                "Selecione o jovem para simular:",
                opcoes_jovens,
                key="select_jovem_simulacao"
            )

            if jovem_selecionado:
                id_jovem = int(float(jovem_selecionado.split(" - ")[0]))
                
                # Busca dados completos do jovem
                with sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db')) as conexao:
                    df_jovem = pd.read_sql_query(
                        "SELECT * FROM jovens_rotas WHERE id = ?",
                        conexao,
                        params=(id_jovem,)
                    )
                
                if not df_jovem.empty:
                    dados_jovem = df_jovem.iloc[0]
                    nome_jovem = dados_jovem['nome']
                    cep_casa = dados_jovem['cep_casa']
                    cep_trab = dados_jovem['cep_trabalho']
                    
                    # Busca endereços
                    end_casa_dict = buscar_endereco_viacep(cep_casa)
                    end_trab_dict = buscar_endereco_viacep(cep_trab)
                    
                    rua_casa = end_casa_dict.get('rua', 'N/A') if isinstance(end_casa_dict, dict) else end_casa_dict
                    rua_trab = end_trab_dict.get('rua', 'N/A') if isinstance(end_trab_dict, dict) else end_trab_dict
                    bairro_casa = end_casa_dict.get('bairro', '') if isinstance(end_casa_dict, dict) else ''
                    bairro_trab = end_trab_dict.get('bairro', '') if isinstance(end_trab_dict, dict) else ''
                    
                    # Calcula rota
                    rota = motor_de_rotas_gratuito(
                        f"{rua_casa}, {bairro_casa}, São Paulo",
                        f"{rua_trab}, {bairro_trab}, São Paulo"
                    )
                    
                    # Exibe card do jovem
                    st.markdown(f"""
                    <div style="background:linear-gradient(135deg,rgba(0,212,255,0.1),rgba(124,58,237,0.1));
                                border:1px solid rgba(0,212,255,0.3);border-radius:16px;padding:24px;margin-bottom:24px;">
                        <h2 style="margin:0 0 8px;color:#00D4FF;font-size:22px;">👤 {nome_jovem}</h2>
                        <p style="color:#94A3B8;font-size:14px;margin:0;">
                            Olá! Sua rota de Vale-Transporte foi calculada e está pronta para que aceite.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Card da rota
                    if rota.get('rotas') and len(rota['rotas']) > 0:
                        rota_principal = rota['rotas'][0]
                        
                        st.markdown("""
                        <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-left:4px solid #444c9b;
                                    border-radius:14px;padding:24px;margin-bottom:24px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                            <h3 style="margin:0 0 16px;color:#444c9b;">🗺️ Sua Rota de Transporte</h3>
                        """, unsafe_allow_html=True)
                        
                        # Origem e Destino
                        st.markdown(f"""
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">
                            <div style="background:rgba(0,212,255,0.05);border:1px solid rgba(0,212,255,0.2);
                                        border-radius:10px;padding:16px;">
                                <p style="color:#64748B;font-size:12px;margin:0 0 6px;text-transform:uppercase;">🏠 Origem</p>
                                <p style="color:#E2E8F0;font-size:14px;font-weight:600;margin:0;">{rua_casa}</p>
                                <p style="color:#94A3B8;font-size:12px;margin:4px 0 0;">{bairro_casa}</p>
                            </div>
                            <div style="background:rgba(124,58,237,0.05);border:1px solid rgba(124,58,237,0.2);
                                        border-radius:10px;padding:16px;">
                                <p style="color:#64748B;font-size:12px;margin:0 0 6px;text-transform:uppercase;">🏢 Destino</p>
                                <p style="color:#E2E8F0;font-size:14px;font-weight:600;margin:0;">{rua_trab}</p>
                                <p style="color:#94A3B8;font-size:12px;margin:4px 0 0;">{bairro_trab}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Detalhes da rota
                        st.markdown(f"""
                        <div style="background:rgba(0,212,255,0.05);border-left:3px solid #00D4FF;
                                    padding:16px;border-radius:0 8px 8px 0;margin-bottom:16px;">
                            <p style="color:#64748B;font-size:12px;margin:0 0 8px;text-transform:uppercase;">📍 Trajeto</p>
                            <p style="color:#E2E8F0;font-size:15px;font-weight:600;margin:0 0 8px;">{rota_principal['trajeto']}</p>
                            <p style="color:#94A3B8;font-size:13px;margin:0;">
                                🎫 {rota_principal['bilhete']}<br>
                                ⏱️ Tempo estimado: {rota_principal['tempo']}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Valor da tarifa
                        st.markdown(f"""
                        <div style="background:linear-gradient(135deg,rgba(16,185,129,0.15),rgba(5,150,105,0.15));
                                    border:1px solid rgba(16,185,129,0.3);border-radius:12px;
                                    text-align:center;padding:20px;margin-bottom:20px;">
                            <p style="color:#94A3B8;font-size:13px;margin:0 0 8px;text-transform:uppercase;letter-spacing:0.08em;">
                                💰 Valor do Vale-Transporte Diário
                            </p>
                            <p style="color:#10B981;font-size:32px;font-weight:800;margin:0;">
                                R$ {rota_principal['valor_diario']:.2f}
                            </p>
                            <p style="color:#64748B;font-size:12px;margin:8px 0 0;">
                                (Ida + Volta)
                            </p>
                        </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Botões de ação
                        st.markdown("<hr style='border-color:rgba(0,212,255,0.1);margin:24px 0;'>", unsafe_allow_html=True)
                        st.markdown("<h3 style='color:#00D4FF;margin-bottom:16px;'>⚡ Escolha uma ação:</h3>", unsafe_allow_html=True)
                        
                        col_aceitar, col_nao_optante, col_contestar = st.columns(3)
                        
                        with col_aceitar:
                            if st.button("✅ Aceitar e Assinar", type="primary", use_container_width=True, key=f"aceitar_{id_jovem}"):
                                st.session_state.modo_assinatura = True
                        
                        with col_nao_optante:
                            if st.button("❌ Não Optante", use_container_width=True, key=f"nao_optante_{id_jovem}"):
                                # Detectar contexto ativo (se houver)
                                contexto_ativo = "Trabalho"  # Padrão para Envios em Massa
                                atualizar_status_rota(id_jovem, 'Não Optante', contexto_ativo)
                                st.success("✅ Status atualizado para 'Não Optante'")
                                time.sleep(2)
                                st.rerun()
                        
                        with col_contestar:
                            if st.button("⚠️ Contestar Rota", use_container_width=True, key=f"contestar_{id_jovem}"):
                                st.session_state.modo_contestacao_jovem = True
                        
                        # Modal de assinatura
                        if st.session_state.get('modo_assinatura', False):
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown("""
                            <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.3);
                                        border-radius:14px;padding:20px;margin-top:20px;">
                                <h3 style="margin:0 0 4px;color:#10B981;">✍️ Assinatura Digital</h3>
                                <p style="color:#94A3B8;font-size:13px;margin:0;">
                                    Digite seu nome completo para confirmar o aceite da rota
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            nome_assinatura = st.text_input(
                                "Nome Completo para Assinatura:",
                                placeholder="Digite seu nome completo",
                                key=f"assinatura_{id_jovem}"
                            )
                            
                            col_confirmar, col_cancelar = st.columns([1, 1])
                            
                            with col_confirmar:
                                if st.button("✅ Confirmar Assinatura", type="primary", use_container_width=True, key=f"confirmar_assinatura_{id_jovem}"):
                                    if not nome_assinatura.strip():
                                        st.error("⚠️ Digite seu nome completo para assinar")
                                    else:
                                        with sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db')) as conexao:
                                            cursor = conexao.cursor()
                                            # Detectar contexto ativo (padrão Trabalho para Envios em Massa)
                                            contexto_ativo = "Trabalho"
                                            cursor.execute(f"""
                                                UPDATE jovens_rotas 
                                                SET status_{contexto_ativo.lower() if contexto_ativo == 'Curso' else 'rota'} = 'Implantado', 
                                                    assinatura_digital = ?,
                                                    assinatura_data = ?
                                                WHERE id = ?
                                            """, (nome_assinatura, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id_jovem))
                                            conexao.commit()
                                        st.success(f"✅ Rota aceita e assinada por {nome_assinatura}!")
                                        st.balloons()
                                        st.session_state.modo_assinatura = False
                                        time.sleep(2)
                                        st.rerun()
                            
                            with col_cancelar:
                                if st.button("❌ Cancelar", use_container_width=True, key=f"cancelar_assinatura_{id_jovem}"):
                                    st.session_state.modo_assinatura = False
                                    st.rerun()
                        
                        # Modal de contestação
                        if st.session_state.get('modo_contestacao_jovem', False):
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown("""
                            <div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.3);
                                        border-radius:14px;padding:20px;margin-top:20px;">
                                <h3 style="margin:0 0 4px;color:#F59E0B;">⚠️ Contestar Rota</h3>
                                <p style="color:#94A3B8;font-size:13px;margin:0;">
                                    Descreva o motivo da contestação
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            motivo_contestacao = st.text_area(
                                "Motivo da contestação:",
                                placeholder="Ex: A rota não passa perto da minha casa, o valor está incorreto, etc.",
                                height=120,
                                key=f"motivo_contestacao_{id_jovem}"
                            )
                            
                            col_confirmar_cont, col_cancelar_cont = st.columns([1, 1])
                            
                            with col_confirmar_cont:
                                if st.button("✅ Enviar Contestação", type="primary", use_container_width=True, key=f"confirmar_contestacao_{id_jovem}"):
                                    if not motivo_contestacao.strip():
                                        st.error("⚠️ Descreva o motivo da contestação")
                                    else:
                                        # Registra contestação
                                        registrar_contestacao(
                                            nome=nome_jovem,
                                            cid_res="São Paulo",
                                            cid_trab="São Paulo",
                                            motivo=motivo_contestacao
                                        )
                                        
                                        # Atualiza status
                                        with sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db')) as conexao:
                                            cursor = conexao.cursor()
                                            # Detectar contexto ativo (padrão Trabalho para Envios em Massa)
                                            contexto_ativo = "Trabalho"
                                            atualizar_status_rota(id_jovem, 'Contestada', contexto_ativo)
                                        
                                        st.success("✅ Contestação registrada! Status atualizado para 'Contestada'")
                                        st.session_state.modo_contestacao_jovem = False
                                        time.sleep(2)
                                        st.rerun()
                            
                            with col_cancelar_cont:
                                if st.button("❌ Cancelar", use_container_width=True, key=f"cancelar_contestacao_{id_jovem}"):
                                    st.session_state.modo_contestacao_jovem = False
                                    st.rerun()
                    
                    else:
                        st.warning("⚠️ Não foi possível calcular a rota para este jovem")


# ══════════════════════════════════════════════════════════════════════════════
# TELA 5 — GERENCIAR UNIDADES
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "🏢 Gerenciar Unidades":

    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
        <div>
            <h1 style="margin:0;font-size:28px;color:#1E293B;font-weight:800;">
                🏢 Gerenciar Unidades de Trabalho e Curso
            </h1>
            <p style="margin:0;color:#666666;font-size:13px;letter-spacing:0.05em;">
                Cadastre e gerencie os locais de trabalho e instituições de ensino da organização
            </p>
        </div>
    </div>
    <hr style="border-color:#E2E8F0;margin-bottom:20px;">
    """, unsafe_allow_html=True)

    # 🚀 AQUI ESTÃO AS 3 ABAS SEPARADAS
    tab_listar, tab_trab, tab_curso = st.tabs(["📋 Listar Unidades", "🏢 Cadastrar Unidade Trabalho", "📚 Cadastrar Unidade Curso"])

    with tab_listar:
        st.markdown("""
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;
                    border-radius:14px;padding:20px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
            <h3 style="margin:0 0 4px;color:#444c9b;">📋 Unidades Cadastradas</h3>
            <p style="color:#64748B;font-size:14px;margin:0;">
                Lista de todos os locais de trabalho e cursos registrados no sistema
            </p>
        </div>
        """, unsafe_allow_html=True)

        locais = obter_locais_trabalho()

        if not locais:
            st.info("📭 Nenhuma unidade cadastrada ainda. Comece criando uma nova unidade!")
        else:
            for local in locais:
                # Pega o tipo_local (se for antigo e não tiver, assume 'Trabalho')
                tipo_exibicao = local.get('tipo_local', 'Trabalho')
                cor_badge = "#0284C7" if tipo_exibicao == "Trabalho" else "#F59E0B"
                icone_badge = "🏢" if tipo_exibicao == "Trabalho" else "📚"

                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"""
                        <div style="background:#FFFFFF;border-radius:8px;padding:12px;">
                            <div style="display:flex; align-items:center; gap:8px;">
                                <p style="margin:0 0 8px;color:#444c9b;font-size:18px;font-weight:700;">
                                    {local['nome_unidade']}
                                </p>
                                <span style="background:{cor_badge}20; color:{cor_badge}; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:bold; margin-bottom:8px;">
                                    {icone_badge} {tipo_exibicao.upper()}
                                </span>
                            </div>
                            <p style="margin:0 0 4px;color:#666666;font-size:14px;">
                                📍 {local['logradouro']}, {local['numero']} - {local['bairro']}
                            </p>
                            <p style="margin:0 0 4px;color:#666666;font-size:14px;">
                                {local['cidade_uf']}
                            </p>
                            <p style="margin:0;color:#94A3B8;font-size:13px;">
                                CEP: {local['cep']}
                            </p>
                            {f'<p style="margin:4px 0 0;color:#64748B;font-size:13px;">📍 Coordenadas: {local["coordenadas"]}</p>' if local['coordenadas'] else ''}
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        if st.button("🗑️", key=f"del_{local['id']}", help="Deletar unidade"):
                            try:
                                conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
                                cursor = conexao.cursor()
                                cursor.execute("DELETE FROM locais_trabalho WHERE id = ?", (local['id'],))
                                conexao.commit()
                                conexao.close()
                                st.success("✅ Unidade deletada com sucesso!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao deletar: {str(e)}")

    # ── ABA: CADASTRAR TRABALHO ──
    with tab_trab:
        st.markdown("""
        <div style="background:#FFFFFF;border:1px solid #E2E8F0; border-radius:14px;padding:20px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
            <h3 style="margin:0 0 4px;color:#444c9b;">🏢 Cadastrar Unidade de Trabalho</h3>
            <p style="color:#64748B;font-size:14px;margin:0;">Locais para rotas C-T (Casa x Trabalho)</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("form_nova_unidade_trab"):
            nome_unidade_t = st.text_input("Nome da Empresa/Unidade", placeholder="Ex: RENAPSI - São Paulo", key="nome_trab")
            cep_t = st.text_input("CEP", placeholder="00000000", max_chars=8, key="cep_trab_form")

            logradouro_t, bairro_t, cidade_uf_t = "", "", ""

            if cep_t and len(cep_t) == 8:
                endereco = buscar_endereco_viacep(cep_t)
                if isinstance(endereco, dict):
                    logradouro_t = st.text_input("Logradouro", value=endereco.get('rua', ''), disabled=True, key="log_t")
                    bairro_t = st.text_input("Bairro", value=endereco.get('bairro', ''), disabled=True, key="bai_t")
                    cidade_uf_t = st.text_input("Cidade/UF", value=endereco.get('cidade_uf', ''), disabled=True, key="cid_t")
                else:
                    st.error("❌ CEP não encontrado")
                    logradouro_t = st.text_input("Logradouro", key="log_manual_t")
                    bairro_t = st.text_input("Bairro", key="bai_manual_t")
                    cidade_uf_t = st.text_input("Cidade/UF", key="cid_manual_t")
            else:
                logradouro_t = st.text_input("Logradouro", key="log_manual2_t")
                bairro_t = st.text_input("Bairro", key="bai_manual2_t")
                cidade_uf_t = st.text_input("Cidade/UF", key="cid_manual2_t")

            numero_t = st.text_input("Número", placeholder="Ex: 123", key="num_t")

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.form_submit_button("🔍 Corrigir Endereço", use_container_width=True):
                    if logradouro_t and numero_t and cidade_uf_t:
                        coords = obter_coordenadas_reais(f"{logradouro_t}, {numero_t}, {cidade_uf_t}")
                        if coords:
                            st.session_state.coord_temp_t = coords
                            st.success(f"✅ Coordenadas: {coords}")
                            st.rerun()
                    else:
                        st.error("⚠️ Preencha logradouro, número e cidade/UF")

            with col_btn2:
                if st.form_submit_button("💾 Salvar Trabalho", use_container_width=True, type="primary"):
                    if not nome_unidade_t or not cep_t or not logradouro_t or not numero_t:
                        st.error("⚠️ Preencha todos os campos obrigatórios")
                    else:
                        coords_t = st.session_state.get('coord_temp_t', '')
                        inserir_local_trabalho(nome_unidade_t, cep_t, logradouro_t, numero_t, bairro_t, cidade_uf_t, coords_t, tipo_local="Trabalho")
                        st.success(f"✅ Unidade de Trabalho '{nome_unidade_t}' cadastrada!")
                        st.session_state.pop('coord_temp_t', None)
                        time.sleep(1)
                        st.rerun()

    # ── ABA: CADASTRAR CURSO ──
    with tab_curso:
        st.markdown("""
        <div style="background:#FFFFFF;border:1px solid #E2E8F0; border-radius:14px;padding:20px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
            <h3 style="margin:0 0 4px;color:#F59E0B;">📚 Cadastrar Unidade de Curso</h3>
            <p style="color:#64748B;font-size:14px;margin:0;">Locais para rotas C-C (Casa x Curso)</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("form_nova_unidade_curso"):
            nome_unidade_c = st.text_input("Nome da Instituição/Curso", placeholder="Ex: RENAPSI - São Paulo", key="nome_curso")
            cep_c = st.text_input("CEP", placeholder="00000000", max_chars=8, key="cep_curso_form")

            logradouro_c, bairro_c, cidade_uf_c = "", "", ""

            if cep_c and len(cep_c) == 8:
                endereco = buscar_endereco_viacep(cep_c)
                if isinstance(endereco, dict):
                    logradouro_c = st.text_input("Logradouro", value=endereco.get('rua', ''), disabled=True, key="log_c")
                    bairro_c = st.text_input("Bairro", value=endereco.get('bairro', ''), disabled=True, key="bai_c")
                    cidade_uf_c = st.text_input("Cidade/UF", value=endereco.get('cidade_uf', ''), disabled=True, key="cid_c")
                else:
                    st.error("❌ CEP não encontrado")
                    logradouro_c = st.text_input("Logradouro", key="log_manual_c")
                    bairro_c = st.text_input("Bairro", key="bai_manual_c")
                    cidade_uf_c = st.text_input("Cidade/UF", key="cid_manual_c")
            else:
                logradouro_c = st.text_input("Logradouro", key="log_manual2_c")
                bairro_c = st.text_input("Bairro", key="bai_manual2_c")
                cidade_uf_c = st.text_input("Cidade/UF", key="cid_manual2_c")

            numero_c = st.text_input("Número", placeholder="Ex: 123", key="num_c")

            col_btn1_c, col_btn2_c = st.columns(2)
            with col_btn1_c:
                if st.form_submit_button("🔍 Corrigir Endereço", use_container_width=True):
                    if logradouro_c and numero_c and cidade_uf_c:
                        coords = obter_coordenadas_reais(f"{logradouro_c}, {numero_c}, {cidade_uf_c}")
                        if coords:
                            st.session_state.coord_temp_c = coords
                            st.success(f"✅ Coordenadas: {coords}")
                            st.rerun()
                    else:
                        st.error("⚠️ Preencha logradouro, número e cidade/UF")

            with col_btn2_c:
                if st.form_submit_button("💾 Salvar Curso", use_container_width=True, type="primary"):
                    if not nome_unidade_c or not cep_c or not logradouro_c or not numero_c:
                        st.error("⚠️ Preencha todos os campos obrigatórios")
                    else:
                        coords_c = st.session_state.get('coord_temp_c', '')
                        inserir_local_trabalho(nome_unidade_c, cep_c, logradouro_c, numero_c, bairro_c, cidade_uf_c, coords_c, tipo_local="Curso")
                        st.success(f"✅ Unidade de Curso '{nome_unidade_c}' cadastrada!")
                        st.session_state.pop('coord_temp_c', None)
                        time.sleep(1)
                        st.rerun()


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
