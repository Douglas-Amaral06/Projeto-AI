"""
RENAPSI - Sistema de Mobilidade Urbana
Entry point da aplicação Streamlit
"""

import streamlit as st
from dotenv import load_dotenv
from banco_dados import inicializar_banco_completo
from telas.theme import aplicar_tema
from telas.sidebar import renderizar_sidebar
from telas.dashboard import renderizar_dashboard
from telas.consultas import renderizar_consultas
from telas.cadastro import renderizar_cadastro
from telas.triagem import renderizar_triagem
from telas.banco_dados import renderizar_banco_dados
from telas.gerenciar_unidades import renderizar_gerenciar_unidades
from telas.portal_jovem import renderizar_portal_jovem

load_dotenv()

st.set_page_config(
    page_title="RENAPSI — Mobilidade",
    page_icon="🚇",
    layout="wide"
)

aplicar_tema()
inicializar_banco_completo()

menu = renderizar_sidebar()

if menu == "Dashboard Principal":
    renderizar_dashboard()
elif menu == "Pesquisar Consultas":
    renderizar_consultas()
elif menu == "Cadastrar Novo Jovem":
    renderizar_cadastro()
elif menu == "🗂️ Triagem de Fichas":
    renderizar_triagem()
elif menu == "Banco de Dados":
    renderizar_banco_dados()
elif menu == "🏢 Gerenciar Unidades":
    renderizar_gerenciar_unidades()
elif menu == "Simulação: Portal do Jovem":
    renderizar_portal_jovem()
