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
            data_geracao TEXT,
            status TEXT DEFAULT 'Pendente',
            tratativa TEXT
        )
    ''')
    # Tenta adicionar as novas colunas caso a tabela antiga já exista
    try:
        cursor.execute("ALTER TABLE contestacoes ADD COLUMN status TEXT DEFAULT 'Pendente'")
        cursor.execute("ALTER TABLE contestacoes ADD COLUMN tratativa TEXT")
    except sqlite3.OperationalError:
        pass
        
    conexao.commit()
    conexao.close()

def resolver_contestacao(id_contestacao, tratativa):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    cursor.execute("UPDATE contestacoes SET status = 'Resolvido', tratativa = ? WHERE id = ?", (tratativa, id_contestacao))
    conexao.commit()
    conexao.close()

def resolver_contestacao(id_contestacao, tratativa):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    cursor.execute("UPDATE contestacoes SET status = 'Resolvido', tratativa = ? WHERE id = ?", (tratativa, id_contestacao))
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
st.sidebar.title("Menu de Navegacao")

menu = st.sidebar.radio("Escolha a area:", [
    "Dashboard Principal", 
    "Pesquisar Consultas", 
    "Cadastrar Novo Jovem"
])

# ==========================================
# --- TELA 0: DASHBOARD PRINCIPAL (ABA 1) ---
# ==========================================
if menu == "Dashboard Principal":
    
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
        st.button("Alterar Período", use_container_width=True)
    with col_btn2:
        st.button("Download Relatório", use_container_width=True)

    total_consultas, sla_medio = obter_dados_dashboard()
    
    # Busca os dados de contestações em tempo real
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    df_contest = pd.read_sql_query("SELECT * FROM contestacoes", conexao)
    conexao.close()
    
    # Prepara as variáveis (se a tabela for nova e estiver vazia)
    if 'status' not in df_contest.columns:
        df_contest['status'] = 'Pendente'
        
    qtd_pendentes = len(df_contest[df_contest['status'] == 'Pendente'])
    qtd_resolvidas = len(df_contest[df_contest['status'] == 'Resolvido'])
    total_contestacoes = qtd_pendentes + qtd_resolvidas

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
        st.markdown(f"**Contestações ({qtd_resolvidas} / {total_contestacoes})**")
        if total_contestacoes == 0:
            st.info("Nenhuma contestação.")
        else:
            fig_contest = px.pie(values=[qtd_resolvidas, qtd_pendentes], names=['Resolvidas', 'Pendentes'], hole=0.75)
            # Verde para resolvidas, vermelho/cinza para pendentes
            fig_contest.update_traces(textinfo='none', marker=dict(colors=['#43b596', '#e2e8f0']), hoverinfo="skip")
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
    
    # EXPANDER COM AS ABAS DE TRATATIVA
    with st.expander("Ver Detalhes das Contestações (Cards / Tabela)"):
        if df_contest.empty:
            st.info("Nenhuma contestação registrada até o momento.")
        else:
            st.markdown(f"### {total_contestacoes} contestações registradas")
            tab_pendentes, tab_resolvidas, tab_tabela = st.tabs(["Pendentes", "Resolvidas", "Tabela Geral"])
            
            with tab_pendentes:
                df_pendentes = df_contest[df_contest['status'] == 'Pendente']
                if df_pendentes.empty:
                    st.success("Tudo limpo! Nenhuma contestação pendente.")
                else:
                    for index, row in df_pendentes.iterrows():
                        st.markdown(f"""
                        <div style="background-color: #FFFFFF; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 10px; border-top: 4px solid #FF4B4B;">
                            <h4 style="margin-top: 0; color: #1E3A8A;">Consulta: {row['id']}</h4>
                            <p style="color: #666; font-size: 14px; margin-bottom: 5px;">Gerada em {row['data_geracao']} | <strong>Funcionário:</strong> {row['nome_jovem']}</p>
                            <div style="background-color: #F4F6F9; padding: 10px; border-radius: 5px; font-size: 14px; margin-bottom: 15px;">
                                <strong>Motivo da Contestação:</strong> {row['motivo']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Botões e input para resolver
                        col_tratativa, col_btn = st.columns([3, 1])
                        with col_tratativa:
                            tratativa_input = st.text_input("Qual a tratativa tomada?", key=f"input_{row['id']}")
                        with col_btn:
                            st.write("") # Espaçador para alinhar com o input
                            st.write("")
                            if st.button("Resolver", type="primary", key=f"btn_{row['id']}", use_container_width=True):
                                if tratativa_input.strip() == "":
                                    st.error("Escreva a tratativa antes de resolver.")
                                else:
                                    resolver_contestacao(row['id'], tratativa_input)
                                    st.rerun()
                        st.markdown("---")

            with tab_resolvidas:
                df_resolvidas = df_contest[df_contest['status'] == 'Resolvido']
                if df_resolvidas.empty:
                    st.info("Nenhuma contestação resolvida ainda.")
                else:
                    for index, row in df_resolvidas.iterrows():
                        st.markdown(f"""
                        <div style="background-color: #FFFFFF; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 15px; border-top: 4px solid #43b596;">
                            <h4 style="margin-top: 0; color: #1E3A8A;">Consulta: {row['id']} - RESOLVIDO</h4>
                            <p style="color: #666; font-size: 14px; margin-bottom: 5px;">Gerada em {row['data_geracao']} | <strong>Funcionário:</strong> {row['nome_jovem']}</p>
                            <p style="color: #666; font-size: 14px; margin-bottom: 5px;"><strong>Motivo:</strong> {row['motivo']}</p>
                            <div style="background-color: #d1f3e0; color: #1e8e3e; padding: 10px; border-radius: 5px; font-size: 14px;">
                                <strong>Tratativa Aplicada:</strong> {row.get('tratativa', '')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            with tab_tabela:
                df_exibicao = df_contest[['id', 'data_geracao', 'nome_jovem', 'motivo', 'status', 'tratativa']]
                df_exibicao.columns = ['ID', 'Data', 'Funcionário', 'Motivo', 'Status', 'Tratativa']
                st.dataframe(df_exibicao, use_container_width=True, hide_index=True)


# ==========================================
# --- TELA 1.5: PESQUISAR CONSULTAS ---
# ==========================================
elif menu == "Pesquisar Consultas":
# 1. Inicializa as variaveis de sessao
    if 'resultado_busca' not in st.session_state:
        st.session_state.resultado_busca = None
    if 'detalhes_abertos' not in st.session_state:
        st.session_state.detalhes_abertos = False
    if 'rota_gerada' not in st.session_state:
        st.session_state.rota_gerada = None
    if 'modo_contestacao' not in st.session_state:
        st.session_state.modo_contestacao = False

    # --- SE A CONSULTA ESTIVER ABERTA (TELA CHEIA) ---
    if st.session_state.detalhes_abertos and st.session_state.resultado_busca is not None:
        
    # Botao para voltar para a tela de pesquisa
        if st.button("<- Voltar"):
            st.session_state.detalhes_abertos = False
            st.session_state.rota_gerada = None
            st.session_state.modo_contestacao = False
            st.rerun()

        dados_jovem = st.session_state.resultado_busca.iloc[0]
        id_selecionado = dados_jovem['id']
        nome_jovem = dados_jovem['nome']
        cpf_cru = str(dados_jovem['cpf']).zfill(11)
        cep_casa = dados_jovem['cep_casa']
        cep_trab = dados_jovem['cep_trabalho']
        matricula_exib = dados_jovem.get('matricula', 'Nao informada')
        status_exib = dados_jovem.get('status_rota', 'Otimizado').upper()
        
        with st.spinner("Carregando detalhes..."):
            endereco_casa = buscar_endereco_viacep(cep_casa)
            endereco_trab = buscar_endereco_viacep(cep_trab)

        st.markdown(f"""
<div style="background-color: #FFFFFF; padding: 30px; border-radius: 8px; box-shadow: 0px 2px 6px rgba(0,0,0,0.1); margin-top: 10px;">
    <div style="display: flex; align-items: center; margin-bottom: 15px;">
        <h2 style="margin: 0; color: #5b677a; font-size: 28px;">Consulta {id_selecionado}</h2>
        <span style="background-color: #d1f3e0; color: #1e8e3e; padding: 6px 12px; border-radius: 4px; font-size: 14px; font-weight: bold; margin-left: 15px;">{status_exib}</span>
    </div>
    <h3 style="color: #64748b; font-size: 18px; margin-top: 0; margin-bottom: 30px; font-weight: normal;">RENAPSI - SAO PAULO - C-T</h3>
    <div style="display: flex; flex-wrap: wrap; justify-content: space-between;">
        <div style="flex: 1; min-width: 250px; margin-bottom: 15px; padding-right: 15px;">
            <h4 style="color: #718096; font-size: 20px; margin-bottom: 15px;">Dados funcionario</h4>
            <p style="margin: 6px 0; font-size: 16px; color: #718096;"><strong style="color: #4a5568;">CPF:</strong> {cpf_cru}</p>
            <p style="margin: 6px 0; font-size: 16px; color: #718096;"><strong style="color: #4a5568;">Matricula:</strong> {matricula_exib}</p>
            <p style="margin: 6px 0; font-size: 16px; color: #718096;"><strong style="color: #4a5568;">Nome:</strong> {nome_jovem}</p>
        </div>
        <div style="flex: 1; min-width: 250px; margin-bottom: 15px; padding-right: 15px;">
            <h4 style="color: #718096; font-size: 20px; margin-bottom: 15px;">Endereco Funcionario</h4>
            <p style="margin: 6px 0; font-size: 16px; color: #718096;"><strong style="color: #4a5568;">CEP:</strong> {cep_casa}</p>
            <p style="margin: 6px 0; font-size: 16px; color: #718096; line-height: 1.6;"><strong style="color: #4a5568;">Endereco:</strong><br>{endereco_casa}</p>
        </div>
        <div style="flex: 1; min-width: 250px; margin-bottom: 15px;">
            <h4 style="color: #718096; font-size: 20px; margin-bottom: 15px;">Local de trabalho</h4>
            <p style="margin: 6px 0; font-size: 16px; color: #718096;"><strong style="color: #4a5568;">CEP:</strong> {cep_trab}</p>
            <p style="margin: 6px 0; font-size: 16px; color: #718096; line-height: 1.6;"><strong style="color: #4a5568;">Endereco:</strong><br>{endereco_trab}</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Criando colunas para os botoes ficarem lado a lado e no tamanho parecido com o print
        col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)
        
        ja_implantado = (status_exib.upper() == "IMPLANTADO")
        
        with col_b1:
            if st.button("Roteirizar", disabled=ja_implantado, use_container_width=True):
                st.session_state.rota_gerada = roteirizar_simulado()
                st.session_state.modo_contestacao = False # Fecha a contestacao se abrir a rota
                
        with col_b2:
            if st.button("Contestacoes", use_container_width=True):
                st.session_state.modo_contestacao = True
                st.session_state.rota_gerada = None # Fecha a rota se abrir a contestacao

        st.markdown("<br>", unsafe_allow_html=True)

        # Logica: O que acontece ao clicar em Roteirizar
        if st.session_state.rota_gerada:
            rota = st.session_state.rota_gerada
            st.success("Nova sugestao de rota calculada com base nos enderecos!")
            c1, c2, c3 = st.columns(3)
            c1.metric(label="Trajeto Sugerido", value=rota["trajeto"])
            c2.metric(label="Tempo Estimado", value=rota["tempo"])
            c3.metric(label="Custo Diario", value=f"R$ {rota['valor_diario']:.2f}")

        # Logica: O que acontece ao clicar em Contestacoes
        if st.session_state.modo_contestacao:
            with st.form(key="form_nova_contestacao"):
                motivo_input = st.text_area("Descreva o problema (Ex: tarifa indevida, rota que nao faz sentido, etc):")
                submit_contestacao = st.form_submit_button("Registrar Contestacao")
                
                if submit_contestacao:
                    if motivo_input.strip() == "":
                        st.error("Por favor, descreva o motivo antes de registrar.")
                    else:
                        registrar_contestacao(nome=nome_jovem, cid_res="Sao Paulo", cid_trab="Sao Paulo", motivo=motivo_input)
                        st.success("Contestacao registrada! O Dashboard na pagina principal ja foi atualizado.")
                        st.session_state.modo_contestacao = False
                        time.sleep(2)
                        st.rerun()
    # --- SE A CONSULTA ESTIVER FECHADA (TELA DE PESQUISA NORMAL) ---
    else:
        st.title("Pesquisar Consultas")
        
        st.markdown("### Contexto da Pesquisa")
        modalidade_pesquisa = st.radio(
            "Selecione o tipo de rota que voce esta avaliando agora:",
            ["Casa x Trabalho", "Casa x Curso"],
            horizontal=True
        )
        st.info(f"Modo Ativo: Voce esta pesquisando e alterando rotas no contexto {modalidade_pesquisa}.")
        st.markdown("---")

        tab_cpf, tab_nome, tab_matricula = st.tabs(["Por CPF", "Por Nome", "Por Matricula"])

        with tab_cpf:
            st.write("Digite o CPF")
            cpf_busca = st.text_input("Apenas numeros", key="input_cpf", max_chars=11)
            if st.button("Pesquisar", type="primary", key="btn_cpf"):
                conexao = sqlite3.connect('mobilidade_renapsi.db')
                st.session_state.resultado_busca = pd.read_sql_query("SELECT * FROM jovens_rotas WHERE cpf = ?", conexao, params=(cpf_busca,))
                st.session_state.detalhes_abertos = False
                conexao.close()

        with tab_nome:
            st.write("Digite o Nome do Jovem")
            nome_busca = st.text_input("Nome completo", key="input_nome")
            if st.button("Pesquisar", type="primary", key="btn_nome"):
                conexao = sqlite3.connect('mobilidade_renapsi.db')
                st.session_state.resultado_busca = pd.read_sql_query("SELECT * FROM jovens_rotas WHERE nome LIKE ?", conexao, params=(f"%{nome_busca}%",))
                st.session_state.detalhes_abertos = False
                conexao.close()

        with tab_matricula:
            st.write("Digite o Codigo de Matricula")
            mat_busca = st.text_input("Apenas numeros", key="input_mat")
            if st.button("Pesquisar", type="primary", key="btn_mat"):
                conexao = sqlite3.connect('mobilidade_renapsi.db')
                st.session_state.resultado_busca = pd.read_sql_query("SELECT * FROM jovens_rotas WHERE matricula = ?", conexao, params=(mat_busca,))
                st.session_state.detalhes_abertos = False
                conexao.close()

        # Renderiza o card de resumo se houver resultado
        if st.session_state.resultado_busca is not None:
            if st.session_state.resultado_busca.empty:
                st.warning("Nenhum aprendiz encontrado com o dado informado.")
            else:
                dados_jovem = st.session_state.resultado_busca.iloc[0]
                id_selecionado = dados_jovem['id']
                nome_jovem = dados_jovem['nome']
                cpf_cru = str(dados_jovem['cpf']).zfill(11)
                cpf_mascarado = f"***.***.{cpf_cru[6:9]}-{cpf_cru[9:11]}"
                matricula_exib = dados_jovem.get('matricula', 'Nao informada')
                status_exib = dados_jovem.get('status_rota', 'Otimizado').upper()
                
                data_roteirizacao = dados_jovem.get('data_consulta')
                if not data_roteirizacao:
                    data_roteirizacao = "Pendente"
                data_geracao = "26/08/2025 as 00h00m"

                st.markdown(f"""
                <div style="background-color: #FFFFFF; padding: 20px; border-radius: 8px; box-shadow: 0px 2px 4px rgba(0,0,0,0.05); margin-top: 10px; margin-bottom: 15px; border-left: 4px solid #0068C9;">
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <h3 style="margin: 0; color: #5b677a; font-size: 16px;">{id_selecionado} - {nome_jovem.upper()}</h3>
                        <span style="background-color: #d1f3e0; color: #1e8e3e; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; margin-left: 10px;">{status_exib}</span>
                    </div>
                    <p style="margin: 3px 0; color: #a0aec0; font-size: 13px;">PRE-ADM</p>
                    <p style="margin: 3px 0; color: #a0aec0; font-size: 13px;">Gerada em {data_geracao}</p>
                    <p style="margin: 3px 0; color: #a0aec0; font-size: 13px;">Ultima roteirizacao em {data_roteirizacao}</p>
                    <p style="margin: 3px 0; color: #a0aec0; font-size: 13px;">CPF: {cpf_mascarado}</p>
                    <p style="margin: 3px 0; color: #a0aec0; font-size: 13px;">Matricula: {matricula_exib}</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Abrir Consulta", type="primary"):
                    st.session_state.detalhes_abertos = True
                    st.rerun()

# ==========================================
# --- TELA 3: CADASTRO DE JOVENS (COM ABAS) ---
# ==========================================
elif menu == "Cadastrar Novo Jovem":
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
            
            botao_salvar = st.form_submit_button("Salvar Jovem na Base de Dados")

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
                
                botao_salvar_massa = st.button("Importar Todos para a Base de Dados", type="primary")
                
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