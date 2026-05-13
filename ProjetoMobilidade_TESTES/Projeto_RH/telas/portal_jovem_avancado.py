"""Portal do Jovem - Versão Avançada com todas as melhorias."""

import streamlit as st
import sqlite3
import os
import pandas as pd
import datetime
import time

# Import opcional do canvas
try:
    from streamlit_drawable_canvas import st_canvas
    CANVAS_DISPONIVEL = True
except ImportError:
    CANVAS_DISPONIVEL = False
    st_canvas = None

from apis import buscar_endereco_viacep, motor_de_rotas_gratuito
from banco_dados import registrar_sla, registrar_contestacao, atualizar_status_rota
from telas.auth_guard import exigir_login


def renderizar_portal_jovem_avancado():
    """Renderiza o portal do jovem com todas as melhorias."""
    exigir_login()
    if st.session_state.get('primeiro_acesso_portal', True):
        _renderizar_tutorial()
        return
    
    # Tabs principais
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Aceite de Rota",
        "📜 Histórico",
        "💬 Suporte",
        "❓ FAQ",
        "⚙️ Meus Dados"
    ])
    
    with tab1:
        _renderizar_aceite_rota()
    
    with tab2:
        _renderizar_historico()
    
    with tab3:
        _renderizar_chat_suporte()
    
    with tab4:
        _renderizar_faq()
    
    with tab5:
        _renderizar_meus_dados()


def _renderizar_tutorial():
    """Tutorial de primeiro acesso."""
    st.title("👋 Bem-vindo ao Portal do Jovem!")
    
    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(0,212,255,0.1),rgba(124,58,237,0.1));
                border:1px solid rgba(0,212,255,0.3);border-radius:16px;padding:24px;margin-bottom:24px;">
        <h2 style="margin:0 0 16px;color:#00D4FF;">🎯 Como funciona?</h2>
        <p style="color:#64748B;font-size:15px;line-height:1.8;">
            Este é o seu portal para gerenciar suas rotas de Vale-Transporte. Aqui você pode:
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### ✅ Aceitar Rotas
        - Visualize sua rota calculada
        - Assine digitalmente
        - Confirme o aceite
        
        ### 📜 Histórico
        - Veja todas as cartas assinadas
        - Baixe documentos anteriores
        - Acompanhe status
        """)
    
    with col2:
        st.markdown("""
        ### 💬 Suporte
        - Chat direto com RH
        - Tire dúvidas
        - Resolva problemas
        
        ### ⚙️ Meus Dados
        - Atualize informações
        - Veja benefícios ativos
        - Altere preferências
        """)
    
    st.markdown("---")
    
    if st.button("🚀 Começar a usar o portal", type="primary", use_container_width=True):
        st.session_state.primeiro_acesso_portal = False
        st.rerun()


def _renderizar_aceite_rota():
    """Renderiza a tela de aceite de rota com assinatura digital."""
    
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
    
    # Notificações de cartas pendentes
    _exibir_notificacoes_pendentes()
    
    # Busca jovens com status Otimizado
    with sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')) as conexao:
        df_otimizados = pd.read_sql_query(
            "SELECT id, nome, cep_casa, cep_trabalho FROM jovens_rotas WHERE status_rota = 'Otimizado'",
            conexao
        )
    
    if df_otimizados.empty:
        st.info("📭 Não há jovens com status 'Otimizado' para simular o aceite.")
        return
    
    # Selectbox para escolher o jovem
    opcoes_jovens = [f"{row['id']} - {row['nome']}" for _, row in df_otimizados.iterrows()]
    jovem_selecionado = st.selectbox(
        "Selecione o jovem para simular:",
        opcoes_jovens,
        key="select_jovem_simulacao"
    )
    
    if not jovem_selecionado:
        return
    
    id_jovem = int(float(jovem_selecionado.split(" - ")[0]))
    
    # Busca dados completos do jovem
    with sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')) as conexao:
        df_jovem = pd.read_sql_query(
            "SELECT * FROM jovens_rotas WHERE id = ?",
            conexao,
            params=(id_jovem,)
        )
    
    if df_jovem.empty:
        return
    
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
    
    # Registra o SLA no banco de dados
    if 'sla_segundos' in rota:
        registrar_sla(id_jovem, rota['sla_segundos'])
    
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
                <p style="color:#1E293B;font-size:14px;font-weight:600;margin:0;">{rua_casa}</p>
                <p style="color:#94A3B8;font-size:12px;margin:4px 0 0;">{bairro_casa}</p>
            </div>
            <div style="background:rgba(124,58,237,0.05);border:1px solid rgba(124,58,237,0.2);
                        border-radius:10px;padding:16px;">
                <p style="color:#64748B;font-size:12px;margin:0 0 6px;text-transform:uppercase;">🏢 Destino</p>
                <p style="color:#1E293B;font-size:14px;font-weight:600;margin:0;">{rua_trab}</p>
                <p style="color:#94A3B8;font-size:12px;margin:4px 0 0;">{bairro_trab}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Detalhes da rota
        st.markdown(f"""
        <div style="background:rgba(0,212,255,0.05);border-left:3px solid #00D4FF;
                    padding:16px;border-radius:0 8px 8px 0;margin-bottom:16px;">
            <p style="color:#64748B;font-size:12px;margin:0 0 8px;text-transform:uppercase;">📍 Trajeto</p>
            <p style="color:#1E293B;font-size:15px;font-weight:600;margin:0 0 8px;">{rota_principal['trajeto']}</p>
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
                contexto_ativo = "Trabalho"
                atualizar_status_rota(id_jovem, 'Não Optante', contexto_ativo)
                st.success("✅ Status atualizado para 'Não Optante'")
                time.sleep(2)
                st.rerun()
        
        with col_contestar:
            if st.button("⚠️ Contestar Rota", use_container_width=True, key=f"contestar_{id_jovem}"):
                st.session_state.modo_contestacao_jovem = True
        
        # Modal de assinatura digital com canvas
        if st.session_state.get('modo_assinatura', False):
            _renderizar_modal_assinatura(id_jovem, nome_jovem)
        
        # Modal de contestação
        if st.session_state.get('modo_contestacao_jovem', False):
            _renderizar_modal_contestacao(id_jovem, nome_jovem)


