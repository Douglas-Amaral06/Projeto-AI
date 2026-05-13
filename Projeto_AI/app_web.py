"""
Portal do Jovem Aprendiz - Atendimento Renapsi
Interface Web com Streamlit para o Bot RAG de Vale-Transporte
"""

import os
import json
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

st.set_page_config(
    page_title="Portal do Jovem Aprendiz - Renapsi",
    page_icon="🚌",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #f5f7fa; }
    .stChatMessage { border-radius: 15px; padding: 10px; margin-bottom: 10px; }
    h1 { color: #1e3a8a; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

def tela_login():
    st.title("🔒 Acesso Restrito")
    st.markdown("---")
    st.info("Este sistema é exclusivo para colaboradores autorizados da Renapsi.")
    senha = st.text_input("Digite o código de acesso da Renapsi", type="password", key="senha_login")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔓 Entrar", use_container_width=True):
            if senha == "RENAPSI2026":
                st.session_state.autenticado = True
                st.success("✅ Acesso autorizado! Redirecionando...")
                st.rerun()
            else:
                st.error("❌ Código de acesso inválido. Tente novamente.")
    st.markdown("---")
    st.caption("💡 Entre em contato com o RH caso tenha esquecido o código de acesso.")

def salvar_log(pergunta, resposta):
    try:
        registro = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "pergunta_usuario": pergunta, "resposta_bot": resposta}
        with open("logs_atendimento.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[ERRO AO SALVAR LOG] {e}")

@st.cache_resource(show_spinner="🔄 Carregando Base de Conhecimento...")
def inicializar_rag():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_txt = os.path.join(base_dir, "conhecimento_rh.txt")
    loader = TextLoader(caminho_txt, encoding="utf-8")
    documentos = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150, length_function=len)
    chunks = text_splitter.split_documents(documentos)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    vector_store = FAISS.from_documents(chunks, embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    template = """Você é o Demà, o assistente virtual da Renapsi, focado EXCLUSIVAMENTE em dúvidas de Vale-Transporte.

REGRAS DE CONDUTA E SEGURANÇA:
1. CORTESIA LIBERADA: Se o jovem aprendiz enviar apenas saudações, aja de forma amigável, apresente-se como Demà e pergunte como pode ajudar com o Vale-Transporte.
2. FLUIDEZ DE CONVERSA: Se o historico_da_conversa não estiver vazio, NUNCA repita saudações iniciais ou apresentações.
3. INTELIGÊNCIA SEMÂNTICA: Entenda as gírias e formas de falar dos jovens.
4. RIGOR NOS DADOS: Para responder sobre regras, prazos, recargas, bloqueios e saldos, você DEVE usar APENAS as informações das tags contexto.
5. O LIMITE DA IA: Se a pergunta for sobre Vale-Transporte e a resposta definitivamente NÃO estiver no contexto, você deve responder EXATAMENTE: 'Não possuo essa informação nos meus manuais, por favor procure o RH.'

<historico_da_conversa>
{chat_history}
</historico_da_conversa>

<contexto>
{context}
</contexto>

<pergunta_atual>
{question}
</pergunta_atual>

Resposta do Demà:"""
    prompt = PromptTemplate.from_template(template)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    rag_chain = ({"context": lambda x: format_docs(retriever.invoke(x["question"])), "question": lambda x: x["question"], "chat_history": lambda x: x["chat_history"]} | prompt | llm | StrOutputParser())
    return rag_chain

if not st.session_state.autenticado:
    tela_login()
else:
    with st.sidebar:
        st.title("🏢 Renapsi - IA")
        st.markdown("---")
        st.markdown("**IA especialista em Vale-Transporte para os Jovens Aprendizes.**")
        st.markdown("---")
        if st.button("🗑️ Limpar Histórico da Conversa", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        st.markdown("---")
        st.caption("💡 Seja específico em suas perguntas.")

    st.title("Assistente Virtual - Demà")
    st.caption("Tire suas dúvidas sobre saldo, recarga e bloqueio do seu cartão de transporte.")
    st.markdown("---")

    try:
        rag_chain = inicializar_rag()
    except Exception as e:
        st.error(f"❌ Erro ao inicializar sistema: {e}")
        st.stop()

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "Olá, Jovem Aprendiz! 👋 Como posso ajudar com seu Vale-Transporte hoje?"})

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Digite sua dúvida aqui..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("🔍 Consultando manuais da Renapsi..."):
                try:
                    historico_formatado = ""
                    if len(st.session_state.messages) > 1:
                        for msg in st.session_state.messages[-5:-1]:
                            role = "Jovem Aprendiz" if msg["role"] == "user" else "Demà"
                            historico_formatado += f"{role}: {msg['content']}\n"
                    resposta = rag_chain.invoke({"question": prompt, "chat_history": historico_formatado})
                    st.markdown(resposta)
                    st.session_state.messages.append({"role": "assistant", "content": resposta})
                    salvar_log(prompt, resposta)
                except Exception as e:
                    print(f"\n[ERRO CRÍTICO NA CHAIN] {e}\n")
                    erro_msg = "⚠️ Desculpe, ocorreu um erro interno. Por favor, tente novamente."
                    st.error(erro_msg)
                    st.session_state.messages.append({"role": "assistant", "content": erro_msg})

    st.markdown("---")
    st.caption("🤖 Powered by LangChain + Google Gemini 2.5 Flash | Renapsi © 2026")
