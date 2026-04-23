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


def _formulario_nova_unidade():
    """Formulário para cadastrar nova unidade."""
    st.subheader("Nova Unidade / Polo de Ensino")
    
    nome_unidade = st.text_input("Nome do Local (Ex: Polo Centro, SAMS Club)")
    
    # ── SELETOR DE TRABALHO OU CURSO ──
    tipo_local_input = st.radio("Tipo de Localidade:", ["Trabalho", "Curso"], horizontal=True)
    
    cep = st.text_input("CEP", max_chars=8)
    
    col1, col2 = st.columns(2)
    with col1: logradouro = st.text_input("Logradouro (Rua, Av)")
    with col2: numero = st.text_input("Número")
    
    bairro = st.text_input("Bairro")
    cidade_uf = st.text_input("Cidade/UF")
    
    coords = st.session_state.get('coordenadas_temp', '')
    st.text_input("Coordenadas (Lat, Lon)", value=coords, disabled=True)
    
    if st.button("🔍 Buscar Coordenadas Reais", type="secondary"):
        if cep and numero:
            end_completo = f"CEP {cep}, {numero}, Brasil"
            lat, lon = obter_coordenadas_reais(end_completo)
            if lat and lon:
                st.session_state.coordenadas_temp = f"{lat}, {lon}"
                st.success(f"✅ Coordenadas: {lat}, {lon}")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Coordenadas não encontradas.")
        else:
            st.warning("⚠️ Preencha CEP e Número.")

    if st.button("💾 Salvar Localidade", type="primary"):
        if not nome_unidade or not cep or not logradouro or not numero:
            st.error("⚠️ Preencha todos os campos obrigatórios")
        else:
            inserir_local_trabalho(
                nome_unidade=nome_unidade, cep=cep, logradouro=logradouro, 
                numero=numero, bairro=bairro, cidade_uf=cidade_uf, 
                coordenadas=coords, tipo_local=tipo_local_input
            )
            st.success(f"✅ Unidade '{nome_unidade}' ({tipo_local_input}) cadastrada com sucesso!")
            if 'coordenadas_temp' in st.session_state:
                del st.session_state.coordenadas_temp
            time.sleep(2)
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
                        tipo_local=tipo_local_input,
                        coordenadas=coords
                    )
                    st.success(f"✅ Unidade '{nome_unidade}' ({tipo_local_input}) cadastrada com sucesso!")
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
