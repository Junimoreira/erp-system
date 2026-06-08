import streamlit as st
import xml.etree.ElementTree as ET
from database.connection import conectar


# ==================================================
# XML -> FORNECEDOR
# ==================================================
def extrair_fornecedor_xml(arquivo):

    tree = ET.parse(arquivo)
    root = tree.getroot()

    ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

    emit = root.find(".//nfe:emit", ns)
    if emit is None:
        return None

    endereco = emit.find("nfe:enderEmit", ns)

    return {
        "cnpj": emit.findtext("nfe:CNPJ", default="", namespaces=ns),
        "razao_social": emit.findtext("nfe:xNome", default="", namespaces=ns),
        "nome_fantasia": emit.findtext("nfe:xFant", default="", namespaces=ns),
        "inscricao_estadual": emit.findtext("nfe:IE", default="", namespaces=ns),

        "endereco": endereco.findtext("nfe:xLgr", default="", namespaces=ns) if endereco is not None else "",
        "numero": endereco.findtext("nfe:nro", default="", namespaces=ns) if endereco is not None else "",
        "bairro": endereco.findtext("nfe:xBairro", default="", namespaces=ns) if endereco is not None else "",
        "cidade": endereco.findtext("nfe:xMun", default="", namespaces=ns) if endereco is not None else "",
        "estado": endereco.findtext("nfe:UF", default="", namespaces=ns) if endereco is not None else "",
        "cep": endereco.findtext("nfe:CEP", default="", namespaces=ns) if endereco is not None else "",
        "ativo": True
    }


# ==================================================
# BANCO
# ==================================================
def salvar_fornecedor(conn, f):

    cur = conn.cursor()

    cur.execute("""
        INSERT INTO fornecedores (
            cnpj, razao_social, nome_fantasia,
            inscricao_estadual,
            endereco, numero, bairro, cidade, estado, cep,
            ativo, data_cadastro
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
        ON CONFLICT (cnpj) DO UPDATE SET
            razao_social = EXCLUDED.razao_social,
            nome_fantasia = EXCLUDED.nome_fantasia,
            inscricao_estadual = EXCLUDED.inscricao_estadual,
            endereco = EXCLUDED.endereco,
            numero = EXCLUDED.numero,
            bairro = EXCLUDED.bairro,
            cidade = EXCLUDED.cidade,
            estado = EXCLUDED.estado,
            cep = EXCLUDED.cep
    """, (
        f["cnpj"],
        f["razao_social"],
        f["nome_fantasia"],
        f["inscricao_estadual"],
        f["endereco"],
        f["numero"],
        f["bairro"],
        f["cidade"],
        f["estado"],
        f["cep"],
        f["ativo"]
    ))

    conn.commit()


# ==================================================
# TELA PRINCIPAL
# ==================================================
def tela_fornecedores():

    st.title("🏢 Fornecedores")

    conn = conectar()

    tab1, tab2, tab3 = st.tabs([
        "📋 Lista",
        "➕ Cadastro",
        "📥 Importar XML"
    ])

    # ==================================================
    # ABA 1 - LISTA
    # ==================================================
    with tab1:
        st.subheader("Lista de Fornecedores")

        df = conn.cursor()
        df.execute("SELECT id, razao_social, cnpj, cidade, estado FROM fornecedores ORDER BY id DESC")
        dados = df.fetchall()

        st.dataframe(dados, use_container_width=True)


    # ==================================================
    # ABA 2 - CADASTRO MANUAL
    # ==================================================
    with tab2:
        st.subheader("Cadastro Manual")

        with st.form("form_fornecedor"):

            razao = st.text_input("Razão Social")
            fantasia = st.text_input("Nome Fantasia")
            cnpj = st.text_input("CNPJ")

            cidade = st.text_input("Cidade")
            estado = st.text_input("Estado")

            enviar = st.form_submit_button("Salvar")

            if enviar:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO fornecedores (razao_social, nome_fantasia, cnpj, cidade, estado, ativo, data_cadastro)
                    VALUES (%s,%s,%s,%s,%s,true,NOW())
                """, (razao, fantasia, cnpj, cidade, estado))

                conn.commit()
                st.success("Fornecedor cadastrado com sucesso!")


    # ==================================================
    # ABA 3 - IMPORTAÇÃO XML
    # ==================================================
    with tab3:

        st.subheader("Importar Fornecedores via XML")

        arquivos = st.file_uploader(
            "Selecione XMLs de NF-e",
            type=["xml"],
            accept_multiple_files=True
        )

        if arquivos:

            progresso = st.progress(0)

            criados = 0
            atualizados = 0
            ignorados = 0

            for i, arquivo in enumerate(arquivos):

                try:
                    f = extrair_fornecedor_xml(arquivo)

                    if not f or not f["cnpj"]:
                        ignorados += 1
                        continue

                    cur = conn.cursor()
                    cur.execute("SELECT id FROM fornecedores WHERE cnpj = %s", (f["cnpj"],))
                    existe = cur.fetchone()

                    salvar_fornecedor(conn, f)

                    if existe:
                        atualizados += 1
                    else:
                        criados += 1

                except Exception as e:
                    st.error(f"Erro: {arquivo.name} - {str(e)}")
                    ignorados += 1

                progresso.progress((i + 1) / len(arquivos))

            st.success("Importação finalizada!")
            st.write(f"Criados: {criados}")
            st.write(f"Atualizados: {atualizados}")
            st.write(f"Ignorados: {ignorados}")