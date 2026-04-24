#!/usr/bin/env python3
"""
Script para testar conexão com Gmail SMTP
Use este script para validar suas credenciais antes de usar no app
"""

import smtplib
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Projeto_RH'))

def teste_conexao_gmail():
    """Testa conexão com Gmail SMTP"""
    print("\n" + "="*70)
    print("TESTE DE CONEXÃO COM GMAIL SMTP")
    print("="*70)
    
    try:
        from email_sender import EMAIL_REMETENTE, EMAIL_SENHA, SMTP_HOST, SMTP_PORT
        
        print(f"\n📧 E-mail: {EMAIL_REMETENTE}")
        print(f"🔐 Senha: {'*' * len(EMAIL_SENHA)}")
        print(f"🖥️  Host: {SMTP_HOST}")
        print(f"🔌 Porta: {SMTP_PORT}")
        
        print("\n⏳ Conectando ao servidor SMTP...")
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as servidor:
            print("✅ Conexão estabelecida")
            
            print("⏳ Iniciando TLS...")
            servidor.starttls()
            print("✅ TLS iniciado")
            
            print("⏳ Autenticando...")
            servidor.login(EMAIL_REMETENTE, EMAIL_SENHA)
            print("✅ Autenticação bem-sucedida!")
            
            print("\n" + "="*70)
            print("🎉 CONEXÃO COM GMAIL FUNCIONANDO!")
            print("="*70)
            print("\nVocê pode usar este e-mail para enviar cartas no app.")
            return True
            
    except smtplib.SMTPAuthenticationError as e:
        print("\n" + "="*70)
        print("❌ ERRO DE AUTENTICAÇÃO")
        print("="*70)
        print("\n⚠️  Sua senha está INCORRETA ou não é uma Senha de Aplicação!")
        print("\nSOLUÇÃO:")
        print("1. Acesse: https://myaccount.google.com/security")
        print("2. Ative 'Autenticação de dois fatores' (se não estiver)")
        print("3. Procure por 'Senhas de aplicação'")
        print("4. Gere uma nova senha para 'Mail' e 'Windows'")
        print("5. Copie a senha (sem espaços)")
        print("6. Atualize EMAIL_PASS no arquivo Projeto_RH/.env")
        print("7. Reinicie o app")
        print(f"\nDetalhes: {str(e)}")
        return False
        
    except smtplib.SMTPException as e:
        print("\n" + "="*70)
        print("❌ ERRO SMTP")
        print("="*70)
        print(f"\nErro: {str(e)}")
        print("\nVerifique:")
        print("- Se o host está correto: smtp.gmail.com")
        print("- Se a porta está correta: 587")
        print("- Se sua conexão de internet está funcionando")
        return False
        
    except Exception as e:
        print("\n" + "="*70)
        print("❌ ERRO INESPERADO")
        print("="*70)
        print(f"\nErro: {str(e)}")
        return False


if __name__ == "__main__":
    sucesso = teste_conexao_gmail()
    sys.exit(0 if sucesso else 1)
