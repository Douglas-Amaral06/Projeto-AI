import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
import random
import datetime
import time
import folium
from streamlit_folium import st_folium

# Configuração da página
st.set_page_config(page_title="Nova Capta - Piloto", page_icon="🚌", layout="wide")

# Inserir CSS
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

def inserir_novo_jovem(nome, cpf, cep_casa, cep_trabalho, matricula):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    status_rota = "Otimizado"
    
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
    cep_limpo = ''.join(filter(str.isdigit, str(cep)))
    if len(cep_limpo) != 8:
        return {"rua": "CEP Inválido", "bairro": "", "cidade_uf": "", "completo": "CEP Inválido"}
        
    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
    try:
        resposta = requests.get(url).json()
        if "erro" not in resposta:
            return {
                "rua": resposta.get('logradouro', 'N/A'),
                "bairro": resposta.get('bairro', 'N/A'),
                "cidade_uf": f"{resposta.get('localidade', 'N/A')} - {resposta.get('uf', 'N/A')}",
                "completo": f"{resposta.get('logradouro')}, {resposta.get('bairro')} - {resposta.get('localidade')}/{resposta.get('uf')}"
            }
    except Exception:
        pass
    return {"rua": "Endereço não encontrado", "bairro": "", "cidade_uf": "", "completo": "Não encontrado"}

def roteirizar_simulado():
    opcoes_rota = [
        {"trajeto": "1 Ônibus Municipal (SPTrans)", "valor_diario": 8.80, "tempo": "45 min"},
        {"trajeto": "1 Ônibus + 1 Metrô (Integração)", "valor_diario": 10.00, "tempo": "1h 10min"},
        {"trajeto": "Metrô Direto (Linha Azul)", "valor_diario": 10.00, "tempo": "30 min"}
    ]
    return random.choice(opcoes_rota)

def atualizar_banco_geral():
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    colunas_novas = [
        ("data_consulta", "TEXT"),
        ("sla_segundos", "REAL"),
        ("matricula", "TEXT"),
        ("status_rota", "TEXT DEFAULT 'Otimizado'"),
        ("email", "TEXT"),
        ("celular", "TEXT"),
        ("numero_casa", "TEXT"),
        ("coordenadas", "TEXT")
    ]
    
    for coluna, tipo in colunas_novas:
        try:
            cursor.execute(f"ALTER TABLE jovens_rotas ADD COLUMN {coluna} {tipo}")
        except sqlite3.OperationalError:
            pass
            
    cursor.execute("UPDATE jovens_rotas SET status_rota = 'Otimizado' WHERE status_rota IS NULL")
    
    conexao.commit()
    conexao.close()

def atualizar_dados_funcionario(id_jovem, matricula, email, celular, cep, numero, coordenadas):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    cursor.execute('''
        UPDATE jovens_rotas 
        SET matricula = ?, email = ?, celular = ?, cep_casa = ?, numero_casa = ?, coordenadas = ?
        WHERE id = ?
    ''', (matricula, email, celular, cep, numero, coordenadas, id_jovem))
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

def extrair_coordenadas(coord_str, default_lat, default_lon):
    if not coord_str:
        return default_lat, default_lon
    try:
        parts = coord_str.replace(" ", "").split(",")
        if len(parts) == 2:
            return float(parts[0]), float(parts[1])
    except:
        pass
    return default_lat, default_lon

atualizar_banco_geral()
atualizar_banco_para_contestacoes()

# --- MENU LATERAL (SIDEBAR) ---
st.sidebar.image("logo_renapsi.png", use_container_width=True)
st.sidebar.title("Menu de Navegação")

menu = st.sidebar.radio("Escolha a área:", [
    "Dashboard Principal", 
    "Pesquisar Consultas", 
    "Cadastrar Novo Jovem"
])

