def formatar_brl(valor: float) -> str:
    """Transforma float em string de moeda formatada no padrao PT-BR com tratamento de excecao."""
    try:
        string_base = f"R$ {valor:,.2f}"
        marcador_provisorio = string_base.replace(",", "X")
        com_pontos_milhar = marcador_provisorio.replace(".", ",")
        return com_pontos_milhar.replace("X", ".")
    except Exception as e:
        return "R$ 0,00"
