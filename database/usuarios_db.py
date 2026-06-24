import pandas as pd
import bcrypt

from database.connection import conectar


# ==================================================
# LISTAR USUÁRIOS
# ==================================================
def listar_usuarios():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                nome,
                usuario,
                perfil,
                ativo,
                pode_dashboard,
                pode_caixa,
                pode_clientes,
                pode_produtos,
                pode_vendas,
                pode_financeiro,
                pode_contas_pagar,
                pode_contas_receber,
                pode_configuracoes
            FROM usuarios
            ORDER BY nome
        """

        return pd.read_sql(query, conn)

    except Exception as erro:

        print("Erro ao listar usuários:", erro)
        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# CRIAR USUÁRIO
# ==================================================
def criar_usuario(
    nome,
    usuario,
    senha,
    perfil,
    ativo,
    pode_dashboard,
    pode_caixa,
    pode_clientes,
    pode_produtos,
    pode_vendas,
    pode_financeiro,
    pode_contas_pagar,
    pode_contas_receber,
    pode_despesas=True,
    pode_configuracoes=True
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        senha_hash = bcrypt.hashpw(
            senha.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute("""
            INSERT INTO usuarios (
                nome,
                usuario,
                senha,
                perfil,
                ativo,
                pode_dashboard,
                pode_caixa,
                pode_clientes,
                pode_produtos,
                pode_vendas,
                pode_financeiro,
                pode_contas_pagar,
                pode_contas_receber,
                pode_configuracoes
            )
            VALUES (
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s
            )
        """, (

            nome,
            usuario,
            senha_hash,
            perfil,
            ativo,

            pode_dashboard,
            pode_caixa,
            pode_clientes,
            pode_produtos,
            pode_vendas,
            pode_financeiro,
            pode_contas_pagar,
            pode_contas_receber,
            pode_configuracoes

        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print("Erro ao criar usuário:", erro)

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# AUTENTICAR USUÁRIO
# ==================================================
def autenticar_usuario(usuario, senha):

    conn = conectar()

    if conn is None:
        print("Erro: conexão com banco falhou.")
        return None

    cursor = conn.cursor()

    try:

        usuario = usuario.strip().lower()

        cursor.execute("""
            SELECT
                id,
                nome,
                usuario,
                senha,
                perfil,
                ativo,
                pode_dashboard,
                pode_caixa,
                pode_clientes,
                pode_produtos,
                pode_vendas,
                pode_financeiro,
                pode_contas_pagar,
                pode_contas_receber,
                pode_configuracoes
            FROM usuarios
            WHERE LOWER(TRIM(usuario)) = %s
        """, (usuario,))

        dados = cursor.fetchone()

        if dados is None:

            print(f"Usuário não encontrado: {usuario}")
            return None

        senha_hash = dados[3]

        try:

            senha_valida = bcrypt.checkpw(
                senha.encode("utf-8"),
                senha_hash.encode("utf-8")
            )

        except Exception as erro:

            print("Erro ao validar hash bcrypt:", erro)
            return None

        if not senha_valida:

            print(f"Senha inválida para usuário: {usuario}")
            return None

        if not dados[5]:

            print(f"Usuário inativo: {usuario}")
            return None

        print(f"Login realizado com sucesso: {usuario}")

        return {

            "id": dados[0],
            "nome": dados[1],
            "usuario": dados[2],
            "perfil": dados[4],

            "pode_dashboard": bool(dados[6]),
            "pode_caixa": bool(dados[7]),
            "pode_clientes": bool(dados[8]),
            "pode_produtos": bool(dados[9]),
            "pode_vendas": bool(dados[10]),
            "pode_financeiro": bool(dados[11]),
            "pode_contas_pagar": bool(dados[12]),
            "pode_contas_receber": bool(dados[13]),
            "pode_configuracoes": bool(dados[14]),

            # permissões extras
            "pode_despesas": True,
            "pode_usuarios": True,
            "pode_movimentacoes": True,
            "pode_fechamento_caixa": True,
            "pode_relatorios": True

        }

    except Exception as erro:

        print("Erro ao autenticar usuário:", erro)

        return None

    finally:

        cursor.close()
        conn.close()