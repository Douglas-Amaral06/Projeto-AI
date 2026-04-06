import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
import random
import datetime
import time

# Configuração da página
st.set_page_config(page_title="Nova Capta - Piloto", page_icon="🚌", layout="wide")

#inserir CSS
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #0068C9;
    }
    
    h1, h2, h3 {
        color: #1E3A8A;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE BANCO DE DADOS E API ---

def carregar_dados():
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    df = pd.read_sql_query("SELECT * FROM jovens_rotas", conexao)
    conexao.close()
    return df

def inserir_novo_jovem(nome, cpf, cep_casa, cep_trabalho):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    # Gera uma matrícula aleatória de 6 dígitos
    matricula = str(random.randint(100000, 999999))
    status_rota = "Otimizado" # Padrão exigido
    
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota))
    conexao.commit()
    conexao.close()

def cpf_ja_existe(cpf):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    cursor.execute("SELECT COUNT(*) FROM jovens_rotas WHERE cpf = ?", (cpf,))
    resultado = cursor.fetchone()[0]
    conexao.close()
    return resultado > 0

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

# Atualização geral do banco de dados (Cria as colunas de Status e Matrícula caso não existam)
def atualizar_banco_geral():
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    colunas_novas = [
        ("data_consulta", "TEXT"),
        ("sla_segundos", "REAL"),
        ("matricula", "TEXT"),
        ("status_rota", "TEXT DEFAULT 'Otimizado'")
    ]
    
    for coluna, tipo in colunas_novas:
        try:
            cursor.execute(f"ALTER TABLE jovens_rotas ADD COLUMN {coluna} {tipo}")
        except sqlite3.OperationalError:
            pass
            
    # Trava de segurança: Se algum jovem antigo estiver com o status vazio, ele vira 'Otimizado'
    cursor.execute("UPDATE jovens_rotas SET status_rota = 'Otimizado' WHERE status_rota IS NULL")
    
    conexao.commit()
    conexao.close()

def obter_dados_dashboard():
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    mes_ano_atual = datetime.datetime.now().strftime("%Y-%m")
    
    cursor.execute("""
        SELECT COUNT(DISTINCT id), AVG(sla_segundos) 
        FROM jovens_rotas 
        WHERE data_consulta LIKE ?
    """, (f"{mes_ano_atual}%",))
    
    resultado = cursor.fetchone()
    conexao.close()
    
    total_consultas = resultado[0] if resultado[0] else 0
    sla_medio = resultado[1] if resultado[1] else 0.0
    return total_consultas, sla_medio

