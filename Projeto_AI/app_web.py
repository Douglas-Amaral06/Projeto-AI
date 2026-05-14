"""
Portal do Jovem Aprendiz - Atendimento Renapsi
Interface Web com Streamlit para o Bot RAG de Vale-Transporte
"""

import os
import json
import time
from datetime import datetime
from glob import glob
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

st.set_page_config(
    page_title="Demà - Assistente Renapsi",
    page_icon="🏢",
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

def salvar_log(pergunta, resposta, avaliacao=None):
    try:
        registro = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            "pergunta_usuario": pergunta, 
            "resposta_bot": resposta,
            "avaliacao": avaliacao if avaliacao else "Sem avaliação"
        }
        with open("logs_atendimento.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[ERRO AO SALVAR LOG] {e}")

def atualizar_avaliacao_log(pergunta, resposta, avaliacao):
    """Atualiza a avaliação de um log existente."""
    try:
        # Ler todos os logs
        logs = []
        if os.path.exists("logs_atendimento.jsonl"):
            with open("logs_atendimento.jsonl", "r", encoding="utf-8") as f:
                logs = [json.loads(linha) for linha in f if linha.strip()]
        
        # Encontrar e atualizar o log correspondente (último matching)
        for i in range(len(logs) - 1, -1, -1):
            if logs[i].get("pergunta_usuario") == pergunta and logs[i].get("resposta_bot") == resposta:
                logs[i]["avaliacao"] = avaliacao
                break
        
        # Reescrever o arquivo
        with open("logs_atendimento.jsonl", "w", encoding="utf-8") as f:
            for log in logs:
                f.write(json.dumps(log, ensure_ascii=False) + "\n")
        
        return True
    except Exception as e:
        print(f"[ERRO AO ATUALIZAR AVALIAÇÃO] {e}")
        return False

def efeito_digitacao(texto):
    """Exibe texto com efeito de digitação (streaming)."""
    placeholder = st.empty()
    texto_acumulado = ""
    
    for char in texto:
        texto_acumulado += char
        placeholder.markdown(texto_acumulado)
        time.sleep(0.01)
    
    return texto_acumulado

