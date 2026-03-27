from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime
from selenium.webdriver.common.keys import Keys

# Leitor da lista de CPFS
with open('cpfs_reaiscc.txt', 'r') as arquivo:
    cpfs = arquivo.readlines()
     
total_cpfs = len(cpfs) # Armazenar o total de CPFs para o contador
print(f"🚀 Iniciando o Robôzinho da Roteirização {total_cpfs} CaptaVT ")

# Config para o sistema não cair (DENOVO)
opcoes = Options()
opcoes.add_argument("--disable-dev-shm-usage") # Não corta a memória do navegador
opcoes.add_argument("--no-sandbox") # Windows não bloqueia com a segurança

# Configuração do Selenium para abrir o navegador (Chrome)
servico = Service(ChromeDriverManager().install())
navegador = webdriver.Chrome(service=servico) # lembrar de definir Chrome como padrão

# Sobe no site
link_login = "https://app.captamobilidade.com.br/" # (Link raiz para o site de login da Capta)
navegador.get(link_login)
navegador.maximize_window() # F11 no google

# Pausa para carregar o Login
time.sleep(2)

# Implementar o CPF
navegador.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[4]/div[1]/div/div/div/input').send_keys("41350968838")
time.sleep(2)

# Implementar a senha
navegador.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[4]/div[2]/div/div/input').send_keys("47824729")
time.sleep(2)

# Clicar no botão de login
navegador.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[5]/div[1]/button').click()

# Retornar mensagem de sucesso
print("✅ Login realizado com sucesso! Acessando a Capta...")
time.sleep(5)

# Loop e contador
contador = 0
for cpf in cpfs:
    cpf_reais = cpf.strip() 
    if not cpf_reais:
        continue 
    
    contador += 1 
    faltam = total_cpfs - contador # Contador para saber quantos CPFs faltam
    print(f"\n[{contador}/{total_cpfs}] Processando CPF: {cpf_reais} | Faltam: {faltam}")
    
    try:
        # 1. (Volta para a página de busca e roda o loop)
        navegador.get("https://app.captamobilidade.com.br/consults/search")
        time.sleep(5)

        #2 Ir para o rota casa x curso

        navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[2]/div/div/div[1]/div[2]').click() # Define o campo da empresa
        time.sleep(1)

        texto_procurado = "45291 - RENAPSI - SÃO PAULO - C-C | 47.312.245/0001-18"
        opcao_cc = navegador.find_element(By.XPATH, F"//*[contains(text(), '{texto_procurado}')]")
        opcao_cc.click()
        time.sleep(2)

        # 3. Clicando em "POR CPF"
        navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[3]/button[1]').click()
        time.sleep(2)

        # 4. Clica no campo de CPF
        navegador.find_element(By.XPATH,'/html/body/div[4]/div/div/div/div[2]/div/div/input').click()
        time.sleep(2)

        # 5. Insere o CPF da fila
        navegador.find_element(By.XPATH,'/html/body/div[4]/div/div/div/div[2]/div/div/input').send_keys(cpf_reais)
        time.sleep(2)

        # 6. Clica em "Pesquisar"
        navegador.find_element(By.XPATH, '/html/body/div[4]/div/div/div/div[3]/button[2]').click()
        time.sleep(5)

        # Começar a variável (Otimizado ou Implantado)
        # 1- Vai ler o que está escrito (Otimizado ou Implantado)
        xpath_da_etiqueta = '//*[@id="root"]/div[1]/div/div/div[3]/div[6]/div/div/div/div/div/div[1]/div/small'
        texto_status =  navegador.find_element(By.XPATH, xpath_da_etiqueta).text

        # Variável para verificar se o status é "Otimizado" ou "Implantado"
        
        if "IMPLANTADO" in texto_status.upper():
            print(f"⚠️ CPF {cpf_reais} já está IMPLANTADO, passando para o próximo.")
            # Registrar no log
            with open('log_roboCC.txt', 'a', encoding='utf-8') as log:
                log.write(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - CPF {cpf_reais} já estava IMPLANTADO, pulando para o próximo.\n")
            continue

        elif "OTIMIZADO" in texto_status.upper():
            print(f"☑️ Status OTIMIZADO encontrado para o CPF {cpf_reais}, dando continuidade para a roteirização.")

        else:
            # Caso apareça um status desconhecido
            print(f"❓ Status desconhecido [{texto_status}] encontrado para o CPF {cpf_reais}, pulando por segurança.")
            with open('log_roboCC.txt', 'a', encoding='utf-8') as log:
                log.write(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Status desconhecido ({texto_status}) no CPF {cpf_reais}, pulando.\n")
            continue

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

        with open('log_roboCC.txt', 'a', encoding='utf-8') as log:
            log.write(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - CPF {cpf_reais} roteirizado e e-mail enviado com sucesso.\n")
        
    except Exception as e:
        print(f"❌ Ocorreu um erro no CPF {cpf_reais}. Pulando para o próximo...")
        with open('log_roboCC.txt', 'a', encoding='utf-8') as log:
            log.write(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Erro no CPF {cpf_reais}: {str(e)}\n")
        continue

# Envios concluidos 
print("\n🎉 Concluido! Todos os CPFs da lista foram processados.") 
navegador.quit()