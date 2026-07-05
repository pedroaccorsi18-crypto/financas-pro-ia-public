from utils.privacy import anonimizar_dados


class PrivacyGuard:
    def sanitize(self, texto: str, *, dados_sensiveis: bool) -> str:
        if not texto:
            return ""
        if not dados_sensiveis:
            return texto
        return anonimizar_dados(texto)
