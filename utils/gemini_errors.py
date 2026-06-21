def classificar_erro_gemini(erro: Exception) -> str | None:
    texto_erro = str(erro).lower()

    if any(
        marcador in texto_erro
        for marcador in (
            "429",
            "resource_exhausted",
            "resource exhausted",
            "quota",
            "rate limit",
            "too many requests",
        )
    ):
        return "cota"

    if any(
        marcador in texto_erro
        for marcador in ("503", "unavailable", "high demand", "overloaded")
    ):
        return "indisponibilidade"

    return None


def mensagem_erro_gemini(erro: Exception) -> str | None:
    classificacao = classificar_erro_gemini(erro)

    if classificacao == "cota":
        return (
            "O limite gratuito da API Gemini foi atingido. "
            "Aguarde a renovação da cota ou confira o uso e os limites da sua chave no Google AI Studio."
        )

    if classificacao == "indisponibilidade":
        return "O Gemini está temporariamente congestionado. Aguarde alguns minutos e tente novamente."

    return None
