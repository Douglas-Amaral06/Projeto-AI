# Requisitos: Atualização do Loader RAG (TXT para PDF)

## Contexto Atual
Nosso aplicativo Streamlit (`app_web.py`) utiliza o LangChain e o Google Gemini 2.5 Flash para um sistema RAG (Retrieval-Augmented Generation). Atualmente, a base de conhecimento é carregada via `TextLoader` a partir de um arquivo chamado `conhecimento_rh.txt`.

## Objetivo da Atualização
A diretoria enviará a documentação oficial formatada. Precisamos preparar o sistema para ler arquivos `.pdf` de forma fluida, sem quebrar o aplicativo caso o PDF ainda não esteja na pasta.

## Regras de Negócio (Lógica do Fallback)
1. A função responsável pela carga dos dados (ex: `inicializar_rag()`) deve procurar primeiro por um arquivo chamado `conhecimento_rh.pdf`.
2. Se o `.pdf` existir, o sistema deve utilizar o `PyPDFLoader` para extrair os documentos.
3. Se o `.pdf` NÃO existir, o sistema deve fazer um "fallback" (plano B) e carregar o arquivo antigo `conhecimento_rh.txt` usando o `TextLoader` atual.
4. O processo de separação de texto (`CharacterTextSplitter` ou `RecursiveCharacterTextSplitter`) e criação do VectorStore (`FAISS`) deve continuar funcionando normalmente, independentemente de a origem ser PDF ou TXT.