def _renderizar_modal_assinatura(id_jovem, nome_jovem):
    """Modal de assinatura digital com canvas para desenhar."""
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.3);
                border-radius:14px;padding:20px;margin-top:20px;">
        <h3 style="margin:0 0 4px;color:#10B981;">✍️ Assinatura Digital</h3>
        <p style="color:#94A3B8;font-size:13px;margin:0;">
            Desenhe sua assinatura no campo abaixo ou digite seu nome completo
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    assinatura_valida = False
    tipo_assinatura = None
    conteudo_assinatura = None
    
    # Se o canvas estiver disponível, mostra tabs
    if CANVAS_DISPONIVEL:
        # Tabs para escolher tipo de assinatura
        tab_canvas, tab_texto = st.tabs(["✍️ Desenhar Assinatura", "⌨️ Digitar Nome"])
        
        with tab_canvas:
            st.markdown("**Desenhe sua assinatura abaixo:**")
            
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 0)",
                stroke_width=3,
                stroke_color="#000000",
                background_color="#FFFFFF",
                height=150,
                width=600,
                drawing_mode="freedraw",
                key=f"canvas_assinatura_{id_jovem}",
            )
            
            if canvas_result.image_data is not None:
                import numpy as np
                # Verifica se há algum desenho (pixels não brancos)
                if np.any(canvas_result.image_data[:, :, :3] != 255):
                    assinatura_valida = True
                    tipo_assinatura = "canvas"
                    conteudo_assinatura = canvas_result.image_data
        
        with tab_texto:
            nome_assinatura = st.text_input(
                "Nome Completo para Assinatura:",
                placeholder="Digite seu nome completo",
                key=f"assinatura_texto_{id_jovem}"
            )
            
            if nome_assinatura.strip():
                assinatura_valida = True
                tipo_assinatura = "texto"
                conteudo_assinatura = nome_assinatura
    else:
        # Se canvas não disponível, apenas texto
        st.info("💡 Para habilitar assinatura desenhada, instale: pip install streamlit-drawable-canvas")
        
        nome_assinatura = st.text_input(
            "Nome Completo para Assinatura:",
            placeholder="Digite seu nome completo",
            key=f"assinatura_texto_{id_jovem}"
        )
        
        if nome_assinatura.strip():
            assinatura_valida = True
            tipo_assinatura = "texto"
            conteudo_assinatura = nome_assinatura
    
    # Verificação de identidade
    st.markdown("---")
    st.markdown("**📸 Verificação de Identidade (Opcional)**")
    
    documento_upload = st.file_uploader(
        "Faça upload de um documento de identidade:",
        type=['jpg', 'jpeg', 'png', 'pdf'],
        key=f"doc_identidade_{id_jovem}"
    )
    
    st.markdown("---")
    
    col_confirmar, col_cancelar = st.columns([1, 1])
    
    with col_confirmar:
        if st.button("✅ Confirmar Assinatura", type="primary", use_container_width=True, key=f"confirmar_assinatura_{id_jovem}"):
            if not assinatura_valida:
                st.error("⚠️ Desenhe sua assinatura ou digite seu nome completo")
            else:
                # Salvar assinatura
                _salvar_assinatura(id_jovem, tipo_assinatura, conteudo_assinatura, documento_upload)
                
                # Atualizar status
                with sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')) as conexao:
                    cursor = conexao.cursor()
                    contexto_ativo = "Trabalho"
                    cursor.execute(f"""
                        UPDATE jovens_rotas 
                        SET status_{contexto_ativo.lower() if contexto_ativo == 'Curso' else 'rota'} = 'Implantado', 
                            assinatura_digital = ?,
                            assinatura_data = ?
                        WHERE id = ?
                    """, (str(conteudo_assinatura)[:100], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id_jovem))
                    conexao.commit()
                
                st.success(f"✅ Rota aceita e assinada com sucesso!")
                st.balloons()
                st.session_state.modo_assinatura = False
                time.sleep(2)
                st.rerun()
    
    with col_cancelar:
        if st.button("❌ Cancelar", use_container_width=True, key=f"cancelar_assinatura_{id_jovem}"):
            st.session_state.modo_assinatura = False
            st.rerun()


