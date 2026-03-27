from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

print("🚀 Iniciando o Robôzinho da Roteirização CaptaVT ")

# Configuração do Selenium para abrir o navegador (Chrome)
servico = Service(ChromeDriverManager().install())
navegador = webdriver.Chrome(service=servico) #lembrar de definir Chrome como padrão

# Sobe no site
link_login = "https://app.captamobilidade.com.br/" # (Link raiz para o site de login da Capta)
navegador.get(link_login)

navegador.maximize_window() # F11 no google

# Pausa de 10 segundos para fazer o login manualmente (caso necessário  )
time.sleep(10)

#Implementar o CPF

navegador.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[4]/div[1]/div/div/div/input').send_keys("49742274835")
time.sleep(2)