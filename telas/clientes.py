import re
from datetime import date

import pandas as pd
import streamlit as st


from database.clientes_db import (
    listar_clientes,
    cadastrar_cliente,
    atualizar_cliente,
    excluir_cliente
)
from services.cep_service import consultar_cep

from utils.formatacao import (
    formatar_dataframe_brasil
)


DATA_MINIMA = date(1900, 1, 1)
DATA_MAXIMA = date.today()

INDICADORES_IE = {
    "1 - Contribuinte do ICMS": 1,
    "2 - Contribuinte isento": 2,
    "9 - Não contribuinte": 9
}

UFS_BRASIL = [
    "",
    "AC", "AL", "AP", "AM", "BA", "CE",
    "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO"
]


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================
def texto(valor):

    if valor is None:
        return ""

    try:
        if pd.isna(valor):
            return ""
    except Exception:
        pass

    return str(valor)


def inteiro(valor, padrao=9):

    try:

        if valor is None or pd.isna(valor):
            return padrao

        return int(valor)

    except Exception:
        return padrao


def booleano(valor, padrao=True):

    try:

        if valor is None or pd.isna(valor):
            return padrao

        return bool(valor)

    except Exception:
        return padrao


def converter_data_opcional(valor):

    if valor is None:
        return None

    try:

        data_convertida = pd.to_datetime(
            valor,
            errors="coerce"
        )

        if pd.isna(data_convertida):
            return None

        data_convertida = data_convertida.date()

        if data_convertida < DATA_MINIMA:
            return None

        if data_convertida > DATA_MAXIMA:
            return None

        return data_convertida

    except Exception:
        return None


def email_valido(email):

    email = texto(
        email
    ).strip()

    if not email:
        return True

    padrao = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(
        re.match(
            padrao,
            email
        )
    )


def telefone_valido(telefone):

    numeros = re.sub(
        r"\D",
        "",
        texto(telefone)
    )

    if not numeros:
        return True

    if (
        numeros.startswith("55")
        and len(numeros) in (12, 13)
    ):
        numeros = numeros[2:]

    return len(numeros) in (10, 11)


def cpf_valido_formato(cpf):

    numeros = re.sub(
        r"\D",
        "",
        texto(cpf)
    )

    if not numeros:
        return True

    return len(numeros) == 11


def cnpj_valido_formato(cnpj):

    valor = re.sub(
        r"[^A-Za-z0-9]",
        "",
        texto(cnpj)
    )

    if not valor:
        return True

    return len(valor) == 14


def cep_valido_formato(cep):

    numeros = re.sub(
        r"\D",
        "",
        texto(cep)
    )

    if not numeros:
        return True

    return len(numeros) == 8


def ibge_valido_formato(codigo):

    numeros = re.sub(
        r"\D",
        "",
        texto(codigo)
    )

    if not numeros:
        return True

    return len(numeros) == 7


def selecionar_indicador_ie(valor):

    valor = inteiro(
        valor,
        9
    )

    for descricao, codigo in INDICADORES_IE.items():

        if codigo == valor:
            return descricao

    return "9 - Não contribuinte"


def indice_uf(uf):

    uf = texto(
        uf
    ).strip().upper()

    if uf in UFS_BRASIL:
        return UFS_BRASIL.index(uf)

    return 0


def mensagem_duplicado(cliente):

    if not cliente:
        return

    st.error(
        "Já existe um cliente cadastrado com "
        "o mesmo CPF, CNPJ, telefone ou e-mail."
    )

    st.warning(
        f"Cadastro encontrado: "
        f"ID {cliente.get('id')} — "
        f"{cliente.get('nome', '')}"
    )

    if cliente.get("cpf"):
        st.write(
            f"CPF: {cliente.get('cpf')}"
        )

    if cliente.get("cnpj"):
        st.write(
            f"CNPJ: {cliente.get('cnpj')}"
        )

    if cliente.get("telefone"):
        st.write(
            f"Telefone: {cliente.get('telefone')}"
        )

    if cliente.get("email"):
        st.write(
            f"E-mail: {cliente.get('email')}"
        )

    st.info(
        "Use a aba Editar Cliente para atualizar "
        "o cadastro existente."
    )


