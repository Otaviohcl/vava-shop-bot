from database import SessionLocal, User

# Cria uma sessão de conexão com o banco de dados
session = SessionLocal()

# Simula a criação de um novo usuário do Discord
novo_usuario = User(discord_id="123456789987654321")

# Adiciona na sessão e confirma (commit) no banco de dados
session.add(novo_usuario)
session.commit()

print("✅ Usuário cadastrado com sucesso no banco de dados!")

# Fecha a sessão
session.close()