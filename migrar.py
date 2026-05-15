from database.connection import conectar


def migrar_fluxo_caixa_para_movimentacoes():

    conn = conectar()
    cursor = conn.cursor()

    try:

        sql = """
            INSERT INTO movimentacoes (tipo, valor, descricao, origem, data)
            SELECT
                LOWER(tipo),
                valor,
                descricao,
                origem,
                NOW()
            FROM fluxo_caixa
            WHERE NOT EXISTS (
                SELECT 1
                FROM movimentacoes m
                WHERE
                    m.valor = fluxo_caixa.valor
                    AND m.descricao = fluxo_caixa.descricao
                    AND m.origem = fluxo_caixa.origem
            );
        """

        cursor.execute(sql)
        conn.commit()

        print("✅ Migração concluída com sucesso!")

    except Exception as erro:
        conn.rollback()
        print("❌ Erro na migração:", erro)

    finally:
        cursor.close()
        conn.close()


# EXECUÇÃO
if __name__ == "__main__":
    migrar_fluxo_caixa_para_movimentacoes()