import streamlit as st
import sqlite3
import os
import time
import datetime

# ─── Configuração da página ───────────────────────────────────────────────────
st.set_page_config(page_title="RENAPSI — Portal do Candidato", page_icon="📝", layout="centered")

# Caminhos Absolutos Seguros
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'mobilidade_renapsi.db')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads_documentos')

# Cria pasta de uploads se não existir
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# ─── CSS Customizado (Tema Claro Renapsi) ───────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; color: #333333; }
    h1, h2, h3 { color: #444c9b !important; }
    .stButton>button[kind="primary"] { background-color: #f8ae28 !important; color: white !important; border: none; border-radius: 8px; font-weight: bold; }
    .stButton>button[kind="primary"]:hover { background-color: #e09a1f !important; }
    div[data-testid="stForm"] { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# ─── Função de Banco de Dados ───────────────────────────────────────────────
def inicializar_tabela_fichas():
    # ── Conexão segura com timeout ──
    conexao = sqlite3.connect(DB_PATH, timeout=20.0)
    cursor = conexao.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fichas_cadastrais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT, nome_social TEXT, data_nascimento TEXT, cpf TEXT UNIQUE, rg TEXT,
            identidade_genero TEXT, raca TEXT, estado_civil TEXT, email_jovem TEXT, email_responsavel TEXT,
            endereco_completo TEXT, cidade_estado TEXT, cep TEXT, tel_jovem TEXT, tel_responsavel TEXT,
            tamanho_uniforme TEXT, nome_mae TEXT, ocupacao_mae TEXT, estado_civil_mae TEXT,
            nome_pai TEXT, ocupacao_pai TEXT, estado_civil_pai TEXT, nome_resp TEXT, ocupacao_resp TEXT, estado_civil_resp TEXT,
            tem_dependentes TEXT,
            path_comp_residencia TEXT, path_rg TEXT, path_conta_salario TEXT, path_titulo TEXT,
            path_reservista TEXT, path_casamento TEXT, path_cert_nasc_dep TEXT, path_vacina_dep TEXT,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status_aprovacao TEXT DEFAULT 'Pendente'
        )
    ''')
    conexao.commit()
    conexao.close()

inicializar_tabela_fichas()

# ── AQUI ESTAVA O ERRO! A função abaixo tinha sumido ──
def salvar_arquivo(uploaded_file, cpf, tipo_doc):
    if uploaded_file is not None:
        pasta_jovem = os.path.join(UPLOAD_DIR, cpf)
        if not os.path.exists(pasta_jovem):
            os.makedirs(pasta_jovem)
        
        # Pega a extensão original do arquivo (.pdf, .jpg, etc)
        extensao = os.path.splitext(uploaded_file.name)[1]
        nome_arquivo = f"{tipo_doc}{extensao}"
        caminho_completo = os.path.join(pasta_jovem, nome_arquivo)
        
        with open(caminho_completo, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return caminho_completo
    return ""

# ─── Interface do Portal ────────────────────────────────────────────────────
st.image("https://renapsi.org.br/wp-content/uploads/2021/02/logo-renapsi-1.png", width=200)
st.title("📝 Ficha Cadastral — Unidade Áurea")
st.markdown("Preencha seus dados com atenção e anexe os documentos solicitados. Seus dados estão seguros e em conformidade com a LGPD.")

# Variáveis de estado para condicionais
if 'genero_selecionado' not in st.session_state: st.session_state.genero_selecionado = 'Mulher Cisgênero'
if 'estado_civil_sel' not in st.session_state: st.session_state.estado_civil_sel = 'Solteiro(a)'
if 'tem_filhos' not in st.session_state: st.session_state.tem_filhos = 'Não'

# Lógica fora do form para atualizar as condicionais em tempo real
st.subheader("⚠️ Informações Iniciais")
col_g, col_ec, col_f = st.columns(3)
with col_g: st.session_state.genero_selecionado = st.selectbox("Identidade de Gênero:", ["Mulher Cisgênero", "Mulher Transgênero", "Homem Cisgênero", "Homem Transgênero"])
with col_ec: st.session_state.estado_civil_sel = st.selectbox("Estado Civil:", ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)"])
with col_f: st.session_state.tem_filhos = st.radio("Possui filhos/dependentes?", ["Não", "Sim"])

st.markdown("---")

# O FORMULÁRIO PRINCIPAL
with st.form("form_cadastro_jovem"):
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Dados Pessoais", "📍 Endereço e Contato", "👨‍👩‍👧 Família", "📄 Documentos (Anexos)"])
    
    with tab1:
        st.markdown("#### Informações Básicas")
        nome = st.text_input("1. Nome Completo *")
        nome_social = st.text_input("2. Nome Social (Opcional)")
        col_dn, col_cpf, col_rg = st.columns(3)
        
        # Calendário ajustado para formato brasileiro e limite até 1950
        dt_nasc = col_dn.date_input(
            "3. Data de Nascimento *",
            min_value=datetime.date(1950, 1, 1),
            max_value=datetime.date.today(),
            format="DD/MM/YYYY"
        )
        
        cpf = col_cpf.text_input("4. CPF (Apenas números) *", max_chars=11)
        rg = col_rg.text_input("5. RG *")
        
        raca = st.selectbox("6. Autodeclaração Racial", ["Amarela", "Branca", "Parda", "Negra", "Indígena"])
        tamanho_uniforme = st.selectbox("7. Tamanho do Uniforme (Camiseta)", ["P", "M", "G", "GG", "G1 OU +"])

    with tab2:
        st.markdown("#### Contato")
        email_jovem = st.text_input("8. E-mail do Jovem *")
        email_resp = st.text_input("9. E-mail do Responsável (Obrigatório se menor de 18)")
        tel_jovem = st.text_input("10. Celular do Jovem *")
        tel_resp = st.text_input("11. Telefone do Responsável")
        
        st.markdown("#### Residência")
        cep = st.text_input("12. CEP *", max_chars=8)
        endereco = st.text_input("13. Endereço + Nº da Casa *")
        cidade_estado = st.text_input("14. Cidade e Estado *")

    with tab3:
        st.markdown("#### Filiação e Responsáveis")
        nome_mae = st.text_input("15. Nome da Mãe")
        col_m1, col_m2 = st.columns(2)
        ocupacao_mae = col_m1.selectbox("16. Ocupação da Mãe", ["Desempregado(a)", "Trabalho Informal", "Trabalho c/ carteira assinada", "Aposentado(a)"])
        est_mae = col_m2.selectbox("17. Estado Civil da Mãe", ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "Falecido(a)"])
        
        st.markdown("---")
        nome_pai = st.text_input("18. Nome do Pai")
        col_p1, col_p2 = st.columns(2)
        
        ocupacao_pai = col_p1.selectbox("19. Ocupação do Pai", ["Desempregado(a)", "Trabalho Informal", "Trabalho c/ carteira assinada", "Aposentado(a)"])
        est_pai = col_p2.selectbox("20. Estado Civil do Pai", ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "Falecido(a)"])

        st.markdown("---")
        nome_resp = st.text_input("21. Nome do Representante Legal (Se NÃO for pai ou mãe)")

    with tab4:
        st.markdown("#### 📎 Anexo de Documentos")
        st.info("Envie arquivos em formato PDF ou Imagem (JPG/PNG).")
        
        doc_residencia = st.file_uploader("1. Comprovante de Residência *", type=['pdf', 'jpg', 'png'])
        doc_rg = st.file_uploader("2. Cópia do RG *", type=['pdf', 'jpg', 'png'])
        doc_conta = st.file_uploader("3. Cópia da Conta Bancária (Salário) *", type=['pdf', 'jpg', 'png'])
        doc_titulo = st.file_uploader("4. Título de Eleitor *", type=['pdf', 'jpg', 'png'])
        
        # Variáveis vazias para os condicionais
        doc_reservista = None
        doc_casamento = None
        doc_cert_dep = None
        doc_vacina_dep = None

        # Lógicas Condicionais de Upload
        if "Homem" in st.session_state.genero_selecionado:
            st.warning("⚠️ Como você se identifica como Homem, anexe o documento abaixo:")
            doc_reservista = st.file_uploader("5. Reservista do Exército *", type=['pdf', 'jpg', 'png'])
            
        if st.session_state.estado_civil_sel == "Casado(a)":
            st.warning("⚠️ Como seu estado civil é Casado(a), anexe o documento abaixo:")
            doc_casamento = st.file_uploader("6. Certidão de Casamento *", type=['pdf', 'jpg', 'png'])
            
        if st.session_state.tem_filhos == "Sim":
            st.warning("⚠️ Como você possui dependentes, anexe os documentos abaixo:")
            doc_cert_dep = st.file_uploader("7. Certidão de Nascimento do Dependente *", type=['pdf', 'jpg', 'png'])
            doc_vacina_dep = st.file_uploader("8. Carteira de Vacinação do Dependente *", type=['pdf', 'jpg', 'png'])

    st.markdown("<br>", unsafe_allow_html=True)
    enviou = st.form_submit_button("🚀 Enviar Ficha Cadastral", type="primary", use_container_width=True)

    if enviou:
        if not nome or not cpf or not cep or not endereco:
            st.error("❌ Por favor, preencha os campos obrigatórios (Nome, CPF, CEP, Endereço).")
        elif not doc_residencia or not doc_rg or not doc_conta or not doc_titulo:
            st.error("❌ Por favor, anexe os 4 documentos básicos obrigatórios na aba 'Documentos'.")
        else:
            with st.spinner("Salvando seus dados e documentos..."):
                try:
                    # 1. Salvar os arquivos fisicamente na pasta uploads_documentos/CPF/
                    path_residencia = salvar_arquivo(doc_residencia, cpf, "comprovante_residencia")
                    path_rg = salvar_arquivo(doc_rg, cpf, "rg")
                    path_conta = salvar_arquivo(doc_conta, cpf, "conta_bancaria")
                    path_titulo = salvar_arquivo(doc_titulo, cpf, "titulo_eleitor")
                    
                    path_reservista = salvar_arquivo(doc_reservista, cpf, "reservista") if doc_reservista else ""
                    path_casamento = salvar_arquivo(doc_casamento, cpf, "certidao_casamento") if doc_casamento else ""
                    path_cert_dep = salvar_arquivo(doc_cert_dep, cpf, "certidao_dependente") if doc_cert_dep else ""
                    path_vacina_dep = salvar_arquivo(doc_vacina_dep, cpf, "vacina_dependente") if doc_vacina_dep else ""

                    # 2. Salvar no Banco de Dados SQLite (Conexão Segura)
                    conexao = sqlite3.connect(DB_PATH, timeout=20.0)
                    cursor = conexao.cursor()
                    cursor.execute('''
                        INSERT INTO fichas_cadastrais (
                            nome_completo, nome_social, data_nascimento, cpf, rg,
                            identidade_genero, raca, estado_civil, email_jovem, email_responsavel,
                            endereco_completo, cidade_estado, cep, tel_jovem, tel_responsavel,
                            tamanho_uniforme, nome_mae, ocupacao_mae, estado_civil_mae,
                            nome_pai, ocupacao_pai, estado_civil_pai, nome_resp,
                            tem_dependentes,
                            path_comp_residencia, path_rg, path_conta_salario, path_titulo,
                            path_reservista, path_casamento, path_cert_nasc_dep, path_vacina_dep
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ''', (
                        nome, nome_social, str(dt_nasc), cpf, rg,
                        st.session_state.genero_selecionado, raca, st.session_state.estado_civil_sel, email_jovem, email_resp,
                        endereco, cidade_estado, cep, tel_jovem, tel_resp,
                        tamanho_uniforme, nome_mae, ocupacao_mae, est_mae,
                        nome_pai, ocupacao_pai, est_pai, nome_resp,
                        st.session_state.tem_filhos,
                        path_residencia, path_rg, path_conta, path_titulo,
                        path_reservista, path_casamento, path_cert_dep, path_vacina_dep
                    ))
                    conexao.commit()
                    conexao.close()
                    
                    st.success("✅ **Ficha Cadastral enviada com sucesso!** O RH entrará em contato em breve.")
                    st.balloons()
                    time.sleep(3)
                    st.rerun()

                except sqlite3.IntegrityError:
                    st.error(f"❌ O CPF {cpf} já enviou uma ficha cadastral.")
                except Exception as e:
                    st.error(f"❌ Ocorreu um erro ao salvar: {e}")