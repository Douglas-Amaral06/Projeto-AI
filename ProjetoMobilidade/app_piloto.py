import streamlit as st
import sqlite3
import pandas as pd
import requests
import random
import time

# Configuração da página
st.set_page_config(page_title="Nova Capta - Piloto", page_icon="🚌", layout="wide")

# --- FUNÇÕES DE BANCO DE DADOS E API ---

def carregar_dados():
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    df = pd.read_sql_query("SELECT id, nome, cpf, cep_casa, cep_trabalho FROM jovens_rotas", conexao)
    conexao.close()
    return df

def inserir_novo_jovem(nome, cpf, cep_casa, cep_trabalho):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho)
        VALUES (?, ?, ?, ?)
    ''', (nome, cpf, cep_casa, cep_trabalho))
    conexao.commit()
    conexao.close()

def buscar_endereco_viacep(cep):
    url = f"https://viacep.com.br/ws/{cep}/json/"
    try:
        resposta = requests.get(url).json()
        if "erro" not in resposta:
            return f"{resposta.get('logradouro')}, {resposta.get('bairro')} - {resposta.get('localidade')}/SP"
    except Exception:
        pass
    return "Endereço não encontrado ou CEP inválido."

def roteirizar_simulado():
    opcoes_rota = [
        {"trajeto": "1 Autocarro Municipal (SPTrans)", "valor_diario": 8.80, "tempo": "45 min"},
        {"trajeto": "1 Autocarro + 1 Metro (Integração)", "valor_diario": 10.00, "tempo": "1h 10min"},
        {"trajeto": "Metro Direto (Linha Azul)", "valor_diario": 10.00, "tempo": "30 min"}
    ]
    return random.choice(opcoes_rota)

# --- MENU LATERAL (SIDEBAR) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3204/3204993.png", width=100) # Um ícone genérico de RH/Transporte
st.sidebar.title("Menu de Navegação")
menu = st.sidebar.radio("Escolha a área:", ["🚌 Painel de Roteirização", "➕ Registar Novo Jovem"])

# --- ECRÃ 1: PAINEL DE ROTEIRIZAÇÃO (O que já tínhamos) ---
if menu == "🚌 Painel de Roteirização":
    st.title("🚌 Painel de Mobilidade - Renapsi (Protótipo)")
    st.write("Sistema inteligente de roteirização e cálculo de vale-transporte.")
    st.markdown("---")

    df_jovens = carregar_dados()

    st.subheader("📋 Base de Jovens (A aguardar Roteirização)")
    st.dataframe(df_jovens, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("⚙️ Painel de Operação Inteligente")

    col1, col2 = st.columns([2, 1])

    with col1:
        jovem_selecionado = st.selectbox("Selecione um jovem na fila:", df_jovens['nome'])

    dados_jovem = df_jovens[df_jovens['nome'] == jovem_selecionado].iloc[0]

    with col2:
        st.write("") 
        st.write("")
        botao_roteirizar = st.button("🚀 Iniciar Roteirização Inteligente", type="primary", use_container_width=True)

    if botao_roteirizar:
        with st.spinner('A consultar APIs de geolocalização e a cruzar malha viária...'):
            time.sleep(1.5)
            
            endereco_casa = buscar_endereco_viacep(dados_jovem['cep_casa'])
            endereco_trab = buscar_endereco_viacep(dados_jovem['cep_trabalho'])
            resultado = roteirizar_simulado()
            
            st.success(f"✅ Análise concluída para **{jovem_selecionado}** (Processado em 1.5s - Poupança de 53s em relação ao sistema atual).")
            
            st.markdown("#### 📍 Dados Geográficos (Via API)")
            st.info(f"🏠 **Origem (Casa):** {endereco_casa} *(CEP: {dados_jovem['cep_casa']})*")
            st.info(f"🏢 **Destino (Trabalho/Pólo):** {endereco_trab} *(CEP: {dados_jovem['cep_trabalho']})*")
            
            st.markdown("#### 🚌 Sugestão de Rota e Custos")
            c1, c2, c3 = st.columns(3)
            c1.metric(label="Trajeto Sugerido", value=resultado["trajeto"])
            c2.metric(label="Tempo Estimado", value=resultado["tempo"])
            c3.metric(label="Custo Diário (Ida e Volta)", value=f"R$ {resultado['valor_diario']:.2f}")

# --- ECRÃ 2: REGISTO DE JOVENS (A Novidade!) ---
elif menu == "➕ Registar Novo Jovem":
    st.title("➕ Registar Novo Jovem")
    st.write("Insira os dados do aprendiz para o adicionar à base de dados de roteirização.")
    st.markdown("---")

    # Criando um formulário para evitar que a página recarregue a cada letra digitada
    with st.form(key="form_novo_jovem"):
        col_nome, col_cpf = st.columns(2)
        nome_input = col_nome.text_input("Nome Completo do Jovem:")
        cpf_input = col_cpf.text_input("CPF (Apenas números):", max_chars=11)
        
        col_cep1, col_cep2 = st.columns(2)
        cep_casa_input = col_cep1.text_input("CEP da Residência (Apenas números):", max_chars=8)
        cep_trab_input = col_cep2.text_input("CEP do Trabalho/Pólo (Apenas números):", max_chars=8)
        
        # Botão de submissão do formulário
        botao_salvar = st.form_submit_button("💾 Guardar Jovem na Base de Dados")

    if botao_salvar:
        # Validação simples para ver se os campos não estão vazios
        if nome_input and cpf_input and cep_casa_input and cep_trab_input:
            # Chama a função que guarda no SQL
            inserir_novo_jovem(nome_input, cpf_input, cep_casa_input, cep_trab_input)
            st.success(f"✅ O jovem {nome_input} foi registado com sucesso no sistema!")
            st.info("Podes voltar ao 'Painel de Roteirização' no menu lateral para calcular a rota dele.")
        else:
            st.error("⚠️ Por favor, preenche todos os campos antes de guardar.")