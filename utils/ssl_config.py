import logging

logger = logging.getLogger(__name__)


def configurar_certificados_ssl_do_sistema() -> bool:
    """Faz clientes Python respeitarem a loja de certificados do sistema."""
    try:
        import truststore
    except ImportError:
        logger.info("truststore nao instalado; usando certificados padrao do Python")
        return False

    try:
        truststore.inject_into_ssl()
        return True
    except Exception:
        logger.warning(
            "Nao foi possivel ativar a loja de certificados do sistema",
            exc_info=True,
        )
        return False
