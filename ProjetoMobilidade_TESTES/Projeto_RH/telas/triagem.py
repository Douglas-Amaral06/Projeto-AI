"""Tela de triagem de fichas."""

import streamlit as st
import os
from banco_dados import obter_fichas_cadastrais, aprovar_ficha_e_integrar, reprovar_ficha


def renderizar_triagem():
    """Renderiza a tela de triagem de fichas com layout visual aprimorado."""
    st.title("🗂️ Triagem de Fichas Cadastrais")
    
    # Filtros
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        filtro_nome = st.text_input("🔍 Buscar por nome", placeholder="Digite o nome do candidato...")
    with col2:
        filtro_status = st.selectbox("📊 Status", ["Todos", "Pendente", "Aprovado", "Reprovado"])
    with col3:
        st.write("")
        st.write("")
        if st.button("🔄 Atualizar", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Carregar fichas
    df_fichas = obter_fichas_cadastrais(filtro_nome, filtro_status)
    
    if df_fichas.empty:
        st.info("📭 Nenhuma ficha encontrada com os filtros aplicados.")
        return
    
    # Exibir fichas em cards
    for idx, ficha in df_fichas.iterrows():
        renderizar_card_ficha(ficha)


def renderizar_card_ficha(ficha):
    """Renderiza um card visual para cada ficha cadastral."""
    
    # Definir cor do status
    status_colors = {
        "Pendente": "#FFA500",
        "Aprovado": "#28A745",
        "Reprovado": "#DC3545"
    }
    status_icons = {
        "Pendente": "⏳",
        "Aprovado": "✅",
        "Reprovado": "❌"
    }
    
    status = ficha.get('status_aprovacao', 'Pendente')
    cor = status_colors.get(status, "#6C757D")
    icone = status_icons.get(status, "❓")
    
    # Card container
    with st.container():
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            border-left: 5px solid {cor};
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="margin: 0; color: #2c3e50;">👤 {ficha['nome_completo']}</h3>
                    <p style="margin: 5px 0; color: #7f8c8d;">
                        <strong>CPF:</strong> {ficha['cpf']} | 
                        <strong>Data Nascimento:</strong> {ficha.get('data_nascimento', 'N/A')} | 
                        <strong>Cadastro:</strong> {ficha.get('data_cadastro', 'N/A')[:10]}
                    </p>
                </div>
                <div style="text-align: right;">
                    <span style="
                        background-color: {cor};
                        color: white;
                        padding: 8px 16px;
                        border-radius: 20px;
                        font-weight: bold;
                        font-size: 14px;
                    ">{icone} {status}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Informações detalhadas em expander
        with st.expander("📋 Ver Detalhes Completos"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📍 Dados Pessoais**")
                st.write(f"**Nome Social:** {ficha.get('nome_social', 'N/A')}")
                st.write(f"**RG:** {ficha.get('rg', 'N/A')}")
                st.write(f"**Identidade de Gênero:** {ficha.get('identidade_genero', 'N/A')}")
                st.write(f"**Raça:** {ficha.get('raca', 'N/A')}")
                st.write(f"**Estado Civil:** {ficha.get('estado_civil', 'N/A')}")
                
                st.markdown("**📞 Contato**")
                st.write(f"**Email Jovem:** {ficha.get('email_jovem', 'N/A')}")
                st.write(f"**Tel. Jovem:** {ficha.get('tel_jovem', 'N/A')}")
                st.write(f"**Email Responsável:** {ficha.get('email_responsavel', 'N/A')}")
                st.write(f"**Tel. Responsável:** {ficha.get('tel_responsavel', 'N/A')}")
            
            with col2:
                st.markdown("**🏠 Endereço**")
                st.write(f"**CEP:** {ficha.get('cep', 'N/A')}")
                st.write(f"**Endereço:** {ficha.get('endereco_completo', 'N/A')}")
                st.write(f"**Cidade/Estado:** {ficha.get('cidade_estado', 'N/A')}")
                
                st.markdown("**👨‍👩‍👧 Família**")
                st.write(f"**Mãe:** {ficha.get('nome_mae', 'N/A')}")
                st.write(f"**Pai:** {ficha.get('nome_pai', 'N/A')}")
                st.write(f"**Responsável:** {ficha.get('nome_resp', 'N/A')}")
                st.write(f"**Tem Dependentes:** {ficha.get('tem_dependentes', 'N/A')}")
                st.write(f"**Tamanho Uniforme:** {ficha.get('tamanho_uniforme', 'N/A')}")
        
        # Seção de documentos com preview e indicador de completude
        with st.expander("📄 Documentos Anexados"):
            renderizar_documentos(ficha)
        
        # Botões de ação (apenas para fichas pendentes)
        if status == "Pendente":
            st.markdown("### 🎯 Ações")
            col_aprovar, col_reprovar = st.columns(2)
            
            with col_aprovar:
                if st.button(f"✅ Aprovar Ficha", key=f"aprovar_{ficha['id']}", type="primary", use_container_width=True):
                    sucesso, mensagem = aprovar_ficha_e_integrar(ficha['id'])
                    if sucesso:
                        st.success(mensagem)
                        st.rerun()
                    else:
                        st.error(mensagem)
            
            with col_reprovar:
                if st.button(f"❌ Reprovar Ficha", key=f"reprovar_{ficha['id']}", use_container_width=True):
                    sucesso, mensagem = reprovar_ficha(ficha['id'])
                    if sucesso:
                        st.warning(mensagem)
                        st.rerun()
                    else:
                        st.error(mensagem)
        
        st.markdown("---")


def renderizar_documentos(ficha):
    """Renderiza a seção de documentos com indicador de completude e preview."""
    
    documentos = {
        "Comprovante de Residência": ficha.get('path_comp_residencia'),
        "RG": ficha.get('path_rg'),
        "Conta Bancária": ficha.get('path_conta_salario'),
        "Título de Eleitor": ficha.get('path_titulo'),
        "Reservista": ficha.get('path_reservista'),
        "Certidão de Casamento": ficha.get('path_casamento'),
        "Certidão Nasc. Dependente": ficha.get('path_cert_nasc_dep'),
        "Vacina Dependente": ficha.get('path_vacina_dep')
    }
    
    # Calcular completude
    docs_obrigatorios = ["Comprovante de Residência", "RG", "Conta Bancária", "Título de Eleitor"]
    total_obrigatorios = len(docs_obrigatorios)
    enviados_obrigatorios = sum(1 for doc in docs_obrigatorios if documentos[doc])
    
    # Barra de progresso
    percentual = (enviados_obrigatorios / total_obrigatorios) * 100
    cor_progresso = "#28A745" if percentual == 100 else "#FFA500" if percentual >= 50 else "#DC3545"
    
    st.markdown(f"""
    <div style="margin-bottom: 15px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span><strong>📊 Completude dos Documentos Obrigatórios</strong></span>
            <span><strong>{enviados_obrigatorios}/{total_obrigatorios}</strong></span>
        </div>
        <div style="background-color: #e9ecef; border-radius: 10px; height: 20px; overflow: hidden;">
            <div style="
                background-color: {cor_progresso};
                width: {percentual}%;
                height: 100%;
                border-radius: 10px;
                transition: width 0.3s ease;
            "></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Listar documentos
    col1, col2 = st.columns(2)
    
    for idx, (nome_doc, path_doc) in enumerate(documentos.items()):
        col = col1 if idx % 2 == 0 else col2
        
        with col:
            if path_doc and path_doc.strip():
                # Documento enviado
                st.markdown(f"✅ **{nome_doc}**")
                
                # Verificar se arquivo existe
                if os.path.exists(path_doc):
                    # Botão para visualizar/baixar
                    with open(path_doc, "rb") as file:
                        st.download_button(
                            label=f"📥 Baixar {nome_doc}",
                            data=file,
                            file_name=os.path.basename(path_doc),
                            mime="application/pdf" if path_doc.endswith('.pdf') else "image/jpeg",
                            key=f"download_{ficha['id']}_{idx}",
                            use_container_width=True
                        )
                    
                    # Preview para imagens
                    if path_doc.lower().endswith(('.jpg', '.jpeg', '.png')):
                        with st.expander(f"👁️ Preview {nome_doc}"):
                            st.image(path_doc, use_container_width=True)
                else:
                    st.markdown(f"⚠️ **{nome_doc}** (arquivo não encontrado)")
            else:
                # Documento não enviado
                obrigatorio = nome_doc in docs_obrigatorios
                icone = "❌" if obrigatorio else "⚪"
                st.markdown(f"{icone} **{nome_doc}** {'(Obrigatório)' if obrigatorio else '(Opcional)'}")
