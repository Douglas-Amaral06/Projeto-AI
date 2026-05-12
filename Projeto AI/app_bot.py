"""
Bot Especialista de Atendimento RAG - Renapsi
MVP para atendimento automatizado de dúvidas sobre Vale-Transporte
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Carregar variáveis de ambiente
load_dotenv()


def carregar_base_conhecimento(caminho_arquivo="conhecimento_rh.txt"):
    """
    Carrega e processa a base de conhecimento em chunks.
    
    Args:
        caminho_arquivo: Caminho para o arquivo de conhecimento
        
    Returns:
        Lista de chunks processados
    """
    print(f"📄 Carregando base de conhecimento: {caminho_arquivo}")
    
    # Carregar o documento
    loader = TextLoader(caminho_arquivo, encoding="utf-8")
    documentos = loader.load()
    
    # Dividir em chunks menores para melhor recuperação
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        length_function=len
    )
    chunks = text_splitter.split_documents(documentos)
    
    print(f"✅ Base carregada: {len(chunks)} chunks criados")
    return chunks


def criar_vector_store(chunks):
    """
    Cria o vector store FAISS com embeddings multilíngue otimizado para PT-BR.
    """
    print("🧠 Criando embeddings multilíngue (PT-BR) e vector store FAISS...")
    
    # Modelo multilíngue otimizado para português
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    # Criar vector store local com FAISS
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    print("✅ Vector store criado com sucesso (Multilingual Mode)")
    return vector_store


def configurar_llm_e_chain(vector_store):
    """
    Configura a LLM (Gemini) e cria a chain de recuperação com prompt rigoroso.
    
    Args:
        vector_store: Vector store FAISS inicializado
        
    Returns:
        Chain de QA configurada
    """
    print("🤖 Configurando LLM e prompt system...")
    
    # Instanciar Gemini com temperature=0 para evitar alucinações
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0  # Zero criatividade - apenas fatos da base
    )
    
    # Prompt BLINDADO com XML tags para grounding absoluto
    template = """Você é um assistente virtual ESTRITAMENTE LIMITADO da Renapsi, responsável por tirar dúvidas de Vale-Transporte.

INSTRUÇÕES DE SEGURANÇA ABSOLUTAS:
1. Você deve basear sua resposta EXCLUSIVAMENTE nas informações contidas dentro das tags <contexto>.
2. É PROIBIDO usar seu conhecimento externo ou mencionar cartões específicos (como TOP, BOM, Bilhete Único) a menos que estejam no <contexto>.
3. Se a resposta para a <pergunta> não puder ser deduzida apenas lendo o <contexto>, você deve responder EXATAMENTE: 'Não possuo essa informação nos meus manuais, por favor procure o RH.'

<contexto>
{context}
</contexto>

<pergunta>
{question}
</pergunta>

Resposta:"""
    
    # Criar o prompt template
    prompt = PromptTemplate.from_template(template)
    
    # Criar retriever com janela ampliada de contexto
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    
    # Criar a chain RAG usando LCEL com DEBUG do contexto
    def format_docs(docs):
        context_str = "\n\n".join(doc.page_content for doc in docs)
        print("\n[DEBUG] Contexto recuperado pelo FAISS:\n", context_str[:200], "...\n")
        return context_str
    
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print("✅ LLM e chain configurados com sucesso")
    return rag_chain


def main():
    """Função principal do bot"""
    print("=" * 60)
    print("BOT ESPECIALISTA RENAPSI - VALE-TRANSPORTE")
    print("=" * 60)
    print("\nInicializando sistema RAG...")
    
    try:
        # Verificar se a API key está configurada
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY não encontrada no arquivo .env")
        
        # Pipeline RAG - Etapa de Ingestão
        chunks = carregar_base_conhecimento()
        vector_store = criar_vector_store(chunks)
        
        # Configurar LLM e Chain
        rag_chain = configurar_llm_e_chain(vector_store)
        
        print("\n✅ Sistema RAG totalmente inicializado!")
        print("📊 Bot pronto para atendimento")
        print("💬 Digite 'sair' para encerrar o atendimento\n")
        print("=" * 60)
        
        # Loop de Interação - Interface Terminal
        while True:
            try:
                # Capturar pergunta do usuário
                pergunta = input("\nJovem Aprendiz: ").strip()
                
                # Verificar comando de saída
                if pergunta.lower() == 'sair':
                    print("\n👋 Encerrando atendimento. Até logo!")
                    break
                
                # Ignorar entradas vazias
                if not pergunta:
                    continue
                
                # Invocar a chain RAG (LCEL usa invoke direto com a pergunta)
                resposta = rag_chain.invoke(pergunta)
                
                # Exibir resposta do bot
                print(f"\nBot Renapsi: {resposta}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Atendimento interrompido. Até logo!")
                break
            except Exception as e:
                print(f"\n⚠️ Erro ao processar pergunta: {e}")
                print("Por favor, tente novamente ou digite 'sair' para encerrar.")
        
    except FileNotFoundError:
        print("❌ Erro: Arquivo 'conhecimento_rh.txt' não encontrado")
    except ValueError as e:
        print(f"❌ Erro de configuração: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

    
if __name__ == "__main__":
    main()
