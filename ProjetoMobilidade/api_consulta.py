import sqlite3
import requests
import time

# Conecta no banco de dados
conexao = sqlite3.connect('mobilidade_renapsi.db')
cursor = conexao.cursor()

# Puxa as informações do banco
cursor.execute("SELECT nome, cep_casa FROM jovens_rotas")
jovens = cursor.fetchall() # Isso traz uma lista com todos os jovens

print("🔎 Iniciando consulta de CEPs via API (ViaCEP)...\n")

# 3. O Loop da API - Para cada jovem, pega o nome e o CEP, consulta a API e imprime o resultado
for jovem in jovens:
    nome = jovem[0]
    cep = jovem[1]
    
    print(f"Buscando endereço do(a) {nome} (CEP: {cep})...")
    
    # Monta a URL para a API 
    url = f"https://viacep.com.br/ws/{cep}/json/"
    
    try:
        # Fazendo a requisição GET (O Python chamando a API)
        resposta = requests.get(url)
        
        # Transforma a resposta em um dicionário (JSON -> Dicionário Python)
        dados = resposta.json()
        
        # Checando se a API retornou erro (CEP inválido)
        if "erro" not in dados:
            rua = dados.get('logradouro', 'Sem rua')
            bairro = dados.get('bairro', 'Sem bairro')
            cidade = dados.get('localidade', 'Sem cidade')
            estado = dados.get('uf', 'Sem UF')
            
            print(f"✅ Encontrado! Endereço: {rua}, {bairro} - {cidade}/{estado}\n")
        else:
            print(f"❌ O CEP {cep} não existe na base dos Correios.\n")
            
    except Exception as e:
        print(f"⚠️ Erro ao consultar a API: {e}\n")
    
    # Pausa rápida (Regra de etiqueta: não metralhar APIs gratuitas)
    time.sleep(1)

# Fecha a conexão
conexao.close()
print("🎯 Consultas finalizadas!")