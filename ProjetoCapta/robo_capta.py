from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

print("🚀 Iniciando o Robôzinho da Roteirização CaptaVT ")

# Configuração do Selenium para abrir o navegador (Chrome)
servico = Service(ChromeDriverManager().install())
navegador = webdriver.Chrome(service=servico) #lembrar de definir Chrome como padrão

# Sobe no site
link_login = "https://app.captamobilidade.com.br/" # (Link raiz para o site de login da Capta)
navegador.get(link_login)

# Pausa de 10 segundos para fazer o login manualmente (caso necessário  )
time.sleep(10)