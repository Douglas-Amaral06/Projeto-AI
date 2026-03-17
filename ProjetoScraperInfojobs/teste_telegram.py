import requests

TOKEN = "8574937481:AAG0GGV1e8Y-aok6wWSb3MlP4xoF60nRYYY"
CHAT_ID = "7930054023"
MENSAGEM = "Fala chefe! O Radar de Vagas tá online e pronto pro corre! 🚀"

# Monta o link da API do Telegram
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={MENSAGEM}"

# Envia a requisição
resposta = requests.get(url)

if resposta.status_code == 200:
    print("Mensagem enviada com sucesso pro seu celular!")
else:
    print(f"Deu erro: {resposta.text}")