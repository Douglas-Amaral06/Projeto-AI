import pywhatkit as kit
import time
import random
import pyautogui

# Leitor dos contatos
with open('contatos.txt', 'r') as arquivo:
    numeros = arquivo.readlines()

saudacoes = ["Oi jovem, bom dia!", "Olá jovem, bom dia!", "E aí jovem, bom dia!", "Opa jovem, bom dia!", "Tudo bem jovem, bom dia?", "Bom dia jovem, tudo bem?!", "Opa jovem, tudo certo?", "E aí jovem, tudo bem?", "Olá jovem, tudo bem?", "Opa jovem, tudo bem?", "Bom dia jovem, tudo bem?", "Fala, jovem, tudo bem?", "Tudo bem, jovem?", "Saudações, jovem!" ]
corpos = [
    "*Douglas RH Jovem Renapsi*. Sua roteirização de VT precisa ser finalizada para não afetar o benefício do mês que vem. Por favor, valide os trajetos que enviamos para o seu e-mail e nos avise. Para encerrar o cadastro, mande também uma foto dos cartões de VT que você usa. Contamos com sua colaboração, obrigado! (Desconsidere a mensagem caso já tenha validado e nos enviado o cartão, ok?)",
    "*Douglas RH Jovem Renapsi*. Verificamos que sua rota de VT não foi concluída. Enviamos uma validação para o seu e-mail com ambas as opções de trajeto. Poderia validar e nos dar um retorno? Ah, precisamos também da foto do seu cartão de transporte para finalizar o processo no sistema. Assim evitamos qualquer erro no próximo mês. Valeu!(Desconsidere a mensagem caso já tenha validado e nos enviado o cartão, ok?)",
    "*Douglas RH Jovem Renapsi*. Identificamos que a validação do seu VT ainda está em aberto. Por favor, acesse seu e-mail e valide as rotas que disponibilizamos lá. Em seguida, nos confirme o envio e anexe aqui uma foto do(s) cartão(ões) de VT que você utiliza. Precisamos disso para garantir que seu benefício caia certinho no próximo mês. Grato! (Desconsidere a mensagem caso já tenha validado e nos enviado o cartão, ok?)",
    "*Douglas RH Jovem Renapsi*. Identificamos uma pendência na sua roteirização de transporte. Pedimos a gentileza de validar as rotas que enviamos para o seu e-mail o mais rápido possível. Não esqueça de nos enviar a foto do(s) seu(s) cartão(ões) de VT também, ok? Isso é fundamental para concluir seu cadastro com sucesso. Obrigado! (Desconsidere a mensagem caso já tenha validado e nos enviado o cartão, ok?)",
    "*Douglas RH Jovem Renapsi*. Para você não ter problemas com o recebimento do seu VT no mês que vem, precisamos que valide sua roteirização. Os links de acesso estão no seu e-mail. Após validar, nos confirme por aqui e aproveite para enviar a foto dos seus cartões de transporte para o nosso sistema. Agradecemos a atenção! (Desconsidere a mensagem caso já tenha validado e nos enviado o cartão, ok?) ",
    "*Douglas RH Jovem Renapsi*. Passando para avisar que falta concluir sua rota do VT. Dá uma olhadinha no seu e-mail, pois mandamos os links de validação das rotas para você confirmar. Para finalizar tudo aqui, também precisamos da foto do(s) cartão(ões) que você usa no dia a dia. Assim evitamos atrasos no seu benefício do próximo mês. Valeu! (Desconsidere a mensagem caso já tenha validado e nos enviado o cartão, ok?)",
    "*Douglas RH Jovem Renapsi*. Notamos que sua roteirização do VT ainda não foi finalizada. Para garantir o benefício do mês que vem, por favor, confirme sua rota o quanto antes. Enviamos os detalhes das duas rotas para o seu e-mail; é só validar por lá e nos avisar. Além disso, mande uma foto dos seus cartões de VT para fecharmos seu cadastro. Obrigado! (Desconsidere a mensagem caso já tenha validado e nos enviado o cartão, ok?)",
    "*Douglas RH Jovem Renapsi*. Para evitar qualquer contratempo com o seu benefício de transporte, precisamos que finalize sua roteirização. Os links para validação estão no seu e-mail, é só acessar e confirmar. Depois disso, nos envie uma foto dos seus cartões de transporte para que possamos concluir o processo. Contamos com sua colaboração, obrigado! (Desconsidere a mensagem caso já tenha validado e nos enviado o cartão, ok?)",
    "*Douglas RH Jovem Renapsi*. Identificamos que sua roteirização de VT ainda não foi concluída. Por favor, acesse seu e-mail e valide as rotas que disponibilizamos lá. Em seguida, nos confirme o envio e anexe aqui uma foto do(s) cartão(ões) de VT que você utiliza. Precisamos disso para garantir que seu benefício caia certinho no próximo mês. Grato! (Desconsidere a mensagem caso já tenha validado e nos enviado o cartão, ok?)",
    "*Douglas RH Jovem Renapsi*. Para garantir que seu benefício de transporte seja processado corretamente no próximo mês, precisamos que finalize sua roteirização. Os links para validação estão no seu e-mail, é só acessar e confirmar. Depois disso, nos envie uma foto dos seus cartões de transporte para que possamos concluir o processo. Contamos com sua colaboração, obrigado! (Desconsidere a mensagem caso já tenha validado e nos enviado o cartão, ok?)",
    "*Douglas RH Jovem Renapsi*. Enviamos um e-mail para você com os detalhes da sua roteirização de VT, mas ainda não recebemos a confirmação. Para garantir que seu benefício do próximo mês seja processado sem problemas, por favor, acesse seu e-mail e valide as rotas o quanto antes. Além disso, precisamos que nos envie uma foto dos seus cartões de transporte para finalizar o cadastro. Agradecemos a atenção! (Desconsidere a mensagem caso já tenha validado e nos enviado o cartão, ok?)",
    "*Douglas RH Jovem Renapsi*. Para garantir que seu benefício de transporte seja processado corretamente no próximo mês, precisamos que finalize sua roteirização. Os links para validação estão no seu e-mail, é só acessar e confirmar. Depois disso, nos envie uma foto dos seus cartões de transporte para que possamos concluir o processo. Contamos com sua colaboração, obrigado! (Desconsidere a mensagem caso já tenha validado e nos enviado o cartão, ok?)",
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
    
    print(f"[{contador}/430] Tentando enviar para: {numero_limpo}")
    
    try:
        # Envia a mensagem instantaneamente (sem agendamento)
        kit.sendwhatmsg_instantly(numero_limpo, msg, wait_time=35, tab_close=False)
        
        time.sleep(2)
        pyautogui.press('enter')
        
        # Nossa log do mal (para controle e possíveis reenvios)
        with open('historico_envios.txt', 'a') as log:
            log.write(f"{time.strftime('%H:%M:%S')} - Tentativa enviada para: {numero_limpo}\n")
        
        time.sleep(2)
        pyautogui.hotkey('ctrl', 'w')
        
        pausa = random.randint(50, 70)
        print(f"✅ Comando enviado. Pausa de {pausa}s...")
        time.sleep(pausa)

    except Exception as e:
        print(f"❌ Erro ao processar {numero_limpo}: {e}")
        continue

    if contador % 35 == 0:
        print("☕ Pausa remunerada obrigatória de 15 min pro café (Anti-Ban).")
        time.sleep(900) # 15 minutos de pausa para evitar bloqueios

print("\n🎯 Pronto, envios concluídos! Agora deixa o coitado do robô descansar um pouco.")

#NÃO MEXER
#Basta escrever "Python disparador.py" no terminal e deixar o programa rodar, ele vai enviar as mensagens para os contatos listados no arquivo "contatos.txt". Lembre-se de não mexer no mouse ou fechar o Chrome durante a execução, caso contrário o programador rouba seu cachorro, By: Douglas!