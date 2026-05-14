import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# 1. Carrega as variáveis de ambiente / 
load_dotenv()

def iniciar_bot():
    # 2. Carrega os arquivo de conhecimento da IA (conhecimentos dentro do .txt)
    loader = TextLoader("conhecimento_rh.txt", encoding="utf-8")
    documentos = loader.load()

    # 3. Chunking (Divisão do texto em partes menores) chunks = renderização (igualno mine )
    # Cria uns blocos de 500 caracteres com uma sobreposição para não perder contexto --
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documentos)

    # 4. Criação dos Embeddings e Vector Store (Cérebro do Bot)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_documents(chunks, embeddings)

    # 5. Configuração do Modelo (Gemini) - API gratuita 2.5 flash
    llm = GoogleGenerativeAI(model="gemini-pro", temperature=0) # Temp 0 = Menos alucinação

    # 6. Criação do Prompt Customizado 
    template = """Você é um assistente virtual especializado em RH da Renapsi.
    Use os seguintes pedaços de contexto para responder à pergunta do jovem aprendiz.
    Se você não sabe a resposta com base no contexto abaixo, diga apenas que não tem essa informação e peça para ele falar com o supervisor. 
    NÃO tente inventar respostas. Seja direto e profissional.

    Contexto: {context}
    Pergunta: {question}

    Resposta útil:"""
    
    QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

    # 7. Construção da Chain de Recuperação
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(),
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
    )

    print("--- Bot da Renapsi Ativo (Digite 'sair' para encerrar) ---")
    while True:
        pergunta = input("Jovem Aprendiz: ")
        if pergunta.lower() == 'sair':
            break
        
        resposta = qa_chain.invoke(pergunta)
        print(f"Bot RH: {resposta['result']}\n")

if __name__ == "__main__":
    iniciar_bot()