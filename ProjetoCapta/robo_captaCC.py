import undetected_chromedriver as uc 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains # <-- Ferramenta ninja de teclado
import time
from datetime import datetime

# Leitor da lista de CPFS do Casa x Curso
with open('cpfs_reaiscc.txt', 'r') as arquivo:
    cpfs = arquivo.readlines()
     
total_cpfs = len(cpfs) 
print(f"🚀 Iniciando o Robôzinho Ninja CC (Força Bruta + Corretor de EAD): {total_cpfs} CPFs na fila.")

# Loop e contador
contador = 0
for cpf in cpfs:
    cpfs_reaisCC = cpf.strip() 
    if not cpfs_reaisCC:
        continue 
    
    contador += 1 
    faltam = total_cpfs - contador 
    print(f"\n[{contador}/{total_cpfs}] Processando CPF: {cpfs_reaisCC} | Faltam: {faltam}")
    
    navegador = None 
    
    try:
        print("🌐 Abrindo um navegador 100% limpo...")
        opcoes = uc.ChromeOptions()
        navegador = uc.Chrome(options=opcoes, version_main=146)
        navegador.maximize_window()

        # Sobe no site e faz o Login
        navegador.get("https://app.captamobilidade.com.br/") 
        time.sleep(3)

        navegador.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[4]/div[1]/div/div/div/input').send_keys("41350968838")
        time.sleep(2)
        navegador.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[4]/div[2]/div/div/input').send_keys("47824729")
        time.sleep(2)
        navegador.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[5]/div[1]/button').click()
        time.sleep(5)

        # 1. Vai direto para a página de busca
        navegador.get("https://app.captamobilidade.com.br/consults/search")
        time.sleep(5)

        # 2. Seleciona Casa x Curso
        caixa_empresa = navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[2]/div/div/div[1]/div[2]')
        caixa_empresa.click()
        time.sleep(1)

        texto_procurado = "45291 - RENAPSI - SÃO PAULO - C-C | 47.312.245/0001-18"
        opcao_cc = navegador.find_element(By.XPATH, f"//*[contains(text(), '{texto_procurado}')]")
        opcao_cc.click()
        time.sleep(2)

        # 3. Clicando em "POR CPF" 
        navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[3]/button[1]').click()
        time.sleep(2)

        # 4. Clica, LIMPA O CAMPO e insere o CPF
        campo_cpf = navegador.find_element(By.XPATH, '/html/body/div[4]/div/div/div/div[2]/div/div/input')
        campo_cpf.click()
        time.sleep(1)
        campo_cpf.clear() 
        campo_cpf.send_keys(cpfs_reaisCC)
        time.sleep(2)

        # 5. Clica em "Pesquisar"
        navegador.find_element(By.XPATH, '/html/body/div[4]/div/div/div/div[3]/button[2]').click()
        time.sleep(5)

        # 6. LENDO O STATUS COM A NOVA REGRA DO "FORA DE ABRANGÊNCIA"
        xpath_da_etiqueta = '//*[@id="root"]/div[1]/div/div/div[3]/div[6]/div/div/div/div/div/div[1]/div/small'
        texto_status = navegador.find_element(By.XPATH, xpath_da_etiqueta).text
        
        # VERIFICAÇÃO 1: É Implantado? Se sim, pula e vai pro próximo.
        if "IMPLANTADO" in texto_status.upper():
            print(f"⚠️ CPF {cpfs_reaisCC} já está IMPLANTADO, passando para o próximo.")
            with open('log_roboCC.txt', 'a', encoding='utf-8') as log:
                log.write(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - CPF {cpfs_reaisCC} já estava IMPLANTADO.\n")
            navegador.quit() 
            time.sleep(2)
            continue

        # VERIFICAÇÃO 2: É Otimizado ou Fora de Abrangência? Ambos abrem o Olho!
        elif "OTIMIZADO" in texto_status.upper() or "ABRANG" in texto_status.upper():
            
            if "OTIMIZADO" in texto_status.upper():
                print(f"☑️ Status OTIMIZADO encontrado! Abrindo a rota...")
            else:
                print(f"⚠️ Status FORA DE ABRANGÊNCIA encontrado! Abrindo a rota para correção...")

            # 7. CLicar no OLHO e abrir a rota (COMUM PARA OS DOIS)
            navegador.execute_script("window.scrollBy(0, 500);") 
            time.sleep(2)
            navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[3]/div[6]/div/div/div/div/div/div[2]/a/img').click()
            time.sleep(5)

            # --- 8. O CURATIVO: Se for Fora de Abrangência, corrige antes de roteirizar! ---
            if "ABRANG" in texto_status.upper():
                print("🔧 Corrigindo o Local de Trabalho para São Paulo (Saindo do EAD)...")
                
                # Clica no ícone de editar
                navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[2]/div[1]/button/img').click()
                time.sleep(3)

                # Clica no dropdown Local de trabalho
                navegador.find_element(By.XPATH, '/html/body/div[4]/div/div/div/div[2]/div/div[3]/div/div/div/div/div[1]/div[2]').click()
                time.sleep(2)

                # Usando o teclado ninja para digitar a cidade e dar Enter
                acoes = ActionChains(navegador)
                acoes.send_keys("RENAPSI - SAO PAULO-SP")
                acoes.pause(1) # Pausinha pra Capta não engasgar
                acoes.send_keys(Keys.ENTER)
                acoes.perform()
                time.sleep(2)

                # Clica em Confirmar
                navegador.find_element(By.XPATH, '/html/body/div[4]/div/div/div/div[3]/button[2]').click()
                time.sleep(5)
                print("✅ Correção feita! O jovem já não é mais EAD.")

            # 9. Roteirizando e Enviando o E-MAIL (COMUM PARA OS DOIS)
            navegador.execute_script("window.scrollBy(0, 300);")
            time.sleep(2)
            navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[2]/header[2]/div[2]/button[1]').click()
            print("⏳ Roteirizando... aguardando 55s.")
            time.sleep(55)
            
            # 10. Clicar no MyLink
            navegador.find_element(By.XPATH, '//*[@id="root"]/div[1]/div/div/div[2]/header[2]/div[2]/button[5]').click()
            time.sleep(3)
        
            # 11. Clicar em "Enviar Link"
            navegador.find_element(By.XPATH, '/html/body/div[4]/div/div/div/div[3]/button[2]').click()
            time.sleep(3)
            
            print(f"✅ E-mail do CPF {cpfs_reaisCC} enviado com sucesso!")
            with open('log_roboCC.txt', 'a', encoding='utf-8') as log:
                log.write(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - CPF {cpfs_reaisCC} roteirizado e enviado com sucesso.\n")
            
            # SUCESSO! Fecha o navegador limpinho para o próximo
            navegador.quit()
            time.sleep(2)

        # VERIFICAÇÃO 3: Deu alguma treta e o status é desconhecido
        else:
            print(f"❓ Status desconhecido [{texto_status}], pulando por segurança.")
            with open('log_roboCC.txt', 'a', encoding='utf-8') as log:
                log.write(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Status desconhecido ({texto_status}) no CPF {cpfs_reaisCC}.\n")
            navegador.quit()
            time.sleep(2)
            continue
            
    except Exception as e:
        print(f"❌ Ocorreu um erro no CPF {cpfs_reaisCC}. Pulando para o próximo...")
        with open('log_roboCC.txt', 'a', encoding='utf-8') as log:
            log.write(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Erro no CPF {cpfs_reaisCC}: {str(e)}\n")
        
        if navegador:
            navegador.quit()
            time.sleep(2)
        continue

print("\n🎉 Concluido! Todos os CPFs da lista foram processados na força bruta.")