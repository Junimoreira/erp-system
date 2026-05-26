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

# ==================================================
# AUTENTICAR USUÁRIO
# ==================================================
def autenticar_usuario(usuario, senha):

    conn = conectar()

    if conn is None:
        return None

    cursor = conn.cursor()

    try:

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
                pode_despesas,
                pode_configuracoes

            FROM usuarios

            WHERE usuario = %s

        """, (usuario,))

        dados = cursor.fetchone()

        if dados is None:

            print("Usuário não encontrado.")

            return None

        senha_hash = dados[3]

        # Valida senha bcrypt
        senha_valida = bcrypt.checkpw(
            senha.encode(),
            senha_hash.encode()
        )

        if not senha_valida:

            print("Senha inválida.")

            return None

        # Verifica se usuário está ativo
        if not dados[5]:

            print("Usuário inativo.")

            return None

        usuario_logado = {

            "id": dados[0],
            "nome": dados[1],
            "usuario": dados[2],
            "perfil": dados[4],

            "pode_dashboard": dados[6],
            "pode_caixa": dados[7],
            "pode_clientes": dados[8],
            "pode_produtos": dados[9],
            "pode_vendas": dados[10],
            "pode_financeiro": dados[11],
            "pode_contas_pagar": dados[12],
            "pode_contas_receber": dados[13],
            "pode_despesas": dados[14],
            "pode_configuracoes": dados[15]

        }

        return usuario_logado

    except Exception as erro:

        print(f"Erro ao autenticar usuário: {erro}")

        return None

    finally:

        cursor.close()
        conn.close()