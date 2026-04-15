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

# ─── CSS Global — Tema Dark Futurista ─────────────────────────────────────────
st.markdown("""
<style>
/* ── Reset ── */
#MainMenu {visibility: hidden;}
footer     {visibility: hidden;}
header     {visibility: hidden;}

/* ── Fundo principal ── */
.stApp {
    background: linear-gradient(135deg, #0A0E1A 0%, #0D1117 60%, #0A0E1A 100%);
    font-size: 16px !important;
}

/* ── Sidebar dark ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1117 0%, #080C14 100%) !important;
    border-right: 1px solid rgba(0,212,255,0.15);
}
[data-testid="stSidebar"] .stRadio > label {
    color: #94A3B8 !important;
    font-size: 16px !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] .stMarkdown p {
    color: #CBD5E1 !important;
    font-size: 15px !important;
}
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
    color: #94A3B8;
    font-size: 16px !important;
    transition: color 0.2s;
}
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p:hover {
    color: #00D4FF;
}

/* ── KPI cards ── */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, rgba(0,212,255,0.08), rgba(124,58,237,0.08));
    border: 1px solid rgba(0,212,255,0.25);
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 0 24px rgba(0,212,255,0.12), inset 0 1px 0 rgba(255,255,255,0.05);
    backdrop-filter: blur(12px);
}
div[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    color: #94A3B8 !important;
    font-size: 15px !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #00D4FF !important;
    font-size: 2.2rem !important;
    font-weight: 700;
}

/* ── Headings ── */
h1, h2, h3 { color: #E2E8F0 !important; font-size: 1.3em !important; }
h4          { color: #CBD5E1 !important; font-size: 1.2em !important; }

/* ── Texto geral ── */
p, span, div, label, input, textarea, select {
    font-size: 15px !important;
}

/* ── Botões primários ── */
.stButton > button[kind="primary"],
button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #00D4FF, #7C3AED) !important;
    border: none !important;
    color: #0A0E1A !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    border-radius: 8px !important;
    box-shadow: 0 0 18px rgba(0,212,255,0.35) !important;
    transition: box-shadow 0.2s, transform 0.1s !important;
}
.stButton > button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover {
    box-shadow: 0 0 30px rgba(0,212,255,0.6) !important;
    transform: translateY(-1px) !important;
}

/* ── Botões secundários ── */
.stButton > button[kind="secondary"],
button[data-testid="baseButton-secondary"] {
    background: rgba(13,17,23,0.8) !important;
    border: 1px solid rgba(0,212,255,0.3) !important;
    color: #00D4FF !important;
    font-size: 16px !important;
    border-radius: 8px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #00D4FF !important;
    box-shadow: 0 0 12px rgba(0,212,255,0.25) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(13,17,23,0.6);
    border-radius: 10px;
    padding: 4px;
    border: 1px solid rgba(0,212,255,0.15);
}
.stTabs [data-baseweb="tab"] {
    color: #94A3B8 !important;
    font-size: 16px !important;
    border-radius: 8px;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0,212,255,0.2), rgba(124,58,237,0.2)) !important;
    color: #00D4FF !important;
    border-bottom: 2px solid #00D4FF !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: rgba(13,17,23,0.8) !important;
    border: 1px solid rgba(0,212,255,0.2) !important;
    color: #E2E8F0 !important;
    font-size: 15px !important;
    border-radius: 8px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #00D4FF !important;
    box-shadow: 0 0 10px rgba(0,212,255,0.2) !important;
}

/* ── Dataframe ── */
.stDataFrame {
    border: 1px solid rgba(0,212,255,0.15) !important;
    border-radius: 10px !important;
    font-size: 15px !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: rgba(13,17,23,0.6) !important;
    border: 1px solid rgba(0,212,255,0.15) !important;
    border-radius: 8px !important;
    color: #CBD5E1 !important;
    font-size: 16px !important;
}

/* ── Divider ── */
hr { border-color: rgba(0,212,255,0.15) !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #00D4FF !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0A0E1A; }
::-webkit-scrollbar-thumb { background: rgba(0,212,255,0.3); border-radius: 3px; }
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
    "<p style='color:#94A3B8;font-size:11px;text-align:center;letter-spacing:0.1em;margin-top:-8px;'>SISTEMA DE MOBILIDADE URBANA</p>",
    unsafe_allow_html=True
)
st.sidebar.markdown("---")
st.sidebar.markdown("<p style='color:#64748B;font-size:11px;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;'>Navegação</p>", unsafe_allow_html=True)

parametros_url = st.query_params
pagina_salva = parametros_url.get("menu", "Dashboard Principal")
opcoes_menu = ["Dashboard Principal", "Pesquisar Consultas", "Cadastrar Novo Jovem", "Banco de Dados", "Simulação: Portal do Jovem"]
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
    "<p style='color:#334155;font-size:10px;text-align:center;'>v1.0 · RENAPSI © 2026</p>",
    unsafe_allow_html=True
)

# ── Selo de Conformidade LGPD ──
st.sidebar.markdown("""
<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(0,212,255,0.2);
            border-radius:10px;padding:14px;margin-top:16px;text-align:center;">
    <p style="color:#00D4FF;font-size:12px;font-weight:600;margin:0 0 8px;letter-spacing:0.05em;">
        🔒 PRIVACIDADE ASSEGURADA
    </p>
    <p style="color:#94A3B8;font-size:10px;line-height:1.4;margin:0;">
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
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
        <div>
            <h1 style="margin:0;font-size:28px;background:linear-gradient(135deg,#00D4FF,#7C3AED);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800;">
                Dashboard de Mobilidade
            </h1>
            <p style="margin:0;color:#64748B;font-size:13px;letter-spacing:0.05em;">
                {mes_atual.upper()} {ano_atual} &nbsp;·&nbsp; SÃO PAULO
            </p>
        </div>
        <div style="display:flex;gap:8px;align-items:center;">
            <span style="background:rgba(0,212,255,0.1);border:1px solid rgba(0,212,255,0.3);
                         color:#00D4FF;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:600;">
                ● SISTEMA ATIVO
            </span>
        </div>
    </div>
    <hr style="border-color:rgba(0,212,255,0.1);margin-bottom:20px;">
    """, unsafe_allow_html=True)

    tipo_rota = st.radio(
        "Modalidade:",
        ["🏠 Casa × Trabalho", "📚 Casa × Curso", "📊 Gestão de Base", "📧 Envios em Massa"],
        horizontal=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    total_consultas, sla_medio = obter_dados_dashboard()

    conexao = sqlite3.connect('mobilidade_renapsi.db')
    df_contest = pd.read_sql_query("SELECT * FROM contestacoes", conexao)
    conexao.close()

    if 'status' not in df_contest.columns:
        df_contest['status'] = 'Pendente'

    qtd_pendentes  = len(df_contest[df_contest['status'] == 'Pendente'])
    qtd_resolvidas = len(df_contest[df_contest['status'] == 'Resolvido'])
    total_contestacoes = qtd_pendentes + qtd_resolvidas

    # ── KPI Cards ──
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.metric("Total de Consultas", f"{total_consultas}", "Mês atual")
    with col_k2:
        st.metric("SLA Médio", f"{sla_medio:.2f}s", "Tempo de resposta")
    with col_k3:
        st.metric("Contestações", f"{total_contestacoes}", f"{qtd_pendentes} pendentes")
    with col_k4:
        st.metric("Implantações", "0", "No período")

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # ROI DASHBOARD — ANÁLISE FINANCEIRA
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div style="background:rgba(13,17,23,0.8);border:1px solid rgba(0,212,255,0.15);
                border-radius:14px;padding:24px;margin-bottom:20px;">
        <h3 style="margin:0 0 4px;color:#00D4FF;">💰 Análise de ROI — Retorno sobre Investimento</h3>
        <p style="color:#94A3B8;font-size:13px;margin:0;">
            Comparativo de custos: Mobilidade Manual vs. Otimizada
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Busca total de jovens na base
    conexao = sqlite3.connect('mobilidade_renapsi.db')
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
            <p style="color:#EF4444;font-size:12px;margin:0 0 8px;text-transform:uppercase;letter-spacing:0.08em;">
                Custo Manual (Mês)
            </p>
            <p style="color:#E2E8F0;font-size:32px;font-weight:800;margin:0;">
                R$ {custo_manual_mes:,.2f}
            </p>
            <p style="color:#64748B;font-size:11px;margin:4px 0 0;letter-spacing:0.05em;">
                {total_jovens} jovens × R${CUSTO_MANUAL_DIARIO:.2f}/dia × {DIAS_UTEIS_MES} dias
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_roi2:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(16,185,129,0.1),rgba(16,185,129,0.05));
                    border:1px solid rgba(16,185,129,0.3);border-radius:12px;padding:20px;text-align:center;">
            <p style="color:#10B981;font-size:12px;margin:0 0 8px;text-transform:uppercase;letter-spacing:0.08em;">
                Custo Otimizado (Mês)
            </p>
            <p style="color:#E2E8F0;font-size:32px;font-weight:800;margin:0;">
                R$ {custo_otimizado_mes:,.2f}
            </p>
            <p style="color:#64748B;font-size:11px;margin:4px 0 0;letter-spacing:0.05em;">
                {total_jovens} jovens × R${CUSTO_OTIMIZADO_DIARIO:.2f}/dia × {DIAS_UTEIS_MES} dias
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_roi3:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(124,58,237,0.1),rgba(124,58,237,0.05));
                    border:1px solid rgba(124,58,237,0.3);border-radius:12px;padding:20px;text-align:center;">
            <p style="color:#A78BFA;font-size:12px;margin:0 0 8px;text-transform:uppercase;letter-spacing:0.08em;">
                Economia Mensal
            </p>
            <p style="color:#E2E8F0;font-size:32px;font-weight:800;margin:0;">
                R$ {economia_mes:,.2f}
            </p>
            <p style="color:#64748B;font-size:11px;margin:4px 0 0;letter-spacing:0.05em;">
                Redução de {percentual_economia:.1f}% nos custos
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráfico de distribuição modal
    col_chart1, col_chart2 = st.columns([1.5, 1])

    with col_chart1:
        st.markdown("""
        <p style="color:#94A3B8;font-size:12px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:12px;">
            Distribuição Modal das Rotas
        </p>
        """, unsafe_allow_html=True)
        
        # Dados de distribuição modal
        modais = ['Integração', 'Ônibus', 'Metrô']
        percentuais = [40, 35, 25]
        cores_modais = ['#00D4FF', '#7C3AED', '#10B981']

        fig_modal = px.pie(
            values=percentuais,
            names=modais,
            hole=0.5,
            color_discrete_sequence=cores_modais
        )
        fig_modal.update_traces(
            textposition='inside',
            textinfo='label+percent',
            textfont=dict(size=12, color='#E2E8F0'),
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
                font=dict(size=11, color='#94A3B8')
            ),
            margin=dict(t=10, b=10, l=10, r=100),
            height=280,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Arial', size=12, color='#E2E8F0')
        )
        st.plotly_chart(fig_modal, use_container_width=True, key="graf_modal_roi")

    with col_chart2:
        st.markdown("""
        <p style="color:#94A3B8;font-size:12px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:12px;">
            Resumo Financeiro
        </p>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background:rgba(13,17,23,0.8);border:1px solid rgba(0,212,255,0.15);
                    border-radius:12px;padding:16px;height:280px;display:flex;flex-direction:column;justify-content:space-around;">
            <div>
                <p style="color:#64748B;font-size:11px;margin:0 0 4px;text-transform:uppercase;">Total de Jovens</p>
                <p style="color:#00D4FF;font-size:24px;font-weight:800;margin:0;">{total_jovens}</p>
            </div>
            <div>
                <p style="color:#64748B;font-size:11px;margin:0 0 4px;text-transform:uppercase;">Dias Úteis/Mês</p>
                <p style="color:#7C3AED;font-size:24px;font-weight:800;margin:0;">{DIAS_UTEIS_MES}</p>
            </div>
            <div>
                <p style="color:#64748B;font-size:11px;margin:0 0 4px;text-transform:uppercase;">Economia Anual</p>
                <p style="color:#10B981;font-size:24px;font-weight:800;margin:0;">R$ {economia_mes * 12:,.2f}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(0,212,255,0.1);margin:20px 0;'>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # ENVIOS EM MASSA
    # ══════════════════════════════════════════════════════════════════════════
    if tipo_rota == "📧 Envios em Massa":
        st.markdown("""
        <div style="background:rgba(13,17,23,0.8);border:1px solid rgba(59,130,246,0.3);
                    border-radius:14px;padding:24px;margin-bottom:20px;">
            <h3 style="margin:0 0 4px;color:#60A5FA;">📧 Envio em Massa de Cartas de VT</h3>
            <p style="color:#94A3B8;font-size:13px;margin:0;">
                Selecione os funcionários e envie as cartas personalizadas automaticamente
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Busca funcionários pendentes (status != Implantado)
        conexao = sqlite3.connect('mobilidade_renapsi.db')
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
                    <p style="color:#60A5FA;font-size:12px;margin:0 0 4px;text-transform:uppercase;">Total Pendentes</p>
                    <p style="color:#E2E8F0;font-size:28px;font-weight:800;margin:0;">{len(df_pendentes)}</p>
                </div>
                <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);
                            border-radius:10px;padding:16px;text-align:center;">
                    <p style="color:#10B981;font-size:12px;margin:0 0 4px;text-transform:uppercase;">Com E-mail</p>
                    <p style="color:#E2E8F0;font-size:28px;font-weight:800;margin:0;">{len(df_com_email)}</p>
                </div>
                <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);
                            border-radius:10px;padding:16px;text-align:center;">
                    <p style="color:#EF4444;font-size:12px;margin:0 0 4px;text-transform:uppercase;">Sem E-mail</p>
                    <p style="color:#E2E8F0;font-size:28px;font-weight:800;margin:0;">{len(df_sem_email)}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if len(df_sem_email) > 0:
                with st.expander(f"⚠️ {len(df_sem_email)} funcionário(s) sem e-mail cadastrado"):
                    for _, row in df_sem_email.iterrows():
                        st.markdown(f"""
                        <div style="background:rgba(239,68,68,0.05);border-left:3px solid #EF4444;
                                    padding:10px 14px;margin-bottom:8px;border-radius:0 6px 6px 0;">
                            <p style="margin:0;color:#E2E8F0;font-size:14px;">
                                <strong>#{row['id']}</strong> - {row['nome']} 
                                <span style="color:#64748B;font-size:12px;">(CPF: {str(row['cpf']).zfill(11)})</span>
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

            if len(df_com_email) > 0:
                st.markdown("<hr style='border-color:rgba(0,212,255,0.1);margin:20px 0;'>", unsafe_allow_html=True)
                st.markdown("<p style='color:#00D4FF;font-size:14px;font-weight:600;margin-bottom:12px;'>Selecione os funcionários para envio:</p>", unsafe_allow_html=True)

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
                            <div style="background:rgba(13,17,23,0.6);border:1px solid rgba(0,212,255,0.15);
                                        border-radius:8px;padding:12px;margin-bottom:8px;">
                                <p style="margin:0;color:#E2E8F0;font-size:14px;">
                                    <strong>#{row['id']}</strong> - {row['nome']}
                                </p>
                                <p style="margin:4px 0 0;color:#64748B;font-size:12px;">
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
                        <p style="color:#60A5FA;font-size:14px;margin:0;">
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
                            <p style="color:#94A3B8;font-size:13px;margin:0;">
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
                                conexao = sqlite3.connect('mobilidade_renapsi.db')
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
                                <p style="color:#60A5FA;font-size:14px;">
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
                                    <p style="color:#64748B;font-size:12px;margin:0 0 4px;text-transform:uppercase;">Enviados com Sucesso</p>
                                    <p style="color:#10B981;font-size:36px;font-weight:800;margin:0;">{sucessos}</p>
                                </div>
                                <div>
                                    <p style="color:#64748B;font-size:12px;margin:0 0 4px;text-transform:uppercase;">Falhas</p>
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
                                <p style="color:#10B981;font-size:14px;font-weight:600;margin:0 0 8px;">
                                    ✅ {sucessos} e-mail(s) enviado(s) com sucesso
                                </p>
                                <p style="color:#94A3B8;font-size:12px;margin:0;">
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
                                    <p style="color:#EF4444;font-size:14px;font-weight:600;margin:0 0 12px;">
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
                                    <p style="color:#94A3B8;font-size:12px;margin:0;">
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
    col_g1, col_g2, col_g3, col_g4 = st.columns(4)

    CORES_NEON = ['#00D4FF', '#7C3AED', '#10B981', '#F59E0B']

    with col_g1:
        st.markdown("""
        <div style="background:rgba(13,17,23,0.7);border:1px solid rgba(0,212,255,0.15);
                    border-radius:12px;padding:16px;text-align:center;">
            <p style="color:#64748B;font-size:11px;text-transform:uppercase;letter-spacing:0.1em;margin:0 0 8px;">
                Implantações
            </p>
            <p style="color:#334155;font-size:13px;margin:0;">Nenhuma no período</p>
        </div>
        """, unsafe_allow_html=True)

    with col_g2:
        st.markdown(f"""
        <p style="color:#94A3B8;font-size:12px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">
            Contestações ({qtd_resolvidas}/{total_contestacoes})
        </p>
        """, unsafe_allow_html=True)
        if total_contestacoes == 0:
            st.markdown("""
            <div style="background:rgba(13,17,23,0.7);border:1px solid rgba(0,212,255,0.15);
                        border-radius:12px;padding:16px;text-align:center;">
                <p style="color:#334155;font-size:13px;margin:0;">Nenhuma contestação</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            fig = px.pie(values=[qtd_resolvidas, qtd_pendentes], names=['Resolvidas','Pendentes'], hole=0.72)
            fig.update_traces(textinfo='none', marker=dict(colors=['#00D4FF','#1E293B']), hoverinfo="skip")
            fig.update_layout(showlegend=False, margin=dict(t=5,b=5,l=5,r=5), height=160,
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True, key="graf_contest")

    with col_g3:
        st.markdown("<p style='color:#94A3B8;font-size:12px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;'>Por Local de Trabalho</p>", unsafe_allow_html=True)
        fig2 = px.pie(values=[10, 0], names=['SP','Outros'], hole=0.72)
        fig2.update_traces(textinfo='none', marker=dict(colors=['#7C3AED','#1E293B']), hoverinfo="skip")
        fig2.update_layout(showlegend=False, margin=dict(t=5,b=5,l=5,r=5), height=160,
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True, key="graf_local")

    with col_g4:
        st.markdown("<p style='color:#94A3B8;font-size:12px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;'>Por UF</p>", unsafe_allow_html=True)
        fig3 = px.pie(values=[10, 0], names=['SP','Outros'], hole=0.72)
        fig3.update_traces(textinfo='none', marker=dict(colors=['#10B981','#1E293B']), hoverinfo="skip")
        fig3.update_layout(showlegend=False, margin=dict(t=5,b=5,l=5,r=5), height=160,
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
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
                        <div style="background:rgba(13,17,23,0.8);border:1px solid rgba(239,68,68,0.4);
                                    border-radius:12px;padding:20px;margin-bottom:12px;
                                    box-shadow:0 0 16px rgba(239,68,68,0.1);">
                            <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                                <span style="color:#EF4444;font-weight:700;font-size:15px;">Consulta #{row['id']}</span>
                                <span style="background:rgba(239,68,68,0.15);color:#EF4444;padding:2px 8px;
                                             border-radius:20px;font-size:11px;">PENDENTE</span>
                            </div>
                            <p style="color:#64748B;font-size:13px;margin:0 0 8px;">
                                {row['data_geracao']} · <strong style="color:#94A3B8;">{row['nome_jovem']}</strong>
                            </p>
                            <div style="background:rgba(239,68,68,0.05);border-left:3px solid #EF4444;
                                        padding:10px 14px;border-radius:0 6px 6px 0;font-size:13px;color:#CBD5E1;">
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
                        <div style="background:rgba(13,17,23,0.8);border:1px solid rgba(16,185,129,0.3);
                                    border-radius:12px;padding:20px;margin-bottom:12px;">
                            <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                                <span style="color:#10B981;font-weight:700;font-size:15px;">Consulta #{row['id']}</span>
                                <span style="background:rgba(16,185,129,0.15);color:#10B981;padding:2px 8px;
                                             border-radius:20px;font-size:11px;">RESOLVIDO</span>
                            </div>
                            <p style="color:#64748B;font-size:13px;margin:0 0 6px;">{row['data_geracao']} · <strong style="color:#94A3B8;">{row['nome_jovem']}</strong></p>
                            <p style="color:#64748B;font-size:13px;margin:0 0 8px;"><strong>Motivo:</strong> {row['motivo']}</p>
                            <div style="background:rgba(16,185,129,0.08);border-left:3px solid #10B981;
                                        padding:10px 14px;border-radius:0 6px 6px 0;font-size:13px;color:#CBD5E1;">
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
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        df_salvo = pd.read_sql_query("SELECT * FROM jovens_rotas WHERE id = ?", conexao, params=(int(id_salvo),))
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
                           'modo_edicao','mostrar_modal_email','resultado_busca']:
                    st.session_state[k] = False if k != 'resultado_busca' else None
                if 'id_consulta' in st.query_params:
                    del st.query_params['id_consulta']
                st.rerun()

        # Verifica se há dados válidos
        if st.session_state.resultado_busca.empty:
            st.error("❌ Nenhum dado encontrado para esta consulta.")
            st.session_state.detalhes_abertos = False
            st.rerun()
            
        dados_jovem      = st.session_state.resultado_busca.iloc[0]
        id_selecionado   = int(dados_jovem['id'])  # Garante que é inteiro
        nome_jovem       = dados_jovem['nome']
        cpf_cru          = str(dados_jovem['cpf']).zfill(11)
        cep_casa         = dados_jovem['cep_casa']
        cep_trab         = dados_jovem['cep_trabalho']
        matricula_exib   = dados_jovem.get('matricula', 'Não informada')
        status_rota_raw  = dados_jovem.get('status_rota', 'Otimizado')
        status_exib      = obter_status_visual(status_rota_raw)
        email_jovem      = dados_jovem.get('email', '')
        celular_jovem    = dados_jovem.get('celular', '')
        numero_casa      = dados_jovem.get('numero_casa', '')
        coordenadas_casa = dados_jovem.get('coordenadas', '')

        # ── MODO EDIÇÃO ──
        if st.session_state.modo_edicao:
            st.markdown("""
            <div style="background:rgba(13,17,23,0.8);border:1px solid rgba(0,212,255,0.2);
                        border-radius:14px;padding:24px;margin-bottom:20px;">
                <h3 style="margin:0 0 4px;color:#00D4FF;">✏️ Editar Dados da Consulta</h3>
                <p style="color:#64748B;font-size:13px;margin:0;">Atualize as informações do funcionário</p>
            </div>
            """, unsafe_allow_html=True)

            col_e1, col_e2 = st.columns(2)
            with col_e1:
                st.markdown("<p style='color:#00D4FF;font-size:12px;text-transform:uppercase;letter-spacing:0.1em;'>👤 Dados do Funcionário</p>", unsafe_allow_html=True)
                mat_input    = st.text_input("Matrícula", value=matricula_exib if matricula_exib != 'Não informada' else '')
                nome_input   = st.text_input("Nome", value=nome_jovem, disabled=True)
                email_input  = st.text_input("E-mail", value=email_jovem or '')
                celular_input= st.text_input("Celular", value=celular_jovem or '')

            with col_e2:
                st.markdown("<p style='color:#00D4FF;font-size:12px;text-transform:uppercase;letter-spacing:0.1em;'>🏠 Endereço</p>", unsafe_allow_html=True)
                cep_input = st.text_input("CEP", value=cep_casa)
                c_rua, c_num = st.columns([3, 1])
                
                # Busca endereço apenas se CEP mudou
                end_atual = buscar_endereco_viacep(cep_input)
                rua_input = c_rua.text_input("Logradouro", value=end_atual.get('completo',''), disabled=True)
                num_input = c_num.text_input("Número", value=numero_casa or '')

                # Coordenadas
                coord_atual = st.session_state.get('coord_temp', coordenadas_casa)
                coord_input = st.text_input("Coordenadas", value=coord_atual or '')
                
                if st.button("🔍 Buscar Coordenadas Reais", use_container_width=True):
                    if cep_input and len(cep_input.strip()) == 8:
                        end_completo = f"CEP {cep_input}, {num_input if num_input else ''}, São Paulo, Brasil"
                        lat, lon = obter_coordenadas_reais(end_completo)
                        if lat is not None and lon is not None:
                            st.session_state.coord_temp = f"{lat}, {lon}"
                            st.success(f"✅ Coordenadas encontradas: {lat}, {lon}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("⚠️ Não foi possível encontrar as coordenadas. Verifique o CEP e número.")
                    else:
                        st.error("❌ Digite um CEP válido (8 dígitos)")

            st.markdown("<br>", unsafe_allow_html=True)
            col_f, col_c = st.columns(2)
            with col_f:
                if st.button("Fechar", use_container_width=True):
                    st.session_state.modo_edicao = False
                    st.session_state.pop('coord_temp', None)
                    st.rerun()
            with col_c:
                if st.button("Confirmar", type="primary", use_container_width=True):
                    try:
                        # SEM VALIDAÇÕES - aceita qualquer valor
                        mat_final = str(mat_input) if mat_input else ''
                        email_final = str(email_input) if email_input else ''
                        celular_final = str(celular_input) if celular_input else ''
                        cep_final = str(cep_input) if cep_input else str(cep_casa)
                        num_final = str(num_input) if num_input else ''
                        coord_final = str(coord_input) if coord_input else ''
                        
                        # Debug detalhado
                        st.write("**Debug - Valores a serem salvos:**")
                        st.write(f"- ID: {id_selecionado} (tipo: {type(id_selecionado).__name__})")
                        st.write(f"- Matrícula: '{mat_final}'")
                        st.write(f"- Email: '{email_final}'")
                        st.write(f"- Celular: '{celular_final}'")
                        st.write(f"- CEP: '{cep_final}'")
                        st.write(f"- Número: '{num_final}'")
                        st.write(f"- Coordenadas: '{coord_final}'")
                        
                        # Atualiza no banco de dados
                        with st.spinner("Salvando no banco de dados..."):
                            sucesso = atualizar_dados_funcionario(
                                id_selecionado, 
                                mat_final, 
                                email_final, 
                                celular_final, 
                                cep_final, 
                                num_final, 
                                coord_final
                            )
                        
                        if not sucesso:
                            st.error(f"❌ Falha ao atualizar registro ID {id_selecionado}")
                            st.warning("💡 Verifique o console/terminal para detalhes do erro")
                        else:
                            st.success("✅ Atualização executada no banco!")
                            
                            # Recarrega os dados do banco
                            with st.spinner("Recarregando dados..."):
                                conexao = sqlite3.connect('mobilidade_renapsi.db')
                                df_atualizado = pd.read_sql_query(
                                    "SELECT * FROM jovens_rotas WHERE id = ?", 
                                    conexao, 
                                    params=(int(id_selecionado),)
                                )
                                conexao.close()
                            
                            if not df_atualizado.empty:
                                # Atualiza o estado com os novos dados
                                st.session_state.resultado_busca = df_atualizado
                                st.session_state.modo_edicao = False
                                st.session_state.pop('coord_temp', None)
                                
                                # Limpa cache de rotas
                                st.session_state.rota_gerada = None
                                st.session_state.analise_ia = None
                                
                                st.success("✅ Dados salvos e recarregados com sucesso!")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("❌ Erro ao recarregar dados do banco.")
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())



        # ── MODO VISUALIZAÇÃO ──
        else:
            end_casa_dict = buscar_endereco_viacep(cep_casa)
            end_trab_dict = buscar_endereco_viacep(cep_trab)

            rua_casa         = end_casa_dict.get('rua','N/A') if isinstance(end_casa_dict, dict) else end_casa_dict
            bairro_cidade_casa = f"{end_casa_dict.get('bairro','')} - {end_casa_dict.get('cidade_uf','')}" if isinstance(end_casa_dict, dict) else ""
            rua_trab         = end_trab_dict.get('rua','N/A') if isinstance(end_trab_dict, dict) else end_trab_dict
            bairro_cidade_trab = f"{end_trab_dict.get('bairro','')} - {end_trab_dict.get('cidade_uf','')}" if isinstance(end_trab_dict, dict) else ""

            if not st.session_state.get('rota_gerada'):
                # Calcula rota (motor já faz geocoding internamente com cache)
                rota = motor_de_rotas_gratuito(
                    f"{rua_casa}, {bairro_cidade_casa}",
                    f"{rua_trab}, {bairro_cidade_trab}"
                )
                st.session_state.rota_gerada = rota
                
                # Análise da IA em background (não bloqueia a UI)
                if not st.session_state.get('analise_ia'):
                    st.session_state.analise_ia = analisar_rota_com_ia(
                        rua_casa, rua_trab, rota['distancia_km'],
                        rota['rotas'], rota['info_tarifas']
                    )

            # Botão editar
            col_fill, col_edit_btn = st.columns([11, 1])
            with col_edit_btn:
                if st.button("✏️", use_container_width=True, help="Editar dados"):
                    st.session_state.modo_edicao = True
                    st.rerun()

            # ── Painel principal do funcionário ──
            # Define cor baseada no status
            if status_rota_raw == "Implantado":
                status_color = "#10B981"  # Verde
                status_bg = "16,185,129"
            elif status_rota_raw == "Otimizado":
                status_color = "#3B82F6"  # Azul
                status_bg = "59,130,246"
            elif status_rota_raw == "Contestada":
                status_color = "#F59E0B"  # Amarelo
                status_bg = "245,158,11"
            else:  # Não Optante
                status_color = "#94A3B8"  # Cinza
                status_bg = "148,163,184"
            
            st.markdown(f"""
            <div style="background:rgba(13,17,23,0.85);border:1px solid rgba(0,212,255,0.2);
                        border-radius:16px;padding:28px;margin-bottom:20px;
                        box-shadow:0 4px 32px rgba(0,0,0,0.4),inset 0 1px 0 rgba(255,255,255,0.03);">
                <div style="display:flex;align-items:center;gap:14px;margin-bottom:20px;">
                    <div style="background:linear-gradient(135deg,rgba(0,212,255,0.15),rgba(124,58,237,0.15));
                                border:1px solid rgba(0,212,255,0.3);border-radius:50%;width:52px;height:52px;
                                display:flex;align-items:center;justify-content:center;font-size:22px;">👤</div>
                    <div>
                        <h2 style="margin:0;font-size:22px;color:#E2E8F0;">Consulta #{id_selecionado}</h2>
                        <p style="margin:0;color:#64748B;font-size:13px;">RENAPSI · SÃO PAULO · C-T</p>
                    </div>
                    <span style="margin-left:auto;background:rgba({status_bg},0.15);
                                 color:{status_color};padding:6px 14px;border-radius:20px;
                                 font-size:12px;font-weight:700;border:1px solid {status_color}40;">
                        {status_exib}
                    </span>
                </div>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;">
                    <div style="border-right:1px solid rgba(0,212,255,0.1);padding-right:20px;">
                        <p style="color:#00D4FF;font-size:11px;text-transform:uppercase;letter-spacing:0.1em;margin:0 0 10px;">Dados do Funcionário</p>
                        <p style="margin:5px 0;font-size:14px;color:#CBD5E1;"><span style="color:#64748B;">CPF:</span> {cpf_cru}</p>
                        <p style="margin:5px 0;font-size:14px;color:#CBD5E1;"><span style="color:#64748B;">Matrícula:</span> {matricula_exib}</p>
                        <p style="margin:5px 0;font-size:14px;color:#CBD5E1;"><span style="color:#64748B;">Nome:</span> {nome_jovem}</p>
                        {f'<p style="margin:5px 0;font-size:14px;color:#CBD5E1;"><span style="color:#64748B;">E-mail:</span> {email_jovem}</p>' if email_jovem else ''}
                        {f'<p style="margin:5px 0;font-size:14px;color:#CBD5E1;"><span style="color:#64748B;">Celular:</span> {celular_jovem}</p>' if celular_jovem else ''}
                    </div>
                    <div style="border-right:1px solid rgba(0,212,255,0.1);padding-right:20px;">
                        <p style="color:#00D4FF;font-size:11px;text-transform:uppercase;letter-spacing:0.1em;margin:0 0 10px;">Endereço Residencial</p>
                        <span style="background:rgba(16,185,129,0.1);color:#10B981;padding:2px 8px;font-size:10px;border-radius:20px;font-weight:600;">● BAIXO RISCO</span>
                        <p style="margin:8px 0 5px;font-size:14px;color:#CBD5E1;"><span style="color:#64748B;">CEP:</span> {cep_casa}</p>
                        <p style="margin:5px 0;font-size:14px;color:#CBD5E1;line-height:1.5;">{rua_casa}{f', {numero_casa}' if numero_casa else ''}<br><span style="color:#64748B;">{bairro_cidade_casa}</span></p>
                    </div>
                    <div>
                        <p style="color:#00D4FF;font-size:11px;text-transform:uppercase;letter-spacing:0.1em;margin:0 0 10px;">Local de Trabalho</p>
                        <p style="margin:5px 0;font-size:14px;color:#CBD5E1;"><span style="color:#64748B;">CEP:</span> {cep_trab}</p>
                        <p style="margin:5px 0;font-size:14px;color:#CBD5E1;line-height:1.5;">{rua_trab}<br><span style="color:#64748B;">{bairro_cidade_trab}</span></p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Barra de ações ──
            st.markdown("<p style='color:#64748B;font-size:12px;margin-bottom:8px;'>AÇÕES DA CONSULTA</p>", unsafe_allow_html=True)
            col_b1, col_b2, col_b3, col_b4, col_b5, col_fill2 = st.columns([1, 1, 1, 1, 1, 1])
            ja_implantado = (status_rota_raw == "Implantado")
            
            with col_b1:
                if st.button("🔄 Recalcular", disabled=ja_implantado, use_container_width=True):
                    # Limpa a rota gerada e força recálculo
                    st.session_state.rota_gerada = None
                    st.session_state.analise_ia = None
                    st.session_state.modo_contestacao = False
                    st.rerun()
                    
            with col_b2:
                if st.button("✉️ Enviar Carta", use_container_width=True):
                    st.session_state.mostrar_modal_email = not st.session_state.get('mostrar_modal_email', False)
                    
            with col_b3:
                if st.button("⚠️ Contestação", use_container_width=True):
                    st.session_state.modo_contestacao = not st.session_state.get('modo_contestacao', False)
                    
            with col_b4:
                if st.button("✍️ Rota Manual", use_container_width=True):
                    st.session_state.modo_rota_manual = not st.session_state.get('modo_rota_manual', False)
                    
            with col_b5:
                if st.button("📋 Implantados", use_container_width=True):
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
                            
                            # Atualiza status para CONTESTADA
                            conexao = sqlite3.connect('mobilidade_renapsi.db')
                            cursor = conexao.cursor()
                            cursor.execute("UPDATE jovens_rotas SET status_rota = 'Contestada' WHERE id = ?", (id_selecionado,))
                            conexao.commit()
                            conexao.close()
                            
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
                            
                            # Atualiza no banco
                            conexao = sqlite3.connect('mobilidade_renapsi.db')
                            cursor = conexao.cursor()
                            cursor.execute(
                                "UPDATE jovens_rotas SET status_rota = ? WHERE id = ?",
                                (novo_status, id_selecionado)
                            )
                            conexao.commit()
                            conexao.close()
                            
                            st.success(f"✅ Status alterado para: {novo_status}")
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
                                conexao = sqlite3.connect('mobilidade_renapsi.db')
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
                rota = motor_de_rotas_gratuito(
                    f"{rua_casa}, {bairro_cidade_casa}",
                    f"{rua_trab}, {bairro_cidade_trab}"
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
                st.markdown("<p style='color:#00D4FF;font-size:12px;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;'>🗺️ Opções de Trajeto</p>", unsafe_allow_html=True)

                if st.session_state.get('rota_gerada') and 'rotas' in st.session_state.rota_gerada:
                    abas = st.tabs([r["modal"] for r in st.session_state.rota_gerada["rotas"]])
                    for i, aba in enumerate(abas):
                        with aba:
                            rt = st.session_state.rota_gerada["rotas"][i]
                            st.markdown(f"""
                            <div style="background:rgba(13,17,23,0.9);border:1px solid rgba(0,212,255,0.2);
                                        border-radius:12px;padding:18px;margin-top:8px;
                                        box-shadow:0 4px 20px rgba(0,0,0,0.3);">
                                <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:16px;">
                                    <div style="background:linear-gradient(135deg,#00D4FF,#7C3AED);border-radius:50%;
                                                min-width:40px;height:40px;display:flex;align-items:center;
                                                justify-content:center;font-weight:800;color:#0A0E1A;font-size:13px;">SP</div>
                                    <div>
                                        <p style="margin:0;font-weight:700;color:#E2E8F0;font-size:14px;">{rt['trajeto']}</p>
                                        <p style="margin:4px 0;font-size:12px;color:#64748B;">{rt['bilhete']}</p>
                                        <p style="margin:4px 0;font-size:12px;color:#A78BFA;font-weight:600;">⏱ {rt['tempo']}</p>
                                    </div>
                                </div>
                                <div style="background:linear-gradient(135deg,rgba(0,212,255,0.15),rgba(124,58,237,0.15));
                                            border:1px solid rgba(0,212,255,0.3);border-radius:8px;
                                            text-align:center;padding:14px;
                                            box-shadow:0 0 16px rgba(0,212,255,0.1);">
                                    <p style="margin:0;color:#94A3B8;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;">VT Diário (Ida + Volta)</p>
                                    <p style="margin:4px 0 0;color:#00D4FF;font-size:22px;font-weight:800;">R$ {rt['valor_diario']:.2f}</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("Calculando rotas...")

            with col_mapa:
                if st.session_state.get('rota_gerada'):
                    (lat_c, lon_c), (lat_t, lon_t) = st.session_state.rota_gerada['coords_reais']
                    m = folium.Map(
                        location=[(lat_c + lat_t) / 2, (lon_c + lon_t) / 2],
                        zoom_start=12, control_scale=True
                    )
                    folium.TileLayer('CartoDB dark_matter').add_to(m)

                    folium.Marker([lat_c, lon_c], icon=folium.DivIcon(html="""
                        <div style="background:linear-gradient(135deg,#00D4FF,#0EA5E9);width:44px;height:44px;
                                    border-radius:50%;border:2px solid rgba(0,212,255,0.6);display:flex;
                                    align-items:center;justify-content:center;font-weight:800;color:#0A0E1A;
                                    font-size:16px;box-shadow:0 0 16px rgba(0,212,255,0.6);">C</div>
                    """), tooltip="Casa").add_to(m)

                    folium.Marker([lat_t, lon_t], icon=folium.DivIcon(html="""
                        <div style="background:linear-gradient(135deg,#7C3AED,#A855F7);width:44px;height:44px;
                                    border-radius:50%;border:2px solid rgba(124,58,237,0.6);display:flex;
                                    align-items:center;justify-content:center;font-weight:800;color:white;
                                    font-size:16px;box-shadow:0 0 16px rgba(124,58,237,0.6);">T</div>
                    """), tooltip="Trabalho").add_to(m)

                    folium.PolyLine(
                        locations=[[lat_c, lon_c], [lat_t, lon_t]],
                        color="#00D4FF", weight=3, opacity=0.7,
                        dash_array="8 4"
                    ).add_to(m)

                    st_folium(m, height=500, use_container_width=True)

    # ── LISTA DE PESQUISA ────────────────────────────────────────────────────
    else:
        st.markdown("""
        <h1 style="background:linear-gradient(135deg,#00D4FF,#7C3AED);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                   font-size:26px;font-weight:800;margin-bottom:4px;">
            Pesquisar Consultas
        </h1>
        <p style="color:#64748B;font-size:13px;margin-bottom:20px;">Localize aprendizes por CPF, nome ou matrícula</p>
        """, unsafe_allow_html=True)

        modalidade_pesquisa = st.radio(
            "Modalidade:",
            ["🏠 Casa × Trabalho", "📚 Casa × Curso"],
            horizontal=True
        )

        st.markdown("<hr style='border-color:rgba(0,212,255,0.1);'>", unsafe_allow_html=True)

        tab_cpf, tab_nome, tab_mat = st.tabs(["🔍 Por CPF", "👤 Por Nome", "🪪 Por Matrícula"])

        with tab_cpf:
            with st.form(key="form_cpf"):
                cpf_busca = st.text_input("CPF (apenas números)", max_chars=11, placeholder="00000000000")
                if st.form_submit_button("Pesquisar", type="primary"):
                    try:
                        conexao = sqlite3.connect('mobilidade_renapsi.db')
                        # CPF está encriptado, então buscamos por ID ou nome
                        st.session_state.resultado_busca = pd.read_sql_query(
                            "SELECT * FROM jovens_rotas WHERE id = ?", conexao, params=(int(cpf_busca),))
                        if st.session_state.resultado_busca.empty:
                            st.warning("❌ Nenhum resultado encontrado para este ID")
                        st.session_state.detalhes_abertos = False
                        conexao.close()
                        st.rerun()
                    except ValueError:
                        st.error("❌ Digite um ID válido (apenas números)")

        with tab_nome:
            with st.form(key="form_nome"):
                nome_busca = st.text_input("Nome completo", placeholder="Digite o nome...")
                if st.form_submit_button("Pesquisar", type="primary"):
                    try:
                        conexao = sqlite3.connect('mobilidade_renapsi.db')
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
                        conexao = sqlite3.connect('mobilidade_renapsi.db')
                        st.session_state.resultado_busca = pd.read_sql_query(
                            "SELECT * FROM jovens_rotas WHERE matricula = ?", conexao, params=(mat_busca,))
                        if st.session_state.resultado_busca.empty:
                            st.warning("❌ Nenhum resultado encontrado para esta matrícula")
                        st.session_state.detalhes_abertos = False
                        conexao.close()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro na busca: {str(e)}")

        if st.session_state.resultado_busca is not None:
            if st.session_state.resultado_busca.empty:
                st.warning("Nenhum aprendiz encontrado.")
            else:
                dados_jovem    = st.session_state.resultado_busca.iloc[0]
                id_sel         = dados_jovem['id']
                nome_jov       = dados_jovem['nome']
                cpf_cru2       = str(dados_jovem['cpf']).zfill(11)
                cpf_mask       = f"***.***.{cpf_cru2[6:9]}-{cpf_cru2[9:11]}"
                mat_exib       = dados_jovem.get('matricula','Não informada')
                status_rota_raw2 = dados_jovem.get('status_rota','Otimizado')
                status_exib2   = obter_status_visual(status_rota_raw2)
                data_rot       = dados_jovem.get('data_consulta') or "Pendente"

                st.markdown(f"""
                <div style="background:rgba(13,17,23,0.85);border:1px solid rgba(0,212,255,0.2);
                            border-left:4px solid #00D4FF;border-radius:12px;padding:20px;
                            margin-top:16px;box-shadow:0 4px 20px rgba(0,0,0,0.3);">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                        <span style="color:#E2E8F0;font-weight:700;font-size:16px;">#{id_sel} — {nome_jov.upper()}</span>
                        <span style="background:rgba(59,130,246,0.15);color:#3B82F6;padding:2px 8px;
                                     border-radius:20px;font-size:10px;font-weight:700;">{status_exib2}</span>
                    </div>
                    <p style="margin:3px 0;color:#64748B;font-size:12px;">PRÉ-ADM · Última roteirização: {data_rot}</p>
                    <p style="margin:3px 0;color:#64748B;font-size:12px;">CPF: {cpf_mask} · Matrícula: {mat_exib}</p>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Abrir Consulta →", type="primary"):
                    st.session_state.detalhes_abertos = True
                    st.query_params["id_consulta"] = id_sel
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TELA 2 — CADASTRAR NOVO JOVEM
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "Cadastrar Novo Jovem":

    st.markdown("""
    <h1 style="background:linear-gradient(135deg,#00D4FF,#7C3AED);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;
               font-size:26px;font-weight:800;margin-bottom:4px;">
        Cadastrar Novo Aprendiz
    </h1>
    <p style="color:#64748B;font-size:13px;margin-bottom:20px;">
        Adicione aprendizes manualmente ou via planilha Excel/CSV
    </p>
    <hr style="border-color:rgba(0,212,255,0.1);margin-bottom:20px;">
    """, unsafe_allow_html=True)

    tab_manual, tab_massa = st.tabs(["✍️ Cadastro Manual", "📂 Importação em Massa"])

    with tab_manual:
        st.markdown("""
        <div style="background:rgba(13,17,23,0.7);border:1px solid rgba(0,212,255,0.15);
                    border-radius:12px;padding:20px;margin-bottom:16px;">
            <p style="color:#64748B;font-size:12px;margin:0;">
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
            elif cpf_ja_existe(cpf_input):
                st.error(f"❌ CPF {cpf_input} já está cadastrado no sistema.")
            else:
                with st.spinner("Validando CEPs..."):
                    v_casa = buscar_endereco_viacep(cep_casa_input)
                    v_trab = buscar_endereco_viacep(cep_trab_input)
                    if "inválido" in v_casa.get('completo','').lower() or "inválido" in v_trab.get('completo','').lower():
                        st.error("❌ Um dos CEPs informados é inválido.")
                    else:
                        inserir_novo_jovem(nome_input, cpf_input, cep_casa_input, cep_trab_input, matricula_input)
                        st.success(f"✅ {nome_input} (Matrícula: {matricula_input}) cadastrado com sucesso!")

    with tab_massa:
        st.markdown("""
        <div style="background:rgba(0,212,255,0.05);border:1px solid rgba(0,212,255,0.2);
                    border-radius:12px;padding:16px;margin-bottom:16px;">
            <p style="color:#94A3B8;font-size:13px;margin:0;">
                💡 A planilha deve conter as colunas:
                <strong style="color:#00D4FF;">nome, cpf, cep_casa, cep_trabalho, matricula</strong>
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
                            conexao = sqlite3.connect('mobilidade_renapsi.db')
                            df_limpo = df_upload[['nome','cpf','cep_casa','cep_trabalho','matricula','status_rota']]
                            df_limpo.to_sql('jovens_rotas', conexao, if_exists='append', index=False)
                            conexao.close()
                            st.success(f"✅ {len(df_limpo)} aprendizes importados com sucesso!")
                            time.sleep(2)
                            st.rerun()

            except Exception as e:
                st.error(f"❌ Erro ao ler o arquivo: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TELA 3 — BANCO DE DADOS
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "Banco de Dados":

    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
        <div>
            <h1 style="margin:0;font-size:28px;background:linear-gradient(135deg,#00D4FF,#7C3AED);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800;">
                Gerenciamento de Banco de Dados
            </h1>
            <p style="margin:0;color:#64748B;font-size:13px;letter-spacing:0.05em;">
                Visualize, edite e gerencie todos os registos da tabela jovens_rotas
            </p>
        </div>
    </div>
    <hr style="border-color:rgba(0,212,255,0.1);margin-bottom:20px;">
    """, unsafe_allow_html=True)

    # Carrega dados do banco
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    df_banco = pd.read_sql_query("SELECT * FROM jovens_rotas", conexao)
    conexao.close()

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
        <div style="background:rgba(13,17,23,0.8);border:1px solid rgba(0,212,255,0.15);
                    border-radius:14px;padding:20px;margin-bottom:20px;">
            <h3 style="margin:0 0 4px;color:#00D4FF;">📊 Tabela de Jovens</h3>
            <p style="color:#94A3B8;font-size:13px;margin:0;">
                Edite os dados diretamente na tabela. Clique em qualquer célula para modificar.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Exibe a tabela editável
        df_editado = st.data_editor(
            df_banco,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_banco",
            hide_index=False
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Botão para salvar alterações
        col_save, col_info = st.columns([1, 4])
        with col_save:
            if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                try:
                    # Força o tipo de dados para CPF (texto)
                    df_editado['cpf'] = df_editado['cpf'].astype(str).str.zfill(11)
                    
                    # Salva no banco de dados
                    conexao = sqlite3.connect('mobilidade_renapsi.db')
                    df_editado.to_sql('jovens_rotas', conexao, if_exists='replace', index=False)
                    conexao.close()

                    # Cria backup automático
                    import shutil
                    shutil.copy('mobilidade_renapsi.db', 'mobilidade_renapsi_backup.db')

                    st.success("✅ Alterações salvas com sucesso! Backup criado automaticamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar: {str(e)}")

        with col_info:
            st.markdown(f"""
            <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);
                        border-radius:10px;padding:12px;text-align:center;">
                <p style="color:#10B981;font-size:12px;margin:0;text-transform:uppercase;">
                    Total de Registos: <strong>{len(df_editado)}</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 2: ADICIONAR COLUNA ──
    with tab_adicionar_coluna:
        st.markdown("""
        <div style="background:rgba(13,17,23,0.8);border:1px solid rgba(0,212,255,0.15);
                    border-radius:14px;padding:20px;margin-bottom:20px;">
            <h3 style="margin:0 0 4px;color:#00D4FF;">➕ Adicionar Nova Coluna</h3>
            <p style="color:#94A3B8;font-size:13px;margin:0;">
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
                # ─── VALIDAÇÃO DE SEGURANÇA: Previne SQL Injection ───────────────────
                # SQLite DDL (ALTER TABLE) não suporta parameterized queries,
                # então validamos rigorosamente o nome da coluna
                import re
                
                # SQL Keywords que não podem ser usados como nomes de coluna
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
                
                # Valida nome da coluna: apenas letras, números e underscore
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', nome_coluna):
                    st.error("❌ Nome da coluna inválido. Use apenas letras, números e underscore (_).")
                elif len(nome_coluna) > 64:
                    st.error("❌ Nome da coluna muito longo (máximo 64 caracteres).")
                elif nome_coluna.upper() in SQL_KEYWORDS:
                    st.error(f"❌ '{nome_coluna}' é uma palavra-chave SQL reservada. Escolha outro nome.")
                elif tipo_coluna not in ["TEXT", "INTEGER", "REAL", "BLOB"]:
                    st.error("❌ Tipo de dados inválido.")
                else:
                    try:
                        conexao = sqlite3.connect('mobilidade_renapsi.db')
                        cursor = conexao.cursor()
                        # Agora é seguro usar f-string pois validamos rigorosamente
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
        <div style="background:rgba(13,17,23,0.8);border:1px solid rgba(239,68,68,0.3);
                    border-radius:14px;padding:20px;margin-bottom:20px;">
            <h3 style="margin:0 0 4px;color:#EF4444;">🚨 Excluir Registro</h3>
            <p style="color:#94A3B8;font-size:13px;margin:0;">
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
                    conexao = sqlite3.connect('mobilidade_renapsi.db')
                    cursor = conexao.cursor()
                    cursor.execute("DELETE FROM jovens_rotas WHERE id = ?", (id_excluir,))
                    conexao.commit()
                    conexao.close()
                    
                    # Cria backup automático
                    import shutil
                    shutil.copy('mobilidade_renapsi.db', 'mobilidade_renapsi_backup.db')
                    
                    st.success(f"✅ Registro #{id_excluir} excluído com sucesso! Backup criado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao excluir: {str(e)}")

    # ── TAB 4: BACKUP ──
    with tab_backup:
        st.markdown("""
        <div style="background:rgba(13,17,23,0.8);border:1px solid rgba(0,212,255,0.15);
                    border-radius:14px;padding:20px;margin-bottom:20px;">
            <h3 style="margin:0 0 4px;color:#00D4FF;">💾 Gerenciamento de Backup</h3>
            <p style="color:#94A3B8;font-size:13px;margin:0;">
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
                    backup_name = f"mobilidade_renapsi_backup_{timestamp}.db"
                    shutil.copy('mobilidade_renapsi.db', backup_name)
                    st.success(f"✅ Backup criado: {backup_name}")
                except Exception as e:
                    st.error(f"❌ Erro ao criar backup: {str(e)}")

        with col_b2:
            if st.button("📥 Restaurar Backup", type="secondary", use_container_width=True):
                try:
                    import shutil
                    if os.path.exists('mobilidade_renapsi_backup.db'):
                        shutil.copy('mobilidade_renapsi_backup.db', 'mobilidade_renapsi.db')
                        st.success("✅ Banco restaurado do backup!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Nenhum backup disponível")
                except Exception as e:
                    st.error(f"❌ Erro ao restaurar: {str(e)}")

        st.markdown("<hr style='border-color:rgba(0,212,255,0.1);margin:20px 0;'>", unsafe_allow_html=True)

        # Informações sobre backups
        st.markdown("""
        <div style="background:rgba(13,17,23,0.6);border:1px solid rgba(0,212,255,0.15);
                    border-radius:10px;padding:16px;">
            <p style="color:#94A3B8;font-size:12px;margin:0;">
                <strong>ℹ️ Informações:</strong><br>
                • Backups automáticos são criados ao salvar alterações<br>
                • Você pode criar backups manuais com timestamp<br>
                • O arquivo de backup padrão é: mobilidade_renapsi_backup.db<br>
                • Restaurar substitui o banco atual pelo backup
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
            <h1 style="margin:0;font-size:28px;background:linear-gradient(135deg,#00D4FF,#7C3AED);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800;">
                Portal do Jovem - Aceite de Rota
            </h1>
            <p style="margin:0;color:#64748B;font-size:13px;letter-spacing:0.05em;">
                Simulação da visão que o jovem teria ao receber o link de aceite
            </p>
        </div>
    </div>
    <hr style="border-color:rgba(0,212,255,0.1);margin-bottom:20px;">
    """, unsafe_allow_html=True)

    # Busca jovens com status Otimizado
    with sqlite3.connect('mobilidade_renapsi.db') as conexao:
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
            id_jovem = int(jovem_selecionado.split(" - ")[0])
            
            # Busca dados completos do jovem
            with sqlite3.connect('mobilidade_renapsi.db') as conexao:
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
                        Olá! Sua rota de Vale-Transporte foi calculada e está pronta para aceite.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Card da rota
                if rota.get('rotas') and len(rota['rotas']) > 0:
                    rota_principal = rota['rotas'][0]
                    
                    st.markdown("""
                    <div style="background:rgba(13,17,23,0.9);border:1px solid rgba(0,212,255,0.2);
                                border-radius:14px;padding:24px;margin-bottom:24px;">
                        <h3 style="margin:0 0 16px;color:#00D4FF;">🗺️ Sua Rota de Transporte</h3>
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
                            with sqlite3.connect('mobilidade_renapsi.db') as conexao:
                                cursor = conexao.cursor()
                                cursor.execute(
                                    "UPDATE jovens_rotas SET status_rota = 'Não Optante' WHERE id = ?",
                                    (id_jovem,)
                                )
                                conexao.commit()
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
                                    with sqlite3.connect('mobilidade_renapsi.db') as conexao:
                                        cursor = conexao.cursor()
                                        cursor.execute("""
                                            UPDATE jovens_rotas 
                                            SET status_rota = 'Implantado', 
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
                                    with sqlite3.connect('mobilidade_renapsi.db') as conexao:
                                        cursor = conexao.cursor()
                                        cursor.execute(
                                            "UPDATE jovens_rotas SET status_rota = 'Contestada' WHERE id = ?",
                                            (id_jovem,)
                                        )
                                        conexao.commit()
                                    
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
