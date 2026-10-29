import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Define o nome e o caminho do arquivo do banco de dados SQLite
DB_NAME = "valorant_bot.db"
DATABASE_URL = f"sqlite:///{DB_NAME}"

# Cria o motor (engine) que gerencia a conexão com o arquivo SQLite
engine = create_engine(DATABASE_URL, echo=False)

# Cria a classe base para definirmos as nossas tabelas
Base = declarative_base()

# Cria a fábrica de sessões para interagir com o banco
SessionLocal = sessionmaker(bind=engine)


# ==========================================
# DEFINIÇÃO DA TABELA DE USUÁRIOS
# ==========================================
class User(Base):
    __tablename__ = "users"  # Nome da tabela no banco de dados SQLite

    # Colunas da tabela
    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(String, unique=True, nullable=False)  # ID único do usuário no Discord
    created_at = Column(DateTime, default=datetime.utcnow)  # Data de cadastro

    def __repr__(self):
        return f"<User discord_id={self.discord_id}>"


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(String, nullable=False)
    skin_uuid = Column(String, nullable=False)
    skin_nome = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # impede a mesma skin de ser favoritada duas vezes pela mesma pessoa
    __table_args__ = (UniqueConstraint("discord_id", "skin_uuid"),)

def init_db():
    """Função para criar fisicamente o arquivo e as tabelas no disco"""
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados e tabelas criados/verificados com sucesso!")