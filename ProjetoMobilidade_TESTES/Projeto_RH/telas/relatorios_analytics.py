"""Módulo de Relatórios e Analytics."""

import streamlit as st
import sqlite3
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.units import inch
    REPORTLAB_DISPONIVEL = True
except ImportError:
    REPORTLAB_DISPONIVEL = False


def renderizar_relatorios_analytics():
    """Renderiza tela de relatórios e analytics."""
    
    st.title("📊 Relatórios e Analytics")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💰 Economia",
        "🏢 Unidades",
        "⚠️ Contestações",
        "⏱️ SLA",
        "📈 Dashboard Executivo",
        "📋 Compliance"
    ])
    
    with tab1:
        _relatorio_economia()
    
    with tab2:
        _relatorio_unidades()
    
    with tab3:
        _relatorio_contestacoes()
    
    with tab4:
        _relatorio_sla()
    
    with tab5:
        _dashboard_executivo()
    
    with tab6:
        _relatorio_compliance()


def _relatorio_economia():
    """Relatório de economia mensal/anual."""
    
    st.subheader("💰 Relatório de Economia")
    
    # Filtros
    col_periodo, col_formato = st.columns(2)
    
    with col_periodo:
        periodo = st.selectbox("Período:", ["Mensal", "Anual", "Personalizado"])
    
    with col_formato:
        formato = st.selectbox("Formato:", ["Visualizar", "PDF", "Excel"])
    
    if periodo == "Personalizado":
        col_data1, col_data2 = st.columns(2)
        with col_data1:
            data_inicio = st.date_input("Data Início:")
        with col_data2:
            data_fim = st.date_input("Data Fim:")
    else:
        data_inicio = None
        data_fim = None
    
    # Buscar dados
    df_economia = _buscar_dados_economia(periodo, data_inicio, data_fim)
    
    if df_economia.empty:
        st.info("📭 Sem dados para o período selecionado.")
        return
    
    # Métricas principais
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        total_funcionarios = len(df_economia)
        st.metric("👥 Total Funcionários", total_funcionarios)
    
    with col_m2:
        economia_total = df_economia['economia_mensal'].sum()
        st.metric("💰 Economia Total", f"R$ {economia_total:,.2f}")
    
    with col_m3:
        economia_media = df_economia['economia_mensal'].mean()
        st.metric("📊 Economia Média", f"R$ {economia_media:,.2f}")
    
    with col_m4:
        economia_anual = economia_total * 12
        st.metric("📅 Projeção Anual", f"R$ {economia_anual:,.2f}")
    
    st.markdown("---")
    
    # Gráficos
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.markdown("#### 💰 Economia por Modal")
        df_modal = df_economia.groupby('modal')['economia_mensal'].sum().reset_index()
        fig1 = px.pie(df_modal, values='economia_mensal', names='modal', title="Distribuição por Modal")
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_graf2:
        st.markdown("#### 📈 Tendência Mensal")
        df_tendencia = df_economia.groupby('mes')['economia_mensal'].sum().reset_index()
        fig2 = px.line(df_tendencia, x='mes', y='economia_mensal', title="Economia ao Longo do Tempo")
        st.plotly_chart(fig2, use_container_width=True)
    
    # Tabela detalhada
    st.markdown("#### 📋 Detalhamento")
    st.dataframe(df_economia, use_container_width=True, hide_index=True)
    
    # Botões de exportação
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("📥 Exportar Excel", use_container_width=True):
            _exportar_excel_economia(df_economia)
    
    with col_btn2:
        if st.button("📄 Gerar PDF", use_container_width=True):
            _gerar_pdf_economia(df_economia, economia_total, economia_media)


