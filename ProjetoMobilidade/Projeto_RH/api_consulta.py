import os
import sqlite3
import requests
import time

# 1. Conectando no seu banco de dados
conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
cursor = conexao.cursor()

# 2. Puxando as informações do Porta-Malas
cursor.execute("SELECT nome, cep_casa FROM jovens_rotas")
jovens = cursor.fetchall() # Isso traz uma lista com todos os jovens

print("🔎 Iniciando consulta de CEPs via API (ViaCEP)...\n")

# 3. O Loop da API (O Garçom trabalhando)
for jovem in jovens:
    nome = jovem[0]
    cep = jovem[1]
    
    print(f"Buscando endereço do(a) {nome} (CEP: {cep})...")
    
    # Montando a URL para a API (Consulta o CEP no VIACEP)
    url = f"https://viacep.com.br/ws/{cep}/json/"
    
    try:
        # Fazendo a requisição GET (O Python chamando a API)
        resposta = requests.get(url)
        
        # Lendo a bandeja que o garçom trouxe (Vem no formato JSON)
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
