import streamlit as st
import pandas as pd
from telas.banco_dados import (
    obter_locais_trabalho, obter_local_trabalho_detalhes,
    salvar_local_trabalho, deletar_local_trabalho
)
from apis import buscar_endereco_viacep, obter_coordenadas_reais

def render_unidades():
    """Renderiza a tela de gerenciamento de unidades"""
    
    st.markdown("""
    <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-left:4px solid #444c9b;
                border-radius:14px;padding:24px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
        <h3 style="margin:0 0 4px;color:#444c9b;">🏢 Gerenciar Unidades de Trabalho</h3>
        <p style="color:#666666;font-size:13px;margin:0;">
            Cadastre e gerencie os locais de trabalho (unidades) da organização
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Abas: Cadastrar / Listar
    tab_cadastro, tab_listagem = st.tabs(["➕ Cadastrar Nova Unidade", "📋 Unidades Cadastradas"])
    
    # ══════════════════════════════════════════════════════════════════════════
    # ABA 1: CADASTRO
    # ══════════════════════════════════════════════════════════════════════════
    with tab_cadastro:
        st.markdown("<p style='color:#444c9b;font-size:14px;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:12px;'>Dados da Unidade</p>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            nome_unidade = st.text_input(
                "Nome da Unidade",
                placeholder="Ex: RENAPSI - SÃO PAULO-SP",
                help="Nome único para identificar a unidade"
            )
        
        with col2:
            cep_input = st.text_input(
                "CEP",
                placeholder="01333010",
                max_chars=8,
                help="Digite apenas os 8 dígitos"
            )
        
        # Busca endereço via ViaCEP
        endereco_info = None
        if cep_input and len(cep_input.strip()) == 8:
            endereco_info = buscar_endereco_viacep(cep_input)
        
        col3, col4 = st.columns([3, 1])
        
        with col3:
            logradouro = st.text_input(
                "Logradouro",
                value=endereco_info.get('rua', '') if endereco_info else '',
                disabled=True,
                help="Preenchido automaticamente via ViaCEP"
            )
        
        with col4:
            numero = st.text_input(
                "Número",
                placeholder="388",
                help="Número do endereço"
            )
        
        col5, col6 = st.columns([1, 1])
        
        with col5:
            bairro = st.text_input(
                "Bairro",
                value=endereco_info.get('bairro', '') if endereco_info else '',
                disabled=True,
                help="Preenchido automaticamente via ViaCEP"
            )
        
        with col6:
            cidade_uf = st.text_input(
                "Cidade/UF",
                value=endereco_info.get('cidade_uf', '') if endereco_info else '',
                disabled=True,
                help="Preenchido automaticamente via ViaCEP"
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Seção de coordenadas
        st.markdown("<p style='color:#444c9b;font-size:14px;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:12px;'>Localização Geográfica</p>", unsafe_allow_html=True)
        
        col_coord, col_btn = st.columns([3, 1])
        
        with col_coord:
            coordenadas = st.text_input(
                "Coordenadas (Latitude, Longitude)",
                placeholder="-23.56774139404297, -46.646541595458984",
                help="Formato: lat, lon (ex: -23.567, -46.646)"
            )
        
        with col_btn:
            st.write("")
            st.write("")
            if st.button("🔍 Buscar Coordenadas", type="secondary", use_container_width=True):
                if cep_input and numero:
                    endereco_completo = f"{logradouro}, {numero}, {bairro}, {cidade_uf}, Brasil"
                    lat, lon = obter_coordenadas_reais(endereco_completo)
                    if lat is not None and lon is not None:
                        st.session_state.coordenadas_temp = f"{lat}, {lon}"
                        st.success(f"✅ Coordenadas encontradas: {lat}, {lon}")
                    else:
                        st.warning("⚠️ Não foi possível encontrar as coordenadas. Verifique o endereço.")
                else:
                    st.error("❌ Preencha CEP e Número para buscar coordenadas")
        
        # Usa coordenadas do session_state se disponível
        if 'coordenadas_temp' in st.session_state:
            coordenadas = st.session_state.coordenadas_temp
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botões de ação
        col_salvar, col_limpar = st.columns([1, 1])
        
        with col_salvar:
            if st.button("💾 Salvar Unidade", type="primary", use_container_width=True):
                # Validações
                if not nome_unidade.strip():
                    st.error("❌ Nome da unidade é obrigatório")
                elif not cep_input or len(cep_input) != 8:
                    st.error("❌ CEP inválido (deve ter 8 dígitos)")
                elif not numero.strip():
                    st.error("❌ Número é obrigatório")
                elif not coordenadas.strip():
                    st.error("❌ Coordenadas são obrigatórias")
                else:
                    sucesso = salvar_local_trabalho(
                        nome_unidade=nome_unidade.strip(),
                        cep=cep_input,
                        logradouro=logradouro,
                        numero=numero.strip(),
                        bairro=bairro,
                        cidade_uf=cidade_uf,
                        coordenadas=coordenadas.strip()
                    )
                    
                    if sucesso:
                        st.success(f"✅ Unidade '{nome_unidade}' salva com sucesso!")
                        st.session_state.pop('coordenadas_temp', None)
                        st.rerun()
                    else:
                        st.error("❌ Erro ao salvar unidade. Verifique se o nome já existe.")
        
        with col_limpar:
            if st.button("🔄 Limpar Formulário", use_container_width=True):
                st.session_state.pop('coordenadas_temp', None)
                st.rerun()
    
    # ══════════════════════════════════════════════════════════════════════════
    # ABA 2: LISTAGEM
    # ══════════════════════════════════════════════════════════════════════════
    with tab_listagem:
        locais = obter_locais_trabalho()
        
        if not locais:
            st.info("📭 Nenhuma unidade cadastrada ainda")
        else:
            st.markdown(f"<p style='color:#666666;font-size:14px;margin-bottom:12px;'><strong>{len(locais)}</strong> unidade(s) cadastrada(s)</p>", unsafe_allow_html=True)
            
            for local_nome in locais:
                local_info = obter_local_trabalho_detalhes(local_nome)
                
                if local_info:
                    col_info, col_acoes = st.columns([4, 1])
                    
                    with col_info:
                        st.markdown(f"""
                        <div style="background:#FFFFFF;border:1px solid #E5E7EB;
                                    border-radius:12px;padding:16px;margin-bottom:12px;
                                    box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                            <p style="margin:0 0 8px;color:#444c9b;font-weight:700;font-size:15px;">
                                📍 {local_info['nome_unidade']}
                            </p>
                            <p style="margin:0 0 4px;color:#666666;font-size:13px;">
                                <strong>Endereço:</strong> {local_info['endereco_completo']}
                            </p>
                            <p style="margin:0 0 4px;color:#666666;font-size:13px;">
                                <strong>CEP:</strong> {local_info['cep']}
                            </p>
                            <p style="margin:0;color:#666666;font-size:13px;">
                                <strong>Coordenadas:</strong> {local_info['coordenadas']}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_acoes:
                        st.write("")
                        st.write("")
                        st.write("")
                        
                        if local_info['nome_unidade'] != 'RENAPSI - SÃO PAULO-SP':
                            if st.button("🗑️", key=f"del_{local_info['id']}", help="Deletar unidade"):
                                if deletar_local_trabalho(local_info['nome_unidade']):
                                    st.success("✅ Unidade deletada")
                                    st.rerun()
                                else:
                                    st.error("❌ Erro ao deletar")
                        else:
                            st.markdown("<p style='color:#94A3B8;font-size:12px;text-align:center;'>🔒 Padrão</p>", unsafe_allow_html=True)
