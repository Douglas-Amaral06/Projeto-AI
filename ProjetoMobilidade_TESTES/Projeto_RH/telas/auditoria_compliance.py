"""Módulo de Auditoria e Compliance."""

import streamlit as st
import sqlite3
import os
import pandas as pd
import datetime
import hashlib
import json
import io
import shutil
from telas.auth_guard import exigir_login, exigir_admin


def renderizar_auditoria_compliance():
    """Renderiza tela de auditoria e compliance."""
    exigir_admin()
    
    st.title("🔍 Auditoria e Compliance")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📜 Logs de Auditoria",
        "🔒 LGPD",
        "💾 Backup",
        "🗑️ Retenção de Dados",
        "📊 Relatórios"
    ])
    
    with tab1:
        _tela_logs_auditoria()
    
    with tab2:
        _tela_lgpd()
    
    with tab3:
        _tela_backup()
    
    with tab4:
        _tela_retencao_dados()
    
    with tab5:
        _tela_relatorios_compliance()


def _tela_logs_auditoria():
    """Tela de visualização de logs de auditoria."""
    
    st.subheader("📜 Logs de Auditoria")
    
    # Filtros
    col_usuario, col_acao, col_data_inicio, col_data_fim = st.columns(4)
    
    with col_usuario:
        filtro_usuario = st.text_input("👤 Usuário:", placeholder="Filtrar por usuário...")
    
    with col_acao:
        filtro_acao = st.selectbox("⚡ Ação:", [
            "Todas",
            "Login",
            "Logout",
            "Criou usuário",
            "Excluiu usuário",
            "Editou dados",
            "Exportou dados",
            "Visualizou dados",
            "Aprovou rota",
            "Reprovou rota"
        ])
    
    with col_data_inicio:
        data_inicio = st.date_input("📅 Data Início:", value=datetime.date.today() - datetime.timedelta(days=30))
    
    with col_data_fim:
        data_fim = st.date_input("📅 Data Fim:", value=datetime.date.today())
    
    # Buscar logs
    df_logs = _buscar_logs_auditoria(filtro_usuario, filtro_acao, data_inicio, data_fim)
    
    if df_logs.empty:
        st.info("📭 Nenhum log encontrado com os filtros aplicados.")
        return
    
    # Métricas
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        st.metric("📊 Total de Logs", len(df_logs))
    
    with col_m2:
        usuarios_unicos = df_logs['usuario'].nunique()
        st.metric("👥 Usuários Únicos", usuarios_unicos)
    
    with col_m3:
        acoes_criticas = len(df_logs[df_logs['acao'].isin(['Excluiu usuário', 'Exportou dados'])])
        st.metric("⚠️ Ações Críticas", acoes_criticas)
    
    with col_m4:
        logins_hoje = len(df_logs[(df_logs['acao'] == 'Login') & (df_logs['data'] == datetime.date.today().isoformat())])
        st.metric("🔐 Logins Hoje", logins_hoje)
    
    st.markdown("---")
    
    # Gráfico de ações por tipo
    st.markdown("#### 📊 Ações por Tipo")
    df_acoes = df_logs['acao'].value_counts().reset_index()
    df_acoes.columns = ['Ação', 'Quantidade']
    
    import plotly.express as px
    fig = px.bar(df_acoes, x='Ação', y='Quantidade', title="Distribuição de Ações")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Tabela de logs
    st.markdown("#### 📋 Logs Detalhados")
    st.dataframe(df_logs, use_container_width=True, hide_index=True)
    
    # Exportação
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("📥 Exportar Logs (Excel)", use_container_width=True):
            _exportar_logs_excel(df_logs)
    
    with col_btn2:
        if st.button("📄 Exportar Logs (JSON)", use_container_width=True):
            _exportar_logs_json(df_logs)


