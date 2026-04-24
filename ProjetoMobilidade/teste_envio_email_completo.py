#!/usr/bin/env python3
"""
Teste completo de envio de e-mail com PDF
Simula o envio de uma carta de VT para validar o sistema
"""

import sys
import os
from io import BytesIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Projeto_RH'))

def criar_pdf_teste():
    """Cria um PDF de teste simples"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "CARTA DE OPÇÃO DE TRANSPORTE E MOBILIDADE")
        
        c.setFont("Helvetica", 12)
        c.drawString(50, 700, "RENAPSI — Sistema de Mobilidade Urbana")
        
        c.drawString(50, 650, "Prezado(a) Candidato(a),")
        c.drawString(50, 620, "Segue em anexo sua Carta de Opção de Transporte e Mobilidade")
        c.drawString(50, 590, "gerada pelo sistema RENAPSI.")
        
        c.drawString(50, 540, "Por favor, leia atentamente o documento, assine e devolva")
        c.drawString(50, 510, "conforme orientação do seu gestor.")
        
        c.drawString(50, 450, "Atenciosamente,")
        c.drawString(50, 420, "RENAPSI — Sistema de Mobilidade Urbana")
        c.drawString(50, 390, "Rua Cincinato Braga, 388 - Bela Vista - São Paulo - SP")
        
        c.save()
        buffer.seek(0)
        return buffer.getvalue()
    except ImportError:
        print("⚠️  reportlab não instalado. Usando PDF vazio para teste.")
        return b"%PDF-1.4\n%EOF"


def teste_envio_email():
    """Testa envio de e-mail com PDF"""
    print("\n" + "="*70)
    print("TESTE COMPLETO DE ENVIO DE E-MAIL COM PDF")
    print("="*70)
    
    try:
        from email_sender import enviar_carta_por_email
        
        # Dados de teste
        destinatario = "douglas.developer06@gmail.com"
        nome_funcionario = "João Silva"
        
        print(f"\n📧 Destinatário: {destinatario}")
        print(f"👤 Funcionário: {nome_funcionario}")
        
        # Cria PDF de teste
        print("\n⏳ Criando PDF de teste...")
        pdf_bytes = criar_pdf_teste()
        print(f"✅ PDF criado ({len(pdf_bytes)} bytes)")
        
        # Envia e-mail
        print("\n⏳ Enviando e-mail...")
        sucesso, mensagem = enviar_carta_por_email(
            destinatario=destinatario,
            nome_funcionario=nome_funcionario,
            pdf_bytes=pdf_bytes
        )
        
        if sucesso:
            print("\n" + "="*70)
            print("✅ E-MAIL ENVIADO COM SUCESSO!")
            print("="*70)
            print(f"\n✓ Destinatário: {destinatario}")
            print(f"✓ Funcionário: {nome_funcionario}")
            print(f"✓ Arquivo: Carta_VT_{nome_funcionario.replace(' ','_')}.pdf")
            print("\n🎉 O sistema de envio de e-mail está funcionando!")
            return True
        else:
            print("\n" + "="*70)
            print("❌ ERRO AO ENVIAR E-MAIL")
            print("="*70)
            print(f"\nMensagem de erro:\n{mensagem}")
            return False
            
    except Exception as e:
        print("\n" + "="*70)
        print("❌ ERRO INESPERADO")
        print("="*70)
        print(f"\nErro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    sucesso = teste_envio_email()
    sys.exit(0 if sucesso else 1)