def _renderizar_modal_contestacao(id_jovem, nome_jovem):
    """Modal de contestação de rota."""
    
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


def _exibir_notificacoes_pendentes():
    """Exibe notificações de cartas pendentes."""
    
    # Simula notificações (você pode buscar do banco)
    cartas_pendentes = 0  # Placeholder
    
    if cartas_pendentes > 0:
        st.warning(f"🔔 Você tem {cartas_pendentes} carta(s) pendente(s) de assinatura!")


def _renderizar_historico():
    """Renderiza histórico de cartas assinadas."""
    
    st.subheader("📜 Histórico de Cartas Assinadas")
    
    # Buscar histórico do banco
    try:
        with sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')) as conexao:
            df_historico = pd.read_sql_query(
                """SELECT id, nome, assinatura_data, status_rota 
                   FROM jovens_rotas 
                   WHERE assinatura_data IS NOT NULL 
                   ORDER BY assinatura_data DESC""",
                conexao
            )
        
        if df_historico.empty:
            st.info("📭 Nenhuma carta assinada ainda.")
        else:
            for _, row in df_historico.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{row['nome']}**")
                        st.caption(f"Assinado em: {row['assinatura_data']}")
                    
                    with col2:
                        status_cor = "#10B981" if row['status_rota'] == 'Implantado' else "#F59E0B"
                        st.markdown(f"<span style='color:{status_cor};font-weight:600;'>{row['status_rota']}</span>", unsafe_allow_html=True)
                    
                    with col3:
                        if st.button("📥 Baixar", key=f"download_{row['id']}"):
                            st.info("Funcionalidade de download em desenvolvimento")
                    
                    st.markdown("---")
    
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {str(e)}")


def _renderizar_chat_suporte():
    """Renderiza chat de suporte com RH."""
    
    st.subheader("💬 Chat de Suporte")
    
    st.info("🚧 Funcionalidade de chat em desenvolvimento. Em breve você poderá conversar diretamente com o RH!")
    
    # Placeholder para chat
    mensagem = st.text_area("Digite sua mensagem:", height=100)
    
    if st.button("📤 Enviar Mensagem", type="primary"):
        if mensagem.strip():
            st.success("✅ Mensagem enviada! O RH responderá em breve.")
        else:
            st.error("⚠️ Digite uma mensagem antes de enviar")


