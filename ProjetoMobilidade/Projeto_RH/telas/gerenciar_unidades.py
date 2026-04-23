"""Tela de gerenciamento de locais de trabalho (unidades)."""

import streamlit as st
import sqlite3
import os
import time
from apis import buscar_endereco_viacep, obter_coordenadas_reais
from banco_dados import inserir_local_trabalho, obter_locais_trabalho


def renderizar_gerenciar_unidades():
    """Renderiza a tela de gerenciamento de unidades."""
    st.title("🏢 Gerenciar Unidades de Trabalho")

    tab1, tab2 = st.tabs(["📋 Listar Unidades", "➕ Cadastrar Nova Unidade"])

    with tab1:
        _listar_unidades()

    with tab2:
        _formulario_nova_unidade()


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
                st.markdown(f"**{local['nome_unidade']}**")
                st.caption(f"CEP: {local['cep']}")
                st.markdown(f"{local['logradouro']}, {local['numero']} - {local['bairro']}")
                st.caption(f"{local['cidade_uf']}")
                if local['coordenadas']:
                    st.caption(f"📍 {local['coordenadas']}")
            with col2:
                if st.button("🗑️", key=f"del_{local['id']}", help="Deletar"):
                    _deletar_unidade(local['id'])
                    st.rerun()


def _formulario_nova_unidade():
    """Formulário para cadastrar nova unidade."""
    st.subheader("Cadastrar Nova Unidade")

    # Inicializa estado da sessão
    if 'coordenadas_temp' not in st.session_state:
        st.session_state.coordenadas_temp = ''

    with st.form("form_nova_unidade"):
        nome_unidade = st.text_input("Nome da Unidade", placeholder="Ex: RENAPSI - São Paulo")
        cep = st.text_input("CEP", placeholder="00000000", max_chars=8)

        if cep and len(cep) == 8:
            endereco = buscar_endereco_viacep(cep)
            if isinstance(endereco, dict):
                logradouro = st.text_input("Logradouro", value=endereco.get('rua', ''), disabled=True)
                bairro = st.text_input("Bairro", value=endereco.get('bairro', ''), disabled=True)
                cidade_uf = st.text_input("Cidade/UF", value=endereco.get('cidade_uf', ''), disabled=True)
            else:
                st.error("CEP não encontrado")
                logradouro = st.text_input("Logradouro")
                bairro = st.text_input("Bairro")
                cidade_uf = st.text_input("Cidade/UF")
        else:
            logradouro = st.text_input("Logradouro")
            bairro = st.text_input("Bairro")
            cidade_uf = st.text_input("Cidade/UF")

        numero = st.text_input("Número", placeholder="Ex: 123")

        # Exibe coordenadas armazenadas ou placeholder
        coordenadas_display = st.session_state.get('coordenadas_temp', '')
        coordenadas = st.text_input(
            "Coordenadas (Lat, Long)",
            value=coordenadas_display,
            placeholder="Ex: -23.5505, -46.6333",
            disabled=True
        )

        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("🔍 Buscar Coordenadas Reais", use_container_width=True):
                if logradouro and numero and cidade_uf:
                    endereco_completo = f"{logradouro}, {numero}, {cidade_uf}"
                    coords = obter_coordenadas_reais(endereco_completo)
                    if coords:
                        st.session_state.coordenadas_temp = coords
                        st.success(f"✅ Coordenadas encontradas: {coords}")
                        st.rerun()
                    else:
                        st.error("❌ Não foi possível encontrar as coordenadas. Verifique o endereço.")
                else:
                    st.error("⚠️ Preencha logradouro, número e cidade/UF")

        with col2:
            if st.form_submit_button("🗑️ Limpar Coordenadas", use_container_width=True):
                st.session_state.coordenadas_temp = ''
                st.info("✅ Coordenadas limpas")
                st.rerun()

        with col3:
            if st.form_submit_button("💾 Salvar Unidade", use_container_width=True, type="primary"):
                if not nome_unidade or not cep or not logradouro or not numero:
                    st.error("⚠️ Preencha todos os campos obrigatórios")
                else:
                    coords = st.session_state.get('coordenadas_temp', '')
                    inserir_local_trabalho(
                        nome_unidade=nome_unidade,
                        cep=cep,
                        logradouro=logradouro,
                        numero=numero,
                        bairro=bairro,
                        cidade_uf=cidade_uf,
                        coordenadas=coords
                    )
                    st.success(f"✅ Unidade '{nome_unidade}' cadastrada com sucesso!")
                    if 'coordenadas_temp' in st.session_state:
                        del st.session_state.coordenadas_temp
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
