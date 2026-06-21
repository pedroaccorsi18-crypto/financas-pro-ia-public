import logging
import smtplib
import threading
from email.mime.text import MIMEText

from utils.formatting import formatar_brl


logger = logging.getLogger(__name__)


def enviar_alerta_fiscal(
    configuracao: dict,
    *,
    usuario: str,
    instituicao: str,
    tipo_doc: str,
    mes: str,
    total_gastos: float,
    total_creditos: float,
    valor_declarado: float,
    smtp_factory=smtplib.SMTP,
    timeout: float = 10,
) -> bool:
    balanco_calculado = total_gastos - total_creditos
    divergencia = abs(balanco_calculado - valor_declarado)
    if divergencia <= 0.05:
        return False

    remetente = configuracao["SMTP_EMAIL_REMETENTE"]
    destinatario = configuracao["EMAIL_DESTINATARIO_ALERTAS"]
    assunto = f"[ALERTA FINANCAS PRO IA] Divergencia em {mes} ({instituicao})"
    corpo = f"""
O Bot Fiscal detectou um desalinhamento contabil.

Usuario: {usuario}
Instituicao: {instituicao}
Tipo de documento: {tipo_doc}
Mes de referencia: {mes}
Soma de gastos: {formatar_brl(total_gastos)}
Soma de creditos: {formatar_brl(total_creditos)}
Balanco liquido interno: {formatar_brl(balanco_calculado)}
Valor declarado no documento: {formatar_brl(valor_declarado)}
Divergencia: {formatar_brl(divergencia)}
"""
    mensagem = MIMEText(corpo)
    mensagem["Subject"] = assunto
    mensagem["From"] = remetente
    mensagem["To"] = destinatario

    servidor = smtp_factory(
        configuracao["SMTP_SERVER"],
        int(configuracao["SMTP_PORT"]),
        timeout=timeout,
    )
    try:
        servidor.starttls()
        servidor.login(remetente, configuracao["SMTP_SENHA_REMETENTE"])
        servidor.sendmail(remetente, [destinatario], mensagem.as_string())
    finally:
        servidor.quit()
    return True


def agendar_alerta_fiscal(configuracao: dict, **dados) -> threading.Thread:
    def executar():
        try:
            enviar_alerta_fiscal(configuracao, **dados)
        except Exception:
            logger.warning("Falha ao enviar alerta fiscal", exc_info=True)

    thread = threading.Thread(
        target=executar,
        name="bot-fiscal-email",
        daemon=True,
    )
    thread.start()
    return thread
