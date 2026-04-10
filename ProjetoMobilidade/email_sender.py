"""
Envio de e-mail via SMTP (Outlook/Office365).
Credenciais lidas do .env.
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
import os

load_dotenv()
logger = logging.getLogger(__name__)

EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE", "douglas.amaral@renapsi.org.br")
EMAIL_SENHA     = os.getenv("EMAIL_SENHA",     "DAtendimento@Jovem25")
SMTP_HOST       = "smtp.office365.com"
SMTP_PORT       = 587


def enviar_carta_por_email(
    destinatario: str,
    nome_funcionario: str,
    pdf_bytes: bytes,
) -> tuple[bool, str]:
    """
    Envia a Carta de Opção de Transporte por e-mail com o PDF em anexo.

    Retorna:
        (True, "")          em caso de sucesso
        (False, mensagem)   em caso de erro
    """
    if not destinatario or "@" not in destinatario:
        return False, "E-mail do destinatário inválido."

    try:
        msg = MIMEMultipart()
        msg["From"]    = EMAIL_REMETENTE
        msg["To"]      = destinatario
        msg["Subject"] = "Carta de Opção de Transporte e Mobilidade — RENAPSI"

        corpo_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; background: #f9f9f9; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white;
                        border-radius: 8px; padding: 32px;
                        border-top: 4px solid #1a3a5c;">
                <h2 style="color: #1a3a5c; margin-top: 0;">
                    Carta de Opção de Transporte e Mobilidade
                </h2>
                <p>Olá, <strong>{nome_funcionario}</strong>,</p>
                <p>
                    Segue em anexo a sua <strong>Carta de Opção de Transporte e Mobilidade</strong>
                    gerada pelo sistema RENAPSI.
                </p>
                <p>
                    Por favor, leia atentamente o documento, assine e devolva conforme
                    orientação do seu gestor.
                </p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
                <p style="font-size: 12px; color: #888;">
                    Este e-mail foi gerado automaticamente pelo sistema de mobilidade RENAPSI.<br>
                    Em caso de dúvidas, entre em contato com o setor de RH.
                </p>
                <p style="font-size: 12px; color: #888;">
                    <strong>RENAPSI — Sistema de Mobilidade Urbana</strong><br>
                    Rua Cincinato Braga, 388 - Bela Vista - São Paulo - SP
                </p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(corpo_html, "html", "utf-8"))

        # Anexa o PDF
        anexo = MIMEApplication(pdf_bytes, _subtype="pdf")
        anexo.add_header(
            "Content-Disposition",
            "attachment",
            filename=f"Carta_VT_{nome_funcionario.replace(' ','_')}.pdf"
        )
        msg.attach(anexo)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as servidor:
            servidor.ehlo()
            servidor.starttls()
            servidor.login(EMAIL_REMETENTE, EMAIL_SENHA)
            servidor.sendmail(EMAIL_REMETENTE, destinatario, msg.as_string())

        logger.info(f"Carta enviada com sucesso para {destinatario}")
        return True, ""

    except smtplib.SMTPAuthenticationError:
        msg_err = "Falha de autenticação no servidor de e-mail. Verifique as credenciais no .env."
        logger.exception(msg_err)
        return False, msg_err
    except smtplib.SMTPException as e:
        msg_err = f"Erro SMTP: {e}"
        logger.exception(msg_err)
        return False, msg_err
    except Exception as e:
        msg_err = f"Erro inesperado ao enviar e-mail: {e}"
        logger.exception(msg_err)
        return False, msg_err
