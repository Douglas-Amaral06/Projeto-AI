import requests
import random

def buscar_endereco_viacep(cep):
    cep_limpo = ''.join(filter(str.isdigit, str(cep)))
    if len(cep_limpo) != 8:
        return {"rua": "CEP Inválido", "bairro": "", "cidade_uf": "", "completo": "CEP Inválido"}
        
    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
    try:
        resposta = requests.get(url).json()
        if "erro" not in resposta:
            return {
                "rua": resposta.get('logradouro', 'N/A'),
                "bairro": resposta.get('bairro', 'N/A'),
                "cidade_uf": f"{resposta.get('localidade', 'N/A')} - {resposta.get('uf', 'N/A')}",
                "completo": f"{resposta.get('logradouro')}, {resposta.get('bairro')} - {resposta.get('localidade')}/{resposta.get('uf')}"
            }
    except Exception:
        pass
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
    url = f"https://nominatim.openstreetmap.org/search?q={endereco_texto}&format=json&limit=1"
    headers = {'User-Agent': 'Renapsi_Routing_App'} 
    try:
        r = requests.get(url, headers=headers).json()
        if r:
            return float(r[0]['lat']), float(r[0]['lon'])
    except:
        pass
    return None, None

def motor_de_rotas_gratuito(end_casa, end_trab):
    lat_c, lon_c = obter_coordenadas_reais(end_casa)
    lat_t, lon_t = obter_coordenadas_reais(end_trab)
    
    if not lat_c: lat_c, lon_c = -23.5505, -46.6333
    if not lat_t: lat_t, lon_t = -23.5874, -46.6576
    
    url_osrm = f"http://router.project-osrm.org/route/v1/driving/{lon_c},{lat_c};{lon_t},{lat_t}?overview=false"
    distancia_km = 15.0
    tempo_min = 60.0
    try:
        r_osrm = requests.get(url_osrm).json()
        if r_osrm.get("code") == "Ok":
            distancia_km = r_osrm["routes"][0]["distance"] / 1000
            tempo_min = r_osrm["routes"][0]["duration"] / 60
    except:
        pass
        
    if distancia_km <= 2.0:
        trajeto, valor, bilhete = "A pé (Curta distância)", 0.00, "Nenhum"
        tempo_final = f"{int(tempo_min * 2)} min (Caminhada)" 
    elif distancia_km <= 8.0:
        trajeto, valor, bilhete = "1 Ônibus Municipal (SPTrans)", 8.80, "Bilhete Único (Comum)"
        tempo_final = f"{int(tempo_min + 15)} min" 
    else:
        trajeto, valor, bilhete = "1 Ônibus + 1 Metrô (Integração)", 16.40, "Bilhete Único (Vale-Transporte)"
        tempo_final = f"{int(tempo_min + 20)} min"
        
    return {
        "trajeto": trajeto, "valor_diario": valor, "tempo": tempo_final,
        "bilhete": bilhete, "coords_reais": [(lat_c, lon_c), (lat_t, lon_t)]
    }

# Mantendo o simulado caso precise como backup
def roteirizar_simulado():
    return motor_de_rotas_gratuito("São Paulo, SP", "Avenida Paulista, SP")