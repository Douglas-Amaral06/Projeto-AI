"""Tela de gerenciamento do banco de dados."""

import streamlit as st
import sqlite3
import pandas as pd
import os
import io
import shutil
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Caminho do banco (dois níveis acima de telas/)
_DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')

# Tabelas que NUNCA devem aparecer nesta tela (segurança)
_TABELAS_OCULTAS = {"usuarios_sistema"}


def renderizar_banco_dados():
    """Renderiza a tela de visualização avançada do banco de dados."""

    st.markdown("""
    <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-left:4px solid #444c9b;
                border-radius:14px;padding:24px;margin-bottom:24px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
        <h3 style="margin:0 0 4px;color:#444c9b;">💾 Banco de Dados Avançado</h3>
        <p style="color:#64748B;font-size:14px;margin:0;">
            Visualização, edição, análise e gerenciamento completo das tabelas do sistema.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Tabs principais
    tab_visualizar, tab_estatisticas, tab_graficos, tab_backup, tab_importar = st.tabs([
        "📊 Visualizar & Editar", "📈 Estatísticas", "📉 Gráficos", "💾 Backup/Restaurar", "📥 Importar Dados"
    ])

    try:
        conexao = sqlite3.connect(_DB_PATH)
        cursor = conexao.cursor()

        # Lista todas as tabelas do banco
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        todas_tabelas = [row[0] for row in cursor.fetchall()]

        # Remove tabelas sensíveis
        tabelas_visiveis = [t for t in todas_tabelas if t not in _TABELAS_OCULTAS]

        if not tabelas_visiveis:
            st.info("Nenhuma tabela disponível para visualização.")
            conexao.close()
            return

        # ─── TAB 1: VISUALIZAR & EDITAR ───────────────────────────────────────
        with tab_visualizar:
            col_tabela, col_limite = st.columns([3, 1])
            
            with col_tabela:
                tabela_selecionada = st.selectbox(
                    "📋 Selecione a tabela:",
                    tabelas_visiveis,
                    index=0
                )
            
            with col_limite:
                limite_registros = st.selectbox(
                    "📊 Limite de registros:",
                    [100, 500, 1000, 5000, "Todos"],
                    index=1
                )

            if tabela_selecionada:
                # Dupla verificação de segurança
                if tabela_selecionada in _TABELAS_OCULTAS:
                    st.error("🚫 Acesso negado a esta tabela.")
                    conexao.close()
                    return

                # Carregar dados
                limite_sql = "" if limite_registros == "Todos" else f"LIMIT {limite_registros}"
                df_original = pd.read_sql_query(
                    f"SELECT * FROM [{tabela_selecionada}] {limite_sql}",
                    conexao
                )

                if df_original.empty:
                    st.info(f"📭 A tabela '{tabela_selecionada}' está vazia.")
                    conexao.close()
                    return

                # ─── FILTROS AVANÇADOS ───────────────────────────────────────
                st.markdown("### 🔍 Filtros Avançados")
                
                col_busca_global, col_ordenar = st.columns([2, 1])
                
                with col_busca_global:
                    busca_global = st.text_input(
                        "🔎 Busca Global (busca em todas as colunas)",
                        placeholder="Digite para buscar em toda a tabela..."
                    )
                
                with col_ordenar:
                    coluna_ordenar = st.selectbox(
                        "📊 Ordenar por:",
                        ["Sem ordenação"] + list(df_original.columns)
                    )

                # Filtros por coluna
                with st.expander("🎯 Filtros por Coluna", expanded=False):
                    filtros_colunas = {}
                    cols_filtro = st.columns(3)
                    
                    for idx, coluna in enumerate(df_original.columns):
                        with cols_filtro[idx % 3]:
                            valores_unicos = df_original[coluna].dropna().unique()
                            
                            if len(valores_unicos) <= 50:  # Selectbox para poucos valores
                                filtro = st.multiselect(
                                    f"🔹 {coluna}",
                                    options=sorted(valores_unicos.astype(str)),
                                    key=f"filtro_{coluna}"
                                )
                                if filtro:
                                    filtros_colunas[coluna] = filtro
                            else:  # Text input para muitos valores
                                filtro = st.text_input(
                                    f"🔹 {coluna} (contém)",
                                    key=f"filtro_{coluna}"
                                )
                                if filtro:
                                    filtros_colunas[coluna] = filtro

                # Aplicar filtros
                df_filtrado = df_original.copy()

                # Busca global
                if busca_global:
                    mask = df_filtrado.astype(str).apply(
                        lambda row: row.str.contains(busca_global, case=False, na=False).any(),
                        axis=1
                    )
                    df_filtrado = df_filtrado[mask]

                # Filtros por coluna
                for coluna, valor_filtro in filtros_colunas.items():
                    if isinstance(valor_filtro, list):  # Multiselect
                        df_filtrado = df_filtrado[df_filtrado[coluna].astype(str).isin(valor_filtro)]
                    else:  # Text input
                        df_filtrado = df_filtrado[
                            df_filtrado[coluna].astype(str).str.contains(valor_filtro, case=False, na=False)
                        ]

                # Ordenação
                if coluna_ordenar != "Sem ordenação":
                    ordem_crescente = st.checkbox("Ordem crescente", value=True)
                    df_filtrado = df_filtrado.sort_values(by=coluna_ordenar, ascending=ordem_crescente)

                # ─── ESTATÍSTICAS RÁPIDAS ─────────────────────────────────────
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                
                with col_stat1:
                    st.metric("📊 Total de Registros", len(df_original))
                with col_stat2:
                    st.metric("✅ Registros Filtrados", len(df_filtrado))
                with col_stat3:
                    st.metric("📋 Colunas", len(df_filtrado.columns))
                with col_stat4:
                    percentual = (len(df_filtrado) / len(df_original) * 100) if len(df_original) > 0 else 0
                    st.metric("📈 % Exibido", f"{percentual:.1f}%")

                st.markdown("---")

                # ─── EXPORTAÇÃO ──────────────────────────────────────────────
                col_exp1, col_exp2, col_exp3 = st.columns(3)
                
                with col_exp1:
                    # Exportar para Excel
                    buffer_excel = io.BytesIO()
                    with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                        df_filtrado.to_excel(writer, index=False, sheet_name=tabela_selecionada[:31])
                    
                    st.download_button(
                        label="📥 Exportar para Excel",
                        data=buffer_excel.getvalue(),
                        file_name=f"{tabela_selecionada}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col_exp2:
                    # Exportar para CSV
                    csv = df_filtrado.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Exportar para CSV",
                        data=csv,
                        file_name=f"{tabela_selecionada}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col_exp3:
                    # Exportar para JSON
                    json_data = df_filtrado.to_json(orient='records', indent=2, force_ascii=False)
                    st.download_button(
                        label="📥 Exportar para JSON",
                        data=json_data,
                        file_name=f"{tabela_selecionada}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )

                st.markdown("---")

                # ─── PAGINAÇÃO ────────────────────────────────────────────────
                st.markdown("### 📄 Visualização Paginada")
                
                # Configurar paginação
                registros_por_pagina = st.selectbox(
                    "Registros por página:",
                    [10, 25, 50, 100],
                    index=2,
                    key="registros_pagina"
                )
                
                total_paginas = (len(df_filtrado) - 1) // registros_por_pagina + 1
                
                if 'pagina_atual' not in st.session_state:
                    st.session_state.pagina_atual = 1
                
                col_pag1, col_pag2, col_pag3, col_pag4, col_pag5 = st.columns([1, 1, 2, 1, 1])
                
                with col_pag1:
                    if st.button("⏮️ Primeira", use_container_width=True, disabled=(st.session_state.pagina_atual == 1)):
                        st.session_state.pagina_atual = 1
                        st.rerun()
                
                with col_pag2:
                    if st.button("◀️ Anterior", use_container_width=True, disabled=(st.session_state.pagina_atual == 1)):
                        st.session_state.pagina_atual -= 1
                        st.rerun()
                
                with col_pag3:
                    st.markdown(f"<div style='text-align:center;padding:8px;'><strong>Página {st.session_state.pagina_atual} de {total_paginas}</strong></div>", unsafe_allow_html=True)
                
                with col_pag4:
                    if st.button("▶️ Próxima", use_container_width=True, disabled=(st.session_state.pagina_atual == total_paginas)):
                        st.session_state.pagina_atual += 1
                        st.rerun()
                
                with col_pag5:
                    if st.button("⏭️ Última", use_container_width=True, disabled=(st.session_state.pagina_atual == total_paginas)):
                        st.session_state.pagina_atual = total_paginas
                        st.rerun()

                # Calcular índices da página
                inicio = (st.session_state.pagina_atual - 1) * registros_por_pagina
                fim = inicio + registros_por_pagina
                df_pagina = df_filtrado.iloc[inicio:fim].copy()

                # ─── INDICADORES VISUAIS E AÇÕES POR LINHA ────────────────────
                st.markdown("### 📋 Dados da Tabela")
                
                # Adicionar coluna de ações
                df_pagina.insert(0, '🎯 Ações', range(inicio, inicio + len(df_pagina)))
                
                # Aplicar indicadores visuais baseados em colunas de status
                def aplicar_indicadores(row):
                    """Aplica indicadores visuais baseados em valores de status"""
                    estilos = [''] * len(row)
                    
                    for idx, (col_name, valor) in enumerate(row.items()):
                        valor_str = str(valor).lower()
                        
                        # Status de aprovação/situação
                        if 'status' in col_name.lower() or 'situacao' in col_name.lower():
                            if any(x in valor_str for x in ['aprovado', 'ativo', 'implantado', 'concluido', 'sucesso']):
                                estilos[idx] = 'background-color: #d4edda; color: #155724;'
                            elif any(x in valor_str for x in ['pendente', 'aguardando', 'em andamento', 'processando']):
                                estilos[idx] = 'background-color: #fff3cd; color: #856404;'
                            elif any(x in valor_str for x in ['reprovado', 'inativo', 'cancelado', 'erro', 'falha']):
                                estilos[idx] = 'background-color: #f8d7da; color: #721c24;'
                            elif any(x in valor_str for x in ['revisao', 'contestada']):
                                estilos[idx] = 'background-color: #d1ecf1; color: #0c5460;'
                    
                    return estilos

                # Renderizar tabela com indicadores
                st.markdown("""
                <style>
                    .dataframe-container {
                        overflow-x: auto;
                        -webkit-overflow-scrolling: touch;
                    }
                    @media (max-width: 768px) {
                        .dataframe {
                            font-size: 12px;
                        }
                    }
                </style>
                """, unsafe_allow_html=True)

                # Exibir tabela com estilo
                st.dataframe(
                    df_pagina,
                    use_container_width=True,
                    height=400,
                    hide_index=True
                )

                # ─── AÇÕES RÁPIDAS POR LINHA ──────────────────────────────────
                st.markdown("### ⚡ Ações Rápidas")
                
                col_acao1, col_acao2 = st.columns([3, 1])
                
                with col_acao1:
                    # Seletor de linha para ações
                    if len(df_pagina) > 0:
                        opcoes_linhas = [f"Linha {i+1}" for i in range(len(df_pagina))]
                        linha_selecionada = st.selectbox(
                            "Selecione uma linha para ações:",
                            opcoes_linhas,
                            key="linha_acao"
                        )
                        linha_idx = int(linha_selecionada.split()[1]) - 1
                
                with col_acao2:
                    st.write("")
                    st.write("")
                    modo_acao = st.radio("Modo:", ["Ver", "Editar", "Excluir"], horizontal=True)

                if len(df_pagina) > 0:
                    # Obter dados da linha selecionada (sem a coluna de ações)
                    dados_linha = df_pagina.iloc[linha_idx, 1:].to_dict()
                    
                    if modo_acao == "Ver":
                        st.markdown("#### 👁️ Detalhes do Registro")
                        
                        # Exibir em cards
                        cols_detalhes = st.columns(2)
                        items = list(dados_linha.items())
                        
                        for idx, (campo, valor) in enumerate(items):
                            with cols_detalhes[idx % 2]:
                                # Aplicar cor baseada no valor
                                valor_str = str(valor).lower()
                                cor_fundo = "#ffffff"
                                cor_texto = "#333333"
                                
                                if 'status' in campo.lower():
                                    if any(x in valor_str for x in ['aprovado', 'ativo', 'implantado']):
                                        cor_fundo = "#d4edda"
                                        cor_texto = "#155724"
                                    elif any(x in valor_str for x in ['pendente', 'aguardando']):
                                        cor_fundo = "#fff3cd"
                                        cor_texto = "#856404"
                                    elif any(x in valor_str for x in ['reprovado', 'cancelado']):
                                        cor_fundo = "#f8d7da"
                                        cor_texto = "#721c24"
                                
                                st.markdown(f"""
                                <div style="background-color: {cor_fundo}; color: {cor_texto}; 
                                            padding: 10px; border-radius: 8px; margin-bottom: 10px;
                                            border: 1px solid #dee2e6;">
                                    <strong>{campo}:</strong><br>
                                    {valor}
                                </div>
                                """, unsafe_allow_html=True)
                    
                    elif modo_acao == "Editar":
                        st.markdown("#### ✏️ Editar Registro")
                        
                        with st.form(f"form_editar_{linha_idx}"):
                            dados_editados = {}
                            
                            cols_edit = st.columns(2)
                            items = list(dados_linha.items())
                            
                            for idx, (campo, valor) in enumerate(items):
                                with cols_edit[idx % 2]:
                                    dados_editados[campo] = st.text_input(
                                        campo,
                                        value=str(valor),
                                        key=f"edit_{campo}_{linha_idx}"
                                    )
                            
                            if st.form_submit_button("💾 Salvar Alterações", type="primary", use_container_width=True):
                                try:
                                    # Construir UPDATE query
                                    set_clause = ", ".join([f"[{k}] = ?" for k in dados_editados.keys()])
                                    valores = list(dados_editados.values())
                                    
                                    # Usar primeira coluna como identificador (geralmente ID)
                                    primeira_coluna = df_filtrado.columns[0]
                                    id_valor = df_filtrado.iloc[inicio + linha_idx][primeira_coluna]
                                    
                                    query = f"UPDATE [{tabela_selecionada}] SET {set_clause} WHERE [{primeira_coluna}] = ?"
                                    valores.append(id_valor)
                                    
                                    cursor.execute(query, valores)
                                    conexao.commit()
                                    
                                    st.success("✅ Registro atualizado com sucesso!")
                                    st.rerun()
                                
                                except Exception as e:
                                    st.error(f"❌ Erro ao atualizar: {str(e)}")
                                    conexao.rollback()
                    
                    elif modo_acao == "Excluir":
                        st.markdown("#### 🗑️ Excluir Registro")
                        
                        st.warning("⚠️ Esta ação não pode ser desfeita!")
                        
                        # Mostrar dados que serão excluídos
                        st.json(dados_linha)
                        
                        col_confirmar, col_cancelar_del = st.columns(2)
                        
                        with col_confirmar:
                            if st.button("🗑️ Confirmar Exclusão", type="primary", use_container_width=True):
                                try:
                                    # Usar primeira coluna como identificador
                                    primeira_coluna = df_filtrado.columns[0]
                                    id_valor = df_filtrado.iloc[inicio + linha_idx][primeira_coluna]
                                    
                                    cursor.execute(f"DELETE FROM [{tabela_selecionada}] WHERE [{primeira_coluna}] = ?", (id_valor,))
                                    conexao.commit()
                                    
                                    st.success("✅ Registro excluído com sucesso!")
                                    st.rerun()
                                
                                except Exception as e:
                                    st.error(f"❌ Erro ao excluir: {str(e)}")
                                    conexao.rollback()
                        
                        with col_cancelar_del:
                            if st.button("❌ Cancelar", use_container_width=True):
                                st.info("Exclusão cancelada.")

                st.markdown("---")

                # ─── EDIÇÃO EM LOTE ───────────────────────────────────────────
                with st.expander("📝 Edição em Lote (Avançado)", expanded=False):
                    st.warning("⚠️ Use com cuidado! Esta função permite editar múltiplos registros de uma vez.")
                    
                    df_editado = st.data_editor(
                        df_filtrado,
                        use_container_width=True,
                        num_rows="dynamic",
                        key=f"editor_lote_{tabela_selecionada}"
                    )

                    col_salvar, col_cancelar = st.columns([1, 1])
                    
                    with col_salvar:
                        if st.button("💾 Salvar Todas as Alterações", type="primary", use_container_width=True):
                            try:
                                cursor.execute(f"DELETE FROM [{tabela_selecionada}]")
                                df_editado.to_sql(tabela_selecionada, conexao, if_exists='append', index=False)
                                conexao.commit()
                                
                                st.success("✅ Alterações salvas com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao salvar: {str(e)}")
                                conexao.rollback()
                    
                    with col_cancelar:
                        if st.button("🔄 Recarregar Dados Originais", use_container_width=True):
                            st.rerun()

        # ─── TAB 2: ESTATÍSTICAS ──────────────────────────────────────────────
        with tab_estatisticas:
            st.markdown("### 📊 Estatísticas da Tabela")
            
            tabela_stats = st.selectbox(
                "Selecione a tabela para análise:",
                tabelas_visiveis,
                key="stats_tabela"
            )
            
            if tabela_stats and tabela_stats not in _TABELAS_OCULTAS:
                df_stats = pd.read_sql_query(f"SELECT * FROM [{tabela_stats}]", conexao)
                
                if not df_stats.empty:
                    col_info1, col_info2 = st.columns(2)
                    
                    with col_info1:
                        st.markdown("#### 📋 Informações Gerais")
                        st.write(f"**Total de Registros:** {len(df_stats)}")
                        st.write(f"**Total de Colunas:** {len(df_stats.columns)}")
                        st.write(f"**Memória Utilizada:** {df_stats.memory_usage(deep=True).sum() / 1024:.2f} KB")
                        
                        # Valores nulos por coluna
                        st.markdown("#### ⚠️ Valores Nulos")
                        nulos = df_stats.isnull().sum()
                        nulos_df = pd.DataFrame({
                            'Coluna': nulos.index,
                            'Nulos': nulos.values,
                            '% Nulos': (nulos.values / len(df_stats) * 100).round(2)
                        })
                        st.dataframe(nulos_df[nulos_df['Nulos'] > 0], use_container_width=True)
                    
                    with col_info2:
                        st.markdown("#### 🔢 Estatísticas Descritivas")
                        
                        # Colunas numéricas
                        colunas_numericas = df_stats.select_dtypes(include=['number']).columns
                        
                        if len(colunas_numericas) > 0:
                            st.dataframe(df_stats[colunas_numericas].describe(), use_container_width=True)
                        else:
                            st.info("Nenhuma coluna numérica encontrada.")
                    
                    # Distribuição de valores por coluna
                    st.markdown("#### 📊 Distribuição de Valores")
                    
                    coluna_dist = st.selectbox(
                        "Selecione uma coluna:",
                        df_stats.columns,
                        key="coluna_distribuicao"
                    )
                    
                    if coluna_dist:
                        valores_contagem = df_stats[coluna_dist].value_counts().head(20)
                        
                        col_tabela_dist, col_grafico_dist = st.columns(2)
                        
                        with col_tabela_dist:
                            st.dataframe(
                                pd.DataFrame({
                                    'Valor': valores_contagem.index,
                                    'Quantidade': valores_contagem.values
                                }),
                                use_container_width=True
                            )
                        
                        with col_grafico_dist:
                            fig = px.bar(
                                x=valores_contagem.index.astype(str),
                                y=valores_contagem.values,
                                labels={'x': coluna_dist, 'y': 'Quantidade'},
                                title=f"Top 20 - {coluna_dist}"
                            )
                            st.plotly_chart(fig, use_container_width=True)

        # ─── TAB 3: GRÁFICOS ──────────────────────────────────────────────────
        with tab_graficos:
            st.markdown("### 📉 Gráficos Dinâmicos")
            
            tabela_grafico = st.selectbox(
                "Selecione a tabela:",
                tabelas_visiveis,
                key="grafico_tabela"
            )
            
            if tabela_grafico and tabela_grafico not in _TABELAS_OCULTAS:
                df_grafico = pd.read_sql_query(f"SELECT * FROM [{tabela_grafico}]", conexao)
                
                if not df_grafico.empty:
                    tipo_grafico = st.selectbox(
                        "Tipo de Gráfico:",
                        ["Barras", "Pizza", "Linha", "Dispersão", "Histograma"]
                    )
                    
                    col_config1, col_config2 = st.columns(2)
                    
                    with col_config1:
                        coluna_x = st.selectbox("Eixo X / Categoria:", df_grafico.columns, key="grafico_x")
                    
                    with col_config2:
                        colunas_numericas = df_grafico.select_dtypes(include=['number']).columns
                        coluna_y = st.selectbox(
                            "Eixo Y / Valor:",
                            ["Contagem"] + list(colunas_numericas),
                            key="grafico_y"
                        )
                    
                    # Gerar gráfico
                    if st.button("📊 Gerar Gráfico", type="primary"):
                        try:
                            if coluna_y == "Contagem":
                                dados_agrupados = df_grafico[coluna_x].value_counts().head(20)
                                
                                if tipo_grafico == "Barras":
                                    fig = px.bar(x=dados_agrupados.index, y=dados_agrupados.values,
                                               labels={'x': coluna_x, 'y': 'Contagem'})
                                elif tipo_grafico == "Pizza":
                                    fig = px.pie(values=dados_agrupados.values, names=dados_agrupados.index)
                                elif tipo_grafico == "Linha":
                                    fig = px.line(x=dados_agrupados.index, y=dados_agrupados.values,
                                                labels={'x': coluna_x, 'y': 'Contagem'})
                                else:
                                    st.warning("Tipo de gráfico não suportado para contagem.")
                                    fig = None
                            else:
                                if tipo_grafico == "Barras":
                                    fig = px.bar(df_grafico, x=coluna_x, y=coluna_y)
                                elif tipo_grafico == "Dispersão":
                                    fig = px.scatter(df_grafico, x=coluna_x, y=coluna_y)
                                elif tipo_grafico == "Linha":
                                    fig = px.line(df_grafico, x=coluna_x, y=coluna_y)
                                elif tipo_grafico == "Histograma":
                                    fig = px.histogram(df_grafico, x=coluna_y)
                                else:
                                    fig = None
                            
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                        
                        except Exception as e:
                            st.error(f"❌ Erro ao gerar gráfico: {str(e)}")

        # ─── TAB 4: BACKUP E RESTAURAÇÃO ──────────────────────────────────────
        with tab_backup:
            st.markdown("### 💾 Backup e Restauração")
            
            col_backup, col_restaurar = st.columns(2)
            
            with col_backup:
                st.markdown("#### 📤 Criar Backup")
                st.info("Cria uma cópia completa do banco de dados atual.")
                
                if st.button("💾 Criar Backup Agora", type="primary", use_container_width=True):
                    try:
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        backup_path = f"{_DB_PATH}.backup_{timestamp}.db"
                        
                        conexao.close()
                        shutil.copy2(_DB_PATH, backup_path)
                        conexao = sqlite3.connect(_DB_PATH)
                        
                        st.success(f"✅ Backup criado: {os.path.basename(backup_path)}")
                        
                        # Oferecer download
                        with open(backup_path, 'rb') as f:
                            st.download_button(
                                label="📥 Baixar Backup",
                                data=f,
                                file_name=os.path.basename(backup_path),
                                mime="application/x-sqlite3",
                                use_container_width=True
                            )
                    except Exception as e:
                        st.error(f"❌ Erro ao criar backup: {str(e)}")
            
            with col_restaurar:
                st.markdown("#### 📥 Restaurar Backup")
                st.warning("⚠️ Esta ação substituirá o banco de dados atual!")
                
                arquivo_backup = st.file_uploader(
                    "Selecione o arquivo de backup (.db):",
                    type=['db'],
                    key="upload_backup"
                )
                
                if arquivo_backup:
                    if st.button("🔄 Restaurar Backup", type="secondary", use_container_width=True):
                        try:
                            # Criar backup de segurança antes de restaurar
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            safety_backup = f"{_DB_PATH}.before_restore_{timestamp}.db"
                            
                            conexao.close()
                            shutil.copy2(_DB_PATH, safety_backup)
                            
                            # Restaurar backup
                            with open(_DB_PATH, 'wb') as f:
                                f.write(arquivo_backup.getvalue())
                            
                            conexao = sqlite3.connect(_DB_PATH)
                            
                            st.success("✅ Backup restaurado com sucesso!")
                            st.info(f"Backup de segurança criado: {os.path.basename(safety_backup)}")
                            st.rerun()
                        
                        except Exception as e:
                            st.error(f"❌ Erro ao restaurar: {str(e)}")

        # ─── TAB 5: IMPORTAR DADOS ────────────────────────────────────────────
        with tab_importar:
            st.markdown("### 📥 Importar Dados de Excel/CSV")
            
            tabela_importar = st.selectbox(
                "Selecione a tabela de destino:",
                tabelas_visiveis,
                key="importar_tabela"
            )
            
            arquivo_importar = st.file_uploader(
                "Selecione o arquivo Excel ou CSV:",
                type=['xlsx', 'xls', 'csv'],
                key="upload_importar"
            )
            
            if arquivo_importar and tabela_importar:
                try:
                    # Ler arquivo
                    if arquivo_importar.name.endswith('.csv'):
                        df_importar = pd.read_csv(arquivo_importar)
                    else:
                        df_importar = pd.read_excel(arquivo_importar)
                    
                    st.markdown("#### 👀 Preview dos Dados")
                    st.dataframe(df_importar.head(10), use_container_width=True)
                    
                    st.markdown(f"**Total de registros:** {len(df_importar)}")
                    st.markdown(f"**Colunas:** {', '.join(df_importar.columns)}")
                    
                    col_modo1, col_modo2 = st.columns(2)
                    
                    with col_modo1:
                        modo_importacao = st.radio(
                            "Modo de importação:",
                            ["Adicionar aos dados existentes", "Substituir todos os dados"]
                        )
                    
                    with col_modo2:
                        st.write("")
                        st.write("")
                        if st.button("📥 Importar Dados", type="primary", use_container_width=True):
                            try:
                                if modo_importacao == "Substituir todos os dados":
                                    cursor.execute(f"DELETE FROM [{tabela_importar}]")
                                
                                df_importar.to_sql(tabela_importar, conexao, if_exists='append', index=False)
                                conexao.commit()
                                
                                st.success(f"✅ {len(df_importar)} registros importados com sucesso!")
                                st.rerun()
                            
                            except Exception as e:
                                st.error(f"❌ Erro ao importar: {str(e)}")
                                conexao.rollback()
                
                except Exception as e:
                    st.error(f"❌ Erro ao ler arquivo: {str(e)}")

        conexao.close()

    except Exception as e:
        st.error(f"❌ Erro ao acessar o banco de dados: {str(e)}")
