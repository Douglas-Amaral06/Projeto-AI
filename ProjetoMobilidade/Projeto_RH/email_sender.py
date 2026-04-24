"""
Envio de e-mail via SMTP.
Credenciais e servidor lidos diretamente do ficheiro .env.
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv, find_dotenv
import os

# ─── Carregamento Blindado do .env ──────────────────────────────────────────
# Estratégia 1: Usar find_dotenv() para localizar o arquivo automaticamente
# Estratégia 2: Se não encontrar, usar o caminho absoluto do diretório atual
dotenv_path = find_dotenv()

if not dotenv_path:
    # Se find_dotenv() não encontrar, tenta o diretório do script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(script_dir, '.env')

# Carrega o .env do caminho descoberto
load_dotenv(dotenv_path)

# Log para debug (remover em produção se necessário)
if os.path.exists(dotenv_path):
    logger_temp = logging.getLogger(__name__)
    logger_temp.debug(f"✅ Arquivo .env carregado de: {dotenv_path}")
else:
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"⚠️ Arquivo .env não encontrado em: {dotenv_path}")

logger = logging.getLogger(__name__)

# ─── Validação de Credenciais ───────────────────────────────────────────────
# Agora procura exatamente os nomes que estão no seu .env
EMAIL_REMETENTE = os.getenv("EMAIL_USER")
EMAIL_SENHA     = os.getenv("EMAIL_PASS")

# Lê o servidor do .env (se não encontrar, assume o Gmail por defeito)
SMTP_HOST       = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT       = int(os.getenv("EMAIL_SMTP_PORT", 587))

if not EMAIL_REMETENTE:
    raise ValueError(
        "❌ ERRO CRÍTICO: Variável EMAIL_USER não encontrada no .env!\n"
        f"Caminho procurado: {dotenv_path}\n"
        "Adicione ao ficheiro .env: EMAIL_USER=seu_email@gmail.com"
    )

if not EMAIL_SENHA:
    raise ValueError(
        "❌ ERRO CRÍTICO: Variável EMAIL_PASS não encontrada no .env!\n"
        f"Caminho procurado: {dotenv_path}\n"
        "Adicione ao ficheiro .env: EMAIL_PASS=sua_senha_de_aplicacao"
    )

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
                    Em caso de dúvidas, entre em contacto com o setor de RH.
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

    except smtplib.SMTPAuthenticationError as e:
        msg_err = (
            "❌ ERRO DE AUTENTICAÇÃO NO GMAIL\n\n"
            "Você está usando a senha REGULAR do Gmail, mas o Gmail rejeita isso por segurança.\n\n"
            "SOLUÇÃO:\n"
            "1. Acesse: https://myaccount.google.com/security\n"
            "2. Ative 'Autenticação de dois fatores' (se não estiver ativada)\n"
            "3. Procure por 'Senhas de aplicação'\n"
            "4. Gere uma nova senha para 'Mail' e 'Windows'\n"
            "5. Copie a senha gerada (sem espaços)\n"
            "6. Atualize EMAIL_PASS no arquivo .env com essa senha\n"
            "7. Reinicie o app\n\n"
            f"Detalhes técnicos: {str(e)}"
        )
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