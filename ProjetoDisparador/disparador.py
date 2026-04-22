import pywhatkit as kit
import time
import random
import pyautogui

# Leitor dos contatos
with open('contatos_reais.txt', 'r') as arquivo:
    numeros = arquivo.readlines()

saudacoes = ["*Douglas RH Jovem Renapsi*, Olá jovem, bom dia.", "*Douglas RH Jovem Renapsi*, Olá jovem, como você está?", "*Douglas RH Jovem Renapsi*, Olá jovem, espero que esteja bem.",
    "*Douglas RH Jovem Renapsi* - Olá jovem, tudo bem?",
    "*Douglas RH Jovem Renapsi* - Olá jovem, como vai?",
    "*Douglas RH Jovem Renapsi* - Olá jovem, espero que esteja tendo um ótimo dia.",
    "*Douglas RH Jovem Renapsi* - Olá jovem, como tem sido seu dia?",
    "*Douglas RH Jovem Renapsi* - Olá jovem, espero que esteja tendo um dia produtivo.",
    "*Douglas RH Jovem Renapsi* - Olá jovem, como estão as coisas por aí?",
    "*Douglas RH Jovem Renapsi* - Olá jovem, espero que esteja se cuidando bem.",
    "*Douglas RH Jovem Renapsi* - Olá jovem, como tem sido sua semana?"
]
corpos = [
    "Gostaria de saber se já está com o cartão TOP em mãos, ou conseguiu fazer a solicitação da via do bilhete, aguardo retorno.",
    "Você já tem o cartão TOP em mãos? Se não, conseguiu solicitar a via do bilhete? Fico no aguardo do seu retorno.",
    "Estou entrando em contato para verificar se você já recebeu o cartão TOP ou se conseguiu solicitar a via do bilhete. Aguardo seu retorno.",
    "Gostaria de confirmar se você já tem o cartão TOP em mãos ou se conseguiu solicitar a via do bilhete. Fico no aguardo do seu retorno.",
    "Gostaria de saber se você já recebeu o cartão TOP ou se conseguiu solicitar a via do bilhete. Aguardo seu retorno para dar continuidade ao processo.",
    "Quero saber se você já tem o cartão TOP em mãos ou se conseguiu solicitar a via do bilhete. Fico no aguardo do seu retorno para dar continuidade ao processo.",
    "Fico entrando em contato para verificar se você já recebeu o cartão TOP ou se conseguiu solicitar a via do bilhete. Aguardo seu retorno para dar continuidade ao processo.",
    "Quero confirmar se você já tem o cartão TOP em mãos ou se conseguiu solicitar a via do bilhete. Fico no aguardo do seu retorno para dar continuidade ao processo.",
]

print(f"🚀 Iniciando disparo em massa: {len(numeros)} contatos.")
print("Lembre-se: NÃO mexa no mouse e feche o Chrome, caso contrário o programador rouba seu cachorro, By: Douglas!")

contador = 0    
for numero in numeros:
    numero_limpo = numero.strip() 
    if not numero_limpo:
        continue 
    
    numero_limpo = f"+55{numero_limpo}" # <-- Adicione esta linha para colocar o +55 na frente
    
    contador += 1 
    msg = f"{random.choice(saudacoes)} {random.choice(corpos)}"
    
    print(f"[{contador}/32] Tentando enviar para: {numero_limpo}")
    
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