def validar_dados(
    tipo_pessoa,
    nome,
    razao_social,
    telefone,
    email,
    email_fiscal,
    cpf,
    cnpj,
    cep,
    codigo_ibge,
    cadastro_fiscal,
    logradouro,
    numero,
    bairro,
    cidade,
    uf,
    indicador_ie,
    inscricao_estadual
):

    if tipo_pessoa == "PF" and not nome.strip():

        return (
            False,
            "Informe o nome da pessoa física."
        )

    if tipo_pessoa == "PJ" and not razao_social.strip():

        return (
            False,
            "Informe a razão social."
        )

    if not telefone_valido(
        telefone
    ):

        return (
            False,
            "Informe um telefone válido com DDD."
        )

    if not email_valido(
        email
    ):

        return (
            False,
            "Informe um e-mail válido."
        )

    if not email_valido(
        email_fiscal
    ):

        return (
            False,
            "Informe um e-mail fiscal válido."
        )

    if not cpf_valido_formato(
        cpf
    ):

        return (
            False,
            "O CPF deve possuir 11 dígitos."
        )

    if not cnpj_valido_formato(
        cnpj
    ):

        return (
            False,
            "O CNPJ deve possuir 14 caracteres."
        )

    if not cep_valido_formato(
        cep
    ):

        return (
            False,
            "O CEP deve possuir 8 dígitos."
        )

    if not ibge_valido_formato(
        codigo_ibge
    ):

        return (
            False,
            "O código IBGE deve possuir 7 dígitos."
        )

    if cadastro_fiscal:

        if tipo_pessoa == "PF" and not cpf.strip():

            return (
                False,
                "Informe o CPF para o cadastro fiscal."
            )

        if tipo_pessoa == "PJ" and not cnpj.strip():

            return (
                False,
                "Informe o CNPJ para o cadastro fiscal."
            )

        campos_endereco = {
            "logradouro": logradouro,
            "número": numero,
            "bairro": bairro,
            "cidade": cidade,
            "UF": uf,
            "código IBGE": codigo_ibge
        }

        faltantes = [
            campo
            for campo, valor in campos_endereco.items()
            if not texto(valor).strip()
        ]

        if faltantes:

            return (
                False,
                "Para o cadastro fiscal, informe: "
                + ", ".join(faltantes)
                + "."
            )

        if (
            int(indicador_ie) == 1
            and not inscricao_estadual.strip()
        ):

            return (
                False,
                "Informe a Inscrição Estadual do contribuinte."
            )

    return True, ""


