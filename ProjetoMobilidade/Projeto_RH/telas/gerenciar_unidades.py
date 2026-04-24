"""Tela de gerenciamento de locais de trabalho (unidades)."""

import streamlit as st
import sqlite3
import os
import time
from apis import buscar_endereco_viacep, obter_coordenadas_reais
from banco_dados import inserir_local_trabalho, obter_locais_trabalho


def renderizar_gerenciar_unidades():
    """Renderiza a tela de gerenciamento de unidades."""
    st.title("🏢 Gerenciar Unidades")

    tab1, tab2, tab3 = st.tabs(["📋 Listar Unidades", "➕ Cadastrar Unidade Trabalho", "➕ Cadastrar Unidade Curso"])

    with tab1:
        _listar_unidades()

    with tab2:
        _formulario_nova_unidade_trabalho()

    with tab3:
        _formulario_nova_unidade_curso()


def _listar_unidades():
    """Lista todas as unidades cadastradas."""
    st.subheader("Unidades Cadastradas")

    locais = obter_locais_trabalho()

    if not locais:
        st.info("Nenhuma unidade cadastrada ainda.")
        return

    for local in locais:
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                tipo_badge = "🏢 Trabalho" if local.get('tipo_local', 'Trabalho') == 'Trabalho' else "📚 Curso"
                st.markdown(f"**{local['nome_unidade']}** `{tipo_badge}`")
                st.caption(f"CEP: {local['cep']}")
                st.markdown(f"{local['logradouro']}, {local['numero']} - {local['bairro']}")
                st.caption(f"{local['cidade_uf']}")
                if local['coordenadas']:
                    st.caption(f"📍 {local['coordenadas']}")
            with col2:
                if st.button("🗑️", key=f"del_{local['id']}", help="Deletar"):
                    _deletar_unidade(local['id'])
                    st.rerun()


def _formulario_nova_unidade_trabalho():
    """Formulário para cadastrar nova unidade de TRABALHO."""
    st.subheader("Cadastrar Nova Unidade de Trabalho")
    st.caption("Empresas, indústrias e locais de trabalho")

    # Inicializa estado da sessão
    if 'coordenadas_temp_trabalho' not in st.session_state:
        st.session_state.coordenadas_temp_trabalho = ''

    with st.form("form_nova_unidade_trabalho"):
        nome_unidade = st.text_input("Nome da Unidade", placeholder="Ex: Empresa XYZ - São Paulo", key="nome_trabalho")
        cep = st.text_input("CEP", placeholder="00000000", max_chars=8, key="cep_trabalho")

        if cep and len(cep) == 8:
            endereco = buscar_endereco_viacep(cep)
            if isinstance(endereco, dict):
                logradouro = st.text_input("Logradouro", value=endereco.get('rua', ''), disabled=True, key="logradouro_trabalho")
                bairro = st.text_input("Bairro", value=endereco.get('bairro', ''), disabled=True, key="bairro_trabalho")
                cidade_uf = st.text_input("Cidade/UF", value=endereco.get('cidade_uf', ''), disabled=True, key="cidade_trabalho")
            else:
                st.error("CEP não encontrado")
                logradouro = st.text_input("Logradouro", key="logradouro_trabalho_manual")
                bairro = st.text_input("Bairro", key="bairro_trabalho_manual")
                cidade_uf = st.text_input("Cidade/UF", key="cidade_trabalho_manual")
        else:
            logradouro = st.text_input("Logradouro", key="logradouro_trabalho_manual2")
            bairro = st.text_input("Bairro", key="bairro_trabalho_manual2")
            cidade_uf = st.text_input("Cidade/UF", key="cidade_trabalho_manual2")

        numero = st.text_input("Número", placeholder="Ex: 123", key="numero_trabalho")

        # Exibe coordenadas armazenadas ou placeholder
        coordenadas_display = st.session_state.get('coordenadas_temp_trabalho', '')
        coordenadas = st.text_input(
            "Coordenadas (Lat, Long)",
            value=coordenadas_display,
            placeholder="Ex: -23.5505, -46.6333",
            disabled=True,
            key="coordenadas_trabalho"
        )

        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("🔍 Buscar Coordenadas Reais", use_container_width=True, key="buscar_coord_trabalho"):
                if logradouro and numero and cidade_uf:
                    endereco_completo = f"{logradouro}, {numero}, {cidade_uf}"
                    coords = obter_coordenadas_reais(endereco_completo)
                    if coords:
                        st.session_state.coordenadas_temp_trabalho = coords
                        st.success(f"✅ Coordenadas encontradas: {coords}")
                        st.rerun()
                    else:
                        st.error("❌ Não foi possível encontrar as coordenadas. Verifique o endereço.")
                else:
                    st.error("⚠️ Preencha logradouro, número e cidade/UF")

        with col2:
            if st.form_submit_button("🗑️ Limpar Coordenadas", use_container_width=True, key="limpar_coord_trabalho"):
                st.session_state.coordenadas_temp_trabalho = ''
                st.info("✅ Coordenadas limpas")
                st.rerun()

        with col3:
            if st.form_submit_button("💾 Salvar Unidade Trabalho", use_container_width=True, type="primary", key="salvar_trabalho"):
                if not nome_unidade or not cep or not logradouro or not numero:
                    st.error("⚠️ Preencha todos os campos obrigatórios")
                else:
                    coords = st.session_state.get('coordenadas_temp_trabalho', '')
                    inserir_local_trabalho(
                        nome_unidade=nome_unidade,
                        cep=cep,
                        logradouro=logradouro,
                        numero=numero,
                        bairro=bairro,
                        cidade_uf=cidade_uf,
                        tipo_local='Trabalho',
                        coordenadas=coords
                    )
                    st.success(f"✅ Unidade de Trabalho '{nome_unidade}' cadastrada com sucesso!")
                    if 'coordenadas_temp_trabalho' in st.session_state:
                        del st.session_state.coordenadas_temp_trabalho
                    st.rerun()


