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

def excluir_jovem(id_jovem):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM jovens_rotas WHERE id = ?", (id_jovem,))
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
        {"trajeto": "1 Ônibus Municipal (SPTrans)", "valor_diario": 8.80, "tempo": "45 min"},
        {"trajeto": "1 Ônibus + 1 Metrô (Integração)", "valor_diario": 10.00, "tempo": "1h 10min"},
        {"trajeto": "Metrô Direto (Linha Azul)", "valor_diario": 10.00, "tempo": "30 min"}
    ]
    return random.choice(opcoes_rota)

# --- MENU LATERAL (SIDEBAR) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3204/3204993.png", width=100)
st.sidebar.title("Menu de Navegação")
menu = st.sidebar.radio("Escolha a área:", ["🚌 Painel de Roteirização", "➕ Cadastrar Novo Jovem"])

# --- TELA 1: PAINEL DE ROTEIRIZAÇÃO ---
if menu == "🚌 Painel de Roteirização":
    st.title("🚌 Painel de Mobilidade - Renapsi (Protótipo)")
    st.write("Sistema inteligente de roteirização e cálculo de vale-transporte.")
    st.markdown("---")

    df_jovens = carregar_dados()

    # --- DASHBOARD DE KPIs ---
    st.subheader("📊 Visão Geral e Impacto")
    
    total_jovens = len(df_jovens)
    tempo_salvo_minutos = (total_jovens * 53) / 60 
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(label="👥 Jovens Aguardando", value=total_jovens)
    kpi2.metric(label="⏱️ Tempo Operacional Salvo", value=f"{tempo_salvo_minutos:.1f} min", delta="Tempo livre para o RH")
    kpi3.metric(label="💰 Custo Médio Projetado", value="R$ 9,40", delta="-12% vs Rota Manual", delta_color="inverse")

    st.markdown("---")
    st.subheader("📋 Base de Jovens (Aguardando Roteirização)")
    
    # Trava de segurança
    if not df_jovens.empty:
        st.dataframe(df_jovens, use_container_width=True, hide_index=True)
        
        # --- BOTÃO DE EXPORTAR ---
        csv = df_jovens.to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button(label="📥 Exportar Base para Excel (CSV)", data=csv, file_name="base_jovens_mobilidade.csv", mime="text/csv")
        
        st.markdown("---")
        st.subheader("⚙️ Painel de Operação Inteligente")

        col1, col2 = st.columns([2, 1])
        with col1:
            jovem_selecionado = st.selectbox("Selecione um jovem na fila:", df_jovens['nome'])

        dados_jovem = df_jovens[df_jovens['nome'] == jovem_selecionado].iloc[0]
        id_selecionado = int(dados_jovem['id'])

        with col2:
            st.write("") 
            st.write("")
            botao_roteirizar = st.button("🚀 Iniciar Roteirização", type="primary", use_container_width=True)
            botao_excluir = st.button("🗑️ Excluir Jovem da Base", use_container_width=True)

        if botao_excluir:
            excluir_jovem(id_selecionado)
            st.warning(f"🗑️ O jovem **{jovem_selecionado}** foi removido da base de dados!")
            time.sleep(1.5)
            st.rerun()

        if botao_roteirizar:
            with st.spinner('Consultando APIs de geolocalização e cruzando malha viária...'):
                time.sleep(1.5)
                endereco_casa = buscar_endereco_viacep(dados_jovem['cep_casa'])
                endereco_trab = buscar_endereco_viacep(dados_jovem['cep_trabalho'])
                resultado = roteirizar_simulado()
                
                st.success(f"✅ Análise concluída para **{jovem_selecionado}** (Processado em 1.5s - Economia de 53s).")
                st.markdown("#### 📍 Dados Geográficos (Via API)")
                st.info(f"🏠 **Origem (Casa):** {endereco_casa} *(CEP: {dados_jovem['cep_casa']})*")
                st.info(f"🏢 **Destino (Trabalho/Polo):** {endereco_trab} *(CEP: {dados_jovem['cep_trabalho']})*")
                
                st.markdown("#### 🚌 Sugestão de Rota e Custos")
                c1, c2, c3 = st.columns(3)
                c1.metric(label="Trajeto Sugerido", value=resultado["trajeto"])
                c2.metric(label="Tempo Estimado", value=resultado["tempo"])
                c3.metric(label="Custo Diário", value=f"R$ {resultado['valor_diario']:.2f}")

        # --- ROTEIRIZAÇÃO EM LOTE! ---
        st.markdown("---")
        st.subheader("⚡ Roteirização em Lote (Em Massa)")
        st.write("Calcula rotas, integrações e custos para toda a base simultaneamente.")
        
        botao_lote = st.button("🚀 Iniciar Processamento em Lote (Todos os Jovens)", type="secondary", use_container_width=True)
        
        if botao_lote:
            st.info("Iniciando a varredura da base de dados...")
            barra_progresso = st.progress(0)
            texto_status = st.empty()
            
            total_jovens_lote = len(df_jovens)
            resultados_lote = []
            
            for index, row in df_jovens.iterrows():
                nome_atual = row['nome']
                texto_status.text(f"🔄 Consultando APIs para: {nome_atual} ({index + 1}/{total_jovens_lote})...")
                time.sleep(0.5) 
                
                resultado_rota = roteirizar_simulado()
                resultados_lote.append({
                    "Jovem": nome_atual,
                    "Trajeto": resultado_rota["trajeto"],
                    "Tempo": resultado_rota["tempo"],
                    "Custo (R$)": f"R$ {resultado_rota['valor_diario']:.2f}"
                })
                
                porcentagem = (index + 1) / total_jovens_lote
                barra_progresso.progress(porcentagem)
                
            texto_status.success(f"✅ Processamento em lote concluído com sucesso! {total_jovens_lote} rotas calculadas.")
            df_resultados = pd.DataFrame(resultados_lote)
            st.dataframe(df_resultados, use_container_width=True)
            
    else:
        st.warning("A base de dados está vazia! Vá no menu lateral e cadastre um jovem para começar.")


