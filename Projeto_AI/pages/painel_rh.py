"""
Painel de Controle RH - Assistente Demà
Dashboard Analítico para Gestão de Atendimentos
"""

import os
import json
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re

# Configuração da página
st.set_page_config(
    page_title="Painel RH - Demà",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inicializar estado de autenticação
if "admin_autenticado" not in st.session_state:
    st.session_state.admin_autenticado = False


def tela_login_admin():
    """Tela de login para administradores do RH"""
    st.title("🔐 Painel Administrativo - RH")
    st.markdown("---")
    st.warning("⚠️ Acesso restrito exclusivamente para gestores de RH autorizados.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        senha_admin = st.text_input(
            "Digite a senha de administrador",
            type="password",
            key="senha_admin_input"
        )
        
        if st.button("🔓 Acessar Painel", use_container_width=True):
            if senha_admin == "ADMIN_RENAPSI2026":
                st.session_state.admin_autenticado = True
                st.success("✅ Acesso autorizado! Carregando painel...")
                st.rerun()
            else:
                st.error("❌ Senha incorreta. Acesso negado.")
    
    st.markdown("---")
    st.caption("🔒 Sistema protegido por autenticação administrativa.")


def carregar_dados():
    """
    Carrega e processa os dados do arquivo logs_atendimento.jsonl
    Retorna um DataFrame do Pandas
    """
    caminho_log = "logs_atendimento.jsonl"
    
    # Verificar se o arquivo existe
    if not os.path.exists(caminho_log):
        return pd.DataFrame()
    
    # Ler arquivo JSONL linha por linha
    dados = []
    try:
        with open(caminho_log, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if linha:  # Ignorar linhas vazias
                    registro = json.loads(linha)
                    dados.append(registro)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()
    
    # Converter para DataFrame
    if dados:
        df = pd.DataFrame(dados)
        # Converter timestamp para datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    else:
        return pd.DataFrame()


def extrair_palavras_frequentes(df, coluna='pergunta_usuario', top_n=10):
    """
    Extrai as palavras mais frequentes de uma coluna de texto,
    excluindo stopwords comuns em português
    """
    # Stopwords básicas em português
    stopwords = {
        'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das',
        'em', 'no', 'na', 'nos', 'nas', 'por', 'para', 'com', 'sem', 'sob',
        'e', 'ou', 'mas', 'que', 'como', 'quando', 'onde', 'qual', 'quais',
        'eu', 'tu', 'ele', 'ela', 'nós', 'vós', 'eles', 'elas',
        'meu', 'minha', 'seu', 'sua', 'nosso', 'nossa',
        'é', 'são', 'foi', 'ser', 'estar', 'ter', 'fazer', 'ir',
        'me', 'te', 'se', 'lhe', 'nos', 'vos', 'lhes',
        'ao', 'à', 'aos', 'às', 'pelo', 'pela', 'pelos', 'pelas',
        'este', 'esta', 'esse', 'essa', 'aquele', 'aquela',
        'mais', 'menos', 'muito', 'pouco', 'todo', 'toda',
        'já', 'ainda', 'só', 'também', 'até', 'depois', 'antes',
        'quero', 'quer', 'pode', 'posso', 'preciso', 'tenho',
        'bom', 'boa', 'dia', 'noite', 'tarde', 'olá', 'oi'
    }
    
    # Concatenar todos os textos
    texto_completo = ' '.join(df[coluna].astype(str).str.lower())
    
    # Extrair palavras (apenas letras, mínimo 3 caracteres)
    palavras = re.findall(r'\b[a-záàâãéèêíïóôõöúçñ]{3,}\b', texto_completo)
    
    # Filtrar stopwords
    palavras_filtradas = [p for p in palavras if p not in stopwords]
    
    # Contar frequências
    contagem = Counter(palavras_filtradas)
    
    # Retornar top N
    return dict(contagem.most_common(top_n))


def aplicar_filtros(df, palavra_chave, data_inicio, data_fim):
    """
    Aplica filtros dinâmicos ao DataFrame
    """
    df_filtrado = df.copy()
    
    # Filtro por palavra-chave
    if palavra_chave:
        df_filtrado = df_filtrado[
            df_filtrado['pergunta_usuario'].str.contains(palavra_chave, case=False, na=False)
        ]
    
    # Filtro por data
    if data_inicio and data_fim:
        df_filtrado = df_filtrado[
            (df_filtrado['data'] >= data_inicio) & 
            (df_filtrado['data'] <= data_fim)
        ]
    elif data_inicio:
        df_filtrado = df_filtrado[df_filtrado['data'] >= data_inicio]
    elif data_fim:
        df_filtrado = df_filtrado[df_filtrado['data'] <= data_fim]
    
    return df_filtrado


def dashboard_principal():
    """Interface principal do dashboard analítico"""
    
    st.title("📊 Painel de Controle RH - Assistente Demà")
    st.markdown("### Dashboard Analítico Enterprise")
    st.markdown("---")
    
    # Carregar dados
    df = carregar_dados()
    
    # Verificar se há dados
    if df.empty:
        st.warning("⚠️ Nenhum dado de atendimento encontrado ainda.")
        st.info("💡 Os logs serão gerados automaticamente conforme os jovens aprendizes interagirem com o assistente Demà.")
        return
    
    # Extrair informações adicionais
    df['data'] = df['timestamp'].dt.date
    df['hora'] = df['timestamp'].dt.hour
    df['dia_semana'] = df['timestamp'].dt.day_name()
    df['tamanho_pergunta'] = df['pergunta_usuario'].str.len()
    df['tamanho_resposta'] = df['resposta_bot'].str.len()
    
    # === BARRA LATERAL DE FILTROS ===
    with st.sidebar:
        st.markdown("### 🔍 Filtros de Análise")
        st.markdown("---")
        
        # Filtro de palavra-chave
        palavra_chave = st.text_input(
            "🔎 Buscar palavra-chave nas perguntas",
            placeholder="Ex: saldo, recarga, bloqueio...",
            help="Digite uma palavra para filtrar as perguntas dos usuários"
        )
        
        st.markdown("---")
        
        # Filtro de período
        st.markdown("📅 **Filtrar por Período**")
        
        col_data1, col_data2 = st.columns(2)
        
        with col_data1:
            data_inicio = st.date_input(
                "Data Início",
                value=None,
                max_value=datetime.now().date(),
                help="Selecione a data inicial"
            )
        
        with col_data2:
            data_fim = st.date_input(
                "Data Fim",
                value=None,
                max_value=datetime.now().date(),
                help="Selecione a data final"
            )
        
        st.markdown("---")
        
        # Botão para limpar filtros
        if st.button("🔄 Limpar Filtros", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        st.success("✅ Autenticado como Admin")
        
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.admin_autenticado = False
            st.rerun()
    
    # === APLICAR FILTROS ===
    df_filtrado = aplicar_filtros(df, palavra_chave, data_inicio, data_fim)
    
    # Verificar se há dados após filtros
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum resultado encontrado com os filtros aplicados.")
        st.info("💡 Tente ajustar os critérios de busca.")
        return
    
    # Mostrar indicador de filtros ativos
    if palavra_chave or data_inicio or data_fim:
        filtros_ativos = []
        if palavra_chave:
            filtros_ativos.append(f"Palavra-chave: '{palavra_chave}'")
        if data_inicio:
            filtros_ativos.append(f"De: {data_inicio}")
        if data_fim:
            filtros_ativos.append(f"Até: {data_fim}")
        
        st.info(f"🔍 **Filtros ativos:** {' | '.join(filtros_ativos)}")
        st.markdown("---")
    
    # === MÉTRICAS PRINCIPAIS ===
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_interacoes = len(df_filtrado)
        st.metric(
            label="📈 Total de Interações",
            value=total_interacoes,
            delta=f"{(total_interacoes/len(df)*100):.1f}% do total" if len(df) > 0 else None
        )
    
    with col2:
        dias_unicos = df_filtrado['data'].nunique()
        st.metric(
            label="📅 Dias com Atendimento",
            value=dias_unicos
        )
    
    with col3:
        media_perguntas_dia = round(total_interacoes / dias_unicos, 1) if dias_unicos > 0 else 0
        st.metric(
            label="💬 Média de Perguntas/Dia",
            value=media_perguntas_dia
        )
    
    with col4:
        hora_pico = df_filtrado['hora'].mode()[0] if not df_filtrado.empty else 0
        st.metric(
            label="⏰ Horário de Pico",
            value=f"{hora_pico}h"
        )
    
    st.markdown("---")
    
    # === GRÁFICOS INTERATIVOS PLOTLY ===
    col_grafico1, col_grafico2 = st.columns(2)
    
    with col_grafico1:
        st.subheader("📊 Volume de Atendimentos por Dia")
        
        # Preparar dados
        atendimentos_por_dia = df_filtrado.groupby('data').size().reset_index(name='Quantidade')
        atendimentos_por_dia['data'] = pd.to_datetime(atendimentos_por_dia['data'])
        
        # Criar gráfico Plotly
        fig_dia = px.line(
            atendimentos_por_dia,
            x='data',
            y='Quantidade',
            markers=True,
            title='Evolução Temporal dos Atendimentos'
        )
        
        fig_dia.update_traces(
            line_color='#2563eb',
            marker=dict(size=8, color='#2563eb')
        )
        
        fig_dia.update_layout(
            xaxis_title='Data',
            yaxis_title='Número de Atendimentos',
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_dia, use_container_width=True)
    
    with col_grafico2:
        st.subheader("⏰ Distribuição por Horário")
        
        # Preparar dados
        atendimentos_por_hora = df_filtrado['hora'].value_counts().sort_index().reset_index()
        atendimentos_por_hora.columns = ['Hora', 'Quantidade']
        
        # Criar gráfico Plotly
        fig_hora = px.bar(
            atendimentos_por_hora,
            x='Hora',
            y='Quantidade',
            title='Volume de Atendimentos por Hora do Dia',
            color='Quantidade',
            color_continuous_scale='Blues'
        )
        
        fig_hora.update_layout(
            xaxis_title='Hora do Dia',
            yaxis_title='Número de Atendimentos',
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_hora, use_container_width=True)
    
    st.markdown("---")
    
    # === ANÁLISE DE CONTEÚDO ===
    st.subheader("🔍 Análise de Conteúdo")
    
    col_analise1, col_analise2, col_analise3 = st.columns(3)
    
    with col_analise1:
        st.metric(
            label="📝 Tamanho Médio das Perguntas",
            value=f"{df_filtrado['tamanho_pergunta'].mean():.0f} caracteres"
        )
    
    with col_analise2:
        st.metric(
            label="💬 Tamanho Médio das Respostas",
            value=f"{df_filtrado['tamanho_resposta'].mean():.0f} caracteres"
        )
    
    with col_analise3:
        pergunta_mais_longa = df_filtrado['tamanho_pergunta'].max()
        st.metric(
            label="📏 Pergunta Mais Longa",
            value=f"{pergunta_mais_longa} caracteres"
        )
    
    st.markdown("---")
    
    # === NUVEM DE PALAVRAS (ANÁLISE DE FREQUÊNCIA) ===
    col_palavras, col_topicos = st.columns(2)
    
    with col_palavras:
        st.subheader("💬 Palavras Mais Frequentes nas Perguntas")
        
        palavras_freq = extrair_palavras_frequentes(df_filtrado, 'pergunta_usuario', top_n=15)
        
        if palavras_freq:
            df_palavras = pd.DataFrame(
                list(palavras_freq.items()),
                columns=['Palavra', 'Frequência']
            ).sort_values('Frequência', ascending=True)
            
            fig_palavras = px.bar(
                df_palavras,
                x='Frequência',
                y='Palavra',
                orientation='h',
                title='Top 15 Palavras-Chave',
                color='Frequência',
                color_continuous_scale='Viridis'
            )
            
            fig_palavras.update_layout(
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400
            )
            
            st.plotly_chart(fig_palavras, use_container_width=True)
        else:
            st.info("Dados insuficientes para análise de palavras.")
    
    with col_topicos:
        st.subheader("❓ Tópicos Mais Consultados")
        
        # Análise de palavras-chave específicas
        palavras_chave = {
            'Saldo': ['saldo', 'consultar'],
            'Recarga': ['recarga', 'recarregar', 'carregar'],
            'Bloqueio': ['bloqueio', 'bloqueado', 'bloquear'],
            'Cartão': ['cartão', 'bilhete', 'card'],
            'Transporte': ['transporte', 'ônibus', 'metrô', 'trem']
        }
        
        contagem_topicos = {}
        
        for topico, palavras in palavras_chave.items():
            contagem = 0
            for palavra in palavras:
                contagem += df_filtrado['pergunta_usuario'].str.lower().str.contains(palavra, na=False).sum()
            if contagem > 0:
                contagem_topicos[topico] = contagem
        
        if contagem_topicos:
            df_topicos = pd.DataFrame(
                list(contagem_topicos.items()),
                columns=['Tópico', 'Quantidade']
            ).sort_values('Quantidade', ascending=True)
            
            fig_topicos = px.bar(
                df_topicos,
                x='Quantidade',
                y='Tópico',
                orientation='h',
                title='Categorias de Dúvidas',
                color='Quantidade',
                color_continuous_scale='RdYlGn'
            )
            
            fig_topicos.update_layout(
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400
            )
            
            st.plotly_chart(fig_topicos, use_container_width=True)
        else:
            st.info("Ainda não há dados suficientes para análise de tópicos.")
    
    st.markdown("---")
    
    # === ÚLTIMOS ATENDIMENTOS ===
    st.subheader("📋 Últimos Atendimentos")
    
    # Configurar exibição do DataFrame
    df_exibicao = df_filtrado[['timestamp', 'pergunta_usuario', 'resposta_bot']].copy()
    df_exibicao = df_exibicao.sort_values('timestamp', ascending=False)
    df_exibicao['timestamp'] = df_exibicao['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Renomear colunas para melhor visualização
    df_exibicao.columns = ['Data/Hora', 'Pergunta do Jovem Aprendiz', 'Resposta do Demà']
    
    st.dataframe(
        df_exibicao,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    st.markdown("---")
    st.caption("🤖 Dashboard Enterprise gerado automaticamente | Powered by Plotly + Streamlit | Renapsi © 2026")


# === CONTROLE DE FLUXO PRINCIPAL ===
if not st.session_state.admin_autenticado:
    tela_login_admin()
else:
    dashboard_principal()
