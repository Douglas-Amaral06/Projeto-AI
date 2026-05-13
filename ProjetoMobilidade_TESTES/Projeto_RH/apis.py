import requests
import random
from functools import lru_cache
import hashlib

# Cache para evitar chamadas repetidas às APIs
@lru_cache(maxsize=100)
def buscar_endereco_viacep(cep):
    cep_limpo = ''.join(filter(str.isdigit, str(cep)))
    if len(cep_limpo) != 8:
        return {"rua": "CEP Inválido", "bairro": "", "cidade_uf": "", "completo": "CEP Inválido"}
        
    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
    try:
        resposta = requests.get(url, timeout=5).json()
        if "erro" not in resposta:
            return {
                "rua": resposta.get('logradouro', 'N/A'),
                "bairro": resposta.get('bairro', 'N/A'),
                "cidade_uf": f"{resposta.get('localidade', 'N/A')} - {resposta.get('uf', 'N/A')}",
                "completo": f"{resposta.get('logradouro')}, {resposta.get('bairro')} - {resposta.get('localidade')}/{resposta.get('uf')}"
            }
    except Exception as e:
        print(f"Erro ao buscar CEP {cep_limpo}: {e}")
    return {"rua": "Endereço não encontrado", "bairro": "", "cidade_uf": "", "completo": "Não encontrado"}

def extrair_coordenadas(coord_str, default_lat, default_lon):
    if not coord_str:
        return default_lat, default_lon
    try:
        parts = coord_str.replace(" ", "").split(",")
        if len(parts) == 2:
            return float(parts[0]), float(parts[1])
    except:
        pass
    return default_lat, default_lon

def obter_coordenadas_reais(endereco_texto):
    """Obtém coordenadas via Nominatim SEM cache para garantir precisão."""
    # REMOVIDO @lru_cache para evitar coordenadas erradas em cache
    url = f"https://nominatim.openstreetmap.org/search?q={endereco_texto}&format=json&limit=1"
    headers = {'User-Agent': 'Renapsi_Routing_App'} 
    try:
        print(f"🔍 Buscando coordenadas para: '{endereco_texto}'")
        r = requests.get(url, headers=headers, timeout=5).json()
        if r and len(r) > 0:
            lat = float(r[0]['lat'])
            lon = float(r[0]['lon'])
            print(f"✅ Coordenadas encontradas: LAT={lat}, LON={lon}")
            return lat, lon
        else:
            print(f"⚠️ Nenhum resultado encontrado para '{endereco_texto}'")
    except Exception as e:
        print(f"❌ Erro ao buscar coordenadas para '{endereco_texto}': {e}")
    return None, None

def motor_de_rotas_gratuito(end_casa, end_trab):
    """
    Calcula rotas entre casa e trabalho com coordenadas REAIS.
    end_casa e end_trab devem ser endereços completos (rua, bairro, cidade).
    Retorna também o tempo de execução (SLA) em segundos.
    """
    import time
    tempo_inicio = time.time()  # Inicia cronômetro
    
    print(f"\n{'='*60}")
    print(f"🏠 ENDEREÇO CASA: {end_casa}")
    print(f"🏢 ENDEREÇO TRABALHO: {end_trab}")
    print(f"{'='*60}\n")
    
    # Obtém coordenadas reais (SEM cache para evitar erros)
    lat_c, lon_c = obter_coordenadas_reais(end_casa)
    lat_t, lon_t = obter_coordenadas_reais(end_trab)
    
    # Fallback apenas se geocoding falhar completamente
    if not lat_c or not lon_c:
        print(f"⚠️ FALLBACK: Usando coordenadas padrão para CASA")
        lat_c, lon_c = -23.5505, -46.6333
    
    if not lat_t or not lon_t:
        print(f"⚠️ FALLBACK: Usando coordenadas padrão para TRABALHO")
        lat_t, lon_t = -23.5874, -46.6576
    
    print(f"\n📍 COORDENADAS FINAIS:")
    print(f"   Casa (C): LAT={lat_c}, LON={lon_c}")
    print(f"   Trabalho (T): LAT={lat_t}, LON={lon_t}\n")
    
    # OSRM usa ordem: longitude, latitude (diferente do folium!)
    url_osrm = f"http://router.project-osrm.org/route/v1/driving/{lon_c},{lat_c};{lon_t},{lat_t}?overview=false"
    distancia_km = 0.0
    tempo_carro_vazio = 0.0
    
    try:
        r_osrm = requests.get(url_osrm, timeout=3).json()
        if r_osrm.get("code") == "Ok":
            distancia_km = r_osrm["routes"][0]["distance"] / 1000 
            tempo_carro_vazio = r_osrm["routes"][0]["duration"] / 60 
            print(f"✅ Rota calculada: {distancia_km:.2f} km, {tempo_carro_vazio:.1f} min")
    except Exception as e:
        print(f"⚠️ Erro no OSRM, usando valores padrão: {e}")
        distancia_km, tempo_carro_vazio = 10.0, 30.0 
        
    # ==========================================
    # 💰 TABELA DE TARIFAS VALE-TRANSPORTE (2026)
    # ==========================================
    TARIFA_ONIBUS_VT = 5.82
    TARIFA_METRO_VT = 5.92
    TARIFA_INTEGRACAO_VT = 11.32
    
    # 3 Opções de rotas (simuladas)
    rotas = [
        {
            "modal": "🚌 Apenas Ônibus",
            "trajeto": "Ônibus Municipal (SPTrans)",
            "valor_diario": TARIFA_ONIBUS_VT * 2,
            "tempo": f"{int((tempo_carro_vazio * 2.5) + 15)} min",
            "bilhete": "SPTrans VT (Ônibus)"
        },
        {
            "modal": "🚇 Apenas Metrô/CPTM",
            "trajeto": "Sistema Metroferroviário",
            "valor_diario": TARIFA_METRO_VT * 2,
            "tempo": f"{int((tempo_carro_vazio * 0.8) + 20)} min",
            "bilhete": "SPTrans VT (Metrô)"
        },
        {
            "modal": "🔄 Integração",
            "trajeto": "Ônibus + Metrô/CPTM",
            "valor_diario": TARIFA_INTEGRACAO_VT * 2,
            "tempo": f"{int((tempo_carro_vazio * 1.2) + 10)} min",
            "bilhete": "SPTtrans VT (Integração Ônibus+Metrô)"
        }
    ]

    # Se for muito perto, substitui a opção de integração por caminhada
    if distancia_km <= 2.0:
        rotas[2] = {
            "modal": "🚶 Caminhada",
            "trajeto": "A pé (Curta distância)",
            "valor_diario": 0.00,
            "tempo": f"{int(distancia_km * 12)} min",
            "bilhete": "Nenhum"
        }

    # Calcula tempo de execução (SLA)
    tempo_fim = time.time()
    sla_segundos = tempo_fim - tempo_inicio
    print(f"⏱️ Tempo de processamento (SLA): {sla_segundos:.2f} segundos\n")

    return {
        "rotas": rotas, 
        "distancia_km": distancia_km,
        "coords_reais": [(lat_c, lon_c), (lat_t, lon_t)],  # Formato: [(lat_casa, lon_casa), (lat_trab, lon_trab)]
        "info_tarifas": f"Ônibus VT: R${TARIFA_ONIBUS_VT} | Metrô VT: R${TARIFA_METRO_VT} | Integração VT: R${TARIFA_INTEGRACAO_VT}",
        "sla_segundos": sla_segundos  # Tempo de execução em segundos
    }