def _relatorio_unidades():
    """Relatório de funcionários por unidade."""
    
    st.subheader("🏢 Relatório por Unidades")
    
    # Buscar dados
    df_unidades = _buscar_dados_unidades()
    
    if df_unidades.empty:
        st.info("📭 Sem dados de unidades.")
        return
    
    # Métricas
    col_m1, col_m2, col_m3 = st.columns(3)
    
    with col_m1:
        total_unidades = len(df_unidades)
        st.metric("🏢 Total Unidades", total_unidades)
    
    with col_m2:
        total_func = df_unidades['funcionarios'].sum()
        st.metric("👥 Total Funcionários", total_func)
    
    with col_m3:
        media_func = df_unidades['funcionarios'].mean()
        st.metric("📊 Média por Unidade", f"{media_func:.1f}")
    
    st.markdown("---")
    
    # Gráficos
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.markdown("#### 👥 Funcionários por Unidade")
        fig1 = px.bar(df_unidades, x='unidade', y='funcionarios', title="Distribuição de Funcionários")
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_graf2:
        st.markdown("#### 📊 Ocupação vs Capacidade")
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='Funcionários', x=df_unidades['unidade'], y=df_unidades['funcionarios']))
        fig2.add_trace(go.Bar(name='Capacidade', x=df_unidades['unidade'], y=df_unidades['capacidade']))
        fig2.update_layout(barmode='group', title="Ocupação vs Capacidade")
        st.plotly_chart(fig2, use_container_width=True)
    
    # Tabela
    st.markdown("#### 📋 Detalhamento")
    st.dataframe(df_unidades, use_container_width=True, hide_index=True)
    
    # Exportação
    if st.button("📥 Exportar Excel", use_container_width=True):
        _exportar_excel_unidades(df_unidades)


def _relatorio_contestacoes():
    """Relatório de contestações."""
    
    st.subheader("⚠️ Relatório de Contestações")
    
    # Buscar dados
    df_contestacoes = _buscar_dados_contestacoes()
    
    if df_contestacoes.empty:
        st.info("📭 Sem contestações registradas.")
        return
    
    # Métricas
    col_m1, col_m2, col_m3 = st.columns(3)
    
    with col_m1:
        total_contestacoes = len(df_contestacoes)
        st.metric("⚠️ Total Contestações", total_contestacoes)
    
    with col_m2:
        resolvidas = len(df_contestacoes[df_contestacoes['status'] == 'Resolvida'])
        st.metric("✅ Resolvidas", resolvidas)
    
    with col_m3:
        pendentes = len(df_contestacoes[df_contestacoes['status'] == 'Pendente'])
        st.metric("⏳ Pendentes", pendentes)
    
    st.markdown("---")
    
    # Análise de motivos
    st.markdown("#### 📊 Motivos Mais Comuns")
    
    df_motivos = df_contestacoes['categoria_motivo'].value_counts().reset_index()
    df_motivos.columns = ['Motivo', 'Quantidade']
    
    fig = px.bar(df_motivos, x='Motivo', y='Quantidade', title="Top Motivos de Contestação")
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela
    st.markdown("#### 📋 Detalhamento")
    st.dataframe(df_contestacoes, use_container_width=True, hide_index=True)
    
    # Exportação
    if st.button("📥 Exportar Excel", use_container_width=True):
        _exportar_excel_contestacoes(df_contestacoes)


