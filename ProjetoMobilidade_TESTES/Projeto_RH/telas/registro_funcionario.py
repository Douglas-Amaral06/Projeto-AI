"""Tela de registro de funcionários — acesso exclusivo Admin."""

import streamlit as st
from banco_dados import listar_usuarios, criar_usuario, excluir_usuario


def renderizar_registro_funcionario():
    """Renderiza o painel de gestão de usuários do sistema."""

    usuario_logado = st.session_state.get("usuario_dados", {})

    # Proteção extra: só admin acessa
    if usuario_logado.get("role") != "admin":
        st.error("🚫 Acesso negado. Esta área é restrita ao administrador.")
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

    # ── Formulário de criação ────────────────────────────────────────────────
    with st.expander("➕ Criar novo acesso", expanded=True):
        with st.form("form_criar_usuario", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                novo_username = st.text_input(
                    "Usuário",
                    placeholder="Ex: FUNC_JOAO01",
                    help="Sem espaços. Use letras maiúsculas e números."
                )
                novo_role = st.selectbox(
                    "Perfil de acesso",
                    ["funcionario", "admin"],
                    index=0
                )
            with col2:
                nova_senha = st.text_input(
                    "Senha",
                    type="password",
                    placeholder="Mínimo 8 caracteres"
                )
                confirmar_senha = st.text_input(
                    "Confirmar senha",
                    type="password",
                    placeholder="Repita a senha"
                )

            criar = st.form_submit_button("Criar Acesso", type="primary", use_container_width=True)

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

    # ── Lista de usuários existentes ─────────────────────────────────────────
    st.markdown("""
    <p style="color:#1E293B;font-size:14px;text-transform:uppercase;
              letter-spacing:0.1em;font-weight:600;margin-bottom:12px;">
        Usuários cadastrados
    </p>
    """, unsafe_allow_html=True)

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
                    <p style="margin:0;color:#1E293B;font-weight:700;font-size:15px;">
                        {row['username']}
                    </p>
                    <p style="margin:4px 0 0;color:#64748B;font-size:13px;">
                        Criado em {criado_em} · por {criado_por}
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col_badge:
                if row["role"] == "admin":
                    badge_color, badge_bg = "#444c9b", "rgba(68,76,155,0.1)"
                    badge_label = "🛡️ Admin"
                else:
                    badge_color, badge_bg = "#10B981", "rgba(16,185,129,0.1)"
                    badge_label = "👤 Funcionário"

                st.markdown(f"""
                <div style="background:{badge_bg};color:{badge_color};border:1px solid {badge_color}40;
                            border-radius:20px;padding:6px 12px;font-size:13px;font-weight:600;
                            text-align:center;margin-top:8px;">
                    {badge_label}
                </div>
                """, unsafe_allow_html=True)

            with col_btn:
                # Não permite excluir a própria conta
                eh_proprio = row["username"] == usuario_logado.get("username")
                if not eh_proprio:
                    if st.button(
                        "🗑️ Remover",
                        key=f"del_user_{row['id']}",
                        use_container_width=True
                    ):
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
                    st.markdown(
                        "<p style='color:#94A3B8;font-size:12px;text-align:center;margin-top:12px;'>(sua conta)</p>",
                        unsafe_allow_html=True
                    )
