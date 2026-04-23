"""Tela de pesquisa e gerenciamento de consultas."""

import streamlit as st
import sqlite3
import pandas as pd
import os
import time
import folium
from streamlit_folium import st_folium
from apis import buscar_endereco_viacep, obter_coordenadas_reais, motor_de_rotas_gratuito
from agente_ia import analisar_rota_com_ia
from banco_dados import obter_dados_dashboard, obter_status_visual, registrar_contestacao, obter_locais_trabalho, obter_local_trabalho_por_id
from carta_pdf import gerar_carta_pdf
from email_sender import enviar_carta_por_email


def renderizar_consultas():
    """Renderiza a tela de pesquisa de consultas."""
    
    # Recupera estado após F5
    if 'id_consulta' in st.query_params and st.session_state.get('resultado_busca') is None:
        id_salvo = st.query_params['id_consulta']
        conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db'))
        df_salvo = pd.read_sql_query("SELECT * FROM jovens_rotas WHERE id = ?", conexao, params=(int(float(id_salvo)),))
        conexao.close()
        if not df_salvo.empty:
            st.session_state.resultado_busca = df_salvo
            st.session_state.detalhes_abertos = True

    # Inicializa estado da sessão
    for key, default in [('resultado_busca', None), ('detalhes_abertos', False),
                          ('rota_gerada', None), ('modo_contestacao', False),
                          ('modo_edicao', False), ('mostrar_modal_email', False)]:
        if key not in st.session_state:
            st.session_state[key] = default

    # ── PAINEL DE DETALHES ──────────────────────────────────────────────────
    if st.session_state.detalhes_abertos and st.session_state.resultado_busca is not None:

        col_voltar, _ = st.columns([1, 11])
        with col_voltar:
            if st.button("← Voltar"):
                for k in ['detalhes_abertos','rota_gerada','modo_contestacao',
                           'modo_edicao','mostrar_modal_email','resultado_busca']:
                    st.session_state[k] = False if k != 'resultado_busca' else None
                if 'id_consulta' in st.query_params:
                    del st.query_params['id_consulta']
                st.rerun()

        # Verifica se há dados válidos
        if st.session_state.resultado_busca.empty:
            st.error("❌ Nenhum dado encontrado para esta consulta.")
            st.session_state.detalhes_abertos = False
            st.rerun()
            
        dados_jovem = st.session_state.resultado_busca.iloc[0]
        
        # ── BLINDAGEM CONTRA ID VAZIO ──
        try:
            id_selecionado = int(dados_jovem['id'])
        except (TypeError, ValueError):
            st.error("⚠️ Este jovem está sem ID no banco de dados! Por favor, vá na aba 'Banco de Dados', adicione um número no campo ID dele e salve.")
            st.stop()
            
        nome_jovem       = dados_jovem['nome']
        cpf_cru          = str(dados_jovem['cpf']).zfill(11)
        cep_casa         = dados_jovem['cep_casa']
        cep_trab         = dados_jovem['cep_trabalho']
        matricula_exib   = dados_jovem.get('matricula', 'Não informada')
        status_rota_raw  = dados_jovem.get('status_rota', 'Otimizado')
        status_exib      = obter_status_visual(status_rota_raw)
        email_jovem      = dados_jovem.get('email', '')
        celular_jovem    = dados_jovem.get('celular', '')
        numero_casa      = dados_jovem.get('numero_casa', '')
        coordenadas_casa = dados_jovem.get('coordenadas', '')

        # ── MODO EDIÇÃO ──
        if st.session_state.modo_edicao:
            st.markdown("""
            <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-left:4px solid #444c9b;
                        border-radius:14px;padding:24px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                <h3 style="margin:0 0 4px;color:#444c9b;">✏️ Editar Dados da Consulta</h3>
                <p style="color:#666666;font-size:13px;margin:0;">Atualize as informações do funcionário e o local de trabalho</p>
            </div>
            """, unsafe_allow_html=True)

            # ── 3 Colunas como você pediu ──
            col_e1, col_e2, col_e3 = st.columns(3)
            
            with col_e1:
                st.markdown("<p style='color:#444c9b;font-size:14px;text-transform:uppercase;letter-spacing:0.1em;'>👤 Dados do Funcionário</p>", unsafe_allow_html=True)
                mat_input    = st.text_input("Matrícula", value=matricula_exib if matricula_exib != 'Não informada' else '')
                nome_input   = st.text_input("Nome", value=nome_jovem, disabled=True)
                email_input  = st.text_input("E-mail", value=email_jovem or '')
                celular_input= st.text_input("Celular", value=celular_jovem or '')

            with col_e2:
                st.markdown("<p style='color:#444c9b;font-size:14px;text-transform:uppercase;letter-spacing:0.1em;'>🏠 Endereço do Funcionário</p>", unsafe_allow_html=True)
                cep_input = st.text_input("CEP Residencial", value=cep_casa)
                c_rua, c_num = st.columns([3, 1])
                
                # Busca endereço
                end_atual = buscar_endereco_viacep(cep_input)
                rua_input = c_rua.text_input("Logradouro", value=end_atual.get('completo','') if isinstance(end_atual, dict) else '', disabled=True)
                num_input = c_num.text_input("Número", value=numero_casa or '')

                # Coordenadas
                coord_atual = st.session_state.get('coord_temp', coordenadas_casa)
                coord_input = st.text_input("Coordenadas (Opcional)", value=coord_atual or '')
                
                if st.button("🔍 Buscar Coordenadas Reais", type="secondary", use_container_width=True):
                    if cep_input and len(cep_input.strip()) == 8:
                        end_completo = f"CEP {cep_input}, {num_input if num_input else ''}, São Paulo, Brasil"
                        lat, lon = obter_coordenadas_reais(end_completo)
                        if lat is not None and lon is not None:
                            st.session_state.coord_temp = f"{lat}, {lon}"
                            st.success(f"✅ Coordenadas: {lat}, {lon}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("⚠️ Não encontradas. Verifique o CEP.")
                    else:
                        st.error("❌ CEP inválido")

            with col_e3:
                st.markdown("<p style='color:#444c9b;font-size:14px;text-transform:uppercase;letter-spacing:0.1em;'>🏢 Local de Trabalho</p>", unsafe_allow_html=True)
                
                # ── TAREFA 2: DINAMIZAR LOCAIS DE TRABALHO ──
                # Busca unidades do banco de dados
                locais_trabalho = obter_locais_trabalho()
                
                if not locais_trabalho:
                    st.warning("⚠️ Nenhuma unidade cadastrada no sistema. Vá em 'Gerenciar Unidades' para adicionar.")
                    local_selecionado = None
                else:
                    # Cria dicionário com nome_unidade como chave
                    dict_locais = {local['nome_unidade']: local for local in locais_trabalho}
                    nomes_unidades = list(dict_locais.keys())
                    
                    # Selectbox com unidades do banco
                    local_selecionado_nome = st.selectbox(
                        "Selecione o local de trabalho:",
                        nomes_unidades,
                        key=f"select_local_trabalho_{id_selecionado}"
                    )
                    
                    if local_selecionado_nome:
                        local_selecionado = dict_locais[local_selecionado_nome]
                        
                        # Card azul com dados reais da unidade
                        st.markdown(f"""
                        <div style="background-color:#BAE6FD; border-radius:8px; padding:15px; text-align:center; margin-top:5px; border: 1px solid #7DD3FC;">
                            <p style="color:#0284C7; font-size:12px; font-weight:700; margin:0;">
                                {local_selecionado['logradouro']}, {local_selecionado['numero']} - {local_selecionado['bairro']}<br>
                                {local_selecionado['cidade_uf']}
                            </p>
                            <p style="color:#0284C7; font-size:11px; margin:8px 0 0;">
                                CEP: {local_selecionado['cep']}
                            </p>
                            {f'<p style="color:#0284C7; font-size:11px; margin:4px 0 0;">COORDENADAS: {local_selecionado["coordenadas"]}</p>' if local_selecionado['coordenadas'] else ''}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        local_selecionado = None

            st.markdown("<br>", unsafe_allow_html=True)
            col_f, col_c = st.columns([1, 1])
            with col_f:
                if st.button("Fechar", use_container_width=True):
                    st.session_state.modo_edicao = False
                    st.session_state.pop('coord_temp', None)
                    st.rerun()
            with col_c:
                if st.button("Confirmar Alterações", type="primary", use_container_width=True):
                    try:
                        if not local_selecionado:
                            st.error("⚠️ Selecione um local de trabalho antes de confirmar.")
                        else:
                            mat_final = str(mat_input) if mat_input else ''
                            email_final = str(email_input) if email_input else ''
                            celular_final = str(celular_input) if celular_input else ''
                            cep_final = str(cep_input) if cep_input else str(cep_casa)
                            num_final = str(num_input) if num_input else ''
                            coord_final = str(coord_input) if coord_input else ''
                            cep_trab_final = local_selecionado['cep']  # Pega o CEP da unidade selecionada
                            
                            with st.spinner("Salvando no banco de dados..."):
                                # Fazemos o UPDATE direto aqui para garantir que o CEP Trabalho seja atualizado
                                conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db'))
                                cursor = conexao.cursor()
                                cursor.execute('''
                                    UPDATE jovens_rotas 
                                    SET matricula = ?, email = ?, celular = ?, cep_casa = ?, numero_casa = ?, coordenadas = ?, cep_trabalho = ?
                                    WHERE id = ?
                                ''', (mat_final, email_final, celular_final, cep_final, num_final, coord_final, cep_trab_final, id_selecionado))
                                conexao.commit()
                                
                                # Atualiza a tela
                                df_atualizado = pd.read_sql_query("SELECT * FROM jovens_rotas WHERE id = ?", conexao, params=(int(id_selecionado),))
                                conexao.close()
                                
                            if not df_atualizado.empty:
                                st.session_state.resultado_busca = df_atualizado
                                st.session_state.modo_edicao = False
                                st.session_state.pop('coord_temp', None)
                                st.session_state.rota_gerada = None # Força o recalculo da rota para a nova empresa
                                st.session_state.analise_ia = None
                                
                                st.success("✅ Dados e Local de Trabalho salvos com sucesso!")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("❌ Erro ao recarregar dados do banco.")
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")

        # ── MODO VISUALIZAÇÃO ──
        else:
            end_casa_dict = buscar_endereco_viacep(cep_casa)
            end_trab_dict = buscar_endereco_viacep(cep_trab)

            rua_casa = end_casa_dict.get('rua','N/A') if isinstance(end_casa_dict, dict) else end_casa_dict
            bairro_cidade_casa = f"{end_casa_dict.get('bairro','')} - {end_casa_dict.get('cidade_uf','')}" if isinstance(end_casa_dict, dict) else ""
            rua_trab = end_trab_dict.get('rua','N/A') if isinstance(end_trab_dict, dict) else end_trab_dict
            bairro_cidade_trab = f"{end_trab_dict.get('bairro','')} - {end_trab_dict.get('cidade_uf','')}" if isinstance(end_trab_dict, dict) else ""

            if not st.session_state.get('rota_gerada'):
                endereco_completo_casa = end_casa_dict.get('completo', f"{rua_casa}, São Paulo, SP, Brasil") if isinstance(end_casa_dict, dict) else f"{rua_casa}, São Paulo, SP, Brasil"
                endereco_completo_trab = end_trab_dict.get('completo', f"{rua_trab}, São Paulo, SP, Brasil") if isinstance(end_trab_dict, dict) else f"{rua_trab}, São Paulo, SP, Brasil"
                
                rota = motor_de_rotas_gratuito(endereco_completo_casa, endereco_completo_trab)
                st.session_state.rota_gerada = rota
                
                if not st.session_state.get('analise_ia'):
                    st.session_state.analise_ia = analisar_rota_com_ia(
                        rua_casa, rua_trab, rota['distancia_km'], rota['rotas'], rota['info_tarifas']
                    )

            col_fill, col_edit_btn = st.columns([11, 1])
            with col_edit_btn:
                if st.button("✏️", use_container_width=True, help="Editar dados"):
                    st.session_state.modo_edicao = True
                    st.rerun()

            # Cor status
            if status_rota_raw == "Implantado":
                status_color, status_bg = "#10B981", "16,185,129"
            elif status_rota_raw == "Otimizado":
                status_color, status_bg = "#3B82F6", "59,130,246"
            elif status_rota_raw == "Contestada":
                status_color, status_bg = "#F59E0B", "245,158,11"
            else:
                status_color, status_bg = "#94A3B8", "148,163,184"

            # ── PREPARAÇÃO DAS STRINGS ──
            linha_num_casa = f', {numero_casa}' if numero_casa else ''

            # ── CARD DO FUNCIONÁRIO ──
            with st.container(border=True):
                # Cabeçalho com ID, título e status
                col_header_left, col_header_right = st.columns([10, 2])
                with col_header_left:
                    st.markdown(f"### 👤 Consulta #{id_selecionado}")
                    st.caption("RENAPSI · SÃO PAULO · C-T")
                with col_header_right:
                    st.markdown(f"""
                    <div style="background:rgba({status_bg},0.15);color:{status_color};padding:6px 14px;border-radius:20px;font-size:12px;font-weight:700;border:1px solid {status_color}40;text-align:center;">
                        {status_exib}
                    </div>
                    """, unsafe_allow_html=True)

                st.divider()

                # Três colunas para os dados
                col1, col2, col3 = st.columns(3)

                # Coluna 1: Dados do Funcionário
                with col1:
                    st.markdown("**Dados do Funcionário**")
                    st.markdown(f"**CPF:** {cpf_cru}")
                    st.markdown(f"**Matrícula:** {matricula_exib}")
                    st.markdown(f"**Nome:** {nome_jovem}")
                    if email_jovem:
                        st.markdown(f"**E-mail:** {email_jovem}")
                    if celular_jovem:
                        st.markdown(f"**Celular:** {celular_jovem}")

                # Coluna 2: Endereço Residencial
                with col2:
                    st.markdown("**Endereço Residencial**")
                    st.markdown("""
                    <span style="background:rgba(16,185,129,0.1);color:#10B981;padding:2px 8px;font-size:12px;border-radius:20px;font-weight:600;">● BAIXO RISCO</span>
                    """, unsafe_allow_html=True)
                    st.markdown(f"**CEP:** {cep_casa}")
                    st.markdown(f"{rua_casa}{linha_num_casa}  \n{bairro_cidade_casa}")

                # Coluna 3: Local de Trabalho
                with col3:
                    st.markdown("**Local de Trabalho**")
                    st.markdown(f"**CEP:** {cep_trab}")
                    st.markdown(f"{rua_trab}  \n{bairro_cidade_trab}")

            st.markdown("<br>", unsafe_allow_html=True)

    # ── LISTA DE PESQUISA ────────────────────────────────────────────────────
    else:
        st.markdown("""
        <h1 style="color:#1E293B;
                   font-size:26px;font-weight:800;margin-bottom:4px;">
            Pesquisar Consultas
        </h1>
        <p style="color:#666666;font-size:13px;margin-bottom:20px;">Localize aprendizes por CPF, nome ou matrícula</p>
        """, unsafe_allow_html=True)

        modalidade_pesquisa = st.radio(
            "Modalidade:",
            ["🏠 Casa × Trabalho", "📚 Casa × Curso"],
            horizontal=True
        )

        st.markdown("<hr style='border-color:rgba(0,212,255,0.1);'>", unsafe_allow_html=True)

        tab_cpf, tab_nome, tab_mat = st.tabs(["🔍 Por CPF", "👤 Por Nome", "🪪 Por Matrícula"])

        with tab_cpf:
            with st.form(key="form_cpf"):
                cpf_busca = st.text_input("CPF", max_chars=14, placeholder="000.000.000-00 ou só números")
                if st.form_submit_button("Pesquisar", type="primary"):
                    if not cpf_busca.strip():
                        st.warning("⚠️ Digite um CPF para buscar.")
                    else:
                        try:
                            # Tira pontos e traços do que a pessoa digitou
                            cpf_limpo = ''.join(filter(str.isdigit, cpf_busca))
                            
                            conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db'))
                            st.session_state.resultado_busca = pd.read_sql_query(
                                "SELECT * FROM jovens_rotas WHERE cpf = ?", conexao, params=(cpf_limpo,))
                            
                            if st.session_state.resultado_busca.empty:
                                st.warning("❌ Nenhum resultado encontrado para este CPF.")
                            st.session_state.detalhes_abertos = False
                            conexao.close()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro na busca: {str(e)}")

        with tab_nome:
            with st.form(key="form_nome"):
                nome_busca = st.text_input("Nome completo", placeholder="Digite o nome...")
                if st.form_submit_button("Pesquisar", type="primary"):
                    try:
                        conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db'))
                        st.session_state.resultado_busca = pd.read_sql_query(
                            "SELECT * FROM jovens_rotas WHERE nome LIKE ?", conexao, params=(f"%{nome_busca}%",))
                        if st.session_state.resultado_busca.empty:
                            st.warning("❌ Nenhum resultado encontrado para este nome")
                        st.session_state.detalhes_abertos = False
                        conexao.close()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro na busca: {str(e)}")

        with tab_mat:
            with st.form(key="form_mat"):
                mat_busca = st.text_input("Matrícula", placeholder="Apenas números")
                if st.form_submit_button("Pesquisar", type="primary"):
                    try:
                        conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db'))
                        st.session_state.resultado_busca = pd.read_sql_query(
                            "SELECT * FROM jovens_rotas WHERE matricula = ?", conexao, params=(mat_busca,))
                        if st.session_state.resultado_busca.empty:
                            st.warning("❌ Nenhum resultado encontrado para esta matrícula")
                        st.session_state.detalhes_abertos = False
                        conexao.close()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro na busca: {str(e)}")

        if st.session_state.resultado_busca is not None and not st.session_state.resultado_busca.empty:
            st.markdown("<hr style='border-color:rgba(0,212,255,0.1);margin:20px 0;'>", unsafe_allow_html=True)
            st.markdown("<p style='color:#444c9b;font-size:12px;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;'>📋 Resultados da Busca</p>", unsafe_allow_html=True)
            
            for _, row in st.session_state.resultado_busca.iterrows():
                col_info, col_btn = st.columns([10, 2])
                with col_info:
                    st.markdown(f"""
                    <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:8px;padding:12px;">
                        <p style="margin:0;color:#444c9b;font-weight:700;font-size:16px;">
                            {row['nome']}
                        </p>
                        <p style="margin:4px 0 0;color:#666666;font-size:13px;">
                            CPF: {str(row['cpf']).zfill(11)} · Matrícula: {row.get('matricula', 'N/A')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    if st.button("Abrir", key=f"btn_abrir_{row['id']}", use_container_width=True):
                        st.session_state.resultado_busca = pd.DataFrame([row])
                        st.session_state.detalhes_abertos = True
                        st.query_params['id_consulta'] = str(row['id'])
                        st.rerun()
