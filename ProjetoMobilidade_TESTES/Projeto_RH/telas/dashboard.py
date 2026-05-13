"""Dashboard principal com KPIs e análise de ROI."""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import datetime
import os
from banco_dados import obter_dados_dashboard


def renderizar_dashboard():
    """Renderiza o dashboard principal."""
    meses_pt = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_atual = meses_pt[datetime.datetime.now().month - 1]
    ano_atual = datetime.datetime.now().year

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
            pass

    tipo_rota = st.radio(
        "Modalidade:",
        ["🏠 Casa × Trabalho", "📚 Casa × Curso", "📊 Gestão de Base", "📧 Envios em Massa"],
        horizontal=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    total_consultas, sla_medio, total_contestacoes, total_implantados = obter_dados_dashboard()

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

    _renderizar_roi()

    st.markdown("<hr style='border-color:rgba(0,212,255,0.1);margin:20px 0;'>", unsafe_allow_html=True)

    if tipo_rota == "📧 Envios em Massa":
        _renderizar_envios_massa()


def _renderizar_roi():
    """Renderiza a seção de análise de ROI."""
    st.markdown("""
    <div style="background:#FFFFFF;border:1px solid #E2E8F0;
                border-radius:14px;padding:24px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
        <h3 style="margin:0 0 4px;color:#f8ae28;">💰 Análise de ROI — Retorno sobre Investimento</h3>
        <p style="color:#64748B;font-size:15px;margin:0;">
            Comparativo de custos: Mobilidade Manual vs. Otimizada
        </p>
    </div>
    """, unsafe_allow_html=True)

    conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db'))
    df_jovens = pd.read_sql_query("SELECT COUNT(*) as total FROM jovens_rotas", conexao)
    total_jovens = df_jovens.iloc[0]['total'] if not df_jovens.empty else 0
    conexao.close()

    CUSTO_MANUAL_DIARIO = 15.00
    CUSTO_OTIMIZADO_DIARIO = 11.32
    DIAS_UTEIS_MES = 22

    custo_manual_mes = CUSTO_MANUAL_DIARIO * DIAS_UTEIS_MES * total_jovens
    custo_otimizado_mes = CUSTO_OTIMIZADO_DIARIO * DIAS_UTEIS_MES * total_jovens
    economia_mes = custo_manual_mes - custo_otimizado_mes
    percentual_economia = (economia_mes / custo_manual_mes * 100) if custo_manual_mes > 0 else 0

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

    col_chart1, col_chart2 = st.columns([1.5, 1])

    with col_chart1:
        st.markdown("""
        <p style="color:#94A3B8;font-size:15px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:12px;">
            Distribuição Modal das Rotas
        </p>
        """, unsafe_allow_html=True)

        modais = ['Integração', 'Ônibus', 'Metrô']
        percentuais = [40, 35, 25]
        cores_modais = ['#f8ae28', '#444c9b', '#64748B']

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


def _renderizar_envios_massa():
    """Renderiza a seção de envios em massa."""
    st.markdown("""
    <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-left:4px solid #444c9b;
                border-radius:14px;padding:24px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
        <h3 style="margin:0 0 4px;color:#444c9b;">📧 Envio em Massa de Cartas de VT</h3>
        <p style="color:#666666;font-size:15px;margin:0;">
            Selecione os funcionários e envie as cartas personalizadas automaticamente
        </p>
    </div>
    """, unsafe_allow_html=True)

    conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db'))
    df_pendentes = pd.read_sql_query("""
        SELECT id, nome, cpf, email, status_rota, cep_casa, cep_trabalho, matricula
        FROM jovens_rotas 
        WHERE status_rota != 'Implantado' OR status_rota IS NULL
        ORDER BY nome
    """, conexao)
    conexao.close()

    if df_pendentes.empty:
        st.info("✅ Não há funcionários pendentes de envio. Todos já foram implantados!")
        return

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
        st.info(f"📋 {len(df_com_email)} funcionário(s) com e-mail disponível para envio")
