import time

from utils.gemini_errors import classificar_erro_gemini


def gerar_conteudo_gemini(
    cliente,
    *,
    tentativas: int = 3,
    pausar=time.sleep,
    **kwargs,
):
    if tentativas < 1:
        raise ValueError("tentativas deve ser maior que zero")

    for tentativa in range(tentativas):
        try:
            return cliente.models.generate_content(**kwargs)
        except Exception as erro:
            ultima_tentativa = tentativa == tentativas - 1
            if classificar_erro_gemini(erro) != "indisponibilidade" or ultima_tentativa:
                raise
            pausar(2 ** tentativa)
