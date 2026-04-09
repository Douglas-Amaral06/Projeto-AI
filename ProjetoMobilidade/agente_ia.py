import os
from dotenv import load_dotenv
import google.generativeai as genai

# Abre o cofre (.env) invisível
load_dotenv()

# Puxa a chave de forma segura
CHAVE_API = os.getenv("GEMINI_API_KEY") 

if CHAVE_API:
    genai.configure(api_key=CHAVE_API)

def analisar_rota_com_ia(rua_casa, rua_trab, distancia_km, tempo_min, valor_diario, trajeto):
    if not CHAVE_API:
        return "⚠️ Chave de API não encontrada no arquivo .env."

    modelo = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Você é um especialista em mobilidade urbana e RH em São Paulo.
    Analise a seguinte rota proposta para um jovem aprendiz:
    - Origem: {rua_casa}
    - Destino: {rua_trab}
    - Distância Real: {distancia_km:.1f} km
    - Tempo Estimado: {tempo_min:.0f} minutos
    - Trajeto Sugerido: {trajeto}
    - Custo Diário: R$ {valor_diario:.2f}

    Diga em 1 parágrafo curto e direto: Essa rota faz sentido para a realidade de São Paulo? O tempo e o custo estão justos para a empresa e para o funcionário? 
    Sugira rapidamente se há alguma alternativa lógica (ex: 'Pela distância curta, uma bicicleta seria ideal' ou 'Uso de CPTM seria mais rápido').
    Mantenha o tom profissional e focado em eficiência.
    """
    
    try:
        resposta = modelo.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"Erro ao consultar a IA: {e}"