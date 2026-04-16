import os
import time
import logging
import warnings
from dotenv import load_dotenv

# Suprime o FutureWarning da biblioteca deprecada
warnings.filterwarnings("ignore", category=FutureWarning, module="google")

import google.generativeai as genai

logger = logging.getLogger(__name__)
load_dotenv()

CHAVE_API = os.getenv("GEMINI_API_KEY")

if CHAVE_API:
    genai.configure(api_key=CHAVE_API)

# Modelos em ordem de fallback (mais leve primeiro para economizar quota)
_MODELOS_FALLBACK = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.0-pro",
]


def _tentar_gerar(prompt: str, tentativas: int = 10) -> str:
    """Tenta gerar conteúdo com fallback entre modelos e retry em 429."""
    if not CHAVE_API:
        return "⚠️ Chave de API não encontrada no arquivo .env."

    for modelo_nome in _MODELOS_FALLBACK:
        for tentativa in range(tentativas):
            try:
                modelo = genai.GenerativeModel(modelo_nome)
                resposta = modelo.generate_content(prompt)
                return resposta.text
            except Exception as e:
                msg = str(e)
                if "429" in msg or "quota" in msg.lower() or "rate" in msg.lower():
                    # Extrai tempo de espera sugerido pela API
                    espera = 60
                    try:
                        import re
                        match = re.search(r'seconds["\s:]+(\d+)', msg)
                        if match:
                            espera = min(int(match.group(1)), 120)
                    except Exception:
                        pass

                    if tentativa < tentativas - 1:
                        logger.warning(
                            f"Quota excedida ({modelo_nome}). "
                            f"Aguardando {espera}s... (tentativa {tentativa+1}/{tentativas})"
                        )
                        time.sleep(espera)
                    else:
                        logger.warning(f"Quota esgotada em {modelo_nome}. Tentando próximo modelo.")
                        break  # vai para o próximo modelo
                else:
                    logger.exception(f"Erro ao consultar modelo {modelo_nome}: {e}")
                    # Não retorna erro, continua tentando outros modelos
                    break

    # Retorna análise padrão se todos os modelos falharem
    return "Análise automática: Recomenda-se avaliar as opções considerando o equilíbrio entre custo e tempo de deslocamento. A opção de integração geralmente oferece melhor custo-benefício."


def analisar_rota_com_ia(rua_casa, rua_trab, distancia_km, rotas, info_tarifas):
    if not CHAVE_API:
        return "⚠️ Chave de API não encontrada no arquivo .env."

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
    return _tentar_gerar(prompt)
