"""Contrato da analise financeira assistida por IA."""


SECOES_OBRIGATORIAS_ORACULO = [
    "Raio-X Comportamental",
    "Tend\u00eancias Preditivas",
    "Plano de Evolu\u00e7\u00e3o",
]
INSTRUCAO_REFORCO_CABECALHOS = "\nUse rigorosamente os cabe\u00e7alhos em '### '."


def montar_prompt_oraculo(historico_formatado: str) -> str:
    return (
        "Voc\u00ea \u00e9 um cientista de dados e mentor comportamental financeiro.\n"
        f"Gere um relat\u00f3rio perspicaz baseado nas movimenta\u00e7\u00f5es:\n{historico_formatado}\n\n"
        "ESTRUTURA OBRIGAT\u00d3RIA RIGOROSA:\n"
        "### \ud83d\udcca 1. Raio-X Comportamental\n"
        "### \ud83d\udcc9 2. Tend\u00eancias Preditivas\n"
        "### \ud83d\udcc8 3. Plano de Evolu\u00e7\u00e3o"
    )


def resposta_oraculo_tem_secoes(texto_resposta: str) -> bool:
    texto = str(texto_resposta or "")
    return all(secao in texto for secao in SECOES_OBRIGATORIAS_ORACULO)


def reforcar_prompt_oraculo(prompt_oraculo: str) -> str:
    return prompt_oraculo + INSTRUCAO_REFORCO_CABECALHOS


def montar_payload_feedback_oraculo(
    *,
    usuario_id,
    email_usuario,
    status_resposta,
    resposta_ia,
    dados_enviados,
    anonimizar,
):
    return {
        "user_id": usuario_id,
        "usuario_email": email_usuario,
        "status_resposta": status_resposta,
        "resposta_ia": anonimizar(resposta_ia),
        "dados_enviados": anonimizar(dados_enviados),
    }
