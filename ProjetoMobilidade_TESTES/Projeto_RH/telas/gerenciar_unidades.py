"""Tela de gerenciamento de locais de trabalho (unidades) - VERSÃO AVANÇADA."""

import streamlit as st
import sqlite3
import os
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from apis import buscar_endereco_viacep, obter_coordenadas_reais
from banco_dados import inserir_local_trabalho, obter_locais_trabalho
from telas.auth_guard import exigir_login


def renderizar_gerenciar_unidades():
    """Renderiza a tela avançada de gerenciamento de unidades."""
    exigir_login()
    st.title("🏢 Gerenciar Unidades - Avançado")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗺️ Mapa & Visão Geral",
        "📋 Listar Unidades",
        "➕ Cadastrar Unidade",
        "📊 Estatísticas",
        "💡 Sugestões"
    ])

    with tab1:
        _mapa_unidades()

    with tab2:
        _listar_unidades_avancado()

    with tab3:
        _formulario_nova_unidade()

    with tab4:
        _estatisticas_unidades()

    with tab5:
        _sugestoes_novas_unidades()


def _mapa_unidades():
    """Exibe mapa com todas as unidades e raios de cobertura."""
    st.subheader("🗺️ Mapa de Unidades")
    
    locais = obter_locais_trabalho()
    
    if not locais:
        st.info("📭 Nenhuma unidade cadastrada ainda.")
        return
    
    # Configurações do mapa
    col_raio, col_tipo_filtro = st.columns(2)
    
    with col_raio:
        raio_km = st.selectbox(
            "📏 Raio de Cobertura:",
            [0, 5, 10, 15, 20],
            index=2,
            format_func=lambda x: f"{x} km" if x > 0 else "Sem raio"
        )
    
    with col_tipo_filtro:
        tipo_filtro = st.selectbox(
            "🔍 Filtrar por tipo:",
            ["Todos", "Trabalho", "Curso"]
        )
    
    # Filtrar locais
    if tipo_filtro != "Todos":
        locais_filtrados = [l for l in locais if l.get('tipo_local') == tipo_filtro]
    else:
        locais_filtrados = locais
    
    if not locais_filtrados:
        st.warning(f"Nenhuma unidade do tipo '{tipo_filtro}' encontrada.")
        return
    
    # Criar mapa centralizado
    coords_validas = []
    for local in locais_filtrados:
        if local.get('coordenadas'):
            try:
                lat, lon = map(float, local['coordenadas'].split(','))
                coords_validas.append((lat, lon))
            except:
                pass
    
    if not coords_validas:
        st.warning("Nenhuma unidade possui coordenadas válidas.")
        return
    
    # Centro do mapa (média das coordenadas)
    lat_centro = sum(c[0] for c in coords_validas) / len(coords_validas)
    lon_centro = sum(c[1] for c in coords_validas) / len(coords_validas)
    
    mapa = folium.Map(
        location=[lat_centro, lon_centro],
        zoom_start=11,
        tiles="OpenStreetMap"
    )
    
    # Adicionar marcadores e raios
    for local in locais_filtrados:
        if local.get('coordenadas'):
            try:
                lat, lon = map(float, local['coordenadas'].split(','))
                
                # Cor do marcador baseado no tipo
                cor = "blue" if local.get('tipo_local') == 'Trabalho' else "green"
                icone = "briefcase" if local.get('tipo_local') == 'Trabalho' else "graduation-cap"
                
                # Popup com informações
                popup_html = f"""
                <div style="width:250px;">
                    <h4>{local['nome_unidade']}</h4>
                    <p><b>Tipo:</b> {local.get('tipo_local', 'N/A')}</p>
                    <p><b>Endereço:</b> {local['logradouro']}, {local['numero']}</p>
                    <p><b>Bairro:</b> {local['bairro']}</p>
                    <p><b>CEP:</b> {local['cep']}</p>
                    <p><b>Telefone:</b> {local.get('telefone', 'N/A')}</p>
                    <p><b>Horário:</b> {local.get('horario_funcionamento', 'N/A')}</p>
                    <p><b>Capacidade:</b> {local.get('capacidade_maxima', 'N/A')} funcionários</p>
                </div>
                """
                
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=local['nome_unidade'],
                    icon=folium.Icon(color=cor, icon=icone, prefix='fa')
                ).add_to(mapa)
                
                # Adicionar raio de cobertura
                if raio_km > 0:
                    folium.Circle(
                        location=[lat, lon],
                        radius=raio_km * 1000,  # Converter km para metros
                        color=cor,
                        fill=True,
                        fillOpacity=0.1,
                        opacity=0.3,
                        popup=f"Raio de {raio_km}km"
                    ).add_to(mapa)
            
            except Exception as e:
                st.warning(f"Erro ao plotar {local['nome_unidade']}: {str(e)}")
    
    # Exibir mapa
    st_folium(mapa, width=None, height=600)
    
    # Estatísticas rápidas
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    with col_stat1:
        st.metric("🏢 Total de Unidades", len(locais_filtrados))
    
    with col_stat2:
        trabalho_count = len([l for l in locais_filtrados if l.get('tipo_local') == 'Trabalho'])
        st.metric("💼 Unidades de Trabalho", trabalho_count)
    
    with col_stat3:
        curso_count = len([l for l in locais_filtrados if l.get('tipo_local') == 'Curso'])
        st.metric("📚 Unidades de Curso", curso_count)


