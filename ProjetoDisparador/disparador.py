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
    "Gostaria que você me enviasse a sua operadora e o número do seu bilhete de transporte (vinculado ao seu CPF). Além disso, peço que assine sua roteirização para a implantação da rota de trabalho/curso. Caso já tenha assinado, pode desconsiderar esta parte.Vale ressaltar que, caso o envio das informações solicitadas não seja feito até o dia 11/05, o benefício será cortado. Faltas decorrentes da ausência do vale-transporte não serão abonadas.",
    "Peço que me envie a sua operadora e o número do seu bilhete de transporte (vinculado ao seu CPF). Além disso, peço que assine sua roteirização para a implantação da rota de trabalho/curso. Caso já tenha assinado, pode desconsiderar esta parte.Vale ressaltar que, caso o envio das informações solicitadas não seja feito até o dia 11/05, o benefício será cortado. Faltas decorrentes da ausência do vale-transporte não serão abonadas.",
    "Solicito que me envie a sua operadora e o número do seu bilhete de transporte (vinculado ao seu CPF). Além disso, peço que assine sua roteirização para a implantação da rota de trabalho/curso. Caso já tenha assinado, pode desconsiderar esta parte.Vale ressaltar que, caso o envio das informações solicitadas não seja feito até o dia 11/05, o benefício será cortado. Faltas decorrentes da ausência do vale-transporte não serão abonadas.",
    "Peço para que me envie a sua operadora e o número do seu bilhete de transporte (vinculado ao seu CPF). Além disso, peço que assine sua roteirização para a implantação da rota de trabalho/curso. Caso já tenha assinado, pode desconsiderar esta parte.Vale ressaltar que, caso o envio das informações solicitadas não seja feito até o dia 11/05, o benefício será cortado. Faltas decorrentes da ausência do vale-transporte não serão abonadas.",
    "Aqui solicito que me envie a sua operadora e o número do seu bilhete de transporte (vinculado ao seu CPF). Além disso, peço que assine sua roteirização para a implantação da rota de trabalho/curso. Caso já tenha assinado, pode desconsiderar esta parte.Vale ressaltar que, caso o envio das informações solicitadas não seja feito até o dia 11/05, o benefício será cortado. Faltas decorrentes da ausência do vale-transporte não serão abonadas.",
    "Por gentileza, me envie a sua operadora e o número do seu bilhete de transporte (vinculado ao seu CPF). Além disso, peço que assine sua roteirização para a implantação da rota de trabalho/curso. Caso já tenha assinado, pode desconsiderar esta parte.Vale ressaltar que, caso o envio das informações solicitadas não seja feito até o dia 11/05, o benefício será cortado. Faltas decorrentes da ausência do vale-transporte não serão abonadas.",
    "Peço encarecidamente que me envie a sua operadora e o número do seu bilhete de transporte (vinculado ao seu CPF). Além disso, peço que assine sua roteirização para a implantação da rota de trabalho/curso. Caso já tenha assinado, pode desconsiderar esta parte.Vale ressaltar que, caso o envio das informações solicitadas não seja feito até o dia 11/05, o benefício será cortado. Faltas decorrentes da ausência do vale-transporte não serão abonadas.",
    "Peço que me encaminhe a sua operadora e o número do seu bilhete de transporte (vinculado ao seu CPF). Além disso, peço que assine sua roteirização para a implantação da rota de trabalho/curso. Caso já tenha assinado, pode desconsiderar esta parte.Vale ressaltar que, caso o envio das informações solicitadas não seja feito até o dia 11/05, o benefício será cortado. Faltas decorrentes da ausência do vale-transporte não serão abonadas.",
    "Solicito que você me encaminhe a sua operadora e o número do seu bilhete de transporte (vinculado ao seu CPF). Além disso, peço que assine sua roteirização para a implantação da rota de trabalho/curso. Caso já tenha assinado, pode desconsiderar esta parte.Vale ressaltar que, caso o envio das informações solicitadas não seja feito até o dia 11/05, o benefício será cortado. Faltas decorrentes da ausência do vale-transporte não serão abonadas.",
    "Jovem, peço que me encaminhe a sua operadora e o número do seu bilhete de transporte (vinculado ao seu CPF). Além disso, peço que assine sua roteirização para a implantação da rota de trabalho/curso. Caso já tenha assinado, pode desconsiderar esta parte.Vale ressaltar que, caso o envio das informações solicitadas não seja feito até o dia 11/05, o benefício será cortado. Faltas decorrentes da ausência do vale-transporte não serão abonadas.",
    "Por gentileza, me encaminhe a sua operadora e o número do seu bilhete de transporte (vinculado ao seu CPF). Além disso, peço que assine sua roteirização para a implantação da rota de trabalho/curso. Caso já tenha assinado, pode desconsiderar esta parte.Vale ressaltar que, caso o envio das informações solicitadas não seja feito até o dia 11/05, o benefício será cortado. Faltas decorrentes da ausência do vale-transporte não serão abonadas.",
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
    
    print(f"[{contador}/352] Tentando enviar para: {numero_limpo}")
    
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