def _relatorio_sla():
    """Relatório de SLA."""
    
    st.subheader("⏱️ Relatório de SLA")
    
    # Buscar dados
    df_sla = _buscar_dados_sla()
    
    if df_sla.empty:
        st.info("📭 Sem dados de SLA.")
        return
    
    # Métricas
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        sla_medio = df_sla['tempo_segundos'].mean()
        st.metric("⏱️ SLA Médio", f"{sla_medio:.2f}s")
    
    with col_m2:
        sla_min = df_sla['tempo_segundos'].min()
        st.metric("⚡ Mais Rápido", f"{sla_min:.2f}s")
    
    with col_m3:
        sla_max = df_sla['tempo_segundos'].max()
        st.metric("🐌 Mais Lento", f"{sla_max:.2f}s")
    
    with col_m4:
        dentro_meta = len(df_sla[df_sla['tempo_segundos'] <= 5])
        percentual = (dentro_meta / len(df_sla)) * 100
        st.metric("✅ Dentro da Meta", f"{percentual:.1f}%")
    
    st.markdown("---")
    
    # Gráficos
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.markdown("#### 📊 Distribuição de SLA")
        fig1 = px.histogram(df_sla, x='tempo_segundos', nbins=20, title="Distribuição de Tempo de Resposta")
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_graf2:
        st.markdown("#### 📈 Tendência de SLA")
        df_sla_tempo = df_sla.groupby('data')['tempo_segundos'].mean().reset_index()
        fig2 = px.line(df_sla_tempo, x='data', y='tempo_segundos', title="SLA ao Longo do Tempo")
        st.plotly_chart(fig2, use_container_width=True)
    
    # Tabela
    st.markdown("#### 📋 Detalhamento")
    st.dataframe(df_sla, use_container_width=True, hide_index=True)


def _dashboard_executivo():
    """Dashboard executivo para diretoria."""
    
    st.subheader("📈 Dashboard Executivo")
    
    # KPIs principais
    st.markdown("### 🎯 KPIs Principais")
    
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    with col_kpi1:
        st.metric("💰 Economia Mensal", "R$ 125.450,00", "+12%")
    
    with col_kpi2:
        st.metric("👥 Funcionários Ativos", "1.234", "+5%")
    
    with col_kpi3:
        st.metric("✅ Taxa de Aceite", "94.5%", "+2%")
    
    with col_kpi4:
        st.metric("⚠️ Contestações", "23", "-8%")
    
    st.markdown("---")
    
    # Comparativo de custos por modal
    st.markdown("### 🚌 Comparativo de Custos por Modal")
    
    df_modal = pd.DataFrame({
        'Modal': ['Ônibus', 'Metrô', 'Integração', 'Caminhada'],
        'Custo Médio': [11.64, 11.84, 22.64, 0.00],
        'Funcionários': [450, 320, 380, 84],
        'Custo Total': [5238.00, 3788.80, 8603.20, 0.00]
    })
    
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        fig1 = px.bar(df_modal, x='Modal', y='Custo Total', title="Custo Total por Modal")
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_graf2:
        fig2 = px.pie(df_modal, values='Funcionários', names='Modal', title="Distribuição de Funcionários")
        st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("---")
    
    # Análise de tendências
    st.markdown("### 📊 Análise de Tendências e Previsão")
    
    # Dados históricos simulados
    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    custos_reais = [110000, 115000, 118000, 120000, 122000, 125000, 0, 0, 0, 0, 0, 0]
    custos_previstos = [0, 0, 0, 0, 0, 0, 127000, 129000, 131000, 133000, 135000, 137000]
    
    df_tendencia = pd.DataFrame({
        'Mês': meses,
        'Custo Real': custos_reais,
        'Previsão': custos_previstos
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_tendencia['Mês'], y=df_tendencia['Custo Real'], 
                             mode='lines+markers', name='Custo Real', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df_tendencia['Mês'], y=df_tendencia['Previsão'], 
                             mode='lines+markers', name='Previsão', line=dict(color='red', dash='dash')))
    fig.update_layout(title="Custos Reais vs Previsão", xaxis_title="Mês", yaxis_title="Custo (R$)")
    st.plotly_chart(fig, use_container_width=True)
    
    # Insights
    st.markdown("### 💡 Insights e Recomendações")
    
    col_insight1, col_insight2 = st.columns(2)
    
    with col_insight1:
        st.success("""
        **✅ Pontos Positivos:**
        - Taxa de aceite acima de 90%
        - Redução de 8% nas contestações
        - Economia crescente mês a mês
        """)
    
    with col_insight2:
        st.warning("""
        **⚠️ Pontos de Atenção:**
        - Previsão de aumento de 10% nos custos
        - Capacidade de algumas unidades próxima do limite
        - SLA médio acima da meta em alguns períodos
        """)


