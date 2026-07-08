from utils.subscriptions import pode_usar_plano_pro


SMTP_SECRET_KEYS = (
    "SMTP_SERVER",
    "SMTP_PORT",
    "SMTP_EMAIL_REMETENTE",
    "SMTP_SENHA_REMETENTE",
    "EMAIL_DESTINATARIO_ALERTAS",
)

NAVEGACAO_GRATUITA = (
    "Visão Geral",
    "Meu Perfil",
    "Transações",
    "Meu Plano",
)

NAVEGACAO_PRO = (
    "Importação",
)

FEATURE_FLAGS_NAVEGACAO_PRO = (
    ("ENABLE_PLANEJAMENTO_360", "Planejamento 360"),
    ("ENABLE_MARKET_RADAR", "Radar de Mercado"),
    ("ENABLE_ORACULO_IA", "Oráculo IA"),
)

VALORES_VERDADEIROS = {"1", "true", "yes", "y", "sim", "s", "on"}


def feature_flag_ativa(secrets, nome, padrao=False):
    valor = secrets.get(nome, padrao)
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return False
    return str(valor).strip().lower() in VALORES_VERDADEIROS


def montar_opcoes_navegacao(secrets, *, is_admin=False, assinatura=None):
    opcoes = list(NAVEGACAO_GRATUITA)

    if pode_usar_plano_pro(assinatura):
        opcoes.extend(NAVEGACAO_PRO)
        for nome_flag, nome_secao in FEATURE_FLAGS_NAVEGACAO_PRO:
            if feature_flag_ativa(secrets, nome_flag):
                opcoes.append(nome_secao)

    if is_admin:
        opcoes.append("Admin")
    return opcoes