def _listar_unidades_avancado():
    """Lista unidades com detalhes avançados em cards visuais."""
    st.subheader("📋 Unidades Cadastradas")
    
    locais = obter_locais_trabalho()
    
    if not locais:
        st.info("📭 Nenhuma unidade cadastrada ainda.")
        return
    
    # Filtros aprimorados
    col_busca, col_tipo, col_cidade = st.columns(3)
    
    with col_busca:
        busca = st.text_input("🔍 Buscar unidade:", placeholder="Digite o nome, endereço ou CEP...")
    
    with col_tipo:
        tipo_filtro = st.selectbox("🏢 Filtrar por tipo:", ["Todos", "Trabalho", "Curso"])
    
    with col_cidade:
        cidades = list(set([l.get('cidade_uf', 'N/A') for l in locais]))
        cidades.sort()
        cidade_filtro = st.selectbox("📍 Filtrar por cidade:", ["Todas"] + cidades)
    
    # Aplicar filtros
    locais_filtrados = locais
    
    if busca:
        locais_filtrados = [
            l for l in locais_filtrados 
            if busca.lower() in l['nome_unidade'].lower() 
            or busca.lower() in l.get('logradouro', '').lower()
            or busca.lower() in l.get('cep', '').lower()
            or busca.lower() in l.get('bairro', '').lower()
        ]
    
    if tipo_filtro != "Todos":
        locais_filtrados = [l for l in locais_filtrados if l.get('tipo_local') == tipo_filtro]
    
    if cidade_filtro != "Todas":
        locais_filtrados = [l for l in locais_filtrados if l.get('cidade_uf') == cidade_filtro]
    
    st.markdown(f"**{len(locais_filtrados)} unidade(s) encontrada(s)**")
    st.markdown("---")
    
    # Exibir unidades em cards visuais
    if not locais_filtrados:
        st.warning("🔍 Nenhuma unidade encontrada com os filtros aplicados.")
        return
    
    # Layout em grid (2 colunas)
    for i in range(0, len(locais_filtrados), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(locais_filtrados):
                local = locais_filtrados[i + j]
                with col:
                    _renderizar_card_unidade(local)


def _renderizar_card_unidade(local):
    """Renderiza uma unidade em formato de card visual."""
    
    # Badge de tipo
    tipo_badge = "🏢 Trabalho" if local.get('tipo_local', 'Trabalho') == 'Trabalho' else "📚 Curso"
    tipo_cor = "#1f77b4" if local.get('tipo_local') == 'Trabalho' else "#2ca02c"
    
    # Container do card
    with st.container():
        # Estilo do card
        st.markdown(f"""
        <div style="
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            background-color: #f9f9f9;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h3 style="margin: 0; color: #333;">{local['nome_unidade']}</h3>
                <span style="
                    background-color: {tipo_cor};
                    color: white;
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-size: 12px;
                    font-weight: bold;
                ">{tipo_badge}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Foto da unidade
        foto_path = local.get('foto_path')
        if foto_path and os.path.exists(foto_path):
            st.image(foto_path, use_container_width=True)
        else:
            st.image("https://via.placeholder.com/400x200?text=Sem+Foto", use_container_width=True)
        
        # Informações principais
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**📍 Endereço:**")
            st.caption(f"{local['logradouro']}, {local['numero']}")
            st.caption(f"{local['bairro']} - {local['cidade_uf']}")
            st.caption(f"CEP: {local['cep']}")
        
        with col2:
            st.markdown(f"**📞 Contato:**")
            st.caption(f"Tel: {local.get('telefone', 'Não informado')}")
            st.caption(f"Email: {local.get('email', 'Não informado')}")
        
        # Capacidade
        capacidade = local.get('capacidade_maxima', 0)
        funcionarios_atuais = _contar_funcionarios_unidade(local['id'])
        
        if capacidade and capacidade > 0:
            percentual = (funcionarios_atuais / capacidade * 100)
            st.markdown(f"**👥 Ocupação:** {funcionarios_atuais}/{capacidade} ({percentual:.1f}%)")
            st.progress(percentual / 100)
        else:
            st.markdown(f"**👥 Funcionários:** {funcionarios_atuais}")
        
        # Horário
        st.markdown(f"**⏰ Horário:** {local.get('horario_funcionamento', 'Não informado')}")
        
        # Botões de ação
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("👁️ Ver Detalhes", key=f"ver_{local['id']}", use_container_width=True):
                st.session_state[f'ver_detalhes_{local["id"]}'] = True
                st.rerun()
        
        with col_btn2:
            if st.button("✏️ Editar", key=f"edit_{local['id']}", use_container_width=True):
                st.session_state[f'editando_{local["id"]}'] = True
                st.rerun()
        
        with col_btn3:
            if st.button("🗑️ Excluir", key=f"del_{local['id']}", use_container_width=True, type="secondary"):
                st.session_state[f'confirmar_exclusao_{local["id"]}'] = True
                st.rerun()
        
        # Modal de confirmação de exclusão
        if st.session_state.get(f'confirmar_exclusao_{local["id"]}', False):
            st.warning(f"⚠️ **Tem certeza que deseja excluir a unidade '{local['nome_unidade']}'?**")
            col_conf1, col_conf2 = st.columns(2)
            
            with col_conf1:
                if st.button("✅ Sim, excluir", key=f"confirmar_sim_{local['id']}", use_container_width=True):
                    _deletar_unidade(local['id'])
                    st.session_state[f'confirmar_exclusao_{local["id"]}'] = False
                    st.success("✅ Unidade excluída com sucesso!")
                    st.rerun()
            
            with col_conf2:
                if st.button("❌ Cancelar", key=f"confirmar_nao_{local['id']}", use_container_width=True):
                    st.session_state[f'confirmar_exclusao_{local["id"]}'] = False
                    st.rerun()
        
        # Modal de detalhes completos
        if st.session_state.get(f'ver_detalhes_{local["id"]}', False):
            with st.expander("📋 Detalhes Completos", expanded=True):
                _renderizar_detalhes_unidade(local)
                if st.button("✖️ Fechar", key=f"fechar_{local['id']}"):
                    st.session_state[f'ver_detalhes_{local["id"]}'] = False
                    st.rerun()


def _renderizar_detalhes_unidade(local):
    """Renderiza detalhes completos de uma unidade."""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📍 Informações Básicas")
        
        tipo_badge = "🏢 Trabalho" if local.get('tipo_local', 'Trabalho') == 'Trabalho' else "📚 Curso"
        st.markdown(f"**Tipo:** {tipo_badge}")
        st.markdown(f"**CEP:** {local['cep']}")
        st.markdown(f"**Endereço:** {local['logradouro']}, {local['numero']}")
        st.markdown(f"**Bairro:** {local['bairro']}")
        st.markdown(f"**Cidade/UF:** {local['cidade_uf']}")
        
        if local.get('coordenadas'):
            st.markdown(f"**Coordenadas:** 📍 {local['coordenadas']}")
        
        st.markdown("---")
        
        st.markdown("### 📞 Contato")
        st.markdown(f"**Telefone:** {local.get('telefone', 'Não informado')}")
        st.markdown(f"**E-mail:** {local.get('email', 'Não informado')}")
        
        st.markdown("---")
        
        st.markdown("### ⏰ Horário de Funcionamento")
        st.markdown(f"{local.get('horario_funcionamento', 'Não informado')}")
        
        st.markdown("---")
        
        st.markdown("### 👥 Capacidade")
        capacidade = local.get('capacidade_maxima', 'Não definida')
        st.markdown(f"**Capacidade Máxima:** {capacidade} funcionários")
        
        # Calcular funcionários atuais
        funcionarios_atuais = _contar_funcionarios_unidade(local['id'])
        st.markdown(f"**Funcionários Atuais:** {funcionarios_atuais}")
        
        if capacidade != 'Não definida' and isinstance(capacidade, (int, float)) and capacidade > 0:
            percentual = (funcionarios_atuais / capacidade * 100)
            st.progress(percentual / 100)
            st.caption(f"{percentual:.1f}% da capacidade utilizada")
    
    with col2:
        # Foto da unidade
        st.markdown("### 📸 Foto da Unidade")
        
        foto_path = local.get('foto_path')
        if foto_path and os.path.exists(foto_path):
            st.image(foto_path, use_container_width=True)
        else:
            st.info("Sem foto cadastrada")
            
            # Upload de foto
            foto_upload = st.file_uploader(
                "Fazer upload de foto:",
                type=['jpg', 'jpeg', 'png'],
                key=f"foto_{local['id']}"
            )
            
            if foto_upload:
                if st.button("💾 Salvar Foto", key=f"salvar_foto_{local['id']}"):
                    _salvar_foto_unidade(local['id'], foto_upload)
                    st.success("✅ Foto salva!")
                    st.rerun()
        
        st.markdown("---")
        
        # Histórico
        st.markdown("### 📜 Histórico")
        
        if st.button("📜 Ver Histórico Completo", key=f"hist_{local['id']}", use_container_width=True):
            _exibir_historico_unidade(local['id'])


def _formulario_nova_unidade():
    """Formulário unificado para cadastrar nova unidade."""
    st.subheader("➕ Cadastrar Nova Unidade")
    
    with st.form("form_nova_unidade"):
        # Tipo de unidade
        tipo_unidade = st.radio(
            "Tipo de Unidade:",
            ["Trabalho", "Curso"],
            horizontal=True
        )
        
        st.markdown("---")
        
        # Informações básicas
        st.markdown("### 📋 Informações Básicas")
        
        nome_unidade = st.text_input(
            "Nome da Unidade *",
            placeholder="Ex: Empresa XYZ - São Paulo"
        )
        
        col_cep, col_numero = st.columns([2, 1])
        
        with col_cep:
            cep = st.text_input("CEP *", placeholder="00000000", max_chars=8)
            
            # Validação de CEP em tempo real
            if cep:
                cep_limpo = ''.join(filter(str.isdigit, cep))
                if len(cep_limpo) != 8:
                    st.error("⚠️ CEP deve conter exatamente 8 dígitos")
                elif not cep_limpo.isdigit():
                    st.error("⚠️ CEP deve conter apenas números")
        
        with col_numero:
            numero = st.text_input("Número *", placeholder="123")
        
        # Buscar endereço automaticamente
        if cep and len(cep) == 8:
            cep_limpo = ''.join(filter(str.isdigit, cep))
            endereco = buscar_endereco_viacep(cep_limpo)
            
            if isinstance(endereco, dict) and endereco.get('rua') != "CEP Inválido" and endereco.get('rua') != "Endereço não encontrado":
                st.success("✅ CEP válido! Endereço encontrado.")
                logradouro = st.text_input("Logradouro", value=endereco.get('rua', ''), disabled=True)
                bairro = st.text_input("Bairro", value=endereco.get('bairro', ''), disabled=True)
                cidade_uf = st.text_input("Cidade/UF", value=endereco.get('cidade_uf', ''), disabled=True)
            else:
                st.error("❌ CEP não encontrado. Preencha manualmente.")
                logradouro = st.text_input("Logradouro *")
                bairro = st.text_input("Bairro *")
                cidade_uf = st.text_input("Cidade/UF *")
        else:
            logradouro = st.text_input("Logradouro *")
            bairro = st.text_input("Bairro *")
            cidade_uf = st.text_input("Cidade/UF *")
        
        st.markdown("---")
        
        # Contato
        st.markdown("### 📞 Contato")
        
        col_tel, col_email = st.columns(2)
        
        with col_tel:
            telefone = st.text_input("Telefone", placeholder="(11) 1234-5678")
        
        with col_email:
            email = st.text_input("E-mail", placeholder="contato@unidade.com")
        
        st.markdown("---")
        
        # Horário e Capacidade
        st.markdown("### ⏰ Operação")
        
        col_horario, col_capacidade = st.columns(2)
        
        with col_horario:
            horario = st.text_input(
                "Horário de Funcionamento",
                placeholder="Seg-Sex: 08:00-18:00"
            )
        
        with col_capacidade:
            capacidade = st.number_input(
                "Capacidade Máxima (funcionários)",
                min_value=0,
                value=100,
                step=10
            )
        
        st.markdown("---")
        
        # Coordenadas
        st.markdown("### 📍 Localização")
        
        if 'coordenadas_temp' not in st.session_state:
            st.session_state.coordenadas_temp = ''
        
        coordenadas = st.text_input(
            "Coordenadas (Lat, Long)",
            value=st.session_state.get('coordenadas_temp', ''),
            placeholder="Ex: -23.5505, -46.6333",
            disabled=True
        )
        
        col_buscar, col_limpar = st.columns(2)
        
        with col_buscar:
            if st.form_submit_button("🔍 Buscar Coordenadas", use_container_width=True):
                if logradouro and numero and cidade_uf:
                    endereco_completo = f"{logradouro}, {numero}, {cidade_uf}"
                    coords = obter_coordenadas_reais(endereco_completo)
                    if coords:
                        st.session_state.coordenadas_temp = coords
                        st.success(f"✅ Coordenadas: {coords}")
                        st.rerun()
                    else:
                        st.error("❌ Coordenadas não encontradas")
                else:
                    st.error("⚠️ Preencha o endereço completo")
        
        with col_limpar:
            if st.form_submit_button("🗑️ Limpar", use_container_width=True):
                st.session_state.coordenadas_temp = ''
                st.rerun()
        
        st.markdown("---")
        
        # Botão de salvar
        if st.form_submit_button("💾 Salvar Unidade", type="primary", use_container_width=True):
            # Validações
            erros = []
            
            if not nome_unidade:
                erros.append("Nome da unidade é obrigatório")
            
            if not cep:
                erros.append("CEP é obrigatório")
            else:
                cep_limpo = ''.join(filter(str.isdigit, cep))
                if len(cep_limpo) != 8:
                    erros.append("CEP deve conter exatamente 8 dígitos")
                elif not cep_limpo.isdigit():
                    erros.append("CEP deve conter apenas números")
            
            if not logradouro:
                erros.append("Logradouro é obrigatório")
            
            if not numero:
                erros.append("Número é obrigatório")
            
            if not bairro:
                erros.append("Bairro é obrigatório")
            
            if not cidade_uf:
                erros.append("Cidade/UF é obrigatório")
            
            if erros:
                for erro in erros:
                    st.error(f"⚠️ {erro}")
            else:
                coords = st.session_state.get('coordenadas_temp', '')
                
                # Salvar no banco com campos adicionais
                sucesso = _inserir_unidade_completa(
                    nome_unidade=nome_unidade,
                    tipo_local=tipo_unidade,
                    cep=cep,
                    logradouro=logradouro,
                    numero=numero,
                    bairro=bairro,
                    cidade_uf=cidade_uf,
                    coordenadas=coords,
                    telefone=telefone,
                    email=email,
                    horario_funcionamento=horario,
                    capacidade_maxima=capacidade
                )
                
                if sucesso:
                    st.success(f"✅ Unidade '{nome_unidade}' cadastrada com sucesso!")
                    
                    if 'coordenadas_temp' in st.session_state:
                        del st.session_state.coordenadas_temp
                    
                    st.rerun()
                else:
                    st.error("❌ Erro ao cadastrar unidade. Tente novamente.")


def _estatisticas_unidades():
    """Exibe estatísticas detalhadas das unidades."""
    st.subheader("📊 Estatísticas por Unidade")
    
    locais = obter_locais_trabalho()
    
    if not locais:
        st.info("📭 Nenhuma unidade cadastrada ainda.")
        return
    
    # Criar DataFrame para análise
    dados_stats = []
    
    for local in locais:
        funcionarios = _contar_funcionarios_unidade(local['id'])
        capacidade = local.get('capacidade_maxima', 0)
        
        dados_stats.append({
            'Unidade': local['nome_unidade'],
            'Tipo': local.get('tipo_local', 'N/A'),
            'Funcionários': funcionarios,
            'Capacidade': capacidade if capacidade else 0,
            'Ocupação %': (funcionarios / capacidade * 100) if capacidade and capacidade > 0 else 0,
            'Cidade': local.get('cidade_uf', 'N/A')
        })
    
    df_stats = pd.DataFrame(dados_stats)
    
    # Métricas gerais
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        st.metric("🏢 Total de Unidades", len(locais))
    
    with col_m2:
        total_funcionarios = df_stats['Funcionários'].sum()
        st.metric("👥 Total de Funcionários", total_funcionarios)
    
    with col_m3:
        total_capacidade = df_stats['Capacidade'].sum()
        st.metric("📊 Capacidade Total", total_capacidade)
    
    with col_m4:
        ocupacao_media = df_stats['Ocupação %'].mean()
        st.metric("📈 Ocupação Média", f"{ocupacao_media:.1f}%")
    
    st.markdown("---")
    
    # Gráficos
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.markdown("#### 👥 Funcionários por Unidade")
        fig1 = px.bar(
            df_stats,
            x='Unidade',
            y='Funcionários',
            color='Tipo',
            title="Distribuição de Funcionários"
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_graf2:
        st.markdown("#### 📊 Ocupação por Unidade")
        fig2 = px.bar(
            df_stats,
            x='Unidade',
            y='Ocupação %',
            color='Ocupação %',
            title="Percentual de Ocupação",
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("---")
    
    # Tabela detalhada
    st.markdown("#### 📋 Detalhamento")
    st.dataframe(df_stats, use_container_width=True, hide_index=True)


def _sugestoes_novas_unidades():
    """Sugere novas unidades baseado em concentração de funcionários."""
    st.subheader("💡 Sugestões de Novas Unidades")
    
    st.info("🔍 Análise baseada na concentração de funcionários por região")
    
    # Buscar dados de funcionários
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
    
    try:
        conexao = sqlite3.connect(db_path)
        df_funcionarios = pd.read_sql_query(
            "SELECT cep_casa, coordenadas FROM jovens_rotas WHERE cep_casa IS NOT NULL",
            conexao
        )
        conexao.close()
        
        if df_funcionarios.empty:
            st.warning("Não há dados suficientes para gerar sugestões.")
            return
        
        # Agrupar por CEP
        concentracao = df_funcionarios['cep_casa'].value_counts().head(10)
        
        st.markdown("### 📍 Top 10 Regiões com Maior Concentração")
        
        for idx, (cep, quantidade) in enumerate(concentracao.items(), 1):
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    endereco = buscar_endereco_viacep(cep)
                    if isinstance(endereco, dict):
                        st.markdown(f"**{idx}. {endereco.get('bairro', 'N/A')} - {endereco.get('cidade_uf', 'N/A')}**")
                        st.caption(f"CEP: {cep}")
                    else:
                        st.markdown(f"**{idx}. CEP: {cep}**")
                
                with col2:
                    st.metric("👥 Funcionários", quantidade)
                
                with col3:
                    if st.button("➕ Criar Unidade", key=f"criar_{cep}"):
                        st.session_state['pre_preencher_cep'] = cep
                        st.info(f"Vá para a aba 'Cadastrar Unidade' para criar uma unidade nesta região.")
        
    except Exception as e:
        st.error(f"❌ Erro ao gerar sugestões: {str(e)}")


# ─── FUNÇÕES AUXILIARES ───────────────────────────────────────────────────────

def _contar_funcionarios_unidade(unidade_id):
    """Conta quantos funcionários estão alocados em uma unidade."""
    # Implementação simulada - você pode buscar do banco real
    # Exemplo: SELECT COUNT(*) FROM jovens_rotas WHERE unidade_id = ?
    return 0  # Placeholder


def _salvar_foto_unidade(unidade_id, foto_upload):
    """Salva foto da unidade no sistema de arquivos."""
    try:
        # Criar diretório de fotos se não existir
        fotos_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'fotos_unidades')
        os.makedirs(fotos_dir, exist_ok=True)
        
        # Salvar arquivo
        extensao = os.path.splitext(foto_upload.name)[1]
        foto_path = os.path.join(fotos_dir, f"unidade_{unidade_id}{extensao}")
        
        with open(foto_path, 'wb') as f:
            f.write(foto_upload.getbuffer())
        
        # Atualizar banco de dados
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        cursor = conexao.cursor()
        cursor.execute(
            "UPDATE locais_trabalho SET foto_path = ? WHERE id = ?",
            (foto_path, unidade_id)
        )
        conexao.commit()
        conexao.close()
        
        return True
    
    except Exception as e:
        st.error(f"Erro ao salvar foto: {str(e)}")
        return False


def _exibir_historico_unidade(unidade_id):
    """Exibe histórico de alterações da unidade."""
    st.markdown("### 📜 Histórico de Alterações")
    
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        
        df_historico = pd.read_sql_query(
            """SELECT * FROM historico_alteracoes 
               WHERE tabela = 'locais_trabalho' AND registro_id = ?
               ORDER BY timestamp DESC""",
            conexao,
            params=(unidade_id,)
        )
        
        conexao.close()
        
        if df_historico.empty:
            st.info("Nenhuma alteração registrada ainda.")
        else:
            st.dataframe(df_historico, use_container_width=True)
    
    except Exception as e:
        st.warning(f"Histórico não disponível: {str(e)}")


def _inserir_unidade_completa(nome_unidade, tipo_local, cep, logradouro, numero, bairro, 
                               cidade_uf, coordenadas, telefone, email, horario_funcionamento, 
                               capacidade_maxima):
    """Insere unidade com todos os campos adicionais."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        cursor = conexao.cursor()
        
        # Adicionar colunas se não existirem
        colunas_extras = [
            ("telefone", "TEXT"),
            ("email", "TEXT"),
            ("horario_funcionamento", "TEXT"),
            ("capacidade_maxima", "INTEGER"),
            ("foto_path", "TEXT")
        ]
        
        for coluna, tipo in colunas_extras:
            try:
                cursor.execute(f"ALTER TABLE locais_trabalho ADD COLUMN {coluna} {tipo}")
            except sqlite3.OperationalError:
                pass
        
        # Inserir unidade
        cursor.execute("""
            INSERT INTO locais_trabalho (
                nome_unidade, tipo_local, cep, logradouro, numero, bairro, cidade_uf, 
                coordenadas, telefone, email, horario_funcionamento, capacidade_maxima
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nome_unidade, tipo_local, cep, logradouro, numero, bairro, cidade_uf,
            coordenadas, telefone, email, horario_funcionamento, capacidade_maxima
        ))
        
        conexao.commit()
        conexao.close()
        
        return True
    
    except Exception as e:
        st.error(f"Erro ao inserir unidade: {str(e)}")
        return False


def _deletar_unidade(unidade_id):
    """Deleta uma unidade do banco."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM locais_trabalho WHERE id = ?", (unidade_id,))
        conexao.commit()
        conexao.close()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao deletar: {str(e)}")
        return False
