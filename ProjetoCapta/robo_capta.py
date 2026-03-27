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

navegador.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[4]/div[1]/div/div/div/input').send_keys("41350968838")
time.sleep(2)

#Implementar a senha
navegador.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[4]/div[2]/div/div/input').send_keys("47824729")
time.sleep(2)

#Clicar no botão de login
navegador.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[5]/div[1]/button').click()

#Retornar mensagem de sucesso
print("✅ Login realizado com sucesso! Logando na Capta...")

# Pausa de 10 segundos para o processo de login ser concluído
time.sleep(10)

#Acessar a roteirização

navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/aside/nav/div[3]/div/h2/button/div').click()
time.sleep(2)