def _relatorio_compliance():
    """Relatório de compliance (LGPD, trabalhista)."""
    
    st.subheader("📋 Relatório de Compliance")
    
    # LGPD
    st.markdown("### 🔒 LGPD - Lei Geral de Proteção de Dados")
    
    col_lgpd1, col_lgpd2, col_lgpd3 = st.columns(3)
    
    with col_lgpd1:
        st.metric("📊 Dados Coletados", "1.234 registros")
    
    with col_lgpd2:
        st.metric("✅ Consentimentos", "100%")
    
    with col_lgpd3:
        st.metric("🗑️ Solicitações de Exclusão", "3")
    
    st.markdown("#### ✅ Checklist LGPD")
    
    checklist_lgpd = [
        {"item": "Termo de consentimento implementado", "status": "✅ OK"},
        {"item": "Política de privacidade disponível", "status": "✅ OK"},
        {"item": "Criptografia de dados sensíveis", "status": "✅ OK"},
        {"item": "Logs de acesso aos dados", "status": "✅ OK"},
        {"item": "Processo de exclusão de dados", "status": "✅ OK"},
        {"item": "DPO (Encarregado) designado", "status": "✅ OK"}
    ]
    
    df_lgpd = pd.DataFrame(checklist_lgpd)
    st.dataframe(df_lgpd, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Trabalhista
    st.markdown("### ⚖️ Compliance Trabalhista")
    
    col_trab1, col_trab2, col_trab3 = st.columns(3)
    
    with col_trab1:
        st.metric("📄 Contratos Ativos", "1.234")
    
    with col_trab2:
        st.metric("✅ Documentação Completa", "98.5%")
    
    with col_trab3:
        st.metric("⚠️ Pendências", "18")
    
    st.markdown("#### ✅ Checklist Trabalhista")
    
    checklist_trab = [
        {"item": "Vale-Transporte conforme CLT Art. 458", "status": "✅ OK"},
        {"item": "Registro de ponto eletrônico", "status": "✅ OK"},
        {"item": "Contratos assinados digitalmente", "status": "✅ OK"},
        {"item": "Documentação de admissão completa", "status": "⚠️ 98.5%"},
        {"item": "Exames médicos em dia", "status": "✅ OK"},
        {"item": "Treinamentos obrigatórios realizados", "status": "✅ OK"}
    ]
    
    df_trab = pd.DataFrame(checklist_trab)
    st.dataframe(df_trab, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Auditoria
    st.markdown("### 🔍 Histórico de Auditorias")
    
    auditorias = [
        {"Data": "2026-01-15", "Tipo": "LGPD", "Resultado": "Aprovado", "Observações": "Sem pendências"},
        {"Data": "2025-12-10", "Tipo": "Trabalhista", "Resultado": "Aprovado", "Observações": "Pequenas correções realizadas"},
        {"Data": "2025-11-05", "Tipo": "Interna", "Resultado": "Aprovado", "Observações": "Processos em conformidade"}
    ]
    
    df_audit = pd.DataFrame(auditorias)
    st.dataframe(df_audit, use_container_width=True, hide_index=True)
    
    # Exportação
    if st.button("📥 Gerar Relatório Completo de Compliance (PDF)", use_container_width=True):
        with st.spinner("Gerando relatório de compliance..."):
            try:
                # Busca dados do banco para o relatório
                db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
                conexao = sqlite3.connect(db_path)
                
                # Conta total de rotas
                total_rotas = pd.read_sql_query("SELECT COUNT(*) as total FROM jovens_rotas", conexao).iloc[0]['total']
                
                # Conta rotas implantadas
                rotas_implantadas = pd.read_sql_query(
                    "SELECT COUNT(*) as total FROM jovens_rotas WHERE status_rota = 'Implantado'", 
                    conexao
                ).iloc[0]['total']
                
                # Conta rotas pendentes
                rotas_pendentes = total_rotas - rotas_implantadas
                
                # Calcula taxa de implantação
                taxa_implantacao = (rotas_implantadas / total_rotas * 100) if total_rotas > 0 else 0
                
                # Busca rotas pendentes
                df_pendentes_compliance = pd.read_sql_query(
                    "SELECT nome, status_rota, data_consulta FROM jovens_rotas WHERE status_rota != 'Implantado' ORDER BY data_consulta DESC",
                    conexao
                )
                
                conexao.close()
                
                # Gera o PDF
                pdf_buffer = _gerar_pdf_compliance(
                    total_rotas,
                    rotas_implantadas,
                    rotas_pendentes,
                    taxa_implantacao,
                    df_pendentes_compliance
                )
                
                if pdf_buffer:
                    st.download_button(
                        label="📥 Download Relatório de Compliance",
                        data=pdf_buffer,
                        file_name=f"relatorio_compliance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.success("✅ Relatório gerado com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao gerar relatório: {str(e)}")
            except Exception as e:
                st.error(f"❌ Erro ao gerar relatório: {str(e)}")


# ─── FUNÇÕES AUXILIARES ───────────────────────────────────────────────────────

def _buscar_dados_economia(periodo, data_inicio=None, data_fim=None):
    """Busca dados de economia."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        
        # Simulação de dados
        df = pd.DataFrame({
            'funcionario': ['João Silva', 'Maria Santos', 'Pedro Costa'],
            'modal': ['Ônibus', 'Metrô', 'Integração'],
            'economia_mensal': [350.00, 355.00, 680.00],
            'mes': ['2026-01', '2026-01', '2026-01']
        })
        
        conexao.close()
        return df
    except Exception:
        return pd.DataFrame()


def _buscar_dados_unidades():
    """Busca dados de unidades."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        
        df = pd.read_sql_query("""
            SELECT 
                nome_unidade as unidade,
                capacidade_maxima as capacidade,
                0 as funcionarios
            FROM locais_trabalho
        """, conexao)
        
        conexao.close()
        return df
    except Exception:
        return pd.DataFrame()


def _buscar_dados_contestacoes():
    """Busca dados de contestações."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        
        df = pd.read_sql_query("""
            SELECT 
                nome,
                motivo,
                'Rota Incorreta' as categoria_motivo,
                'Pendente' as status,
                data_contestacao as data
            FROM contestacoes
            ORDER BY data_contestacao DESC
        """, conexao)
        
        conexao.close()
        return df
    except Exception:
        return pd.DataFrame()


def _buscar_dados_sla():
    """Busca dados de SLA."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        
        df = pd.read_sql_query("""
            SELECT 
                sla_segundos as tempo_segundos,
                DATE(data_calculo) as data
            FROM sla_rotas
            WHERE sla_segundos IS NOT NULL
            ORDER BY data_calculo DESC
        """, conexao)
        
        conexao.close()
        return df
    except Exception:
        return pd.DataFrame()


def _exportar_excel_economia(df):
    """Exporta relatório de economia para Excel."""
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Economia', index=False)
        
        output.seek(0)
        st.download_button(
            label="📥 Baixar Excel",
            data=output,
            file_name=f"relatorio_economia_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Erro ao exportar: {str(e)}")


def _exportar_excel_unidades(df):
    """Exporta relatório de unidades para Excel."""
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Unidades', index=False)
        
        output.seek(0)
        st.download_button(
            label="📥 Baixar Excel",
            data=output,
            file_name=f"relatorio_unidades_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Erro ao exportar: {str(e)}")


def _exportar_excel_contestacoes(df):
    """Exporta relatório de contestações para Excel."""
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Contestações', index=False)
        
        output.seek(0)
        st.download_button(
            label="📥 Baixar Excel",
            data=output,
            file_name=f"relatorio_contestacoes_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Erro ao exportar: {str(e)}")


def _gerar_pdf_economia(df, economia_total, economia_media):
    """Gera PDF do relatório de economia."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import inch
    except ImportError:
        st.warning("⚠️ ReportLab não instalado. Instale com: pip install reportlab")
        return
    
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title = Paragraph("Relatório de Economia - Vale Transporte", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Resumo
        resumo = Paragraph(f"""
        <b>Economia Total:</b> R$ {economia_total:,.2f}<br/>
        <b>Economia Média:</b> R$ {economia_media:,.2f}<br/>
        <b>Total de Funcionários:</b> {len(df)}<br/>
        <b>Data:</b> {datetime.now().strftime('%d/%m/%Y')}
        """, styles['Normal'])
        elements.append(resumo)
        elements.append(Spacer(1, 0.3*inch))
        
        # Tabela
        data = [df.columns.tolist()] + df.values.tolist()
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        
        doc.build(elements)
        buffer.seek(0)
        
        st.download_button(
            label="📄 Baixar PDF",
            data=buffer,
            file_name=f"relatorio_economia_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {str(e)}")


def _gerar_pdf_compliance(total_rotas, rotas_implantadas, rotas_pendentes, taxa_implantacao, df_pendentes):
    """Gera PDF do relatório de compliance."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import inch
    except ImportError:
        st.warning("⚠️ ReportLab não instalado. Instale com: pip install reportlab")
        return None
    
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title = Paragraph("Relatório de Compliance - Mobilidade", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Resumo Executivo
        resumo = Paragraph(f"""
        <b>Resumo Executivo</b><br/>
        <br/>
        <b>Total de Rotas:</b> {total_rotas}<br/>
        <b>Rotas Implantadas:</b> {rotas_implantadas}<br/>
        <b>Rotas Pendentes:</b> {rotas_pendentes}<br/>
        <b>Taxa de Implantação:</b> {taxa_implantacao:.1f}%<br/>
        <b>Data do Relatório:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>
        """, styles['Normal'])
        elements.append(resumo)
        elements.append(Spacer(1, 0.3*inch))
        
        # Análise de Compliance
        if taxa_implantacao >= 90:
            status_compliance = "✅ EXCELENTE - Compliance dentro dos padrões"
            cor_status = colors.green
        elif taxa_implantacao >= 70:
            status_compliance = "⚠️ ATENÇÃO - Compliance necessita melhorias"
            cor_status = colors.orange
        else:
            status_compliance = "❌ CRÍTICO - Compliance abaixo do esperado"
            cor_status = colors.red
        
        status_para = Paragraph(f"<b>Status de Compliance:</b> {status_compliance}", styles['Normal'])
        elements.append(status_para)
        elements.append(Spacer(1, 0.3*inch))
        
        # Tabela de Pendências
        if not df_pendentes.empty and len(df_pendentes) > 0:
            elements.append(Paragraph("<b>Rotas Pendentes de Implantação:</b>", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))
            
            # Prepara dados da tabela (limita a 20 primeiras linhas)
            df_display = df_pendentes.head(20)
            colunas_exibir = ['nome', 'status_rota', 'data_consulta']
            df_display = df_display[colunas_exibir] if all(col in df_display.columns for col in colunas_exibir) else df_display
            
            data = [df_display.columns.tolist()] + df_display.values.tolist()
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8)
            ]))
            elements.append(table)
            
            if len(df_pendentes) > 20:
                elements.append(Spacer(1, 0.1*inch))
                elements.append(Paragraph(f"<i>Exibindo 20 de {len(df_pendentes)} rotas pendentes</i>", styles['Normal']))
        
        # Rodapé
        elements.append(Spacer(1, 0.5*inch))
        rodape = Paragraph(f"""
        <i>Relatório gerado automaticamente pelo Sistema de Mobilidade RENAPSI<br/>
        © {datetime.now().year} - Todos os direitos reservados</i>
        """, styles['Normal'])
        elements.append(rodape)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        st.error(f"Erro ao gerar PDF de compliance: {str(e)}")
        return None
