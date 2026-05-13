import os
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega a chave do seu arquivo .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Erro: Chave de API não encontrada.")
else:
    genai.configure(api_key=api_key)
    print("🔍 Buscando modelos autorizados para a sua chave...")
    print("-" * 50)
    
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
    
    print("-" * 50)