from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime # <-- NOVA IMPORTAÇÃO PARA A LOG

# Leitor da lista de CPFS
with open('cpfs_reais.txt', 'r') as arquivo:
    cpfs = arquivo.readlines()

total_cpfs = len(cpfs) # Guardando o total para a matemática do contador
print(f"🚀 Iniciando o Robôzinho da Roteirização: {total_cpfs} CPFs na fila.")

# Config para o sistema não cair 
opcoes = Options()
opcoes.add_argument("--disable-dev-shm-usage")
opcoes.add_argument("--no-sandbox")

# Configuração do Selenium para abrir o navegador
servico = Service(ChromeDriverManager().install())
navegador = webdriver.Chrome(service=servico) 

# Sobe no site
link_login = "https://app.captamobilidade.com.br/" 
navegador.get(link_login)
navegador.maximize_window()

# Pausa para carregar o Login
time.sleep(5)

# Implementar o CPF
navegador.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[4]/div[1]/div/div/div/input').send_keys("41350968838")
time.sleep(2)

# Implementar a senha
navegador.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[4]/div[2]/div/div/input').send_keys("47824729")
time.sleep(2)

# Clicar no botão de login
navegador.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[5]/div[1]/button').click()

print("✅ Login realizado com sucesso! Acessando a Capta...")
time.sleep(10)

# Loop e contador
contador = 0
for cpf in cpfs:
    cpf_reais = cpf.strip() 
    if not cpf_reais:
        continue 
    
    contador += 1 
    faltam = total_cpfs - contador # A matemática de quantos faltam
    hora_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S") # Pega a hora do PC
    
    print(f"\n[{contador}/{total_cpfs}] Processando CPF: {cpf_reais} | Faltam: {faltam}")
    
    try:
        # 1. O Pulo do Gato: Vai direto para a página limpa de pesquisa
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
        navegador.execute_script("window.scrollBy(0, 500);")
        time.sleep(2)
        navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[3]/div[6]/div/div/div/div/div/div[2]/a/img').click()
        time.sleep(5)

        # 7. Roteirizando e Enviando o E-MAIL
        navegador.execute_script("window.scrollBy(0, 300);") 
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
        
        # --- SALVANDO A LOG DE SUCESSO ---
        with open('log_roteirizacao.txt', 'a', encoding='utf-8') as log:
            log.write(f"[{hora_atual}] SUCESSO - CPF {cpf_reais} roteirizado e enviado.\n")
        
    except Exception as e:
        print(f"❌ Ocorreu um erro no CPF {cpf_reais}. Pulando para o próximo...")
        
        # --- SALVANDO A LOG DE ERRO ---
        with open('log_roteirizacao.txt', 'a', encoding='utf-8') as log:
            log.write(f"[{hora_atual}] ERRO - Falha no CPF {cpf_reais}. Detalhe: {e}\n")
        continue

# FORA DO LOOP
print("\n🎉 Trabalho concluido! Todos os CPF da lista foram processados.") 
navegador.quit()