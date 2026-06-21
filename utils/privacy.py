import re


def anonimizar_dados(texto):
    if not texto:
        return ""
    texto = re.sub(r'R\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?', '[VALOR_OCULTO]', texto)
    texto = re.sub(r'\b\d+(?:[\.,]\d{2})\b', '[NUMERO_OCULTO]', texto)
    return texto
