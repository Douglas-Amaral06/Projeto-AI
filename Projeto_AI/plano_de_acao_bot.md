# Projeto: Bot Especialista de Atendimento (RAG) - Renapsi

## Visão Geral
Este projeto é a Fase 2 do ecossistema de Ficheiro e Roteirização. Trata-se de um MVP de um bot de atendimento em Python focado em resolver chamados de nível 1 (dúvidas sobre Vale-Transporte, recargas, saldos e bloqueios) para jovens aprendizes. 
O bot utiliza a arquitetura RAG (Retrieval-Augmented Generation) para garantir que as respostas sejam extraídas ESTRITAMENTE da base de conhecimento da empresa, sem alucinações.

## Arquitetura e Stack Tecnológico
- **Linguagem:** Python
- **Orquestração:** LangChain
- **LLM:** Google Gemini (via `langchain-google-genai`)
- **Vector Store:** FAISS (local)
- **Interface atual:** Terminal/CLI (para validação do MVP)

## Próximos Passos (A serem executados pelo Assistente AI)

O assistente de IA da IDE deve seguir estes passos sequencialmente, aguardando validação do desenvolvedor entre as etapas críticas:

1. **Configuração de Dependências:**
   - Verificar ou criar o arquivo `requirements.txt` incluindo: `langchain-google-genai`, `langchain`, `langchain-community`, `faiss-cpu`, `pypdf`.
   - Instruir o desenvolvedor sobre o comando de instalação.

2. **Estruturação do Diretório:**
   - Garantir a existência do script principal (ex: `app_bot.py`).
   - Garantir a existência do arquivo de base de conhecimento (`conhecimento_rh.txt`), populando-o com dados de exemplo sobre recarga e saldo se estiver vazio.

3. **Implementação do Pipeline RAG:**
   - Desenvolver a função de ingestão: carregar o `.txt` e aplicar o `RecursiveCharacterTextSplitter`.
   - Configurar os embeddings usando `GoogleGenerativeAIEmbeddings`.
   - Inicializar o banco FAISS localmente a partir dos chunks gerados.

4. **Configuração da LLM e Prompt System (Grounding):**
   - Instanciar o `GoogleGenerativeAI` com `temperature=0` para evitar criatividade fora do escopo.
   - Criar um `PromptTemplate` rigoroso que instrua a IA a:
     - Usar APENAS o contexto fornecido.
     - Responder que "não possui a informação" caso o dado não esteja no contexto.
     - Manter um tom profissional e acolhedor, adequado aos jovens da Renapsi.

5. **Loop de Interação e Teste:**
   - Criar o loop `while True:` no terminal para simular o chat contínuo.
   - Tratar exceções básicas (ex: chave de API ausente, arquivo não encontrado).