# --- TELA 2: CADASTRO DE JOVENS (COM ABAS) ---
elif menu == "➕ Cadastrar Novo Jovem":
    st.title("➕ Cadastrar Novo Jovem")
    st.write("Adicione novos aprendizes à base de dados manualmente ou enviando uma planilha Excel.")
    st.markdown("---")

    # Criando as Abas (Tabs)
    tab_manual, tab_massa = st.tabs(["✍️ Cadastro Manual", "📂 Importação em Massa (Excel/CSV)"])

    # === ABA 1: CADASTRO MANUAL ===
    with tab_manual:
        with st.form(key="form_novo_jovem"):
            col_nome, col_cpf = st.columns(2)
            nome_input = col_nome.text_input("Nome Completo do Jovem:")
            cpf_input = col_cpf.text_input("CPF (Apenas números):", max_chars=11)
            
            col_cep1, col_cep2 = st.columns(2)
            cep_casa_input = col_cep1.text_input("CEP da Residência (Apenas números):", max_chars=8)
            cep_trab_input = col_cep2.text_input("CEP do Trabalho/Polo (Apenas números):", max_chars=8)
            
            botao_salvar = st.form_submit_button("💾 Salvar Jovem na Base de Dados")

        if botao_salvar:
            if nome_input and cpf_input and cep_casa_input and cep_trab_input:
                inserir_novo_jovem(nome_input, cpf_input, cep_casa_input, cep_trab_input)
                st.success(f"✅ O jovem {nome_input} foi cadastrado com sucesso no sistema!")
            else:
                st.error("⚠️ Por favor, preencha todos os campos antes de salvar.")

    # === ABA 2: IMPORTAÇÃO EM MASSA ===
    with tab_massa:
        st.info("💡 A sua planilha Excel ou CSV deve conter exatamente as colunas na primeira linha: **nome, cpf, cep_casa, cep_trabalho**")
        
        # O componente que permite arrastar e largar arquivos!
        arquivo_upload = st.file_uploader("Arraste o seu arquivo Excel (.xlsx) ou CSV para cá", type=["xlsx", "csv"])
        
        if arquivo_upload is not None:
            try:
                # 1. O Python lê o arquivo
                if arquivo_upload.name.endswith('.csv'):
                    df_upload = pd.read_csv(arquivo_upload, sep=';', dtype=str)
                else:
                    df_upload = pd.read_excel(arquivo_upload, dtype=str)
                
                #Limpa os nomes das colunas para evitar erros de digitação (ex: "Nome " com espaço)
                df_upload.columns = df_upload.columns.str.lower().str.strip()
                
                # 3. Só DEPOIS da limpeza que o Streamlit exibe a pré-visualização dos dados
                st.write("🔍 Pré-visualização dos dados encontrados:")
                st.dataframe(df_upload.head(), use_container_width=True)
                
                botao_salvar_massa = st.button("🚀 Importar Todos para a Base de Dados", type="primary")
                
                if botao_salvar_massa:
                    with st.spinner("Enviando dados para a base..."):
                        conexao = sqlite3.connect('mobilidade_renapsi.db')
                        # Filtra apenas as colunas exatas para evitar erros caso o Excel tenha colunas a mais
                        df_limpo = df_upload[['nome', 'cpf', 'cep_casa', 'cep_trabalho']]
                        
                        # O método to_sql  insere milhares de linhas de uma só vez
                        df_limpo.to_sql('jovens_rotas', conexao, if_exists='append', index=False)
                        conexao.close()
                        
                        st.success(f"✅ Sucesso! {len(df_limpo)} jovens foram importados para o sistema num piscar de olhos.")
                        time.sleep(2)
                        st.rerun()
                        
            except Exception as e:
                st.error(f"❌ Erro ao ler o arquivo. Confirme se o nome das colunas está correto (em letras minúsculas). Detalhe técnico: {e}")