def _renderizar_faq():
    """Renderiza FAQ integrado."""
    
    st.subheader("❓ Perguntas Frequentes")
    
    faqs = [
        {
            "pergunta": "Como aceito minha rota?",
            "resposta": "Vá para a aba 'Aceite de Rota', visualize os detalhes e clique em 'Aceitar e Assinar'. Você pode desenhar sua assinatura ou digitar seu nome."
        },
        {
            "pergunta": "Posso contestar uma rota?",
            "resposta": "Sim! Clique em 'Contestar Rota' e descreva o motivo. O RH analisará sua solicitação."
        },
        {
            "pergunta": "Como vejo minhas cartas antigas?",
            "resposta": "Acesse a aba 'Histórico' para ver todas as cartas assinadas e fazer download."
        },
        {
            "pergunta": "O que significa 'Não Optante'?",
            "resposta": "Significa que você optou por não receber o Vale-Transporte para esta rota."
        },
        {
            "pergunta": "Como altero meus dados cadastrais?",
            "resposta": "Vá para a aba 'Meus Dados' e clique em 'Editar Informações'."
        }
    ]
    
    for faq in faqs:
        with st.expander(f"❓ {faq['pergunta']}"):
            st.markdown(faq['resposta'])


def _renderizar_meus_dados():
    """Renderiza tela de dados cadastrais e benefícios."""
    
    st.subheader("⚙️ Meus Dados")
    
    # Tabs
    tab_dados, tab_beneficios = st.tabs(["📋 Dados Cadastrais", "🎁 Benefícios Ativos"])
    
    with tab_dados:
        st.markdown("### 📋 Informações Cadastrais")
        
        # Placeholder - você pode buscar do banco
        st.text_input("Nome Completo", value="João da Silva", disabled=True)
        st.text_input("CPF", value="123.456.789-00", disabled=True)
        st.text_input("E-mail", value="joao@email.com")
        st.text_input("Telefone", value="(11) 98765-4321")
        
        if st.button("💾 Salvar Alterações", type="primary"):
            st.success("✅ Dados atualizados com sucesso!")
    
    with tab_beneficios:
        st.markdown("### 🎁 Benefícios Ativos")
        
        beneficios = [
            {"nome": "Vale-Transporte", "status": "Ativo", "valor": "R$ 11,64/dia"},
            {"nome": "Vale-Refeição", "status": "Ativo", "valor": "R$ 25,00/dia"},
            {"nome": "Plano de Saúde", "status": "Pendente", "valor": "—"}
        ]
        
        for beneficio in beneficios:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**{beneficio['nome']}**")
            
            with col2:
                status_cor = "#10B981" if beneficio['status'] == "Ativo" else "#F59E0B"
                st.markdown(f"<span style='color:{status_cor};font-weight:600;'>{beneficio['status']}</span>", unsafe_allow_html=True)
            
            with col3:
                st.markdown(beneficio['valor'])
            
            st.markdown("---")


def _salvar_assinatura(id_jovem, tipo, conteudo, documento=None):
    """Salva assinatura no banco de dados."""
    
    try:
        # Criar diretório de assinaturas se não existir
        assinaturas_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'assinaturas_digitais')
        os.makedirs(assinaturas_dir, exist_ok=True)
        
        if tipo == "canvas" and CANVAS_DISPONIVEL:
            # Salvar imagem da assinatura
            try:
                from PIL import Image
                import numpy as np
                
                img = Image.fromarray(conteudo.astype('uint8'), 'RGBA')
                img_path = os.path.join(assinaturas_dir, f"assinatura_{id_jovem}.png")
                img.save(img_path)
            except ImportError:
                st.warning("⚠️ PIL/Pillow não instalado. Assinatura salva como texto.")
        
        # Salvar documento de identidade se fornecido
        if documento:
            doc_path = os.path.join(assinaturas_dir, f"documento_{id_jovem}_{documento.name}")
            with open(doc_path, 'wb') as f:
                f.write(documento.getbuffer())
        
        return True
    
    except Exception as e:
        st.error(f"Erro ao salvar assinatura: {str(e)}")
        return False
