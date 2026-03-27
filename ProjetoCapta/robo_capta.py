from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

#Leitor da lista de CPFS

with open('cpfs_reais.txt', 'r') as arquivo:
	cpfs = arquivo.readlines()
    
print(f"🚀 Iniciando o Robôzinho da Roteirização {len(cpfs)} CaptaVT ")

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
print("✅ Login realizado com sucesso! Acessando a Capta...")

# Pausa de 10 segundos para o processo de login ser concluído
time.sleep(10)

#Loop e contador
contador = 0
for cpf in cpfs:
    cpf_reais = cpf.strip() 
    if not cpf_reais:
        continue 
    
    contador += 1 
    print(f"[{contador}/145] Processando CPF: {cpf_reais}")
    
    try:
        #Acessa a página de consulta

        

        #Acessa a roteirização
        navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/aside/nav/div[3]/div/h2/button/div').click()
        time.sleep(5)

        #Clicando em Pesquisar Consulta

        navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/aside/nav/div[3]/div/div/div/a[3]/div').click()
        time.sleep(2)

        #Clicando em "POR CPF"

        navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[3]/button[1]').click()
        time.sleep(2)

        navegador.find_element(By.XPATH,'/html/body/div[4]/div/div/div/div[2]/div/div/input').click()
        time.sleep(2)

        #Insere o CPF
        navegador.find_element(By.XPATH,'/html/body/div[4]/div/div/div/div[2]/div/div/input').send_keys(cpf_reais)
        time.sleep(2)

        #Clica em "Pesquisar"
        navegador.find_element(By.XPATH, '/html/body/div[4]/div/div/div/div[3]/button[2]').click()
        time.sleep(5)

        #CLicar no OLHO e abrir a rota

        navegador.execute_script("window.scrollBy(0, 500);") # Scroll para baixo para encontrar o "Olho"
        time.sleep(2)

        navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[3]/div[6]/div/div/div/div/div/div[2]/a/img').click()
        time.sleep(5)

        #Roteirizando e Enviando o E-MAIL
        navegador.execute_script("window.scrollBy(0, 300);") # Scroll para baixo para encontrar o "Olho"
        time.sleep(2)

        navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[2]/header[2]/div[2]/button[1]').click()
        time.sleep(55)
        time.sleep(2)
        print("✅ Roteirização realizada, próximo passo, enviar o e-mail")

        #Clicar no MyLink e envia o e-mail

        navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[2]/header[2]/div[2]/button[5]').click()
        time.sleep(3) # clica no MyLink

        navegador.find_element(By.XPATH, '/html/body/div[4]/div/div/div/div[3]/button[2]').click()
        time.sleep(3) # clica em "Enviar Link"

        print(f"   ✅ E-mail do CPF {cpf_reais} enviado com sucesso! Processo concluído.")

    except Exception as e:
        print(f"❌ Ocorreu um erro no CPF {cpf_reais}: {e} - Continuando para o próximo CPF.")
        continue

    print("\n 🎉Trabalho concluido! Todos os CPF foram roteirizados e enviados") # Linha em branco para melhor visualização entre os CPFs