def atualizar_banco_para_contestacoes():
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contestacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_jovem TEXT,
            cidade_residencia TEXT,
            cidade_trabalho TEXT,
            motivo TEXT,
            data_geracao TEXT
        )
    ''')
    conexao.commit()
    conexao.close()

def registrar_contestacao(nome, cid_res, cid_trab, motivo):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    data_atual = datetime.datetime.now().strftime("%d/%m/%Y às %Hh%Mm")
    cursor.execute('''
        INSERT INTO contestacoes (nome_jovem, cidade_residencia, cidade_trabalho, motivo, data_geracao)
        VALUES (?, ?, ?, ?, ?)
    ''', (nome, cid_res, cid_trab, motivo, data_atual))
    conexao.commit()
    conexao.close()

# Dispara as atualizações do banco assim que o sistema roda
atualizar_banco_geral()
atualizar_banco_para_contestacoes()


# --- MENU LATERAL (SIDEBAR) ---
st.sidebar.image("logo_renapsi.png", use_container_width=True)
st.sidebar.title("Menu de Navegação")

menu = st.sidebar.radio("Escolha a área:", [
    "📊 Dashboard Principal", 
    "🔍 Pesquisar Consultas", 
    "🚌 Painel de Roteirização", 
    "➕ Cadastrar Novo Jovem"
])

# ==========================================
# --- TELA 0: DASHBOARD PRINCIPAL (ABA 1) ---
# ==========================================
if menu == "📊 Dashboard Principal":
    
    tipo_rota = st.radio(
        "Selecione a modalidade de análise:",
        ["Casa x Trabalho", "Casa x Curso", "Gestão de Base"],
        horizontal=True
    )
    st.write("São as roteirizações realizadas para os aprendizes selecionados.")
    st.markdown("<br>", unsafe_allow_html=True) 
    
    meses_pt = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_atual = meses_pt[datetime.datetime.now().month - 1]
    ano_atual = datetime.datetime.now().year
    
    col_titulo, col_btn1, col_btn2 = st.columns([2, 1, 1])
    with col_titulo:
        st.markdown(f"<h2 style='color: #1E3A8A; margin-top: 0px;'>Dashboard {mes_atual} de {ano_atual}</h2>", unsafe_allow_html=True)
    with col_btn1:
        st.button("📅 Alterar Período", use_container_width=True)
    with col_btn2:
        st.button("📥 Download Relatório", use_container_width=True)

    total_consultas, sla_medio = obter_dados_dashboard()

    col_kpi1, col_kpi2 = st.columns(2)
    with col_kpi1:
        st.metric(label="Total de Consultas", value=f"{total_consultas}", delta="Consultas únicas no mês", delta_color="off")
    with col_kpi2:
        st.metric(label="SLA Médio - Tempo de Resposta", value=f"{sla_medio:.2f}", delta="Segundos", delta_color="off")
        
    st.markdown("<br>", unsafe_allow_html=True)

    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
        
    with col_g1:
        st.markdown("**Implantações (0 / 1)**")
        st.info("📦 Não foi realizada nenhuma implantação no período selecionado.")
            
    with col_g2:
        st.markdown("**Contestações (2 / 1)**")
        fig_contest = px.pie(values=[2, 1], names=['Aprovadas', 'Contestadas'], hole=0.75)
        fig_contest.update_traces(textinfo='none', marker=dict(colors=['#43b596', '#FFFFFF']), hoverinfo="skip")
        fig_contest.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=180, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_contest, use_container_width=True, key="graf_contest")

    with col_g3:
        st.markdown("**Consultas por Local de Trabalho**")
        fig_local = px.pie(values=[10, 0], names=['SP', 'Outros'], hole=0.75)
        fig_local.update_traces(textinfo='none', marker=dict(colors=['#2a4b5d', '#FFFFFF']), hoverinfo="skip")
        fig_local.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=180, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_local, use_container_width=True, key="graf_local")

    with col_g4:
        st.markdown("**Consultas por UF**")
        fig_uf = px.pie(values=[10, 0], names=['SP', 'Outros'], hole=0.75)
        fig_uf.update_traces(textinfo='none', marker=dict(colors=['#2a4b5d', '#FFFFFF']), hoverinfo="skip")
        fig_uf.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=180, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_uf, use_container_width=True, key="graf_uf")

    st.markdown("---")
    with st.expander("🔍 Ver Detalhes das Contestações (Cards / Tabela)"):
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        df_contestacoes = pd.read_sql_query("SELECT * FROM contestacoes", conexao)
        conexao.close()
        
        if df_contestacoes.empty:
            st.info("Nenhuma contestação registrada até o momento.")
        else:
            st.markdown(f"### {len(df_contestacoes)} contestações")
            tab_cards, tab_tabela = st.tabs(["🗂️ Cards", "📊 Tabela"])
            
            with tab_cards:
                cols = st.columns(2)
                for index, row in df_contestacoes.iterrows():
                    col_atual = cols[index % 2]
                    with col_atual:
                        st.markdown(f"""
                        <div style="background-color: #FFFFFF; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 15px; border-top: 4px solid #0068C9;">
                            <h4 style="margin-top: 0; color: #1E3A8A;">Consulta: {row['id']}</h4>
                            <p style="color: #666; font-size: 14px; margin-bottom: 5px;">Gerada em {row['data_geracao']}</p>
                            <p style="color: #888; font-size: 14px; margin-bottom: 5px;">{row['cidade_residencia']} ⟷ {row['cidade_trabalho']}</p>
                            <p style="color: #333; font-weight: bold; margin-bottom: 10px;">Funcionário: {row['nome_jovem']}</p>
                            <div style="background-color: #F4F6F9; padding: 10px; border-radius: 5px; font-size: 14px;">
                                <strong>Motivo:</strong> {row['motivo']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            with tab_tabela:
                df_exibicao = df_contestacoes[['id', 'cidade_residencia', 'cidade_trabalho', 'data_geracao', 'nome_jovem', 'motivo']]
                df_exibicao.columns = ['Consulta', 'Cidade Residência', 'Cidade Trabalho', 'Data Geração', 'Funcionário', 'Motivo']
                st.dataframe(df_exibicao, use_container_width=True, hide_index=True)


# ==========================================
# --- TELA 1.5: PESQUISAR CONSULTAS ---
# ==========================================
elif menu == "🔍 Pesquisar Consultas":
    st.title("🔍 Pesquisar Consultas")
    
    # 1. SEPARAÇÃO CLARA: Casa x Curso vs Casa x Trabalho
    st.markdown("### Contexto da Pesquisa")
    modalidade_pesquisa = st.radio(
        "Selecione o tipo de rota que você está avaliando agora:",
        ["Casa x Trabalho", "Casa x Curso"],
        horizontal=True
    )
    st.info(f"📍 **Modo Ativo:** Você está pesquisando e alterando rotas no contexto **{modalidade_pesquisa}**.")
    st.markdown("---")

    tab_cpf, tab_nome, tab_matricula = st.tabs(["Por CPF", "Por Nome", "Por Matrícula"])

    def renderizar_resultado_busca(df_resultado):
        if df_resultado.empty:
            st.warning("⚠️ Nenhum aprendiz encontrado com o dado informado.")
        else:
            dados_jovem = df_resultado.iloc[0]
            id_selecionado = dados_jovem['id']
            nome_jovem = dados_jovem['nome']
            
            # Puxando os novos dados do banco
            matricula_exib = dados_jovem.get('matricula', 'Não Gerada')
            status_exib = dados_jovem.get('status_rota', 'Otimizado')

            st.success(f"✅ Jovem encontrado: **{nome_jovem}** | Matrícula: {matricula_exib} | Status: **{status_exib}**")
            
            with st.spinner("Carregando rota atual..."):
                time.sleep(1) 
                endereco_casa = buscar_endereco_viacep(dados_jovem['cep_casa'])
                endereco_trab = buscar_endereco_viacep(dados_jovem['cep_trabalho'])
                resultado = roteirizar_simulado()

                st.markdown("#### 📍 Dados Geográficos (Via API)")
                st.info(f"🏠 **Origem (Casa):** {endereco_casa} *(CEP: {dados_jovem['cep_casa']})*")
                st.info(f"🏢 **Destino ({modalidade_pesquisa}):** {endereco_trab} *(CEP: {dados_jovem['cep_trabalho']})*")
                
                st.markdown("#### 🚌 Trajeto e Custos Atuais")
                c1, c2, c3 = st.columns(3)
                c1.metric(label="Trajeto", value=resultado["trajeto"])
                c2.metric(label="Tempo Estimado", value=resultado["tempo"])
                c3.metric(label="Custo Diário", value=f"R$ {resultado['valor_diario']:.2f}")

                st.markdown("---")
                st.markdown("#### ⚠️ Ações Pós-Consulta (Contestar)")
                with st.form(key=f"form_contest_busca_{id_selecionado}"):
                    motivo_input = st.text_area("A rota está incorreta? Informe o motivo da contestação:")
                    btn_enviar_contestacao = st.form_submit_button("Registrar Contestação")
                    
                    if btn_enviar_contestacao:
                        if motivo_input == "":
                            st.error("Por favor, descreva o motivo da contestação.")
                        else:
                            registrar_contestacao(nome_jovem=nome_jovem, cid_res="São Paulo", cid_trab="São Paulo", motivo=motivo_input)
                            st.success("✅ Contestação registrada com sucesso! Já está visível no Dashboard Principal.")

    with tab_cpf:
        st.write("Digite o CPF")
        cpf_busca = st.text_input("Apenas números", key="input_cpf", max_chars=11)
        if st.button("Pesquisar", type="primary", key="btn_cpf"):
            conexao = sqlite3.connect('mobilidade_renapsi.db')
            df_busca = pd.read_sql_query("SELECT * FROM jovens_rotas WHERE cpf = ?", conexao, params=(cpf_busca,))
            conexao.close()
            renderizar_resultado_busca(df_busca)

    with tab_nome:
        st.write("Digite o Nome do Jovem")
        nome_busca = st.text_input("Nome completo", key="input_nome")
        if st.button("Pesquisar", type="primary", key="btn_nome"):
            conexao = sqlite3.connect('mobilidade_renapsi.db')
            df_busca = pd.read_sql_query("SELECT * FROM jovens_rotas WHERE nome LIKE ?", conexao, params=(f"%{nome_busca}%",))
            conexao.close()
            renderizar_resultado_busca(df_busca)

    with tab_matricula:
        st.write("Digite o Código de Matrícula")
        mat_busca = st.text_input("Apenas números (Ex: 123456)", key="input_mat")
        if st.button("Pesquisar", type="primary", key="btn_mat"):
            conexao = sqlite3.connect('mobilidade_renapsi.db')
            df_busca = pd.read_sql_query("SELECT * FROM jovens_rotas WHERE matricula = ?", conexao, params=(mat_busca,))
            conexao.close()
            renderizar_resultado_busca(df_busca)


# ==========================================
# --- TELA 2: PAINEL DE ROTEIRIZAÇÃO ---
# ==========================================
elif menu == "🚌 Painel de Roteirização":
    st.title("🚌 Painel de Mobilidade - Renapsi (Protótipo)")
    st.write("Sistema inteligente de roteirização e cálculo de vale-transporte.")
    st.markdown("---")

    df_jovens = carregar_dados()

    st.subheader("📊 Visão Geral e Impacto")
    total_jovens = len(df_jovens)
    tempo_salvo_minutos = (total_jovens * 53) / 60 
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(label="👥 Jovens Aguardando", value=total_jovens)
    kpi2.metric(label="⏱️ Tempo Operacional Salvo", value=f"{tempo_salvo_minutos:.1f} min", delta="Tempo livre para o RH")
    kpi3.metric(label="💰 Custo Médio Projetado", value="R$ 9,40", delta="-12% vs Rota Manual", delta_color="inverse")

    st.markdown("---")
    st.subheader("📈 Analise da mobilidade (Visão Estratégica.) ")

    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        dados_modais = pd.DataFrame({
            "Modal": ["Só Ônibus", "Integração (Ônibus + Metrô)", "Só Metrô"],
            "Quantidade": [int(total_jovens * 0.5), int(total_jovens * 0.3), int(total_jovens * 0.2)]
        })
        fig_pizza = px.pie(dados_modais, values = "Quantidade", names="Modal", title="Distribuição de Modais", hole=0.4)
        st.plotly_chart(fig_pizza, use_container_width=True)

        with col_graf2:
            dados_polos = pd.DataFrame({
                "Polo": ["Centro", "Zona Leste", "Zona Sul", "Zona Norte", "Zona Oeste"],
                "Custo Médio (R$)": [8.80, 11.50, 10.00, 9.40, 10.50]
            })
            fig_barras = px.bar(dados_polos, x="Polo", y="Custo Médio (R$)", title="Custo Médio por Região")
            st.plotly_chart(fig_barras, use_container_width=True)

    st.markdown("---")
    st.subheader("🗺️ Mapa de Calor: Origem e Destino")
    st.info("Mapa de calor simulado com base em dados fictícios para ilustrar a concentração de jovens por região.")
    
    dados_mapa = pd.DataFrame({
        "lat":[-23.5505, -23.5824, -23.5201, -23.6123, -23.5412],
         "lon":[-46.6333, -46.6417, -46.6000, -46.7000, -46.6200],
         "nome": ["Centro", "Polo Faria Lima", "Zona Norte", "Zona Sul", "Residência"],
         "tipo": ["Trabalho", "Trabalho", "Casa", "Casa", "Casa"]
    })

    fig_mapa = px.scatter_mapbox(
        dados_mapa, lat="lat", lon="lon", hover_name="nome", color="tipo", 
        color_discrete_sequence=["#FF4B4B", "#0068C9"], zoom=10, height=400
    )
    fig_mapa.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_mapa, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Base de Jovens (Aguardando Roteirização)")
    
    if not df_jovens.empty:
        st.dataframe(df_jovens, use_container_width=True, hide_index=True)
        
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
            inicio_cronometro = time.time()
            
            with st.spinner('Consultando APIs de geolocalização e cruzando malha viária...'):
                time.sleep(1.5)
                endereco_casa = buscar_endereco_viacep(dados_jovem['cep_casa'])
                endereco_trab = buscar_endereco_viacep(dados_jovem['cep_trabalho'])
                resultado = roteirizar_simulado()
                
                fim_cronometro = time.time()
                tempo_gasto = fim_cronometro - inicio_cronometro
                data_atual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                conexao = sqlite3.connect('mobilidade_renapsi.db')
                cursor = conexao.cursor()
                cursor.execute("""
                    UPDATE jovens_rotas 
                    SET data_consulta = ?, sla_segundos = ? 
                    WHERE id = ?
                """, (data_atual, tempo_gasto, id_selecionado))
                conexao.commit()
                conexao.close()
                
                st.success(f"✅ Análise concluída para **{jovem_selecionado}** (Processado em {tempo_gasto:.2f}s - Economia de 53s).")
                st.markdown("#### 📍 Dados Geográficos (Via API)")
                st.info(f"🏠 **Origem (Casa):** {endereco_casa} *(CEP: {dados_jovem['cep_casa']})*")
                st.info(f"🏢 **Destino (Trabalho/Polo):** {endereco_trab} *(CEP: {dados_jovem['cep_trabalho']})*")
                
                st.markdown("#### 🚌 Sugestão de Rota e Custos")
                c1, c2, c3 = st.columns(3)
                c1.metric(label="Trajeto Sugerido", value=resultado["trajeto"])
                c2.metric(label="Tempo Estimado", value=resultado["tempo"])
                c3.metric(label="Custo Diário", value=f"R$ {resultado['valor_diario']:.2f}")

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

# ==========================================
# --- TELA 3: CADASTRO DE JOVENS (COM ABAS) ---
# ==========================================
elif menu == "➕ Cadastrar Novo Jovem":
    st.title("➕ Cadastrar Novo Jovem")
    st.write("Adicione novos aprendizes à base de dados manualmente ou enviando uma planilha Excel.")
    st.markdown("---")

    tab_manual, tab_massa = st.tabs(["✍️ Cadastro Manual", "📂 Importação em Massa (Excel/CSV)"])

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
            if not (nome_input and cpf_input and cep_casa_input and cep_trab_input):
                st.error("⚠️ Por favor, preencha todos os campos antes de salvar.")
            elif cpf_ja_existe(cpf_input):
                st.error(f"❌ Operação bloqueada: O CPF {cpf_input} já está cadastrado para outro jovem no sistema!")
            else:
                with st.spinner("Validando CEPs nos Correios..."):
                    validacao_casa = buscar_endereco_viacep(cep_casa_input)
                    validacao_trab = buscar_endereco_viacep(cep_trab_input)
                    
                    if "inválido" in validacao_casa or "inválido" in validacao_trab:
                        st.error("❌ Operação bloqueada: Um dos CEPs informados é inválido ou não existe no mapa.")
                        st.info(f"Retorno Casa: {validacao_casa} | Retorno Trabalho: {validacao_trab}")
                    else:
                        inserir_novo_jovem(nome_input, cpf_input, cep_casa_input, cep_trab_input)
                        st.success(f"✅ Sucesso! O jovem {nome_input} foi cadastrado com Status 'Otimizado' e os CEPs foram validados.")

    with tab_massa:
        st.info("💡 A sua planilha Excel ou CSV deve conter exatamente as colunas na primeira linha: **nome, cpf, cep_casa, cep_trabalho**")
        arquivo_upload = st.file_uploader("Arraste o seu arquivo Excel (.xlsx) ou CSV para cá", type=["xlsx", "csv"])
        
        if arquivo_upload is not None:
            try:
                if arquivo_upload.name.endswith('.csv'):
                    df_upload = pd.read_csv(arquivo_upload, sep=';', dtype=str)
                else:
                    df_upload = pd.read_excel(arquivo_upload, dtype=str)
                
                df_upload.columns = df_upload.columns.str.lower().str.strip()
                
                # Gera matrículas aleatórias para a importação em massa e seta o Status padrão
                df_upload['matricula'] = [str(random.randint(100000, 999999)) for _ in range(len(df_upload))]
                df_upload['status_rota'] = "Otimizado"
                
                st.write("🔍 Pré-visualização dos dados encontrados:")
                st.dataframe(df_upload.head(), use_container_width=True)
                
                botao_salvar_massa = st.button("🚀 Importar Todos para a Base de Dados", type="primary")
                
                if botao_salvar_massa:
                    with st.spinner("Enviando dados para a base..."):
                        conexao = sqlite3.connect('mobilidade_renapsi.db')
                        df_limpo = df_upload[['nome', 'cpf', 'cep_casa', 'cep_trabalho', 'matricula', 'status_rota']]
                        
                        df_limpo.to_sql('jovens_rotas', conexao, if_exists='append', index=False)
                        conexao.close()
                        
                        st.success(f"✅ Sucesso! {len(df_limpo)} jovens foram importados para o sistema num piscar de olhos.")
                        time.sleep(2)
                        st.rerun()
                        
            except Exception as e:
                st.error(f"❌ Erro ao ler o arquivo. Confirme se o nome das colunas está correto (em letras minúsculas). Detalhe técnico: {e}")