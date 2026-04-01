import pywhatkit as kit
import time
import random
import pyautogui

# Leitor dos contatos
with open('contatos_reais2.txt', 'r') as arquivo:
    numeros = arquivo.readlines()

saudacoes = ["Oi jovem, bom dia!", "Olá jovem, bom dia!", "E aí jovem, bom dia!", "Opa jovem, bom dia!", "Tudo bem jovem, bom dia?", "Bom dia jovem, tudo bem?!", "Opa jovem, tudo certo?", "E aí jovem, tudo bem?", "Olá jovem, tudo bem?", "Opa jovem, tudo bem?", "Bom dia jovem, tudo bem?", "Fala, jovem, tudo bem?", "Tudo bem, jovem?", "Saudações, jovem!" ]
corpos = [
    "*Douglas RH JOVEM RENAPSI.* Percebemos que você alterou seu endereço, poderia me informar se com o novo local de residência vai ser necessário alterações no valor de vale-trasnporte? Aguardamos retorno.",
    "*Douglas RH JOVEM RENAPSI.* Notamos que houve uma mudança no seu endereço, poderia nos informar se com o novo local de residência será necessário ajustes no valor do vale-transporte? Aguardamos seu retorno.",
    "*Douglas RH JOVEM RENAPSI.* Identificamos que seu endereço foi atualizado, poderia nos informar se com a nova localização será necessário modificar o valor do vale-transporte? Aguardamos sua resposta.",
    "*Douglas RH JOVEM RENAPSI.* Observamos que houve uma alteração no seu endereço, poderia nos informar se com a nova residência será necessário ajustar o valor do vale-transporte? Aguardamos seu retorno.",
    "*Douglas RH JOVEM RENAPSI.* Notamos que seu endereço foi modificado, poderia nos informar se com a nova localização será necessário alterar o valor do vale-transporte? Aguardamos sua resposta.",
]

print(f"🚀 Iniciando disparo em massa: {len(numeros)} contatos.")
print("Lembre-se: NÃO mexa no mouse e feche o Chrome, caso contrário o programador rouba seu cachorro, By: Douglas!")

contador = 0    
for numero in numeros:
    numero_limpo = numero.strip() 
    if not numero_limpo:
        continue 
    
    contador += 1 
    msg = f"{random.choice(saudacoes)} {random.choice(corpos)}"
    
    print(f"[{contador}/12] Tentando enviar para: {numero_limpo}")
    
    try:
        # Envia a mensagem instantaneamente (sem agendamento)
        kit.sendwhatmsg_instantly(numero_limpo, msg, wait_time=20, tab_close=False)
        
        time.sleep(2)
        pyautogui.press('enter')
        
        # Nossa log do mal (para controle e possíveis reenvios)
        with open('historico_envios.txt', 'a') as log:
            log.write(f"{time.strftime('%H:%M:%S')} - Tentativa enviada para: {numero_limpo}\n")
        
        time.sleep(2)
        pyautogui.hotkey('ctrl', 'w')
        
        pausa = random.randint(20, 25)
        print(f"✅ Comando enviado. Pausa de {pausa}s...")
        time.sleep(pausa)

    except Exception as e:
        print(f"❌ Erro ao processar {numero_limpo}: {e}")
        continue

    if contador % 25 == 0:
        print("☕ Pausa remunerada obrigatória de 15 min pro café (Anti-Ban).")
        time.sleep(900) # 15 minutos de pausa para evitar bloqueios

print("\n🎯 Pronto, envios concluídos! Agora deixa o coitado do robô descansar um pouco.")

#NÃO MEXER
#Basta escrever "Python disparador.py" no terminal e deixar o programa rodar, ele vai enviar as mensagens para os contatos listados no arquivo "contatos.txt". Lembre-se de não mexer no mouse ou fechar o Chrome durante a execução, caso contrário o programador rouba seu cachorro, By: Douglas!