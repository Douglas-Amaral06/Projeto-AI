import requests
import os
from dotenv import load_dotenv

# Abre o cofre
load_dotenv()

# Puxa as informações escondidas
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MENSAGEM = "Fala chefe! O Radar de Vagas tá online e pronto pro corre! 🚀"

# Monta o link da API do Telegram
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={MENSAGEM}"

# Envia a requisição
resposta = requests.get(url)

if resposta.status_code == 200:
    print("Mensagem enviada com sucesso pro seu celular!")
else:
    print(f"Deu erro: {resposta.text}")