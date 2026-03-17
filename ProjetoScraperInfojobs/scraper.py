import requests
import os 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

TOKEN = "8574937481:AAG0GGV1e8Y-aok6wWSb3MlP4xoF60nRYYY" 
CHAT_ID = "7930054023"
ARQUIVO_LOG = "vagas_enviadas.txt"

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}"
    requests.get(url)

enviar_telegram("🤖 Radar ligado! Lendo a memória de vagas...")

# --- SISTEMA DE MEMÓRIA (LOG TXT) ---
if os.path.exists(ARQUIVO_LOG):
    with open(ARQUIVO_LOG, "r") as arquivo:
        vagas_ja_enviadas = set(arquivo.read().splitlines())
    print(f"Memória carregada: {len(vagas_ja_enviadas)} vagas já enviadas anteriormente.")
else:
    vagas_ja_enviadas = set()
    print("Nenhum log anterior encontrado. Começando memória do zero.")

while True:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    try:
        link_busca = "https://www.infojobs.com.br/vagas-de-emprego-auxiliar-administrativo-em-sao-paulo.aspx"
        print("\nIniciando varredura...")
        
        driver.get(link_busca)
        driver.maximize_window()
        wait = WebDriverWait(driver, 15)

        try:
            botao_cookie = wait.until(EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button")))
            botao_cookie.click()
        except:
            pass

        time.sleep(3)
        vagas = driver.find_elements(By.XPATH, "//div[contains(@class, 'card') or contains(@class, 'vaga')]")
        
        vagas_novas_agora = 0
        
        for vaga in vagas: 
            texto_completo = vaga.text.strip().lower()
            
            if "patrocinada" in texto_completo:
                continue
            if "pcd" in texto_completo or "deficiência" in texto_completo:
                continue

            if "hoje" in texto_completo and "são paulo" in texto_completo:
                try:
                    elemento_link = vaga.find_element(By.XPATH, ".//a")
                    link = elemento_link.get_attribute("href")
                    titulo = vaga.text.split('\n')[0] 
                    
                    if titulo and link and link not in vagas_ja_enviadas:
                        print(f"Enviando vaga INÉDITA: {titulo}")
                        texto_vaga = f"📌 Nova Vaga: {titulo}\n📅 Data: Hoje\n📍 Local: São Paulo\n🔗 Link: {link}"
                        enviar_telegram(texto_vaga)
                        
                        vagas_ja_enviadas.add(link)
                        
                        # ESSA É A PARTE QUE CRIA E SALVA NO ARQUIVO TXT
                        with open(ARQUIVO_LOG, "a") as arquivo:
                            arquivo.write(link + "\n")
                            
                        vagas_novas_agora += 1
                        time.sleep(2)
                except:
                    continue 
                    
            if vagas_novas_agora >= 5:
                break

        print(f"Varredura finalizada. {vagas_novas_agora} vagas inéditas enviadas.")

    except Exception as e:
        print(f"Erro: {e}")

    finally:
        driver.quit()
    
    print("Dormindo por 1 hora... Zzz...")
    time.sleep(3600)