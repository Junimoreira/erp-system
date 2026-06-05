import bcrypt
from database.connection import conectar

# ==========================================
# DADOS DO USUÁRIO
# ==========================================
nome = "Administrador"
usuario = "admin"
senha = "123456@"
perfil = "admin"  # admin / diretor / atendente

# ==========================================
# HASH DA SENHA
# ==========================================
senha_hash = bcrypt.hashpw(
    senha.encode(),
    bcrypt.gensalt()
).decode()

# ==========================================
# CONEXÃO
# ==========================================
conn = conectar()
cur = conn.cursor()

try:

    cur.execute("""
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
            pode_movimentacoes,
            pode_relatorios,
            pode_configuracoes,
            pode_usuarios,
            pode_fechamento_caixa
        )
        VALUES (
            %s, %s, %s, %s, TRUE,

            TRUE, TRUE, TRUE, TRUE, TRUE,
            TRUE, TRUE, TRUE, TRUE,
            TRUE, TRUE, TRUE, TRUE
        )
    """, (
        nome,
        usuario,
        senha_hash,
        perfil
    ))

    conn.commit()

    print("✅ Usuário ADMIN criado com todas permissões!")

except Exception as e:

    conn.rollback()
    print("❌ Erro ao criar usuário:", e)

finally:

    cur.close()
    conn.close()