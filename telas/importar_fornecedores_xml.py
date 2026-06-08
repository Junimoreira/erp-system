import streamlit as st
import xml.etree.ElementTree as ET
from database.connection import conectar


# ==================================================
# EXTRAI FORNECEDOR DO XML
# ==================================================
def extrair_fornecedor_xml(arquivo):
    tree = ET.parse(arquivo)
    root = tree.getroot()

    ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

    emit = root.find(".//nfe:emit", ns)
    if emit is None:
        return None

    endereco = emit.find("nfe:enderEmit", ns)

    fornecedor = {
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

        "telefone": "",
        "email": "",
        "ativo": True
    }

    return fornecedor


# ==================================================
# VERIFICAR SE EXISTE
# ==================================================
def fornecedor_existe(conn, cnpj):
    cur = conn.cursor()
    cur.execute("SELECT id FROM fornecedores WHERE cnpj = %s", (cnpj,))
    return cur.fetchone()


# ==================================================
# INSERIR / ATUALIZAR
# ==================================================
def salvar_fornecedor(conn, f):

    cur = conn.cursor()

    cur.execute("""
        INSERT INTO fornecedores (
            cnpj, razao_social, nome_fantasia,
            inscricao_estadual, telefone, email,
            endereco, numero, bairro, cidade, estado, cep,
            ativo, data_cadastro
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
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
        f["telefone"],
        f["email"],
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
# TELA STREAMLIT
# ==================================================
def tela_importar_fornecedores_xml():

    st.title("📥 Importação de Fornecedores via XML (NF-e)")

    conn = conectar()

    arquivos = st.file_uploader(
        "Selecione os XMLs de NF-e",
        type=["xml"],
        accept_multiple_files=True
    )

    if arquivos:

        total = len(arquivos)
        progresso = st.progress(0)

        criados = 0
        atualizados = 0
        ignorados = 0

        log = st.empty()

        for i, arquivo in enumerate(arquivos):

            try:
                fornecedor = extrair_fornecedor_xml(arquivo)

                if not fornecedor:
                    st.warning(f"XML inválido: {arquivo.name}")
                    ignorados += 1
                    continue

                cnpj = fornecedor["cnpj"]

                if not cnpj:
                    st.warning(f"Sem CNPJ: {arquivo.name}")
                    ignorados += 1
                    continue

                existe = fornecedor_existe(conn, cnpj)

                salvar_fornecedor(conn, fornecedor)

                if existe:
                    atualizados += 1
                else:
                    criados += 1

            except Exception as e:
                st.error(f"Erro no arquivo {arquivo.name}: {str(e)}")
                ignorados += 1

            progresso.progress((i + 1) / total)

            log.info(
                f"Processando... {i+1}/{total} | "
                f"Criados: {criados} | Atualizados: {atualizados} | Ignorados: {ignorados}"
            )

        st.success("✔ Importação finalizada!")

        st.write("### 📊 Resumo")
        st.write(f"✔ Criados: {criados}")
        st.write(f"🔄 Atualizados: {atualizados}")
        st.write(f"⚠ Ignorados: {ignorados}")