@st.cache_resource(show_spinner="🔄 Carregando Base de Conhecimento...")
def inicializar_rag():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pasta_documentos = os.path.join(base_dir, "documentos_rh")
    caminho_txt_fallback = os.path.join(base_dir, "conhecimento_rh.txt")
    
    documentos = []
    
    # Verificar se a pasta documentos_rh existe e tem arquivos
    if os.path.exists(pasta_documentos) and os.path.isdir(pasta_documentos):
        # Buscar todos os arquivos PDF na pasta
        arquivos_pdf = glob(os.path.join(pasta_documentos, "*.pdf"))
        
        # Buscar todos os arquivos TXT na pasta
        arquivos_txt = glob(os.path.join(pasta_documentos, "*.txt"))
        
        # Carregar todos os PDFs encontrados
        for arquivo_pdf in arquivos_pdf:
            try:
                loader = PyPDFLoader(arquivo_pdf)
                documentos.extend(loader.load())
                print(f"[INFO] PDF carregado: {os.path.basename(arquivo_pdf)}")
            except Exception as e:
                print(f"[ERRO] Falha ao carregar PDF {arquivo_pdf}: {e}")
        
        # Carregar todos os TXTs encontrados
        for arquivo_txt in arquivos_txt:
            try:
                loader = TextLoader(arquivo_txt, encoding="utf-8")
                documentos.extend(loader.load())
                print(f"[INFO] TXT carregado: {os.path.basename(arquivo_txt)}")
            except Exception as e:
                print(f"[ERRO] Falha ao carregar TXT {arquivo_txt}: {e}")
    
    # Fallback: se nenhum documento foi carregado, usar o arquivo TXT da raiz
    if not documentos:
        print("[INFO] Nenhum documento encontrado em documentos_rh/. Usando fallback: conhecimento_rh.txt")
        if os.path.exists(caminho_txt_fallback):
            loader = TextLoader(caminho_txt_fallback, encoding="utf-8")
            documentos = loader.load()
        else:
            raise FileNotFoundError(
                "Nenhum documento encontrado! Crie a pasta 'documentos_rh' com arquivos PDF/TXT "
                "ou adicione o arquivo 'conhecimento_rh.txt' na raiz do projeto."
            )
    
    print(f"[INFO] Total de documentos carregados: {len(documentos)}")
    
    # Processar documentos e criar VectorStore
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150, length_function=len)
    chunks = text_splitter.split_documents(documentos)
    
    print(f"[INFO] Total de chunks gerados: {len(chunks)}")
    
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    vector_store = FAISS.from_documents(chunks, embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    
    template = """Você é o Demà, o assistente virtual de RH da Renapsi, especializado em tirar dúvidas gerais dos Jovens Aprendizes (como Vale-Transporte, Folha Ponto, Férias, etc.). Você é acolhedor, prestativo e sempre disposto a ajudar os jovens aprendizes com suas dúvidas.

PERSONALIDADE E TOM:
- Seja educado, cordial e empático em todas as respostas
- Elabore suas respostas de forma clara e completa, explicando os detalhes importantes
- Use uma linguagem acessível, mas profissional
- Sempre finalize suas respostas perguntando se pode ajudar em algo mais ou se despedindo de forma amigável
- Demonstre interesse genuíno em resolver a dúvida do jovem aprendiz
- Sempre que precisar fornecer um link ou URL, formate-o OBRIGATORIAMENTE em Markdown clicável (exemplo: [Nome do Site](https://exemplo.com)). Nunca deixe URLs soltas no meio do texto.

REGRAS DE CONDUTA E SEGURANÇA:
1. CORTESIA LIBERADA: Se o jovem aprendiz enviar apenas saudações, aja de forma amigável, apresente-se como Demà e pergunte como pode ajudar com dúvidas de RH.
2. FLUIDEZ DE CONVERSA: Se o historico_da_conversa não estiver vazio, NUNCA repita saudações iniciais ou apresentações.
3. INTELIGÊNCIA SEMÂNTICA: Entenda as gírias e formas de falar dos jovens.
4. RIGOR NOS DADOS: Para responder sobre regras, prazos, procedimentos e políticas de RH, você DEVE usar APENAS as informações das tags contexto. Elabore a resposta de forma completa e didática.
5. O LIMITE DA IA: Se a pergunta for sobre RH e a resposta definitivamente NÃO estiver no contexto, você deve responder de forma educada: 'Não possuo essa informação específica nos meus manuais no momento. Para essa dúvida, recomendo que você entre em contato diretamente com o RH, que poderá te ajudar com mais detalhes. Posso ajudar com alguma outra questão? 😊'

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
    retriever = vector_store.as_retriever(search_kwargs={"k": 10})
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    rag_chain = (
        {
            "context": lambda x: format_docs(retriever.invoke(x["question"])), 
            "question": lambda x: x["question"], 
            "chat_history": lambda x: x["chat_history"]
        } 
        | prompt 
        | llm 
        | StrOutputParser()
    )
    
    return rag_chain

if not st.session_state.autenticado:
    tela_login()
else:
    with st.sidebar:
        st.title("🏢 Renapsi - IA")
        st.markdown("---")
        st.markdown("**Bot especialista em RH e dúvidas gerais do Jovem Aprendiz**")
        st.markdown("---")
        if st.button("🗑️ Limpar Histórico da Conversa", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        st.markdown("---")
        st.caption("💡 Seja específico em suas perguntas.")
        st.markdown("---")
        st.caption("v1.2.0-stable | Build 2026")

    st.title("Assistente Virtual - Demà")
    st.caption("Tire suas dúvidas sobre Vale-Transporte, Folha Ponto, Férias e outros assuntos de RH.")
    st.info("💡 Experimente perguntar: Como gerar minha folha ponto?, Preciso da 2ª via do meu cartão Guarupass, ou Como enviar meu atestado?")
    st.markdown("---")

    try:
        rag_chain = inicializar_rag()
    except Exception as e:
        st.error(f"❌ Erro ao inicializar sistema: {e}")
        st.stop()

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "Olá, Jovem Aprendiz! 👋 Como posso ajudar com suas dúvidas de RH hoje?"})
    
    if "feedback_dado" not in st.session_state:
        st.session_state.feedback_dado = set()  # Armazena índices das mensagens que já receberam feedback

    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Adicionar botões de feedback apenas para respostas do assistente (exceto a primeira saudação)
            if message["role"] == "assistant" and idx > 0 and idx not in st.session_state.feedback_dado:
                col1, col2, col3 = st.columns([1, 1, 4])
                
                with col1:
                    if st.button("👍 Útil", key=f"positivo_{idx}", use_container_width=True):
                        # Buscar a pergunta correspondente (mensagem anterior)
                        pergunta = st.session_state.messages[idx - 1]["content"] if idx > 0 else ""
                        resposta = message["content"]
                        
                        if atualizar_avaliacao_log(pergunta, resposta, "positivo"):
                            st.session_state.feedback_dado.add(idx)
                            st.toast("✅ Obrigado pelo feedback positivo!", icon="👍")
                            time.sleep(0.5)
                            st.rerun()
                
                with col2:
                    if st.button("👎 Não ajudou", key=f"negativo_{idx}", use_container_width=True):
                        # Buscar a pergunta correspondente (mensagem anterior)
                        pergunta = st.session_state.messages[idx - 1]["content"] if idx > 0 else ""
                        resposta = message["content"]
                        
                        if atualizar_avaliacao_log(pergunta, resposta, "negativo"):
                            st.session_state.feedback_dado.add(idx)
                            st.toast("📝 Obrigado pelo feedback! Vamos melhorar.", icon="👎")
                            time.sleep(0.5)
                            st.rerun()
            
            # Mostrar mensagem de agradecimento se feedback já foi dado
            elif message["role"] == "assistant" and idx > 0 and idx in st.session_state.feedback_dado:
                st.caption("✅ Feedback registrado. Obrigado!")

    if prompt := st.chat_input("Digite sua dúvida aqui..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("🔍 Consultando manuais da Renapsi..."):
                # Configuração de retry automático
                max_tentativas = 3
                resposta = None
                erro_final = None
                
                for tentativa in range(1, max_tentativas + 1):
                    try:
                        historico_formatado = ""
                        if len(st.session_state.messages) > 1:
                            for msg in st.session_state.messages[-5:-1]:
                                role = "Jovem Aprendiz" if msg["role"] == "user" else "Demà"
                                historico_formatado += f"{role}: {msg['content']}\n"
                        
                        # Tentar invocar a chain
                        resposta = rag_chain.invoke({"question": prompt, "chat_history": historico_formatado})
                        
                        # Se chegou aqui, a chamada foi bem-sucedida
                        efeito_digitacao(resposta)
                        st.session_state.messages.append({"role": "assistant", "content": resposta})
                        salvar_log(prompt, resposta)
                        st.rerun()  # Recarrega a tela para exibir os botões de feedback
                        break  # Sai do loop se bem-sucedido
                        
                    except Exception as e:
                        erro_final = e
                        print(f"\n[TENTATIVA {tentativa}/{max_tentativas} FALHOU] {e}\n")
                        
                        # Se não for a última tentativa, aguarda antes de tentar novamente
                        if tentativa < max_tentativas:
                            print(f"[AGUARDANDO 2 SEGUNDOS ANTES DA PRÓXIMA TENTATIVA...]\n")
                            time.sleep(2)
                        else:
                            # Última tentativa falhou - exibir mensagem de erro
                            print(f"\n[ERRO CRÍTICO] Todas as {max_tentativas} tentativas falharam.\n")
                            erro_msg = "Ops! Nossos sistemas estão com alto volume de acessos no momento. Por favor, aguarde um minutinho e tente enviar sua dúvida novamente! 🔄"
                            st.warning(erro_msg)
                            st.session_state.messages.append({"role": "assistant", "content": erro_msg})

    st.markdown("---")
    st.caption("🤖 Powered by LangChain + Google Gemini 2.5 Flash | Renapsi © 2026")