def _formulario_nova_unidade_curso():
    """Formulário para cadastrar nova unidade de CURSO."""
    st.subheader("Cadastrar Nova Unidade de Curso")
    st.caption("Escolas, polos educacionais e centros de treinamento")

    # Inicializa estado da sessão
    if 'coordenadas_temp_curso' not in st.session_state:
        st.session_state.coordenadas_temp_curso = ''

    with st.form("form_nova_unidade_curso"):
        nome_unidade = st.text_input("Nome da Unidade", placeholder="Ex: Escola ABC - São Paulo", key="nome_curso")
        cep = st.text_input("CEP", placeholder="00000000", max_chars=8, key="cep_curso")

        if cep and len(cep) == 8:
            endereco = buscar_endereco_viacep(cep)
            if isinstance(endereco, dict):
                logradouro = st.text_input("Logradouro", value=endereco.get('rua', ''), disabled=True, key="logradouro_curso")
                bairro = st.text_input("Bairro", value=endereco.get('bairro', ''), disabled=True, key="bairro_curso")
                cidade_uf = st.text_input("Cidade/UF", value=endereco.get('cidade_uf', ''), disabled=True, key="cidade_curso")
            else:
                st.error("CEP não encontrado")
                logradouro = st.text_input("Logradouro", key="logradouro_curso_manual")
                bairro = st.text_input("Bairro", key="bairro_curso_manual")
                cidade_uf = st.text_input("Cidade/UF", key="cidade_curso_manual")
        else:
            logradouro = st.text_input("Logradouro", key="logradouro_curso_manual2")
            bairro = st.text_input("Bairro", key="bairro_curso_manual2")
            cidade_uf = st.text_input("Cidade/UF", key="cidade_curso_manual2")

        numero = st.text_input("Número", placeholder="Ex: 456", key="numero_curso")

        # Exibe coordenadas armazenadas ou placeholder
        coordenadas_display = st.session_state.get('coordenadas_temp_curso', '')
        coordenadas = st.text_input(
            "Coordenadas (Lat, Long)",
            value=coordenadas_display,
            placeholder="Ex: -23.5505, -46.6333",
            disabled=True,
            key="coordenadas_curso"
        )

        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("🔍 Buscar Coordenadas Reais", use_container_width=True, key="buscar_coord_curso"):
                if logradouro and numero and cidade_uf:
                    endereco_completo = f"{logradouro}, {numero}, {cidade_uf}"
                    coords = obter_coordenadas_reais(endereco_completo)
                    if coords:
                        st.session_state.coordenadas_temp_curso = coords
                        st.success(f"✅ Coordenadas encontradas: {coords}")
                        st.rerun()
                    else:
                        st.error("❌ Não foi possível encontrar as coordenadas. Verifique o endereço.")
                else:
                    st.error("⚠️ Preencha logradouro, número e cidade/UF")

        with col2:
            if st.form_submit_button("🗑️ Limpar Coordenadas", use_container_width=True, key="limpar_coord_curso"):
                st.session_state.coordenadas_temp_curso = ''
                st.info("✅ Coordenadas limpas")
                st.rerun()

        with col3:
            if st.form_submit_button("💾 Salvar Unidade Curso", use_container_width=True, type="primary", key="salvar_curso"):
                if not nome_unidade or not cep or not logradouro or not numero:
                    st.error("⚠️ Preencha todos os campos obrigatórios")
                else:
                    coords = st.session_state.get('coordenadas_temp_curso', '')
                    inserir_local_trabalho(
                        nome_unidade=nome_unidade,
                        cep=cep,
                        logradouro=logradouro,
                        numero=numero,
                        bairro=bairro,
                        cidade_uf=cidade_uf,
                        tipo_local='Curso',
                        coordenadas=coords
                    )
                    st.success(f"✅ Unidade de Curso '{nome_unidade}' cadastrada com sucesso!")
                    if 'coordenadas_temp_curso' in st.session_state:
                        del st.session_state.coordenadas_temp_curso
                    st.rerun()


def _deletar_unidade(unidade_id):
    """Deleta uma unidade do banco."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mobilidade_renapsi.db')
        conexao = sqlite3.connect(db_path)
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM locais_trabalho WHERE id = ?", (unidade_id,))
        conexao.commit()
        conexao.close()
        st.success("✅ Unidade deletada com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao deletar: {str(e)}")
