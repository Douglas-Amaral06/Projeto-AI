from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime

#Leitor da lista de CPFS

with open('cpfs_reais.txt', 'r') as arquivo:
	cpfs = arquivo.readlines()
     
total_cpfs = len(cpfs) #Armazenar o total de CPFs para o contador
print(f"🚀 Iniciando o Robôzinho da Roteirização {len(cpfs)} CaptaVT ")

#Config para o sistema não cair (DENOVO)
opcoes = Options()
opcoes.add_argument("--disable-dev-shm-usage") #Não corta a memória do navegador
opcoes.add_argument("--no-sandbox") #Windows não bloqueia com a segurança

# Configuração do Selenium para abrir o navegador (Chrome)
servico = Service(ChromeDriverManager().install())
navegador = webdriver.Chrome(service=servico) #lembrar de definir Chrome como padrão

# Sobe no site
link_login = "https://app.captamobilidade.com.br/" # (Link raiz para o site de login da Capta)
navegador.get(link_login)
navegador.maximize_window() # F11 no google

# Pausa para carregar o Login
time.sleep(2)

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
time.sleep(5)

#Loop e contador
contador = 0
for cpf in cpfs:
    cpf_reais = cpf.strip() 
    if not cpf_reais:
        continue 
    
    contador += 1 
    faltam = total_cpfs - contador #  Contador para saber quantos CPFs faltam
    print(f"\n[{contador}/{len(cpfs)}] Processando CPF: {cpf_reais}")
    
    try:
        # 1. (Volta para a página de busca e roda o loop)
        navegador.get("https://app.captamobilidade.com.br/consults/search")
        time.sleep(5)

        # 2. Clicando em "POR CPF"
        navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[3]/button[1]').click()
        time.sleep(2)

        # 3. Clica no campo de CPF
        navegador.find_element(By.XPATH,'/html/body/div[4]/div/div/div/div[2]/div/div/input').click()
        time.sleep(2)

        # 4. Insere o CPF da fila
        navegador.find_element(By.XPATH,'/html/body/div[4]/div/div/div/div[2]/div/div/input').send_keys(cpf_reais)
        time.sleep(2)

        # 5. Clica em "Pesquisar"
        navegador.find_element(By.XPATH, '/html/body/div[4]/div/div/div/div[3]/button[2]').click()
        time.sleep(5)

        # 6. CLicar no OLHO e abrir a rota
        navegador.execute_script("window.scrollBy(0, 500);") # Scroll para baixo
        time.sleep(2)
        navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[3]/div[6]/div/div/div/div/div/div[2]/a/img').click()
        time.sleep(5)

        # 7. Roteirizando e Enviando o E-MAIL
        navegador.execute_script("window.scrollBy(0, 300);") # Scroll para baixo
        time.sleep(2)
        navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[2]/header[2]/div[2]/button[1]').click()
        print("⏳ Roteirizando... aguardando 55s.")
        time.sleep(55)
        
        print("✅ Roteirização realizada, próximo passo: enviar o e-mail")

        # 8. Clicar no MyLink
        navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[2]/header[2]/div[2]/button[5]').click()
        time.sleep(3)
    
        # 9. Clicar em "Enviar Link"
        navegador.find_element(By.XPATH, '/html/body/div[4]/div/div/div/div[3]/button[2]').click()
        time.sleep(3)
        
        print(f"✅ E-mail do CPF {cpf_reais} enviado com sucesso!")

        with open('log_robo.txt', 'a')as log:
            log.write(f"{datetime.now()} - CPF {cpf_reais} roteirizado e e-mail enviado com sucesso.\n")
        
    except Exception as e:
        # Repare que o except agora está na mesma reta do try!
        print(f"❌ Ocorreu um erro no CPF {cpf_reais}. Pulando para o próximo...")
        with open('log_robo.txt', 'a')as log:
            log.write(f"{datetime.now()} - Erro no CPF {cpf_reais}: {str(e)}\n")
        continue

# Envios concluidos 
print("\n🎉 Concluido, todos os CPFS foram roteirizados.") 
navegador.quit()