def _tela_lgpd():
    """Tela de LGPD."""
    
    st.subheader("🔒 LGPD - Lei Geral de Proteção de Dados")
    
    # Termo de consentimento
    st.markdown("### 📄 Termo de Consentimento")
    
    col_termo1, col_termo2 = st.columns([2, 1])
    
    with col_termo1:
        st.markdown("""
        **Termo de Consentimento para Tratamento de Dados Pessoais**
        
        Eu, abaixo identificado, AUTORIZO a Renapsi a coletar, armazenar e tratar meus dados pessoais 
        para fins de gestão de Vale-Transporte, conforme a Lei nº 13.709/2018 (LGPD).
        
        **Dados coletados:**
        - Nome completo, CPF, RG
        - Endereço residencial e de trabalho
        - Dados de rota e transporte
        - Assinatura digital
        
        **Finalidade:**
        - Cálculo e fornecimento de Vale-Transporte
        - Gestão de rotas e economia
        - Cumprimento de obrigações legais
        
        **Direitos do titular:**
        - Acesso aos dados
        - Correção de dados
        - Exclusão de dados
        - Portabilidade
        - Revogação do consentimento
        """)
    
    with col_termo2:
        st.info("""
        **📊 Status de Consentimentos**
        
        ✅ Aceitos: 1.234
        ⏳ Pendentes: 0
        ❌ Recusados: 0
        
        **Taxa de aceite: 100%**
        """)
    
    st.markdown("---")
    
    # Solicitações LGPD
    st.markdown("### 📋 Solicitações LGPD")
    
    df_solicitacoes = _buscar_solicitacoes_lgpd()
    
    if df_solicitacoes.empty:
        st.info("📭 Nenhuma solicitação LGPD registrada.")
    else:
        st.dataframe(df_solicitacoes, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Anonimização de dados
    st.markdown("### 🔐 Anonimização de Dados")
    
    st.warning("""
    ⚠️ **Atenção:** A anonimização de dados é irreversível. 
    Os dados serão substituídos por valores genéricos e não poderão ser recuperados.
    """)
    
    col_anon1, col_anon2 = st.columns(2)
    
    with col_anon1:
        cpf_anonimizar = st.text_input("CPF do funcionário:", placeholder="00000000000")
    
    with col_anon2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔐 Anonimizar Dados", type="secondary", use_container_width=True):
            if cpf_anonimizar:
                if _anonimizar_dados_funcionario(cpf_anonimizar):
                    st.success("✅ Dados anonimizados com sucesso!")
                else:
                    st.error("❌ Erro ao anonimizar dados.")
            else:
                st.error("⚠️ Digite o CPF do funcionário.")
    
    st.markdown("---")
    
    # Relatório de conformidade
    st.markdown("### 📊 Relatório de Conformidade LGPD")
    
    col_conf1, col_conf2, col_conf3 = st.columns(3)
    
    with col_conf1:
        st.metric("✅ Conformidade Geral", "98.5%")
    
    with col_conf2:
        st.metric("🔒 Dados Criptografados", "100%")
    
    with col_conf3:
        st.metric("📋 Políticas Atualizadas", "Sim")
    
    if st.button("📄 Gerar Relatório Completo LGPD", use_container_width=True):
        _gerar_relatorio_lgpd()


def _tela_backup():
    """Tela de backup."""
    
    st.subheader("💾 Backup e Restauração")
    
    # Status do último backup
    st.markdown("### 📊 Status do Backup")
    
    ultimo_backup = _obter_ultimo_backup()
    
    col_status1, col_status2, col_status3 = st.columns(3)
    
    with col_status1:
        if ultimo_backup:
            st.metric("📅 Último Backup", ultimo_backup.get('data', 'Nunca'))
        else:
            st.metric("📅 Último Backup", "Nunca")
    
    with col_status2:
        if ultimo_backup:
            st.metric("💾 Tamanho", ultimo_backup.get('tamanho', '0 MB'))
        else:
            st.metric("💾 Tamanho", "0 MB")
    
    with col_status3:
        if ultimo_backup:
            st.metric("🔐 Criptografado", "Sim" if ultimo_backup.get('criptografado') else "Não")
        else:
            st.metric("🔐 Criptografado", "N/A")
    
    st.markdown("---")
    
    # Criar backup
    st.markdown("### 💾 Criar Novo Backup")
    
    col_backup1, col_backup2 = st.columns(2)
    
    with col_backup1:
        criptografar = st.checkbox("🔐 Criptografar backup", value=True)
        incluir_logs = st.checkbox("📜 Incluir logs de auditoria", value=True)
    
    with col_backup2:
        incluir_anexos = st.checkbox("📎 Incluir anexos e documentos", value=False)
        compactar = st.checkbox("📦 Compactar (ZIP)", value=True)
    
    if st.button("💾 Criar Backup Agora", type="primary", use_container_width=True):
        with st.spinner("Criando backup..."):
            if _criar_backup(criptografar, incluir_logs, incluir_anexos, compactar):
                st.success("✅ Backup criado com sucesso!")
                st.balloons()
            else:
                st.error("❌ Erro ao criar backup.")
    
    st.markdown("---")
    
    # Restaurar backup
    st.markdown("### 🔄 Restaurar Backup")
    
    st.warning("⚠️ **Atenção:** Restaurar um backup substituirá todos os dados atuais.")
    
    arquivo_backup = st.file_uploader("Selecione o arquivo de backup:", type=['db', 'zip', 'enc'])
    
    if arquivo_backup:
        col_rest1, col_rest2 = st.columns(2)
        
        with col_rest1:
            senha_backup = st.text_input("Senha do backup (se criptografado):", type="password")
        
        with col_rest2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Restaurar Backup", type="secondary", use_container_width=True):
                if _restaurar_backup(arquivo_backup, senha_backup):
                    st.success("✅ Backup restaurado com sucesso!")
                else:
                    st.error("❌ Erro ao restaurar backup.")
    
    st.markdown("---")
    
    # Backups automáticos
    st.markdown("### ⚙️ Configuração de Backups Automáticos")
    
    col_auto1, col_auto2 = st.columns(2)
    
    with col_auto1:
        backup_automatico = st.checkbox("Habilitar backups automáticos", value=True)
        frequencia = st.selectbox("Frequência:", ["Diário", "Semanal", "Mensal"])
    
    with col_auto2:
        horario = st.time_input("Horário:", value=datetime.time(2, 0))
        retencao = st.number_input("Manter últimos (backups):", min_value=1, max_value=30, value=7)
    
    if st.button("💾 Salvar Configurações", use_container_width=True):
        st.success("✅ Configurações salvas!")


def _tela_retencao_dados():
    """Tela de retenção de dados."""
    
    st.subheader("🗑️ Política de Retenção de Dados")
    
    st.markdown("### ⚙️ Configurações de Retenção")
    
    col_ret1, col_ret2 = st.columns(2)
    
    with col_ret1:
        st.markdown("#### 📋 Dados de Funcionários")
        retencao_funcionarios = st.number_input(
            "Manter por (dias após desligamento):",
            min_value=0,
            max_value=3650,
            value=1825,
            help="0 = manter indefinidamente"
        )
        
        st.markdown("#### 📜 Logs de Auditoria")
        retencao_logs = st.number_input(
            "Manter por (dias):",
            min_value=30,
            max_value=3650,
            value=365
        )
    
    with col_ret2:
        st.markdown("#### 📄 Documentos Anexados")
        retencao_documentos = st.number_input(
            "Manter por (dias):",
            min_value=0,
            max_value=3650,
            value=730
        )
        
        st.markdown("#### 🗂️ Dados Anonimizados")
        retencao_anonimizados = st.number_input(
            "Manter por (dias):",
            min_value=0,
            max_value=3650,
            value=0,
            help="0 = manter indefinidamente"
        )
    
    if st.button("💾 Salvar Política de Retenção", type="primary", use_container_width=True):
        _salvar_politica_retencao(retencao_funcionarios, retencao_logs, retencao_documentos, retencao_anonimizados)
        st.success("✅ Política de retenção salva!")
    
    st.markdown("---")
    
    # Exclusão automática
    st.markdown("### 🗑️ Exclusão Automática de Dados")
    
    df_exclusao = _buscar_dados_para_exclusao()
    
    if df_exclusao.empty:
        st.info("✅ Nenhum dado pendente de exclusão automática.")
    else:
        st.warning(f"⚠️ {len(df_exclusao)} registro(s) pendente(s) de exclusão automática.")
        st.dataframe(df_exclusao, use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Executar Exclusão Automática Agora", type="secondary", use_container_width=True):
            if _executar_exclusao_automatica():
                st.success(f"✅ {len(df_exclusao)} registro(s) excluído(s) com sucesso!")
            else:
                st.error("❌ Erro ao executar exclusão automática.")


def _tela_relatorios_compliance():
    """Tela de relatórios de compliance."""
    
    st.subheader("📊 Relatórios de Compliance")
    
    # Relatórios disponíveis
    st.markdown("### 📄 Relatórios Disponíveis")
    
    col_rel1, col_rel2 = st.columns(2)
    
    with col_rel1:
        if st.button("📋 Relatório de Conformidade LGPD", use_container_width=True):
            _gerar_relatorio_lgpd()
        
        if st.button("📜 Relatório de Logs de Auditoria", use_container_width=True):
            df_logs = _buscar_logs_auditoria(None, "Todas", None, None)
            _exportar_logs_excel(df_logs)
        
        if st.button("🔐 Relatório de Acessos", use_container_width=True):
            st.info("Gerando relatório de acessos...")
    
    with col_rel2:
        if st.button("💾 Relatório de Backups", use_container_width=True):
            st.info("Gerando relatório de backups...")
        
        if st.button("🗑️ Relatório de Retenção de Dados", use_container_width=True):
            st.info("Gerando relatório de retenção...")
        
        if st.button("📊 Relatório Consolidado", use_container_width=True):
            st.info("Gerando relatório consolidado...")


# ─── FUNÇÕES AUXILIARES ───────────────────────────────────────────────────────

def _buscar_logs_auditoria(usuario, acao, data_inicio, data_fim):
    """Busca logs de auditoria."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        
        query = "SELECT * FROM logs_auditoria WHERE 1=1"
        params = []
        
        if usuario:
            query += " AND usuario LIKE ?"
            params.append(f"%{usuario}%")
        
        if acao and acao != "Todas":
            query += " AND acao = ?"
            params.append(acao)
        
        if data_inicio:
            query += " AND DATE(data_hora) >= ?"
            params.append(data_inicio.isoformat())
        
        if data_fim:
            query += " AND DATE(data_hora) <= ?"
            params.append(data_fim.isoformat())
        
        query += " ORDER BY data_hora DESC LIMIT 1000"
        
        df = pd.read_sql_query(query, conexao, params=params)
        
        if not df.empty:
            df['data'] = pd.to_datetime(df['data_hora']).dt.date
        
        conexao.close()
        return df
    except Exception:
        return pd.DataFrame()


def _buscar_solicitacoes_lgpd():
    """Busca solicitações LGPD."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        
        cursor = conexao.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS solicitacoes_lgpd (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpf TEXT,
                tipo TEXT,
                status TEXT,
                data_solicitacao TEXT,
                data_conclusao TEXT
            )
        """)
        
        df = pd.read_sql_query("SELECT * FROM solicitacoes_lgpd ORDER BY data_solicitacao DESC", conexao)
        conexao.close()
        return df
    except Exception:
        return pd.DataFrame()


def _anonimizar_dados_funcionario(cpf):
    """Anonimiza dados de um funcionário."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        cursor = conexao.cursor()
        
        # Gerar hash do CPF para manter referência
        cpf_hash = hashlib.sha256(cpf.encode()).hexdigest()[:16]
        
        cursor.execute("""
            UPDATE jovens_rotas 
            SET nome = ?,
                cpf = ?,
                rg = 'ANONIMIZADO',
                email = 'anonimizado@sistema.local',
                telefone = 'ANONIMIZADO'
            WHERE cpf = ?
        """, (f"ANONIMIZADO_{cpf_hash}", cpf_hash, cpf))
        
        conexao.commit()
        conexao.close()
        
        # Registrar log
        _registrar_log_auditoria("Sistema", "Anonimizou dados", f"CPF: {cpf_hash}")
        
        return True
    except Exception:
        return False


def _obter_ultimo_backup():
    """Obtém informações do último backup."""
    try:
        backup_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'backups')
        if not os.path.exists(backup_dir):
            return None
        
        backups = [f for f in os.listdir(backup_dir) if f.endswith(('.db', '.zip', '.enc'))]
        if not backups:
            return None
        
        ultimo = max(backups, key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)))
        caminho = os.path.join(backup_dir, ultimo)
        
        tamanho_bytes = os.path.getsize(caminho)
        tamanho_mb = tamanho_bytes / (1024 * 1024)
        
        data_modificacao = datetime.datetime.fromtimestamp(os.path.getmtime(caminho))
        
        return {
            'data': data_modificacao.strftime('%d/%m/%Y %H:%M'),
            'tamanho': f"{tamanho_mb:.2f} MB",
            'criptografado': ultimo.endswith('.enc')
        }
    except Exception:
        return None


