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
                pode_configuracoes
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
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
                pode_configuracoes
            FROM usuarios
            WHERE usuario = %s
        """, (usuario,))

        dados = cursor.fetchone()

        if dados is None:
            return None

        senha_hash = dados[3]

        if not bcrypt.checkpw(
            senha.encode(),
            senha_hash.encode()
        ):
            return None

        if not dados[5]:
            return None

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

            # permissões extras temporárias
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