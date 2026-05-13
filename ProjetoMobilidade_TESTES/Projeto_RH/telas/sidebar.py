"""Configuração da sidebar e navegação."""

import streamlit as st


def renderizar_sidebar():
    """Renderiza a sidebar com logo, menu e informações."""
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

    # ── Informações do usuário logado ────────────────────────────────────────
    usuario_dados = st.session_state.get("usuario_dados", {})
    username_exib = usuario_dados.get("username", "")
    role_exib = usuario_dados.get("role", "funcionario")

    if role_exib == "admin":
        badge = "🛡️ Admin"
        badge_color = "#444c9b"
    else:
        badge = "👤 Funcionário"
        badge_color = "#10B981"

    st.sidebar.markdown(f"""
    <div style="background:#F1F5F9;border:1px solid #E2E8F0;border-radius:8px;
                padding:10px 14px;margin-bottom:12px;">
        <p style="margin:0;color:#1E293B;font-size:13px;font-weight:700;">{username_exib}</p>
        <p style="margin:2px 0 0;color:{badge_color};font-size:12px;font-weight:600;">{badge}</p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown(
        "<p style='color:#1E293B;font-size:13px;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;'>Navegação</p>",
        unsafe_allow_html=True
    )

    # ── Monta opções de menu conforme perfil ─────────────────────────────────
    opcoes_menu = [
        "Dashboard Principal",
        "Pesquisar Consultas",
        "Cadastrar Novo Jovem",
        "🗂️ Triagem de Fichas",
        "Banco de Dados",
        "🏢 Gerenciar Unidades",
        "Simulação: Portal do Jovem",
    ]

    # Aba exclusiva do admin
    if role_exib == "admin":
        opcoes_menu.append("👥 Registro de Funcionário")

    parametros_url = st.query_params
    pagina_salva = parametros_url.get("menu", "Dashboard Principal")
    indice_padrao = opcoes_menu.index(pagina_salva) if pagina_salva in opcoes_menu else 0

    menu = st.sidebar.radio("", opcoes_menu, index=indice_padrao)

    if st.query_params.get("menu") != menu:
        if st.query_params.get("menu") == "Pesquisar Consultas":
            for k in ['resultado_busca', 'detalhes_abertos', 'rota_gerada',
                      'modo_contestacao', 'modo_edicao', 'mostrar_modal_email', 'analise_ia']:
                if k in st.session_state:
                    del st.session_state[k]
            if 'id_consulta' in st.query_params:
                del st.query_params['id_consulta']

    st.query_params["menu"] = menu

    st.sidebar.markdown("---")

    # ── Botão de logout ──────────────────────────────────────────────────────
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.query_params.clear()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<p style='color:#334155;font-size:14px;text-align:center;'>Copyright ©️ Renapsi - 2026. Todos os direitos reservados. CNPJ 37.381.902/0001-25.</p>",
        unsafe_allow_html=True
    )

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

    return menu