# ==========================================
# --- TELA 0: DASHBOARD PRINCIPAL ---
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
    
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    df_contest = pd.read_sql_query("SELECT * FROM contestacoes", conexao)
    conexao.close()
    
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
    
    with st.expander("Ver Detalhes das Contestações (Cards / Tabela)"):
        if df_contest.empty:
            st.info("Nenhuma contestação registada até ao momento.")
        else:
            st.markdown(f"### {total_contestacoes} contestações registadas")
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
                            <p style="color: #666; font-size: 14px; margin-bottom: 5px;">Gerada a {row['data_geracao']} | <strong>Funcionário:</strong> {row['nome_jovem']}</p>
                            <div style="background-color: #F4F6F9; padding: 10px; border-radius: 5px; font-size: 14px; margin-bottom: 15px;">
                                <strong>Motivo da Contestação:</strong> {row['motivo']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_tratativa, col_btn = st.columns([3, 1])
                        with col_tratativa:
                            tratativa_input = st.text_input("Qual a tratativa aplicada?", key=f"input_{row['id']}")
                        with col_btn:
                            st.write("") 
                            st.write("")
                            if st.button("Resolver", type="primary", key=f"btn_{row['id']}", use_container_width=True):
                                if tratativa_input.strip() == "":
                                    st.error("Escreve a tratativa antes de resolver.")
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
                            <p style="color: #666; font-size: 14px; margin-bottom: 5px;">Gerada a {row['data_geracao']} | <strong>Funcionário:</strong> {row['nome_jovem']}</p>
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
    if 'resultado_busca' not in st.session_state:
        st.session_state.resultado_busca = None
    if 'detalhes_abertos' not in st.session_state:
        st.session_state.detalhes_abertos = False
    if 'rota_gerada' not in st.session_state:
        st.session_state.rota_gerada = None
    if 'modo_contestacao' not in st.session_state:
        st.session_state.modo_contestacao = False
    if 'modo_edicao' not in st.session_state:
        st.session_state.modo_edicao = False
    if 'mostrar_modal_email' not in st.session_state:
        st.session_state.mostrar_modal_email = False

    if st.session_state.detalhes_abertos and st.session_state.resultado_busca is not None:
        col_voltar, col_vazia = st.columns([1, 10])
        with col_voltar:
            if st.button("<- Voltar"):
                st.session_state.detalhes_abertos = False
                st.session_state.rota_gerada = None
                st.session_state.modo_contestacao = False
                st.session_state.modo_edicao = False
                st.session_state.mostrar_modal_email = False
                st.rerun()

        dados_jovem = st.session_state.resultado_busca.iloc[0]
        id_selecionado = dados_jovem['id']
        nome_jovem = dados_jovem['nome']
        cpf_cru = str(dados_jovem['cpf']).zfill(11)
        cep_casa = dados_jovem['cep_casa']
        cep_trab = dados_jovem['cep_trabalho']
        matricula_exib = dados_jovem.get('matricula', 'Não informada')
        status_exib = dados_jovem.get('status_rota', 'Otimizado').upper()
        
        email_jovem = dados_jovem.get('email', '')
        celular_jovem = dados_jovem.get('celular', '')
        numero_casa = dados_jovem.get('numero_casa', '')
        coordenadas_casa = dados_jovem.get('coordenadas', '')

        if st.session_state.modo_edicao:
            st.markdown("### Editar dados da consulta")
            st.markdown("---")
            
            col_edit1, col_edit2 = st.columns(2)
            
            with col_edit1:
                st.markdown("<h4 style='color:#5b677a;'>👤 Dados funcionário</h4>", unsafe_allow_html=True)
                mat_input = st.text_input("Matrícula do colaborador", value=matricula_exib if matricula_exib != 'Não informada' else '')
                nome_input = st.text_input("Nome", value=nome_jovem, disabled=True)
                email_input = st.text_input("E-mail", value=email_jovem if email_jovem else '')
                celular_input = st.text_input("Celular do colaborador", value=celular_jovem if celular_jovem else '')
                
            with col_edit2:
                st.markdown("<h4 style='color:#5b677a;'>🏠 Endereço funcionário</h4>", unsafe_allow_html=True)
                cep_input = st.text_input("CEP", value=cep_casa)
                
                c_rua, c_num = st.columns([3, 1])
                rua_input = c_rua.text_input("Logradouro/Bairro/Cidade", value=buscar_endereco_viacep(cep_input).get('completo', ''), disabled=True)
                num_input = c_num.text_input("Número", value=numero_casa if numero_casa else '')
                
                if st.button("Buscar Coordenada Correspondente", use_container_width=True):
                    st.session_state.coord_temp = f"-23.{random.randint(10000, 99999)}, -46.{random.randint(10000, 99999)}"
                    st.rerun()
                    
                coord_atual = st.session_state.get('coord_temp', coordenadas_casa)
                coord_input = st.text_input("Coordenadas", value=coord_atual if coord_atual else '')
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_btn_fechar, col_btn_confirmar = st.columns([1, 1])
            
            with col_btn_fechar:
                if st.button("Fechar", use_container_width=True):
                    st.session_state.modo_edicao = False
                    if 'coord_temp' in st.session_state:
                        del st.session_state.coord_temp
                    st.rerun()
                    
            with col_btn_confirmar:
                if st.button("Confirmar", type="primary", use_container_width=True):
                    atualizar_dados_funcionario(id_selecionado, mat_input, email_input, celular_input, cep_input, num_input, coord_input)
                    conexao = sqlite3.connect('mobilidade_renapsi.db')
                    st.session_state.resultado_busca = pd.read_sql_query(f"SELECT * FROM jovens_rotas WHERE id = {id_selecionado}", conexao)
                    conexao.close()
                    
                    st.session_state.modo_edicao = False
                    if 'coord_temp' in st.session_state:
                        del st.session_state.coord_temp
                    st.success("Dados atualizados com sucesso!")
                    time.sleep(1)
                    st.rerun()

        else:
            with st.spinner("A carregar detalhes..."):
                end_casa_dict = buscar_endereco_viacep(cep_casa)
                end_trab_dict = buscar_endereco_viacep(cep_trab)
                
                rua_casa = end_casa_dict.get('rua', 'N/A') if isinstance(end_casa_dict, dict) else end_casa_dict
                bairro_cidade_casa = f"{end_casa_dict.get('bairro', '')} - {end_casa_dict.get('cidade_uf', '')}" if isinstance(end_casa_dict, dict) else ""
                
                rua_trab = end_trab_dict.get('rua', 'N/A') if isinstance(end_trab_dict, dict) else end_trab_dict
                bairro_cidade_trab = f"{end_trab_dict.get('bairro', '')} - {end_trab_dict.get('cidade_uf', '')}" if isinstance(end_trab_dict, dict) else ""

            col_filler, col_edit_btn = st.columns([9, 1])
            with col_edit_btn:
                if st.button("📝 Editar", use_container_width=True):
                    st.session_state.modo_edicao = True
                    st.rerun()

            # HTML totalmente sem indentação no inicio para não gerar bloco de código do Markdown
            html_painel_principal = f"""
<div style="background-color: #FFFFFF; padding: 30px; border-radius: 8px; box-shadow: 0px 2px 6px rgba(0,0,0,0.1); margin-top: -10px; margin-bottom: 20px;">
    <div style="display: flex; align-items: center; margin-bottom: 15px;">
        <h2 style="margin: 0; color: #5b677a; font-size: 28px;">Consulta Numero {id_selecionado}</h2>
        <span style="background-color: #d1f3e0; color: #1e8e3e; padding: 6px 12px; border-radius: 4px; font-size: 14px; font-weight: bold; margin-left: 15px;">{status_exib}</span>
    </div>
    <h3 style="color: #64748b; font-size: 18px; margin-top: 0; margin-bottom: 30px; font-weight: normal;">RENAPSI - SÃO PAULO - C-T</h3>
    <div style="display: flex; flex-wrap: wrap; justify-content: space-between;">
        <div style="flex: 1; min-width: 250px; margin-bottom: 15px; padding-right: 15px;">
            <h4 style="color: #718096; font-size: 20px; margin-bottom: 15px;">Dados funcionário</h4>
            <p style="margin: 6px 0; font-size: 16px; color: #718096;"><strong style="color: #4a5568;">CPF:</strong> {cpf_cru}</p>
            <p style="margin: 6px 0; font-size: 16px; color: #718096;"><strong style="color: #4a5568;">Matrícula:</strong> {matricula_exib}</p>
            <p style="margin: 6px 0; font-size: 16px; color: #718096;"><strong style="color: #4a5568;">Nome:</strong> {nome_jovem}</p>
            {f'<p style="margin: 6px 0; font-size: 16px; color: #718096;"><strong style="color: #4a5568;">E-mail:</strong> {email_jovem}</p>' if email_jovem else ''}
            {f'<p style="margin: 6px 0; font-size: 16px; color: #718096;"><strong style="color: #4a5568;">Celular:</strong> {celular_jovem}</p>' if celular_jovem else ''}
        </div>
        <div style="flex: 1; min-width: 250px; margin-bottom: 15px; padding-right: 15px;">
            <h4 style="color: #718096; font-size: 20px; margin-bottom: 15px;">Endereço Funcionário</h4>
            <span style='background-color:#d1fae5;color:#065f46;padding:3px 8px;font-size:11px;border-radius:4px; font-weight: bold;'>CRIMINALIDADE BAIXO RISCO</span><br><br>
            <p style="margin: 6px 0; font-size: 16px; color: #718096;"><strong style="color: #4a5568;">CEP:</strong> {cep_casa}</p>
            <p style="margin: 6px 0; font-size: 16px; color: #718096; line-height: 1.6;"><strong style="color: #4a5568;">Endereço:</strong><br>{rua_casa}{f', {numero_casa}' if numero_casa else ''}<br>{bairro_cidade_casa}</p>
        </div>
        <div style="flex: 1; min-width: 250px; margin-bottom: 15px;">
            <h4 style="color: #718096; font-size: 20px; margin-bottom: 15px;">Local de trabalho</h4>
            <p style="margin: 6px 0; font-size: 16px; color: #718096;"><strong style="color: #4a5568;">CEP:</strong> {cep_trab}</p>
            <p style="margin: 6px 0; font-size: 16px; color: #718096; line-height: 1.6;"><strong style="color: #4a5568;">Endereço:</strong><br>{rua_trab}<br>{bairro_cidade_trab}</p>
        </div>
    </div>
</div>
"""
            st.markdown(html_painel_principal, unsafe_allow_html=True)

            # Botões de Ação
            st.markdown("### Resultado")
            col_res1, col_res2 = st.columns([1, 2])
            with col_res1:
                st.caption(f"Última roteirização em: {dados_jovem.get('data_ultima_roteirizacao', 'Pendente')}")
            
            with col_res2:
                col_b1, col_b2, col_b3 = st.columns(3)
                ja_implantado = (status_exib.upper() == "IMPLANTADO")
                
                with col_b1:
                    if st.button("🔄 Roteirizar", disabled=ja_implantado, use_container_width=True):
                        st.session_state.rota_gerada = roteirizar_simulado()
                        st.session_state.modo_contestacao = False 
                        st.rerun()
                with col_b2:
                    if st.button("✉️ Enviar Carta", use_container_width=True):
                        st.session_state.mostrar_modal_email = not st.session_state.get('mostrar_modal_email', False)
                with col_b3:
                    if st.button("⚙️ Contestações", use_container_width=True):
                        st.session_state.modo_contestacao = not st.session_state.get('modo_contestacao', False)
                        st.session_state.rota_gerada = None

            if st.session_state.get('mostrar_modal_email'):
                st.info("**Enviar Resultado My-Link**")
                st.write(f"Deseja enviar o link de assinatura para o e-mail **{email_jovem if email_jovem else 'Não informado'}**?")
                c_conf1, c_conf2 = st.columns([2, 8])
                with c_conf1:
                    if st.button("Confirmar Envio", type="primary"):
                        st.success("E-mail enviado com sucesso!")
                        time.sleep(1.5)
                        st.session_state.mostrar_modal_email = False
                        st.rerun()

            if st.session_state.modo_contestacao:
                with st.form(key="form_nova_contestacao"):
                    motivo_input = st.text_area("Descreve o problema (Ex: tarifa indevida, rota que não faz sentido, etc):")
                    submit_contestacao = st.form_submit_button("Registar Contestação")
                    
                    if submit_contestacao:
                        if motivo_input.strip() == "":
                            st.error("Por favor, descreve o motivo antes de registar.")
                        else:
                            registrar_contestacao(nome=nome_jovem, cid_res="São Paulo", cid_trab="São Paulo", motivo=motivo_input)
                            st.success("Contestação registada! O Dashboard na página principal já foi atualizado.")
                            st.session_state.modo_contestacao = False
                            time.sleep(2)
                            st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

            # Painel do Bilhete e Mapa
            col_painel, col_mapa = st.columns([1, 2.8])
            
            with col_painel:
                aba_selecionada = st.radio(
                    "Selecione:",
                    ["Ida", "Volta", "Bilhetes"],
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                if st.session_state.get('rota_gerada'):
                    nome_trajeto = st.session_state.rota_gerada["trajeto"]
                    valor_total = st.session_state.rota_gerada["valor_diario"]
                else:
                    nome_trajeto = "2x SPTRANS"
                    valor_total = 22.64
                    
                if aba_selecionada == "Ida":
                    valor_exibir = valor_total / 2
                    label_trajeto = nome_trajeto.replace("2x", "1x") if "2x" in nome_trajeto else nome_trajeto
                    desc_label = "Total Ida"
                elif aba_selecionada == "Volta":
                    valor_exibir = valor_total / 2
                    label_trajeto = nome_trajeto.replace("2x", "1x") if "2x" in nome_trajeto else nome_trajeto
                    desc_label = "Total Volta"
                else:
                    valor_exibir = valor_total
                    label_trajeto = nome_trajeto
                    desc_label = "Total Bilhetes"

                html_painel = f"<div style='background-color: #FFFFFF; padding: 20px; border-radius: 8px; box-shadow: 0px 2px 6px rgba(0,0,0,0.1);'><div style='display: flex; align-items: flex-start; gap: 15px; margin-top: 15px; margin-bottom: 20px;'><div style='background-color: #e2e8f0; border-radius: 50%; min-width: 45px; height: 45px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #718096; font-size: 16px;'>SP</div><div><p style='margin: 0; font-weight: bold; color: #4a5568; font-size: 16px;'>{label_trajeto}</p><p style='margin: 4px 0; font-size: 14px; color: #718096;'>Integração</p><p style='margin: 10px 0 0 0; font-size: 16px; color: #4a5568; font-weight: bold;'>{desc_label}: R$ {valor_exibir:.2f}</p></div></div><div style='background-color: #0068C9; color: white; text-align: center; padding: 15px; border-radius: 6px; font-weight: bold; font-size: 16px; box-shadow: 0 2px 4px rgba(0,104,201,0.3);'>VT Total por dia R$ {valor_total:.2f}</div></div>"
                st.markdown(html_painel, unsafe_allow_html=True)
            
            with col_mapa:
                lat_c, lon_c = extrair_coordenadas(coordenadas_casa, -23.6834, -46.7813)
                lat_t, lon_t = -23.5677, -46.6465 
                
                m = folium.Map(location=[(lat_c + lat_t) / 2, (lon_c + lon_t) / 2], zoom_start=11, control_scale=True)
                
                icone_casa = folium.DivIcon(html=f"""
                    <div style="background-color: #00BFA5; width: 48px; height: 48px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; font-size: 22px; box-shadow: 0 4px 8px rgba(0,0,0,0.4);">
                        C
                    </div>
                """)
                folium.Marker([lat_c, lon_c], icon=icone_casa, tooltip="Casa").add_to(m)
                
                icone_trab = folium.DivIcon(html=f"""
                    <div style="background-color: #FF6D00; width: 48px; height: 48px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; font-size: 22px; box-shadow: 0 4px 8px rgba(0,0,0,0.4);">
                        T
                    </div>
                """)
                folium.Marker([lat_t, lon_t], icon=icone_trab, tooltip="Trabalho").add_to(m)
                
                folium.PolyLine(locations=[[lat_c, lon_c], [lat_t, lon_t]], color="#3182bd", weight=4, opacity=0.8).add_to(m)
                
                st_folium(m, height=510, use_container_width=True)

    else:
        st.title("Pesquisar Consultas")
        
        st.markdown("### Contexto da Pesquisa")
        modalidade_pesquisa = st.radio(
            "Seleciona o tipo de rota que estás a avaliar agora:",
            ["Casa x Trabalho", "Casa x Curso"],
            horizontal=True
        )
        st.info(f"Modo Ativo: Estás a pesquisar e alterar rotas no contexto {modalidade_pesquisa}.")
        st.markdown("---")

        tab_cpf, tab_nome, tab_matricula = st.tabs(["Por CPF", "Por Nome", "Por Matrícula"])

        with tab_cpf:
            st.write("Digita o CPF")
            with st.form(key="form_cpf"):
                cpf_busca = st.text_input("Apenas números", max_chars=11)
                btn_cpf = st.form_submit_button("Pesquisar", type="primary")
                if btn_cpf:
                    conexao = sqlite3.connect('mobilidade_renapsi.db')
                    st.session_state.resultado_busca = pd.read_sql_query("SELECT * FROM jovens_rotas WHERE cpf = ?", conexao, params=(cpf_busca,))
                    st.session_state.detalhes_abertos = False
                    conexao.close()
                    st.rerun()

        with tab_nome:
            st.write("Digita o Nome do Jovem")
            with st.form(key="form_nome"):
                nome_busca = st.text_input("Nome completo")
                btn_nome = st.form_submit_button("Pesquisar", type="primary")
                if btn_nome:
                    conexao = sqlite3.connect('mobilidade_renapsi.db')
                    st.session_state.resultado_busca = pd.read_sql_query("SELECT * FROM jovens_rotas WHERE nome LIKE ?", conexao, params=(f"%{nome_busca}%",))
                    st.session_state.detalhes_abertos = False
                    conexao.close()
                    st.rerun()

        with tab_matricula:
            st.write("Digita o Código de Matrícula")
            with st.form(key="form_mat"):
                mat_busca = st.text_input("Apenas números")
                btn_mat = st.form_submit_button("Pesquisar", type="primary")
                if btn_mat:
                    conexao = sqlite3.connect('mobilidade_renapsi.db')
                    st.session_state.resultado_busca = pd.read_sql_query("SELECT * FROM jovens_rotas WHERE matricula = ?", conexao, params=(mat_busca,))
                    st.session_state.detalhes_abertos = False
                    conexao.close()
                    st.rerun()

        if st.session_state.resultado_busca is not None:
            if st.session_state.resultado_busca.empty:
                st.warning("Nenhum aprendiz encontrado com o dado informado.")
            else:
                dados_jovem = st.session_state.resultado_busca.iloc[0]
                id_selecionado = dados_jovem['id']
                nome_jovem = dados_jovem['nome']
                cpf_cru = str(dados_jovem['cpf']).zfill(11)
                cpf_mascarado = f"***.***.{cpf_cru[6:9]}-{cpf_cru[9:11]}"
                matricula_exib = dados_jovem.get('matricula', 'Não informada')
                status_exib = dados_jovem.get('status_rota', 'Otimizado').upper()
                
                data_roteirizacao = dados_jovem.get('data_consulta')
                if not data_roteirizacao:
                    data_roteirizacao = "Pendente"
                data_geracao = "26/08/2025 às 00h00m"

                st.markdown(f"""
                <div style="background-color: #FFFFFF; padding: 20px; border-radius: 8px; box-shadow: 0px 2px 4px rgba(0,0,0,0.05); margin-top: 10px; margin-bottom: 15px; border-left: 4px solid #0068C9;">
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <h3 style="margin: 0; color: #5b677a; font-size: 16px;">{id_selecionado} - {nome_jovem.upper()}</h3>
                        <span style="background-color: #d1f3e0; color: #1e8e3e; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; margin-left: 10px;">{status_exib}</span>
                    </div>
                    <p style="margin: 3px 0; color: #a0aec0; font-size: 13px;">PRÉ-ADM</p>
                    <p style="margin: 3px 0; color: #a0aec0; font-size: 13px;">Gerada a {data_geracao}</p>
                    <p style="margin: 3px 0; color: #a0aec0; font-size: 13px;">Última roteirização a {data_roteirizacao}</p>
                    <p style="margin: 3px 0; color: #a0aec0; font-size: 13px;">CPF: {cpf_mascarado}</p>
                    <p style="margin: 3px 0; color: #a0aec0; font-size: 13px;">Matrícula: {matricula_exib}</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Abrir Consulta", type="primary"):
                    st.session_state.detalhes_abertos = True
                    st.rerun()

# ==========================================
# --- TELA 3: CADASTRO DE JOVENS ---
# ==========================================
elif menu == "Cadastrar Novo Jovem":
    st.title("➕ Cadastrar Novo Jovem")
    st.write("Adicione novos aprendizes à base de dados manualmente ou enviando uma planilha Excel.")
    st.markdown("---")

    tab_manual, tab_massa = st.tabs(["✍️ Cadastro Manual", "📂 Importação em Massa (Excel/CSV)"])

    with tab_manual:
        with st.form(key="form_novo_jovem"):
            col_nome, col_cpf, col_mat = st.columns([2, 1, 1])
            nome_input = col_nome.text_input("Nome Completo do Jovem:")
            cpf_input = col_cpf.text_input("CPF (Apenas números):", max_chars=11)
            matricula_input = col_mat.text_input("Matrícula (Apenas números):")
            
            col_cep1, col_cep2 = st.columns(2)
            cep_casa_input = col_cep1.text_input("CEP da Residência:", max_chars=8)
            cep_trab_input = col_cep2.text_input("CEP do Trabalho:", max_chars=8)
            
            botao_salvar = st.form_submit_button("💾 Salvar Jovem na Base de Dados")

    if botao_salvar:
            if not (nome_input and cpf_input and cep_casa_input and cep_trab_input and matricula_input):
                st.error("⚠️ Por favor, preencha todos os campos (incluindo a Matrícula) antes de salvar.")
            elif cpf_ja_existe(cpf_input):
                st.error(f"❌ Operação bloqueada: O CPF {cpf_input} já está cadastrado no sistema!")
            else:
                with st.spinner("A validar CEPs nos Correios..."):
                    validacao_casa = buscar_endereco_viacep(cep_casa_input)
                    validacao_trab = buscar_endereco_viacep(cep_trab_input)
                    
                    if "inválido" in validacao_casa.get('completo', '').lower() or "inválido" in validacao_trab.get('completo', '').lower():
                        st.error("❌ Operação bloqueada: Um dos CEPs informados é inválido ou não existe no mapa.")
                    else:
                        inserir_novo_jovem(nome_input, cpf_input, cep_casa_input, cep_trab_input, matricula_input)
                        st.success(f"✅ Sucesso! O jovem {nome_input} (Matrícula: {matricula_input}) foi cadastrado!")

    with tab_massa:
        st.info("💡 A sua planilha Excel ou CSV deve conter as colunas: **nome, cpf, cep_casa, cep_trabalho, matricula**")
        arquivo_upload = st.file_uploader("Arraste a sua planilha Excel (.xlsx) ou CSV para cá", type=["xlsx", "csv"])
        
        if arquivo_upload is not None:
            try:
                if arquivo_upload.name.endswith('.csv'):
                    df_upload = pd.read_csv(arquivo_upload, sep=';', dtype=str)
                else:
                    df_upload = pd.read_excel(arquivo_upload, dtype=str)
                
                df_upload.columns = df_upload.columns.str.lower().str.strip()
                
                if 'matricula' not in df_upload.columns:
                    st.error("❌ Erro: O seu arquivo precisa ter uma coluna chamada 'matricula' na primeira linha.")
                else:
                    df_upload['status_rota'] = "Otimizado"
                    
                    st.write("🔍 Pré-visualização dos dados encontrados:")
                    st.dataframe(df_upload.head(), use_container_width=True)
                    
                    botao_salvar_massa = st.button("🚀 Importar Todos para a Base de Dados", type="primary")
                    
                    if botao_salvar_massa:
                        with st.spinner("A enviar dados para a base..."):
                            conexao = sqlite3.connect('mobilidade_renapsi.db')
                            df_limpo = df_upload[['nome', 'cpf', 'cep_casa', 'cep_trabalho', 'matricula', 'status_rota']]
                            df_limpo.to_sql('jovens_rotas', conexao, if_exists='append', index=False)
                            conexao.close()
                            
                            st.success(f"✅ Sucesso! {len(df_limpo)} jovens foram importados com as suas matrículas.")
                            time.sleep(2)
                            st.rerun()
                        
            except Exception as e:
                st.error(f"❌ Erro ao ler o arquivo. Confirme as colunas. Detalhe técnico: {e}")