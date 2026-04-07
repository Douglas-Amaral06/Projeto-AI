import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
import random
import datetime
import time

st.set_page_config(page_title="Nova Capta - Piloto", page_icon="🚌", layout="wide")

# ── Estado da sessão ───────────────────────────────────────────
for chave, padrao in [
    ("jovem_em_visualizacao", None),
    ("mostrar_modal_email",   False),
    ("mostrar_contestacao",   False),
    ("modalidade_pesquisa",   "Casa x Trabalho"),
    ("rota_cache",            None),
]:
    if chave not in st.session_state:
        st.session_state[chave] = padrao

# ── CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
div[data-testid="metric-container"] {
    background:#fff; border-radius:10px; padding:15px;
    box-shadow:0 4px 6px rgba(0,0,0,.05);
    border-left:5px solid #0068C9;
}
h1,h2,h3 { color:#1E3A8A; }
.badge {
    background:#d1fae5; color:#065f46;
    padding:3px 10px; border-radius:4px;
    font-size:12px; font-weight:700;
    text-transform:uppercase; margin-left:8px;
    display:inline-block;
}
.badge-risco {
    background:#d1fae5; color:#065f46;
    padding:2px 8px; border-radius:4px;
    font-size:11px; font-weight:700; display:inline-block;
    margin-bottom:6px;
}
.card {
    background:#fff; border-radius:10px;
    padding:20px 24px;
    box-shadow:0 1px 4px rgba(0,0,0,.10);
    margin-bottom:16px;
}
.card-busca {
    background:#fff; padding:15px; border-radius:8px;
    box-shadow:0 1px 3px rgba(0,0,0,.10);
    border-left:4px solid #4ade80;
}
.lbl  { font-weight:700; color:#1E3A8A; font-size:15px; }
.info { color:#444; font-size:14px; margin:4px 0; }
.vt   {
    background:#1D4ED8; color:#fff;
    border-radius:8px; padding:12px 16px;
    text-align:center; font-weight:700; font-size:15px; margin-top:14px;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  UTILITÁRIOS
# ══════════════════════════════════════════════════════════════

def s(val, d="Não informado"):
    return str(val).strip() if val not in (None, "", "None") else d

def mascarar_cpf(cpf):
    c = str(cpf).zfill(11)
    return f"{'*'*6}{c[6:9]}-{c[9:11]}"

def viacep(cep):
    try:
        r = requests.get(
            f"https://viacep.com.br/ws/{str(cep).replace('-','').zfill(8)}/json/",
            timeout=5
        ).json()
        if "erro" not in r:
            return {
                "rua":       r.get("logradouro") or "N/A",
                "bairro":    r.get("bairro")     or "N/A",
                "cidade_uf": f"{r.get('localidade','N/A')} - {r.get('uf','N/A')}",
            }
    except Exception:
        pass
    return {"rua": "N/A", "bairro": "N/A", "cidade_uf": "N/A"}

def rota_simulada():
    return random.choice([
        {"trajeto": "2x SPTRANS",         "valor": 8.80,  "tempo": "45 min"},
        {"trajeto": "1 Onibus + 1 Metro",  "valor": 10.00, "tempo": "1h 10min"},
    ])

# ══════════════════════════════════════════════════════════════
#  BANCO DE DADOS
# ══════════════════════════════════════════════════════════════

def init_db():
    con = sqlite3.connect("mobilidade_renapsi.db")
    cur = con.cursor()
    for col, tipo in [
        ("data_consulta","TEXT"), ("sla_segundos","REAL"),
        ("matricula","TEXT"),     ("status_rota","TEXT DEFAULT 'Otimizado'"),
        ("data_geracao","TEXT"),  ("data_ultima_roteirizacao","TEXT"),
        ("email","TEXT"),         ("celular","TEXT"),
        ("empresa","TEXT DEFAULT 'Renapsi - SP'"),
    ]:
        try:
            cur.execute(f"ALTER TABLE jovens_rotas ADD COLUMN {col} {tipo}")
        except sqlite3.OperationalError:
            pass
    cur.execute("UPDATE jovens_rotas SET status_rota='Otimizado' WHERE status_rota IS NULL")
    cur.execute("UPDATE jovens_rotas SET data_geracao='26/08/2025 as 00h00m' WHERE data_geracao IS NULL")
    cur.execute("UPDATE jovens_rotas SET celular='Nao informado' WHERE celular IS NULL")
    cur.execute("UPDATE jovens_rotas SET empresa='Renapsi - SP' WHERE empresa IS NULL")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contestacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_jovem TEXT, cidade_residencia TEXT,
            cidade_trabalho TEXT, motivo TEXT, data_geracao TEXT
        )
    """)
    con.commit()
    con.close()

def inserir_jovem(nome, cpf, cep_casa, cep_trab):
    con = sqlite3.connect("mobilidade_renapsi.db")
    con.execute("""
        INSERT INTO jovens_rotas
        (nome,cpf,cep_casa,cep_trabalho,matricula,status_rota,data_geracao,email,celular,empresa)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (nome, cpf, cep_casa, cep_trab,
          str(random.randint(100000,999999)), "Otimizado",
          datetime.datetime.now().strftime("%d/%m/%Y as %Hh%Mm"),
          f"{nome.split()[0].lower()}.renapsi@gmail.com",
          "(11) 98888-7777", "Renapsi - SP"))
    con.commit()
    con.close()

def cpf_existe(cpf):
    con = sqlite3.connect("mobilidade_renapsi.db")
    n = con.execute("SELECT COUNT(*) FROM jovens_rotas WHERE cpf=?", (cpf,)).fetchone()[0]
    con.close()
    return n > 0

def gravar_contestacao(nome, cid_r, cid_t, motivo):
    con = sqlite3.connect("mobilidade_renapsi.db")
    con.execute(
        "INSERT INTO contestacoes (nome_jovem,cidade_residencia,cidade_trabalho,motivo,data_geracao) VALUES (?,?,?,?,?)",
        (nome, cid_r, cid_t, motivo, datetime.datetime.now().strftime("%d/%m/%Y as %Hh%Mm"))
    )
    con.commit()
    con.close()

def kpis_dashboard():
    con = sqlite3.connect("mobilidade_renapsi.db")
    mes = datetime.datetime.now().strftime("%Y-%m")
    r = con.execute(
        "SELECT COUNT(DISTINCT id), AVG(sla_segundos) FROM jovens_rotas WHERE data_consulta LIKE ?",
        (f"{mes}%",)
    ).fetchone()
    con.close()
    return (r[0] or 0), (r[1] or 0.0)

init_db()

# ══════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════
try:
    st.sidebar.image("logo_renapsi.png", use_container_width=True)
except Exception:
    st.sidebar.markdown("## Renapsi")

st.sidebar.title("Menu de Navegacao")
menu = st.sidebar.radio("Escolha a area:", [
    "Dashboard Principal",
    "Pesquisar Consultas",
    "Cadastrar Novo Jovem",
])

# ══════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════
if menu == "Dashboard Principal":
    meses = ["Janeiro","Fevereiro","Marco","Abril","Maio","Junho",
             "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
    mes_nome = meses[datetime.datetime.now().month - 1]
    ano      = datetime.datetime.now().year

    c1, c2, c3 = st.columns([3, 1, 1])
    c1.markdown(f"<h2 style='margin:0'>Dashboard {mes_nome} de {ano}</h2>", unsafe_allow_html=True)
    c2.button("Alterar Periodo",    use_container_width=True)
    c3.button("Download Relatorio", use_container_width=True)

    total, sla = kpis_dashboard()
    k1, k2 = st.columns(2)
    k1.metric("Total de Consultas",        total,        delta="Consulta", delta_color="off")
    k2.metric("SLA Medio - Tempo Resposta", f"{sla:.2f}", delta="Minutos",  delta_color="off")

    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2, g3, g4 = st.columns(4)

    with g1:
        st.markdown("**Implantacoes (0 / 1)**")
        st.info("Nenhuma implantacao no periodo.")

    def mini_pie(vals, names, cor, key):
        fig = px.pie(values=vals, names=names, hole=0.75)
        fig.update_traces(textinfo="none", marker=dict(colors=[cor,"#FFF"]), hoverinfo="skip")
        fig.update_layout(showlegend=False, margin=dict(t=10,b=10,l=10,r=10),
                          height=180, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, key=key)

    with g2:
        st.markdown("**Contestacoes (2 / 1)**")
        mini_pie([2,1], ["Aprovadas","Contestadas"], "#43b596", "pie_contest")
    with g3:
        st.markdown("**Consultas por Local de Trabalho**")
        mini_pie([10,0], ["SP","Outros"], "#2a4b5d", "pie_local")
    with g4:
        st.markdown("**Consultas por UF**")
        mini_pie([10,0], ["SP","Outros"], "#2a4b5d", "pie_uf")

    st.markdown("---")
    with st.expander("Ver Detalhes das Contestacoes"):
        con = sqlite3.connect("mobilidade_renapsi.db")
        df_c = pd.read_sql_query("SELECT * FROM contestacoes", con)
        con.close()
        if df_c.empty:
            st.info("Nenhuma contestacao registrada.")
        else:
            t1, t2 = st.tabs(["Cards", "Tabela"])
            with t1:
                cols = st.columns(2)
                for i, row in df_c.iterrows():
                    with cols[i % 2]:
                        st.markdown(f"""
                        <div class='card' style='border-top:4px solid #0068C9'>
                          <h4 style='margin-top:0;color:#1E3A8A'>Consulta {row['id']}</h4>
                          <p style='color:#666;font-size:14px'>Gerada em {row['data_geracao']}</p>
                          <p style='color:#888;font-size:14px'>{row['cidade_residencia']} x {row['cidade_trabalho']}</p>
                          <p style='color:#333;font-weight:700'>Funcionario: {row['nome_jovem']}</p>
                          <div style='background:#F4F6F9;padding:10px;border-radius:5px;font-size:14px'>
                            <b>Motivo:</b> {row['motivo']}
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
            with t2:
                st.dataframe(df_c[["id","cidade_residencia","cidade_trabalho",
                                   "data_geracao","nome_jovem","motivo"]],
                             use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
#  PESQUISAR CONSULTAS
# ══════════════════════════════════════════════════════════════
elif menu == "Pesquisar Consultas":

    # ─────────────────────────────────────────────────────────
    #  TELA DE BUSCA
    # ─────────────────────────────────────────────────────────
    if st.session_state.jovem_em_visualizacao is None:

        st.markdown("### Contexto da Pesquisa")
        modalidade = st.radio(
            "Selecione o tipo de rota:",
            ["Casa x Trabalho", "Casa x Curso"],
            horizontal=True,
            key="radio_modalidade",
        )
        st.session_state.modalidade_pesquisa = modalidade
        st.markdown("---")

        tab_cpf, tab_nome, tab_mat = st.tabs(["Por CPF", "Por Nome", "Por Matricula"])

        def mostrar_resultados(df_res):
            if df_res.empty:
                st.warning("Nenhum aprendiz encontrado.")
                return
            st.markdown(f"**{len(df_res)} resultado(s) encontrado(s)**")
            for _, row in df_res.iterrows():
                col_card, col_btn = st.columns([9, 1])
                with col_card:
                    st.markdown(f"""
                    <div class='card-busca'>
                      <h4 style='margin:0;color:#1E3A8A'>
                        {row['id']} - {row['nome']}
                        <span class='badge'>{s(row.get('status_rota'),'OTIMIZADO').upper()}</span>
                      </h4>
                      <p style='color:#999;margin:5px 0;font-size:13px'>PRE-ADM</p>
                      <p style='color:#666;margin:2px 0;font-size:14px'>Gerada em {s(row.get('data_geracao'))}</p>
                      <p style='color:#666;margin:2px 0;font-size:14px'>
                        Ultima roterizacao: {s(row.get('data_ultima_roteirizacao'),'Nao roteirizado')}</p>
                      <p style='color:#666;margin:2px 0;font-size:14px'>CPF: {mascarar_cpf(row['cpf'])}</p>
                      <p style='color:#666;margin:2px 0;font-size:14px'>Matricula: {s(row.get('matricula'))}</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    if st.button("Abrir", key=f"abrir_{row['id']}"):
                        st.session_state.jovem_em_visualizacao = int(row["id"])
                        st.session_state.rota_cache = rota_simulada()
                        st.rerun()

        with tab_cpf:
            cpf_i = st.text_input("CPF (somente numeros)", key="i_cpf", max_chars=11)
            if st.button("Pesquisar", type="primary", key="b_cpf"):
                con = sqlite3.connect("mobilidade_renapsi.db")
                mostrar_resultados(pd.read_sql_query(
                    "SELECT * FROM jovens_rotas WHERE cpf=?", con, params=(cpf_i,)))
                con.close()

        with tab_nome:
            nome_i = st.text_input("Nome completo", key="i_nome")
            if st.button("Pesquisar", type="primary", key="b_nome"):
                con = sqlite3.connect("mobilidade_renapsi.db")
                mostrar_resultados(pd.read_sql_query(
                    "SELECT * FROM jovens_rotas WHERE nome LIKE ?", con, params=(f"%{nome_i}%",)))
                con.close()

        with tab_mat:
            mat_i = st.text_input("Matricula (numeros)", key="i_mat")
            if st.button("Pesquisar", type="primary", key="b_mat"):
                con = sqlite3.connect("mobilidade_renapsi.db")
                mostrar_resultados(pd.read_sql_query(
                    "SELECT * FROM jovens_rotas WHERE matricula=?", con, params=(mat_i,)))
                con.close()

    # ─────────────────────────────────────────────────────────
    #  PAINEL DE DETALHES  — sem st.tabs aqui
    # ─────────────────────────────────────────────────────────
    else:

        if st.button("Voltar para a Pesquisa", key="btn_voltar"):
            st.session_state.jovem_em_visualizacao = None
            st.session_state.mostrar_modal_email   = False
            st.session_state.mostrar_contestacao   = False
            st.session_state.rota_cache            = None
            st.rerun()

        try:
            con = sqlite3.connect("mobilidade_renapsi.db")
            df_j = pd.read_sql_query(
                "SELECT * FROM jovens_rotas WHERE id=?",
                con, params=(st.session_state.jovem_em_visualizacao,)
            )
            con.close()

            if df_j.empty:
                st.error("Registro nao encontrado.")
                st.stop()

            j = df_j.iloc[0]

            nome      = s(j.get("nome"))
            cpf_mask  = mascarar_cpf(s(j.get("cpf"), "00000000000"))
            matricula = s(j.get("matricula"))
            email     = s(j.get("email"))
            celular   = s(j.get("celular"))
            empresa   = s(j.get("empresa"))
            status    = s(j.get("status_rota"), "OTIMIZADO").upper()
            data_imp  = j.get("data_ultima_roteirizacao")
            cep_casa  = s(j.get("cep_casa"), "")
            cep_trab  = s(j.get("cep_trabalho"), "")
            id_jovem  = int(j["id"])
            modalidade = st.session_state.modalidade_pesquisa

            end_c = viacep(cep_casa)
            end_t = viacep(cep_trab)
            rota  = st.session_state.rota_cache or rota_simulada()

            # Cabecalho
            st.markdown(
                f"<h2 style='margin-bottom:2px;color:#111'>"
                f"Consulta {id_jovem}"
                f"<span class='badge'>{status}</span>"
                f"</h2>"
                f"<p style='color:#555;font-size:14px;margin-bottom:16px'>"
                f"<b>{empresa.upper()}</b> — {modalidade.upper()}</p>",
                unsafe_allow_html=True,
            )

            # 3 colunas
            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown(f"""
                <div class='card'>
                  <p class='lbl'>Dados do funcionario</p>
                  <p class='info'><b>CPF:</b> {cpf_mask}</p>
                  <p class='info'><b>Matricula:</b> {matricula}</p>
                  <p class='info'><b>E-mail:</b> {email}</p>
                  <p class='info'><b>Celular:</b> {celular}</p>
                  <p class='info'><b>Nome:</b> {nome}</p>
                </div>
                """, unsafe_allow_html=True)

            with c2:
                st.markdown(f"""
                <div class='card'>
                  <p class='lbl'>Endereco do funcionario</p>
                  <span class='badge-risco'>CRIMINALIDADE BAIXO RISCO</span>
                  <p class='info'><b>CEP:</b> {cep_casa}</p>
                  <p class='info'><b>Rua:</b> {end_c['rua']}</p>
                  <p class='info'>{end_c['bairro']} - {end_c['cidade_uf']}</p>
                </div>
                """, unsafe_allow_html=True)

            with c3:
                st.markdown(f"""
                <div class='card'>
                  <p class='lbl'>Local de trabalho</p>
                  <p class='info'><b>{empresa}</b></p>
                  <p class='info'><b>CEP:</b> {cep_trab}</p>
                  <p class='info'><b>Rua:</b> {end_t['rua']}</p>
                  <p class='info'>{end_t['bairro']} - {end_t['cidade_uf']}</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### Resultado")
            st.caption(f"Implantado em {data_imp}" if data_imp else "Nao implantado ainda")

            # Botoes de acao
            b1, b2, b3, b4, b5, b6 = st.columns(6)
            with b1:
                st.button("Roteirizar", disabled=True, use_container_width=True, key="btn_rot")
            with b2:
                if st.button("Contestacoes", use_container_width=True, key="btn_cont"):
                    st.session_state.mostrar_contestacao = not st.session_state.mostrar_contestacao
            with b3:
                st.button("Implantacao", use_container_width=True, key="btn_impl")
            with b4:
                st.button("Carta", use_container_width=True, key="btn_carta")
            with b5:
                if st.button("My-Link", use_container_width=True, key="btn_mylink"):
                    st.session_state.mostrar_modal_email = not st.session_state.mostrar_modal_email
            with b6:
                st.button("Tendencia", use_container_width=True, key="btn_tend")

            # Contestacao
            if st.session_state.mostrar_contestacao:
                st.markdown("---")
                st.markdown("#### Registrar Contestacao")
                motivo = st.text_area("Descreva o motivo:", key="ta_motivo")
                if st.button("Confirmar", type="primary", key="btn_conf_cont"):
                    if motivo.strip():
                        gravar_contestacao(nome, end_c["cidade_uf"], end_t["cidade_uf"], motivo)
                        st.success("Contestacao registrada!")
                        st.session_state.mostrar_contestacao = False
                        st.rerun()
                    else:
                        st.warning("Preencha o motivo.")

            # Modal My-Link
            if st.session_state.mostrar_modal_email:
                st.markdown("---")
                st.info(f"Deseja enviar o resultado para **{email}**?")
                mc1, mc2, _ = st.columns([1, 1, 5])
                with mc1:
                    if st.button("Fechar", key="btn_fechar"):
                        st.session_state.mostrar_modal_email = False
                        st.rerun()
                with mc2:
                    if st.button("Enviar", type="primary", key="btn_enviar"):
                        st.success(f"E-mail enviado para {email}!")
                        time.sleep(1)
                        st.session_state.mostrar_modal_email = False
                        st.rerun()

            st.markdown("---")

            # Bilhete + Mapa
            col_bil, col_map = st.columns([1, 3])

            with col_bil:
                vt = rota["valor"] * 2
                st.markdown(f"""
                <div class='card'>
                  <p style='font-size:15px;font-weight:700;margin:8px 0 2px'>{rota['trajeto']}</p>
                  <p class='info'>R$ {rota['valor']:.2f} - Integracao</p>
                  <p class='info'>Total R$ {rota['valor']*2:.2f}</p>
                  <p class='info'>Tempo: {rota['tempo']}</p>
                  <div class='vt'>VT Total por dia R$ {vt:.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            with col_map:
                df_map = pd.DataFrame({
                    "lat":  [-23.6000, -23.5505],
                    "lon":  [-46.7000, -46.6333],
                    "nome": ["Casa", "Trabalho"],
                    "tipo": ["Casa", "Trabalho"],
                    "lbl":  ["C",    "T"],
                })
                fig_m = px.scatter_mapbox(
                    df_map, lat="lat", lon="lon",
                    hover_name="nome", color="tipo",
                    color_discrete_map={"Casa":"#10b981","Trabalho":"#f97316"},
                    text="lbl", zoom=11, height=370,
                )
                fig_m.update_traces(
                    marker=dict(size=22, opacity=0.95),
                    textposition="middle center",
                    textfont=dict(color="white", size=15, family="Arial Black"),
                )
                fig_m.update_layout(
                    mapbox_style="open-street-map",
                    margin={"r":0,"t":0,"l":0,"b":0},
                    showlegend=False,
                )
                st.plotly_chart(fig_m, use_container_width=True, key="mapa_detalhe")

        except Exception as err:
            st.error(f"Erro no painel: {err}")
            st.exception(err)

# ══════════════════════════════════════════════════════════════
#  CADASTRAR NOVO JOVEM
# ══════════════════════════════════════════════════════════════
elif menu == "Cadastrar Novo Jovem":
    st.title("Cadastrar Novo Jovem")
    st.markdown("---")

    with st.form("form_cadastro"):
        c1, c2 = st.columns(2)
        nome_i = c1.text_input("Nome Completo:")
        cpf_i  = c2.text_input("CPF (somente numeros):", max_chars=11)
        c3, c4 = st.columns(2)
        cep1   = c3.text_input("CEP da Residencia:", max_chars=8)
        cep2   = c4.text_input("CEP do Trabalho:",   max_chars=8)
        salvar = st.form_submit_button("Salvar Jovem")

    if salvar:
        if not all([nome_i, cpf_i, cep1, cep2]):
            st.error("Preencha todos os campos.")
        elif cpf_existe(cpf_i):
            st.error("CPF ja cadastrado.")
        else:
            inserir_jovem(nome_i, cpf_i, cep1, cep2)
            st.success("Jovem cadastrado com sucesso!")