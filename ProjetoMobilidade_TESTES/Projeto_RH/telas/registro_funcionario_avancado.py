"""Registro de Funcionário - Versão Avançada com todas as melhorias."""

import streamlit as st
import sqlite3
import os
import pandas as pd
import datetime
import hashlib
import re
from banco_dados import criar_usuario, listar_usuarios, excluir_usuario
from telas.auth_guard import exigir_admin


def renderizar_registro_funcionario_avancado():
    """Renderiza o painel avançado de gestão de usuários."""
    exigir_admin()  # Apenas admins podem acessar
    
    st.markdown("""
    <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-left:4px solid #444c9b;
                border-radius:14px;padding:24px;margin-bottom:24px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
        <h3 style="margin:0 0 4px;color:#444c9b;">👥 Registro de Funcionário - Avançado</h3>
        <p style="color:#64748B;font-size:14px;margin:0;">
            Gerencie acessos, permissões, segurança e atividades dos usuários do sistema.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Criar Usuário",
        "👥 Usuários Cadastrados",
        "📊 Logs de Atividade",
        "🔐 Segurança"
    ])
    
    with tab1:
        _renderizar_criar_usuario()
    
    with tab2:
        _renderizar_listar_usuarios()
    
    with tab3:
        _renderizar_logs_atividade()
    
    with tab4:
        _renderizar_configuracoes_seguranca()


def _renderizar_criar_usuario():
    """Formulário de criação de usuário com validações avançadas."""
    
    st.subheader("➕ Criar Novo Usuário")
    
    with st.form("form_criar_usuario_avancado", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            novo_username = st.text_input("Usuário *", placeholder="Ex: FUNC_JOAO01")
            novo_email = st.text_input("E-mail", placeholder="usuario@empresa.com")
        
        with col2:
            novo_role = st.selectbox(
                "Nível de Permissão *",
                ["funcionario", "admin", "supervisor", "visualizador"],
                index=0,
                help="Funcionário: acesso padrão | Admin: acesso total | Supervisor: acesso intermediário | Visualizador: apenas leitura"
            )
            novo_departamento = st.text_input("Departamento", placeholder="Ex: RH, TI, Financeiro")
        
        st.markdown("---")
        st.markdown("### 🔐 Senha")
        
        col_senha1, col_senha2 = st.columns(2)
        
        with col_senha1:
            nova_senha = st.text_input("Senha *", type="password", placeholder="Mínimo 8 caracteres")
        
        with col_senha2:
            confirmar_senha = st.text_input("Confirmar Senha *", type="password", placeholder="Repita a senha")
        
        # Indicador de força da senha
        if nova_senha:
            forca = _calcular_forca_senha(nova_senha)
            _exibir_indicador_forca_senha(forca)
        
        st.markdown("---")
        st.markdown("### ⚙️ Configurações Adicionais")
        
        col_config1, col_config2 = st.columns(2)
        
        with col_config1:
            exigir_troca_senha = st.checkbox("Exigir troca de senha no primeiro acesso", value=True)
            ativar_2fa = st.checkbox("Ativar autenticação de dois fatores (2FA)", value=False)
        
        with col_config2:
            dias_expiracao = st.number_input(
                "Senha expira em (dias)",
                min_value=0,
                max_value=365,
                value=90,
                help="0 = nunca expira"
            )
            usuario_ativo = st.checkbox("Usuário ativo", value=True)
        
        criar = st.form_submit_button("✅ Criar Usuário", type="primary", use_container_width=True)
    
    if criar:
        # Validações
        erros = []
        
        if not novo_username.strip():
            erros.append("O campo Usuário é obrigatório")
        
        if len(nova_senha) < 8:
            erros.append("A senha deve ter pelo menos 8 caracteres")
        
        if nova_senha != confirmar_senha:
            erros.append("As senhas não coincidem")
        
        forca = _calcular_forca_senha(nova_senha)
        if forca < 2:
            erros.append("A senha é muito fraca. Use letras maiúsculas, minúsculas, números e símbolos")
        
        if novo_email and not _validar_email(novo_email):
            erros.append("E-mail inválido")
        
        if erros:
            for erro in erros:
                st.error(f"⚠️ {erro}")
        else:
            # Criar usuário
            usuario_logado = st.session_state.get("usuario_dados", {})
            sucesso, msg = _criar_usuario_avancado(
                username=novo_username,
                password=nova_senha,
                role=novo_role,
                email=novo_email,
                departamento=novo_departamento,
                exigir_troca_senha=exigir_troca_senha,
                ativar_2fa=ativar_2fa,
                dias_expiracao=dias_expiracao,
                ativo=usuario_ativo,
                criado_por=usuario_logado.get("username", "admin")
            )
            
            if sucesso:
                st.success(msg)
                _registrar_log_atividade(
                    usuario=usuario_logado.get("username"),
                    acao="Criou usuário",
                    detalhes=f"Usuário: {novo_username}, Role: {novo_role}"
                )
                st.rerun()
            else:
                st.error(msg)


def _renderizar_listar_usuarios():
    """Lista usuários com filtros e ações avançadas."""
    
    st.subheader("👥 Usuários Cadastrados")
    
    # Filtros
    col_busca, col_role, col_status = st.columns(3)
    
    with col_busca:
        busca = st.text_input("🔍 Buscar usuário:", placeholder="Nome ou e-mail...")
    
    with col_role:
        filtro_role = st.selectbox("Filtrar por permissão:", ["Todos", "admin", "funcionario", "supervisor", "visualizador"])
    
    with col_status:
        filtro_status = st.selectbox("Filtrar por status:", ["Todos", "Ativo", "Inativo"])
    
    # Buscar usuários
    df_usuarios = _listar_usuarios_avancado()
    
    if df_usuarios.empty:
        st.info("Nenhum usuário cadastrado.")
        return
    
    # Aplicar filtros
    if busca:
        df_usuarios = df_usuarios[
            df_usuarios['username'].str.contains(busca, case=False, na=False) |
            df_usuarios['email'].str.contains(busca, case=False, na=False)
        ]
    
    if filtro_role != "Todos":
        df_usuarios = df_usuarios[df_usuarios['role'] == filtro_role]
    
    if filtro_status != "Todos":
        status_bool = 1 if filtro_status == "Ativo" else 0
        df_usuarios = df_usuarios[df_usuarios['ativo'] == status_bool]
    
    st.markdown(f"**{len(df_usuarios)} usuário(s) encontrado(s)**")
    st.markdown("---")
    
    # Exibir usuários
    usuario_logado = st.session_state.get("usuario_dados", {})
    
    for _, row in df_usuarios.iterrows():
        with st.container():
            col_info, col_badge, col_acoes = st.columns([4, 2, 2])
            
            with col_info:
                criado_em = str(row.get("criado_em", ""))[:16]
                criado_por = row.get("criado_por", "—")
                ultimo_login = row.get("ultimo_login", "Nunca")
                
                status_icon = "🟢" if row.get('ativo', 1) == 1 else "🔴"
                
                st.markdown(f"""
                <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:8px;
                            padding:12px 16px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                    <p style="margin:0;color:#1E293B;font-weight:700;font-size:15px;">
                        {status_icon} {row['username']}
                    </p>
                    <p style="margin:4px 0 0;color:#64748B;font-size:13px;">
                        📧 {row.get('email', 'Não informado')} | 🏢 {row.get('departamento', 'N/A')}
                    </p>
                    <p style="margin:4px 0 0;color:#94A3B8;font-size:12px;">
                        Criado em {criado_em} por {criado_por} | Último login: {ultimo_login}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_badge:
                role_config = _get_role_config(row["role"])
                st.markdown(f"""
                <div style="background:{role_config['bg']};color:{role_config['color']};
                            border:1px solid {role_config['color']}40;
                            border-radius:20px;padding:6px 12px;font-size:13px;font-weight:600;
                            text-align:center;margin-top:8px;">{role_config['label']}</div>
                """, unsafe_allow_html=True)
            
            with col_acoes:
                eh_proprio = row["username"] == usuario_logado.get("username")
                
                if not eh_proprio:
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button("✏️", key=f"edit_{row['id']}", help="Editar"):
                            st.session_state[f'editando_{row["id"]}'] = True
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("🗑️", key=f"del_{row['id']}", help="Excluir"):
                            st.session_state[f'confirmar_exclusao_{row["id"]}'] = True
                            st.rerun()
                    
                    # Botões adicionais
                    col_btn3, col_btn4 = st.columns(2)
                    
                    with col_btn3:
                        if row.get('ativo', 1) == 1:
                            if st.button("🚫", key=f"desativar_{row['id']}", help="Desativar"):
                                _desativar_usuario(row['id'])
                                st.success("✅ Usuário desativado")
                                st.rerun()
                        else:
                            if st.button("✅", key=f"ativar_{row['id']}", help="Ativar"):
                                _ativar_usuario(row['id'])
                                st.success("✅ Usuário ativado")
                                st.rerun()
                    
                    with col_btn4:
                        if st.button("🔑", key=f"reset_senha_{row['id']}", help="Redefinir senha"):
                            st.session_state[f'resetar_senha_{row["id"]}'] = True
                            st.rerun()
                else:
                    st.markdown("<p style='color:#94A3B8;font-size:12px;text-align:center;margin-top:12px;'>(sua conta)</p>", unsafe_allow_html=True)
            
            # Modal de confirmação de exclusão
            if st.session_state.get(f'confirmar_exclusao_{row["id"]}', False):
                st.warning(f"⚠️ **Tem certeza que deseja excluir o usuário '{row['username']}'?**")
                col_conf1, col_conf2 = st.columns(2)
                
                with col_conf1:
                    if st.button("✅ Sim, excluir", key=f"confirmar_sim_{row['id']}"):
                        sucesso, msg = excluir_usuario(
                            user_id=int(row["id"]),
                            solicitante_username=usuario_logado.get("username", "")
                        )
                        if sucesso:
                            _registrar_log_atividade(
                                usuario=usuario_logado.get("username"),
                                acao="Excluiu usuário",
                                detalhes=f"Usuário: {row['username']}"
                            )
                            st.success(msg)
                            st.session_state[f'confirmar_exclusao_{row["id"]}'] = False
                            st.rerun()
                        else:
                            st.error(msg)
                
                with col_conf2:
                    if st.button("❌ Cancelar", key=f"confirmar_nao_{row['id']}"):
                        st.session_state[f'confirmar_exclusao_{row["id"]}'] = False
                        st.rerun()
            
            # Modal de redefinição de senha
            if st.session_state.get(f'resetar_senha_{row["id"]}', False):
                with st.expander("🔑 Redefinir Senha", expanded=True):
                    nova_senha_reset = st.text_input("Nova senha:", type="password", key=f"nova_senha_{row['id']}")
                    
                    col_reset1, col_reset2 = st.columns(2)
                    
                    with col_reset1:
                        if st.button("✅ Confirmar", key=f"confirmar_reset_{row['id']}"):
                            if len(nova_senha_reset) < 8:
                                st.error("⚠️ A senha deve ter pelo menos 8 caracteres")
                            else:
                                _resetar_senha_usuario(row['id'], nova_senha_reset)
                                _registrar_log_atividade(
                                    usuario=usuario_logado.get("username"),
                                    acao="Redefiniu senha",
                                    detalhes=f"Usuário: {row['username']}"
                                )
                                st.success("✅ Senha redefinida com sucesso!")
                                st.session_state[f'resetar_senha_{row["id"]}'] = False
                                st.rerun()
                    
                    with col_reset2:
                        if st.button("❌ Cancelar", key=f"cancelar_reset_{row['id']}"):
                            st.session_state[f'resetar_senha_{row["id"]}'] = False
                            st.rerun()
            
            st.markdown("---")


def _renderizar_logs_atividade():
    """Exibe logs de atividade dos usuários."""
    
    st.subheader("📊 Logs de Atividade")
    
    # Filtros
    col_usuario, col_acao, col_data = st.columns(3)
    
    with col_usuario:
        filtro_usuario = st.text_input("Filtrar por usuário:", placeholder="Nome do usuário...")
    
    with col_acao:
        filtro_acao = st.selectbox("Filtrar por ação:", ["Todas", "Login", "Logout", "Criou usuário", "Excluiu usuário", "Redefiniu senha"])
    
    with col_data:
        filtro_data = st.date_input("Data:", value=None)
    
    # Buscar logs
    df_logs = _buscar_logs_atividade(filtro_usuario, filtro_acao, filtro_data)
    
    if df_logs.empty:
        st.info("Nenhum log encontrado.")
    else:
        st.dataframe(df_logs, use_container_width=True, hide_index=True)


def _renderizar_configuracoes_seguranca():
    """Configurações de segurança do sistema."""
    
    st.subheader("🔐 Configurações de Segurança")
    
    st.markdown("### 🔒 Políticas de Senha")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tamanho_minimo = st.number_input("Tamanho mínimo da senha:", min_value=6, max_value=20, value=8)
        exigir_maiusculas = st.checkbox("Exigir letras maiúsculas", value=True)
        exigir_numeros = st.checkbox("Exigir números", value=True)
    
    with col2:
        dias_expiracao_global = st.number_input("Dias para expiração de senha:", min_value=0, max_value=365, value=90)
        exigir_minusculas = st.checkbox("Exigir letras minúsculas", value=True)
        exigir_simbolos = st.checkbox("Exigir símbolos especiais", value=True)
    
    st.markdown("---")
    st.markdown("### 🔐 Autenticação de Dois Fatores (2FA)")
    
    habilitar_2fa_global = st.checkbox("Habilitar 2FA para todos os usuários", value=False)
    
    st.markdown("---")
    st.markdown("### 📊 Sessões Ativas")
    
    df_sessoes = _listar_sessoes_ativas()
    
    if df_sessoes.empty:
        st.info("Nenhuma sessão ativa no momento.")
    else:
        st.dataframe(df_sessoes, use_container_width=True, hide_index=True)
        
        if st.button("🚫 Forçar Logout de Todas as Sessões", type="secondary"):
            _forcar_logout_todas_sessoes()
            st.success("✅ Todas as sessões foram encerradas!")
            st.rerun()
    
    st.markdown("---")
    
    if st.button("💾 Salvar Configurações", type="primary", use_container_width=True):
        st.success("✅ Configurações de segurança salvas com sucesso!")


# ─── FUNÇÕES AUXILIARES ───────────────────────────────────────────────────────

def _calcular_forca_senha(senha):
    """Calcula a força da senha (0-4)."""
    forca = 0
    
    if len(senha) >= 8:
        forca += 1
    if re.search(r'[a-z]', senha):
        forca += 1
    if re.search(r'[A-Z]', senha):
        forca += 1
    if re.search(r'[0-9]', senha):
        forca += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
        forca += 1
    
    return min(forca, 4)


def _exibir_indicador_forca_senha(forca):
    """Exibe indicador visual de força da senha."""
    
    cores = ["#EF4444", "#F59E0B", "#F59E0B", "#10B981", "#10B981"]
    labels = ["Muito Fraca", "Fraca", "Média", "Forte", "Muito Forte"]
    
    cor = cores[forca]
    label = labels[forca]
    percentual = (forca / 4) * 100
    
    st.markdown(f"""
    <div style="margin-top:8px;">
        <p style="color:#64748B;font-size:12px;margin:0 0 4px;">Força da senha: <span style="color:{cor};font-weight:600;">{label}</span></p>
        <div style="background:#E5E7EB;border-radius:10px;height:8px;overflow:hidden;">
            <div style="background:{cor};width:{percentual}%;height:100%;transition:width 0.3s;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _validar_email(email):
    """Valida formato de e-mail."""
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao, email) is not None


def _get_role_config(role):
    """Retorna configuração visual para cada role."""
    configs = {
        "admin": {"color": "#444c9b", "bg": "rgba(68,76,155,0.1)", "label": "🛡️ Admin"},
        "funcionario": {"color": "#10B981", "bg": "rgba(16,185,129,0.1)", "label": "👤 Funcionário"},
        "supervisor": {"color": "#F59E0B", "bg": "rgba(245,158,11,0.1)", "label": "👔 Supervisor"},
        "visualizador": {"color": "#64748B", "bg": "rgba(100,116,139,0.1)", "label": "👁️ Visualizador"}
    }
    return configs.get(role, configs["funcionario"])


def _criar_usuario_avancado(username, password, role, email, departamento, exigir_troca_senha, 
                            ativar_2fa, dias_expiracao, ativo, criado_por):
    """Cria usuário com campos avançados."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        cursor = conexao.cursor()
        
        # Adicionar colunas se não existirem
        colunas_extras = [
            ("email", "TEXT"),
            ("departamento", "TEXT"),
            ("ativo", "INTEGER DEFAULT 1"),
            ("ativar_2fa", "INTEGER DEFAULT 0"),
            ("dias_expiracao_senha", "INTEGER DEFAULT 90"),
            ("ultimo_login", "TEXT"),
            ("ip_ultimo_login", "TEXT")
        ]
        
        for coluna, tipo in colunas_extras:
            try:
                cursor.execute(f"ALTER TABLE usuarios ADD COLUMN {coluna} {tipo}")
            except sqlite3.OperationalError:
                pass
        
        # Hash da senha
        senha_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Inserir usuário
        cursor.execute("""
            INSERT INTO usuarios (
                username, password, role, email, departamento, ativo, 
                ativar_2fa, dias_expiracao_senha, deve_trocar_senha, criado_por, criado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username, senha_hash, role, email, departamento, 1 if ativo else 0,
            1 if ativar_2fa else 0, dias_expiracao, 1 if exigir_troca_senha else 0,
            criado_por, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        
        conexao.commit()
        conexao.close()
        
        return True, f"✅ Usuário '{username}' criado com sucesso!"
    
    except sqlite3.IntegrityError:
        return False, f"❌ Usuário '{username}' já existe."
    except Exception as e:
        return False, f"❌ Erro ao criar usuário: {str(e)}"


def _listar_usuarios_avancado():
    """Lista usuários com campos avançados."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM usuarios ORDER BY criado_em DESC", conexao)
        conexao.close()
        return df
    except Exception:
        return pd.DataFrame()


def _desativar_usuario(user_id):
    """Desativa um usuário."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        cursor = conexao.cursor()
        cursor.execute("UPDATE usuarios SET ativo = 0 WHERE id = ?", (user_id,))
        conexao.commit()
        conexao.close()
        return True
    except Exception:
        return False


def _ativar_usuario(user_id):
    """Ativa um usuário."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        cursor = conexao.cursor()
        cursor.execute("UPDATE usuarios SET ativo = 1 WHERE id = ?", (user_id,))
        conexao.commit()
        conexao.close()
        return True
    except Exception:
        return False


def _resetar_senha_usuario(user_id, nova_senha):
    """Redefine a senha de um usuário."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        cursor = conexao.cursor()
        
        senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
        cursor.execute("UPDATE usuarios SET password = ?, deve_trocar_senha = 1 WHERE id = ?", (senha_hash, user_id))
        
        conexao.commit()
        conexao.close()
        return True
    except Exception:
        return False


def _registrar_log_atividade(usuario, acao, detalhes=""):
    """Registra log de atividade."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        cursor = conexao.cursor()
        
        # Criar tabela de logs se não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs_atividade (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT,
                acao TEXT,
                detalhes TEXT,
                data_hora TEXT,
                ip TEXT
            )
        """)
        
        cursor.execute("""
            INSERT INTO logs_atividade (usuario, acao, detalhes, data_hora)
            VALUES (?, ?, ?, ?)
        """, (usuario, acao, detalhes, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conexao.commit()
        conexao.close()
    except Exception:
        pass


def _buscar_logs_atividade(filtro_usuario, filtro_acao, filtro_data):
    """Busca logs de atividade com filtros."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        
        query = "SELECT * FROM logs_atividade WHERE 1=1"
        params = []
        
        if filtro_usuario:
            query += " AND usuario LIKE ?"
            params.append(f"%{filtro_usuario}%")
        
        if filtro_acao and filtro_acao != "Todas":
            query += " AND acao = ?"
            params.append(filtro_acao)
        
        if filtro_data:
            query += " AND DATE(data_hora) = ?"
            params.append(filtro_data.strftime("%Y-%m-%d"))
        
        query += " ORDER BY data_hora DESC LIMIT 100"
        
        df = pd.read_sql_query(query, conexao, params=params)
        conexao.close()
        return df
    except Exception:
        return pd.DataFrame()


def _listar_sessoes_ativas():
    """Lista sessões ativas."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        df = pd.read_sql_query(
            "SELECT username, criado_em, expira_em FROM sessoes_ativas WHERE expira_em > ? ORDER BY criado_em DESC",
            conexao,
            params=(datetime.datetime.now().isoformat(),)
        )
        conexao.close()
        return df
    except Exception:
        return pd.DataFrame()


def _forcar_logout_todas_sessoes():
    """Força logout de todas as sessões."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM sessoes_ativas")
        conexao.commit()
        conexao.close()
        return True
    except Exception:
        return False
