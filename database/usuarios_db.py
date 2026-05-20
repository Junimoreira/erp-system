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
                pode_despesas,
                pode_configuracoes

            FROM usuarios

            ORDER BY nome
        """

        df = pd.read_sql(query, conn)

        return df

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
    pode_despesas,
    pode_configuracoes
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        senha_hash = bcrypt.hashpw(
            senha.encode(),
            bcrypt.gensalt()
        ).decode()

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
                pode_despesas,
                pode_configuracoes

            )

            VALUES (

                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s

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
            pode_despesas,
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