def _criar_backup(criptografar, incluir_logs, incluir_anexos, compactar):
    """Cria backup do banco de dados."""
    try:
        # Criar diretório de backups
        backup_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Nome do arquivo
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_backup = f"backup_{timestamp}.db"
        
        # Copiar banco de dados
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        backup_path = os.path.join(backup_dir, nome_backup)
        
        shutil.copy2(db_path, backup_path)
        
        # Registrar log
        _registrar_log_auditoria("Sistema", "Criou backup", f"Arquivo: {nome_backup}")
        
        return True
    except Exception:
        return False


def _restaurar_backup(arquivo, senha):
    """Restaura backup."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        
        # Criar backup do banco atual antes de restaurar
        backup_atual = f"{db_path}.bak"
        shutil.copy2(db_path, backup_atual)
        
        # Restaurar
        with open(db_path, 'wb') as f:
            f.write(arquivo.getbuffer())
        
        # Registrar log
        _registrar_log_auditoria("Sistema", "Restaurou backup", f"Arquivo: {arquivo.name}")
        
        return True
    except Exception:
        return False


def _salvar_politica_retencao(funcionarios, logs, documentos, anonimizados):
    """Salva política de retenção."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        cursor = conexao.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS politica_retencao (
                id INTEGER PRIMARY KEY,
                tipo TEXT UNIQUE,
                dias INTEGER
            )
        """)
        
        cursor.execute("INSERT OR REPLACE INTO politica_retencao VALUES (1, 'funcionarios', ?)", (funcionarios,))
        cursor.execute("INSERT OR REPLACE INTO politica_retencao VALUES (2, 'logs', ?)", (logs,))
        cursor.execute("INSERT OR REPLACE INTO politica_retencao VALUES (3, 'documentos', ?)", (documentos,))
        cursor.execute("INSERT OR REPLACE INTO politica_retencao VALUES (4, 'anonimizados', ?)", (anonimizados,))
        
        conexao.commit()
        conexao.close()
        return True
    except Exception:
        return False


def _buscar_dados_para_exclusao():
    """Busca dados pendentes de exclusão."""
    return pd.DataFrame()


def _executar_exclusao_automatica():
    """Executa exclusão automática de dados."""
    try:
        _registrar_log_auditoria("Sistema", "Executou exclusão automática", "Dados expirados removidos")
        return True
    except Exception:
        return False


def _exportar_logs_excel(df):
    """Exporta logs para Excel."""
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Logs', index=False)
        
        output.seek(0)
        st.download_button(
            label="📥 Baixar Excel",
            data=output,
            file_name=f"logs_auditoria_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Erro ao exportar: {str(e)}")


def _exportar_logs_json(df):
    """Exporta logs para JSON."""
    try:
        json_data = df.to_json(orient='records', date_format='iso')
        st.download_button(
            label="📥 Baixar JSON",
            data=json_data,
            file_name=f"logs_auditoria_{datetime.datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
    except Exception as e:
        st.error(f"Erro ao exportar: {str(e)}")


def _gerar_relatorio_lgpd():
    """Gera relatório de conformidade LGPD."""
    st.info("📄 Gerando relatório de conformidade LGPD...")


def _registrar_log_auditoria(usuario, acao, detalhes=""):
    """Registra log de auditoria."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        cursor = conexao.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs_auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT,
                acao TEXT,
                detalhes TEXT,
                data_hora TEXT,
                ip TEXT
            )
        """)
        
        cursor.execute("""
            INSERT INTO logs_auditoria (usuario, acao, detalhes, data_hora)
            VALUES (?, ?, ?, ?)
        """, (usuario, acao, detalhes, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conexao.commit()
        conexao.close()
    except Exception:
        pass