# ==================================================
# TELA
# ==================================================
def tela_clientes():

    st.title("👥 Clientes")

    # Controle usado para recriar o formulário vazio
    # somente depois de um cadastro concluído.
    if "novo_cliente_seq" not in st.session_state:
        st.session_state["novo_cliente_seq"] = 0

    if st.session_state.pop(
        "cliente_cadastrado_sucesso",
        False
    ):
        st.success(
            "Cliente cadastrado com sucesso! "
            "O formulário está pronto para o próximo cadastro."
        )

    abas = st.tabs([
        "📋 Listar Clientes",
        "➕ Novo Cliente",
        "✏️ Editar Cliente",
        "🗑️ Excluir Cliente"
    ])

    # ==================================================
    # LISTAGEM
    # ==================================================
    with abas[0]:

        st.subheader(
            "📋 Clientes Cadastrados"
        )

        df = listar_clientes()

        if df.empty:

            st.info(
                "Nenhum cliente cadastrado."
            )

        else:

            pesquisa = st.text_input(
                "🔎 Pesquisar cliente",
                placeholder=(
                    "Nome, CPF, CNPJ, telefone, "
                    "e-mail ou cidade"
                ),
                key="pesquisa_clientes"
            )

            mostrar_fiscal = st.checkbox(
                "Mostrar dados fiscais e endereço",
                value=False,
                key="mostrar_dados_fiscais_clientes"
            )

            df_filtrado = df.copy()

            if pesquisa:

                termo = pesquisa.strip().lower()

                mascara = pd.Series(
                    False,
                    index=df_filtrado.index
                )

                colunas_pesquisa = [
                    "nome",
                    "razao_social",
                    "nome_fantasia",
                    "cpf",
                    "cnpj",
                    "telefone",
                    "email",
                    "cidade"
                ]

                for coluna in colunas_pesquisa:

                    if coluna in df_filtrado.columns:

                        mascara = mascara | (
                            df_filtrado[coluna]
                            .fillna("")
                            .astype(str)
                            .str.lower()
                            .str.contains(
                                termo,
                                na=False
                            )
                        )

                df_filtrado = df_filtrado[
                    mascara
                ]

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Total",
                len(df)
            )

            col2.metric(
                "Resultado",
                len(df_filtrado)
            )

            col3.metric(
                "Pessoa Física",
                int(
                    (
                        df["tipo_pessoa"]
                        .fillna("PF")
                        .astype(str)
                        .str.upper()
                        == "PF"
                    ).sum()
                )
            )

            col4.metric(
                "Pessoa Jurídica",
                int(
                    (
                        df["tipo_pessoa"]
                        .fillna("")
                        .astype(str)
                        .str.upper()
                        == "PJ"
                    ).sum()
                )
            )

            if mostrar_fiscal:

                colunas = [
                    "id",
                    "tipo_pessoa",
                    "nome",
                    "razao_social",
                    "nome_fantasia",
                    "cpf",
                    "cnpj",
                    "inscricao_estadual",
                    "indicador_ie",
                    "telefone",
                    "email",
                    "email_fiscal",
                    "cep",
                    "logradouro",
                    "numero",
                    "complemento",
                    "bairro",
                    "cidade",
                    "uf",
                    "codigo_municipio_ibge",
                    "ativo"
                ]

            else:

                colunas = [
                    "id",
                    "tipo_pessoa",
                    "nome",
                    "telefone",
                    "email",
                    "cidade",
                    "data_nascimento",
                    "ativo"
                ]

            colunas = [
                coluna
                for coluna in colunas
                if coluna in df_filtrado.columns
            ]

            df_exibicao = (
                formatar_dataframe_brasil(
                    df_filtrado[colunas].copy(),
                    com_hora=False,
                    moedas=False
                )
            )

            df_exibicao = df_exibicao.rename(
                columns={
                    "id": "Código",
                    "tipo_pessoa": "Tipo",
                    "nome": "Nome",
                    "telefone": "Telefone",
                    "email": "E-mail",
                    "cidade": "Cidade",
                    "data_nascimento": "Nascimento",
                    "cpf": "CPF",
                    "cnpj": "CNPJ",
                    "razao_social": "Razão social",
                    "nome_fantasia": "Nome fantasia",
                    "inscricao_estadual": "Inscrição Estadual",
                    "indicador_ie": "Indicador IE",
                    "email_fiscal": "E-mail fiscal",
                    "cep": "CEP",
                    "logradouro": "Logradouro",
                    "numero": "Número",
                    "complemento": "Complemento",
                    "bairro": "Bairro",
                    "uf": "UF",
                    "codigo_municipio_ibge": "Código IBGE",
                    "ativo": "Ativo"
                }
            )

            st.dataframe(
                df_exibicao,
                use_container_width=True,
                hide_index=True
            )

    # ==================================================
    # NOVO CLIENTE
    # ==================================================
    with abas[1]:

        st.subheader(
            "➕ Cadastrar Cliente"
        )

        seq = st.session_state[
            "novo_cliente_seq"
        ]

        # ==================================================
        # CONSULTA AUTOMÁTICA DE CEP
        # ==================================================
        # O retorno da consulta é aplicado antes da criação
        # dos widgets do formulário. Isso evita o erro:
        # "session_state não pode ser modificado após a
        # instanciação do widget".
        chave_cep_pendente = f"cep_pendente_novo_{seq}"
        chave_mensagem_cep = f"mensagem_cep_novo_{seq}"

        dados_cep_pendentes = st.session_state.pop(
            chave_cep_pendente,
            None
        )

        if dados_cep_pendentes:
            st.session_state[f"cep_novo_{seq}"] = (
                dados_cep_pendentes.get("cep", "")
            )
            st.session_state[f"logradouro_novo_{seq}"] = (
                dados_cep_pendentes.get("logradouro", "")
            )
            st.session_state[f"complemento_novo_{seq}"] = (
                dados_cep_pendentes.get("complemento", "")
            )
            st.session_state[f"bairro_novo_{seq}"] = (
                dados_cep_pendentes.get("bairro", "")
            )
            st.session_state[f"cidade_novo_{seq}"] = (
                dados_cep_pendentes.get("cidade", "")
            )

            uf_retornada = str(
                dados_cep_pendentes.get("uf", "")
            ).upper().strip()

            st.session_state[f"uf_novo_{seq}"] = (
                uf_retornada
                if uf_retornada in UFS_BRASIL
                else ""
            )

            st.session_state[f"codigo_ibge_novo_{seq}"] = (
                dados_cep_pendentes.get(
                    "codigo_municipio_ibge",
                    ""
                )
            )

        st.markdown("### 📍 Consulta automática de endereço")

        col_cep, col_consultar = st.columns([3, 1])

        with col_cep:
            cep_consulta = st.text_input(
                "CEP para consulta",
                placeholder="Digite o CEP com 8 números",
                key=f"cep_consulta_novo_{seq}"
            )

        with col_consultar:
            st.write("")

            consultar_endereco = st.button(
                "🔎 Consultar CEP",
                use_container_width=True,
                key=f"consultar_cep_novo_{seq}"
            )

        if consultar_endereco:
            resultado_cep = consultar_cep(
                cep_consulta
            )

            if resultado_cep.get("status") == "sucesso":
                st.session_state[chave_cep_pendente] = (
                    resultado_cep.get("dados", {})
                )
                st.session_state[chave_mensagem_cep] = {
                    "tipo": "sucesso",
                    "texto": (
                        "CEP localizado. Confira o endereço, "
                        "informe o número e complete os campos "
                        "que forem necessários."
                    )
                }
            else:
                st.session_state[chave_mensagem_cep] = {
                    "tipo": "erro",
                    "texto": resultado_cep.get(
                        "mensagem",
                        "Não foi possível consultar o CEP."
                    )
                }

            st.rerun()

        mensagem_cep = st.session_state.get(
            chave_mensagem_cep
        )

        if mensagem_cep:
            if mensagem_cep.get("tipo") == "sucesso":
                st.success(
                    mensagem_cep.get("texto", "")
                )
            else:
                st.warning(
                    mensagem_cep.get("texto", "")
                )

        tipo_pessoa = st.radio(
            "Tipo de pessoa",
            options=["PF", "PJ"],
            format_func=lambda valor: (
                "Pessoa Física"
                if valor == "PF"
                else "Pessoa Jurídica"
            ),
            horizontal=True,
            key=f"tipo_pessoa_novo_cliente_{seq}"
        )

        with st.form(
            f"form_novo_cliente_{tipo_pessoa}_{seq}"
        ):

            cadastro_fiscal = st.checkbox(
                "Cadastro fiscal completo para NF-e/NFC-e",
                value=False,
                key=f"cadastro_fiscal_novo_{seq}"
            )

            st.markdown(
                "### 👤 Dados principais"
            )

            if tipo_pessoa == "PF":

                nome = st.text_input(
                    "Nome completo *",
                    key=f"nome_pf_novo_{seq}"
                )

                razao_social = ""
                nome_fantasia = ""

                cpf = st.text_input(
                    "CPF",
                    placeholder="000.000.000-00",
                    key=f"cpf_novo_{seq}"
                )

                cnpj = ""

            else:

                razao_social = st.text_input(
                    "Razão social *",
                    key=f"razao_social_novo_{seq}"
                )

                nome_fantasia = st.text_input(
                    "Nome fantasia",
                    key=f"nome_fantasia_novo_{seq}"
                )

                nome = razao_social

                cnpj = st.text_input(
                    "CNPJ",
                    placeholder="00.000.000/0000-00",
                    key=f"cnpj_novo_{seq}"
                )

                cpf = ""

            col1, col2 = st.columns(2)

            with col1:

                telefone = st.text_input(
                    "Telefone / WhatsApp",
                    placeholder="(35) 99999-9999",
                    key=f"telefone_novo_{seq}"
                )

            with col2:

                email = st.text_input(
                    "E-mail",
                    placeholder="cliente@email.com",
                    key=f"email_novo_{seq}"
                )

            data_nascimento = None

            if tipo_pessoa == "PF":

                data_nascimento = st.date_input(
                    "🎂 Data de nascimento (opcional)",
                    value=None,
                    min_value=DATA_MINIMA,
                    max_value=DATA_MAXIMA,
                    format="DD/MM/YYYY",
                    key=f"data_nascimento_novo_{seq}"
                )

            with st.expander(
                "📄 Dados fiscais",
                expanded=cadastro_fiscal
            ):

                descricao_indicador = st.selectbox(
                    "Indicador de Inscrição Estadual",
                    options=list(
                        INDICADORES_IE.keys()
                    ),
                    index=2,
                    key=f"indicador_ie_novo_{seq}"
                )

                indicador_ie = INDICADORES_IE[
                    descricao_indicador
                ]

                inscricao_estadual = st.text_input(
                    "Inscrição Estadual",
                    key=f"inscricao_estadual_novo_{seq}"
                )

                inscricao_municipal = st.text_input(
                    "Inscrição Municipal",
                    key=f"inscricao_municipal_novo_{seq}"
                )

                email_fiscal = st.text_input(
                    "E-mail fiscal",
                    key=f"email_fiscal_novo_{seq}"
                )

            with st.expander(
                "📍 Endereço",
                expanded=cadastro_fiscal
            ):

                col1, col2 = st.columns([1, 2])

                with col1:

                    cep = st.text_input(
                        "CEP",
                        placeholder="00000-000",
                        key=f"cep_novo_{seq}"
                    )

                with col2:

                    logradouro = st.text_input(
                        "Logradouro",
                        key=f"logradouro_novo_{seq}"
                    )

                col3, col4 = st.columns([1, 2])

                with col3:

                    numero = st.text_input(
                        "Número",
                        key=f"numero_novo_{seq}"
                    )

                with col4:

                    complemento = st.text_input(
                        "Complemento",
                        key=f"complemento_novo_{seq}"
                    )

                bairro = st.text_input(
                    "Bairro",
                    key=f"bairro_novo_{seq}"
                )

                col5, col6 = st.columns([3, 1])

                with col5:

                    cidade = st.text_input(
                        "Cidade",
                        key=f"cidade_novo_{seq}"
                    )

                with col6:

                    uf = st.selectbox(
                        "UF",
                        options=UFS_BRASIL,
                        key=f"uf_novo_{seq}"
                    )

                codigo_municipio_ibge = st.text_input(
                    "Código IBGE do município",
                    max_chars=7,
                    key=f"codigo_ibge_novo_{seq}"
                )

                codigo_pais = st.text_input(
                    "Código do país",
                    value="1058",
                    key=f"codigo_pais_novo_{seq}"
                )

                pais = st.text_input(
                    "País",
                    value="Brasil",
                    key=f"pais_novo_{seq}"
                )

            observacoes = st.text_area(
                "Observações",
                key=f"observacoes_novo_{seq}"
            )

            ativo = st.checkbox(
                "Cliente ativo",
                value=True,
                key=f"ativo_novo_{seq}"
            )

            salvar = st.form_submit_button(
                "💾 Salvar Cliente",
                use_container_width=True
            )

            if salvar:

                valido, mensagem = validar_dados(
                    tipo_pessoa=tipo_pessoa,
                    nome=nome,
                    razao_social=razao_social,
                    telefone=telefone,
                    email=email,
                    email_fiscal=email_fiscal,
                    cpf=cpf,
                    cnpj=cnpj,
                    cep=cep,
                    codigo_ibge=codigo_municipio_ibge,
                    cadastro_fiscal=cadastro_fiscal,
                    logradouro=logradouro,
                    numero=numero,
                    bairro=bairro,
                    cidade=cidade,
                    uf=uf,
                    indicador_ie=indicador_ie,
                    inscricao_estadual=inscricao_estadual
                )

                if not valido:

                    st.warning(
                        mensagem
                    )

                else:

                    resultado = cadastrar_cliente(
                        nome=nome,
                        telefone=telefone,
                        email=email,
                        cidade=cidade,
                        data_nascimento=data_nascimento,
                        tipo_pessoa=tipo_pessoa,
                        cpf=cpf,
                        cnpj=cnpj,
                        razao_social=razao_social,
                        nome_fantasia=nome_fantasia,
                        inscricao_estadual=inscricao_estadual,
                        inscricao_municipal=inscricao_municipal,
                        indicador_ie=indicador_ie,
                        email_fiscal=email_fiscal,
                        cep=cep,
                        logradouro=logradouro,
                        numero=numero,
                        complemento=complemento,
                        bairro=bairro,
                        uf=uf,
                        codigo_municipio_ibge=codigo_municipio_ibge,
                        codigo_pais=codigo_pais,
                        pais=pais,
                        observacoes=observacoes,
                        ativo=ativo
                    )

                    status = resultado.get(
                        "status"
                    )

                    if status == "sucesso":

                        # Não altera diretamente widgets já criados.
                        # A sequência muda e o formulário seguinte
                        # nasce completamente limpo.
                        st.session_state[
                            "novo_cliente_seq"
                        ] += 1

                        st.session_state[
                            "cliente_cadastrado_sucesso"
                        ] = True

                        # Remove a mensagem da consulta do CEP
                        # vinculada ao formulário concluído.
                        st.session_state.pop(
                            chave_mensagem_cep,
                            None
                        )

                        st.rerun()

                    elif status == "duplicado":

                        mensagem_duplicado(
                            resultado.get(
                                "cliente"
                            )
                        )

                    else:

                        st.error(
                            "Erro ao cadastrar cliente."
                        )

                        if resultado.get("mensagem"):

                            st.caption(
                                resultado["mensagem"]
                            )

    # ==================================================
    # EDITAR CLIENTE
    # ==================================================
    with abas[2]:

        st.subheader(
            "✏️ Editar Cliente"
        )

        df = listar_clientes()

        if df.empty:

            st.info(
                "Nenhum cliente cadastrado."
            )

        else:

            opcoes = {
                (
                    f"{int(row['id'])} - "
                    f"{row.get('nome', '')}"
                ): row
                for _, row in df.iterrows()
            }

            selecionado = st.selectbox(
                "Selecione o cliente",
                options=list(opcoes.keys()),
                index=None,
                placeholder=(
                    "Selecione um cliente para editar"
                ),
                key="cliente_edicao_fiscal"
            )

            if selecionado is None:

                st.info(
                    "Selecione um cliente para editar."
                )

            else:

                cliente = opcoes[
                    selecionado
                ]

                cliente_id = int(
                    cliente.get("id")
                )

                tipo_atual = texto(
                    cliente.get(
                        "tipo_pessoa"
                    )
                ).upper()

                if tipo_atual not in ["PF", "PJ"]:
                    tipo_atual = "PF"

                tipo_pessoa = st.radio(
                    "Tipo de pessoa",
                    options=["PF", "PJ"],
                    index=(
                        0
                        if tipo_atual == "PF"
                        else 1
                    ),
                    format_func=lambda valor: (
                        "Pessoa Física"
                        if valor == "PF"
                        else "Pessoa Jurídica"
                    ),
                    horizontal=True,
                    key=(
                        f"tipo_pessoa_edicao_"
                        f"{cliente_id}"
                    )
                )

                with st.form(
                    (
                        f"form_editar_cliente_"
                        f"{cliente_id}_{tipo_pessoa}"
                    )
                ):

                    st.markdown(
                        "### 👤 Dados principais"
                    )

                    if tipo_pessoa == "PF":

                        nome = st.text_input(
                            "Nome completo *",
                            value=texto(
                                cliente.get("nome")
                            )
                        )

                        cpf = st.text_input(
                            "CPF",
                            value=texto(
                                cliente.get("cpf")
                            )
                        )

                        razao_social = ""
                        nome_fantasia = ""
                        cnpj = ""

                    else:

                        razao_social = st.text_input(
                            "Razão social *",
                            value=(
                                texto(
                                    cliente.get(
                                        "razao_social"
                                    )
                                )
                                or texto(
                                    cliente.get("nome")
                                )
                            )
                        )

                        nome_fantasia = st.text_input(
                            "Nome fantasia",
                            value=texto(
                                cliente.get(
                                    "nome_fantasia"
                                )
                            )
                        )

                        cnpj = st.text_input(
                            "CNPJ",
                            value=texto(
                                cliente.get("cnpj")
                            )
                        )

                        nome = razao_social
                        cpf = ""

                    col1, col2 = st.columns(2)

                    with col1:

                        telefone = st.text_input(
                            "Telefone / WhatsApp",
                            value=texto(
                                cliente.get("telefone")
                            )
                        )

                    with col2:

                        email = st.text_input(
                            "E-mail",
                            value=texto(
                                cliente.get("email")
                            )
                        )

                    data_nascimento = None

                    if tipo_pessoa == "PF":

                        data_nascimento = st.date_input(
                            "🎂 Data de nascimento (opcional)",
                            value=converter_data_opcional(
                                cliente.get(
                                    "data_nascimento"
                                )
                            ),
                            min_value=DATA_MINIMA,
                            max_value=DATA_MAXIMA,
                            format="DD/MM/YYYY"
                        )

                    with st.expander(
                        "📄 Dados fiscais",
                        expanded=False
                    ):

                        indicador_atual = (
                            selecionar_indicador_ie(
                                cliente.get(
                                    "indicador_ie"
                                )
                            )
                        )

                        descricao_indicador = st.selectbox(
                            "Indicador de Inscrição Estadual",
                            options=list(
                                INDICADORES_IE.keys()
                            ),
                            index=list(
                                INDICADORES_IE.keys()
                            ).index(
                                indicador_atual
                            )
                        )

                        indicador_ie = INDICADORES_IE[
                            descricao_indicador
                        ]

                        inscricao_estadual = st.text_input(
                            "Inscrição Estadual",
                            value=texto(
                                cliente.get(
                                    "inscricao_estadual"
                                )
                            )
                        )

                        inscricao_municipal = st.text_input(
                            "Inscrição Municipal",
                            value=texto(
                                cliente.get(
                                    "inscricao_municipal"
                                )
                            )
                        )

                        email_fiscal = st.text_input(
                            "E-mail fiscal",
                            value=texto(
                                cliente.get(
                                    "email_fiscal"
                                )
                            )
                        )

                    with st.expander(
                        "📍 Endereço",
                        expanded=False
                    ):

                        col1, col2 = st.columns([1, 2])

                        with col1:

                            cep = st.text_input(
                                "CEP",
                                value=texto(
                                    cliente.get("cep")
                                )
                            )

                        with col2:

                            logradouro = st.text_input(
                                "Logradouro",
                                value=texto(
                                    cliente.get(
                                        "logradouro"
                                    )
                                )
                            )

                        col3, col4 = st.columns([1, 2])

                        with col3:

                            numero = st.text_input(
                                "Número",
                                value=texto(
                                    cliente.get("numero")
                                )
                            )

                        with col4:

                            complemento = st.text_input(
                                "Complemento",
                                value=texto(
                                    cliente.get(
                                        "complemento"
                                    )
                                )
                            )

                        bairro = st.text_input(
                            "Bairro",
                            value=texto(
                                cliente.get("bairro")
                            )
                        )

                        col5, col6 = st.columns([3, 1])

                        with col5:

                            cidade = st.text_input(
                                "Cidade",
                                value=texto(
                                    cliente.get("cidade")
                                )
                            )

                        with col6:

                            uf = st.selectbox(
                                "UF",
                                options=UFS_BRASIL,
                                index=indice_uf(
                                    cliente.get("uf")
                                )
                            )

                        codigo_municipio_ibge = st.text_input(
                            "Código IBGE do município",
                            value=texto(
                                cliente.get(
                                    "codigo_municipio_ibge"
                                )
                            ),
                            max_chars=7
                        )

                        codigo_pais = st.text_input(
                            "Código do país",
                            value=(
                                texto(
                                    cliente.get(
                                        "codigo_pais"
                                    )
                                )
                                or "1058"
                            )
                        )

                        pais = st.text_input(
                            "País",
                            value=(
                                texto(
                                    cliente.get("pais")
                                )
                                or "Brasil"
                            )
                        )

                    observacoes = st.text_area(
                        "Observações",
                        value=texto(
                            cliente.get(
                                "observacoes"
                            )
                        )
                    )

                    ativo = st.checkbox(
                        "Cliente ativo",
                        value=booleano(
                            cliente.get("ativo"),
                            True
                        )
                    )

                    atualizar = st.form_submit_button(
                        "💾 Atualizar Cliente",
                        use_container_width=True
                    )

                    if atualizar:

                        valido, mensagem = validar_dados(
                            tipo_pessoa=tipo_pessoa,
                            nome=nome,
                            razao_social=razao_social,
                            telefone=telefone,
                            email=email,
                            email_fiscal=email_fiscal,
                            cpf=cpf,
                            cnpj=cnpj,
                            cep=cep,
                            codigo_ibge=(
                                codigo_municipio_ibge
                            ),
                            cadastro_fiscal=False,
                            logradouro=logradouro,
                            numero=numero,
                            bairro=bairro,
                            cidade=cidade,
                            uf=uf,
                            indicador_ie=indicador_ie,
                            inscricao_estadual=(
                                inscricao_estadual
                            )
                        )

                        if not valido:

                            st.warning(
                                mensagem
                            )

                        else:

                            resultado = atualizar_cliente(
                                cliente_id=cliente_id,
                                nome=nome,
                                telefone=telefone,
                                email=email,
                                cidade=cidade,
                                data_nascimento=data_nascimento,
                                tipo_pessoa=tipo_pessoa,
                                cpf=cpf,
                                cnpj=cnpj,
                                razao_social=razao_social,
                                nome_fantasia=nome_fantasia,
                                inscricao_estadual=(
                                    inscricao_estadual
                                ),
                                inscricao_municipal=(
                                    inscricao_municipal
                                ),
                                indicador_ie=indicador_ie,
                                email_fiscal=email_fiscal,
                                cep=cep,
                                logradouro=logradouro,
                                numero=numero,
                                complemento=complemento,
                                bairro=bairro,
                                uf=uf,
                                codigo_municipio_ibge=(
                                    codigo_municipio_ibge
                                ),
                                codigo_pais=codigo_pais,
                                pais=pais,
                                observacoes=observacoes,
                                ativo=ativo
                            )

                            status = resultado.get(
                                "status"
                            )

                            if status == "sucesso":

                                st.success(
                                    "Cliente atualizado "
                                    "com sucesso!"
                                )

                                st.rerun()

                            elif status == "duplicado":

                                mensagem_duplicado(
                                    resultado.get(
                                        "cliente"
                                    )
                                )

                            else:

                                st.error(
                                    "Erro ao atualizar cliente."
                                )

                                if resultado.get(
                                    "mensagem"
                                ):

                                    st.caption(
                                        resultado["mensagem"]
                                    )

    # ==================================================
    # EXCLUIR CLIENTE
    # ==================================================
    with abas[3]:

        st.subheader(
            "🗑️ Excluir Cliente"
        )

        df = listar_clientes()

        if df.empty:

            st.info(
                "Nenhum cliente cadastrado."
            )

        else:

            opcoes = {
                (
                    f"{int(row['id'])} - "
                    f"{row.get('nome', '')}"
                ): row
                for _, row in df.iterrows()
            }

            selecionado = st.selectbox(
                "Selecione o cliente",
                options=list(opcoes.keys()),
                index=None,
                placeholder="Selecione um cliente",
                key="cliente_exclusao_fiscal"
            )

            if selecionado is None:

                st.info(
                    "Selecione o cliente que deseja excluir."
                )

            else:

                cliente = opcoes[
                    selecionado
                ]

                cliente_id = int(
                    cliente.get("id")
                )

                with st.container(
                    border=True
                ):

                    st.write(
                        f"**Cliente:** "
                        f"{cliente.get('nome', '')}"
                    )

                    st.write(
                        f"**Tipo:** "
                        f"{cliente.get('tipo_pessoa', 'PF')}"
                    )

                    if cliente.get("cpf"):

                        st.write(
                            f"**CPF:** "
                            f"{cliente.get('cpf')}"
                        )

                    if cliente.get("cnpj"):

                        st.write(
                            f"**CNPJ:** "
                            f"{cliente.get('cnpj')}"
                        )

                confirmar = st.checkbox(
                    "Confirmo que desejo excluir este cliente",
                    key=f"confirmar_exclusao_{cliente_id}"
                )

                if st.button(
                    "🗑️ Excluir Cliente",
                    use_container_width=True,
                    key=f"excluir_cliente_{cliente_id}"
                ):

                    if not confirmar:

                        st.warning(
                            "Marque a confirmação "
                            "antes de excluir."
                        )

                    else:

                        resultado = excluir_cliente(
                            cliente_id
                        )

                        if resultado is True:

                            st.success(
                                "Cliente excluído "
                                "com sucesso!"
                            )

                            st.rerun()

                        elif resultado == "possui_vendas":

                            st.error(
                                "Não é possível excluir: "
                                "o cliente possui vendas vinculadas."
                            )

                        elif resultado == "possui_contas":

                            st.error(
                                "Não é possível excluir: "
                                "o cliente possui contas vinculadas."
                            )

                        elif resultado == "nao_encontrado":

                            st.error(
                                "Cliente não encontrado."
                            )

                        else:

                            st.error(
                                "Erro ao excluir cliente."
                            )