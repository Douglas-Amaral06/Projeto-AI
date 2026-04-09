import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
CHAVE_API = os.getenv("GEMINI_API_KEY") 

if CHAVE_API:
    genai.configure(api_key=CHAVE_API)

def analisar_rota_com_ia(rua_casa, rua_trab, distancia_km, rotas, info_tarifas):
    if not CHAVE_API:
        return "⚠️ Chave de API não encontrada no arquivo .env."

    modelo = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Você é um Analista de RH e Mobilidade Urbana em São Paulo.
    O sistema gerou 3 opções de rotas de Vale-Transporte para um aprendiz:
    
    - Origem: {rua_casa}
    - Destino: {rua_trab}
    - Distância Real de carro: {distancia_km:.1f} km

    Opções de Deslocamento Diário (Ida e Volta inclusas):
    1) {rotas[0]['modal']} - Tempo: {rotas[0]['tempo']} por trecho | Custo Diário: R$ {rotas[0]['valor_diario']:.2f}
    2) {rotas[1]['modal']} - Tempo: {rotas[1]['tempo']} por trecho | Custo Diário: R$ {rotas[1]['valor_diario']:.2f}
    3) {rotas[2]['modal']} - Tempo: {rotas[2]['tempo']} por trecho | Custo Diário: R$ {rotas[2]['valor_diario']:.2f}

    Tabela Base SP: {info_tarifas}

    Sua tarefa em 1 parágrafo curto: 
    Compare o Tempo vs. Custo das opções e recomende A MELHOR OPÇÃO para a empresa (economia) e para o aprendiz (saúde/tempo). Seja direto na escolha.
    """
    
    try:
        resposta = modelo.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"Erro ao consultar a IA: {e}"