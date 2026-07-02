import pandas as pd


def formatar_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def formatar_data(valor):
    try:
        if pd.isna(valor) or valor == "":
            return ""
        return pd.to_datetime(valor).strftime("%d/%m/%Y")
    except Exception:
        return valor


def formatar_data_hora(valor):
    try:
        if pd.isna(valor) or valor == "":
            return ""
        return pd.to_datetime(valor).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return valor


def formatar_percentual(valor):
    try:
        return f"{float(valor):,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00%"


def formatar_dataframe_datas(df, com_hora=False):
    if df is None or df.empty:
        return df

    df_formatado = df.copy()

    for coluna in df_formatado.columns:
        nome = coluna.lower()

        if (
            "data" in nome
            or "vencimento" in nome
            or "criado_em" in nome
            or "pagamento" in nome
            or "recebimento" in nome
        ):
            if com_hora:
                df_formatado[coluna] = df_formatado[coluna].apply(formatar_data_hora)
            else:
                df_formatado[coluna] = df_formatado[coluna].apply(formatar_data)

    return df_formatado


def formatar_dataframe_moedas(df, colunas=None):
    if df is None or df.empty:
        return df

    df_formatado = df.copy()

    if colunas is None:
        colunas = [
            "valor",
            "valor_total",
            "valor_final",
            "preco",
            "preco_unitario",
            "subtotal",
            "saldo",
            "saldo_inicial",
            "saldo_final",
            "total_entradas",
            "total_saidas",
            "valor_conferido",
            "diferenca",
            "custo",
            "custo_unitario"
        ]

    for coluna in colunas:
        if coluna in df_formatado.columns:
            df_formatado[coluna] = df_formatado[coluna].apply(formatar_moeda)

    return df_formatado


def formatar_dataframe_brasil(df, com_hora=False, moedas=True):
    if df is None or df.empty:
        return df

    df_formatado = df.copy()
    df_formatado = formatar_dataframe_datas(df_formatado, com_hora=com_hora)

    if moedas:
        df_formatado = formatar_dataframe_moedas(df_formatado)

    return df_formatado