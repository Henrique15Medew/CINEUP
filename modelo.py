from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Base declarativa
Base = declarative_base()

# =========================
# Tabela de Usuários
# =========================
class Usuario(Base):
   __tablename__ = 'usuarios'

   id = Column(Integer, primary_key=True)
   nome = Column(String(100), nullable=False)
   email = Column(String(100), unique=True, nullable=False)
   senha_hash = Column(String(200), nullable=False)
   is_admin = Column(Boolean, default=False)

   # Relacionamento com Avaliações
   avaliacoes = relationship("Avaliacao", back_populates="usuario", cascade="all, delete-orphan")

   # Métodos para senha segura
   def set_senha(self, senha):
       self.senha_hash = generate_password_hash(senha)

   def verificar_senha(self, senha):
       return check_password_hash(self.senha_hash, senha)

   def __repr__(self):
       return f"<Usuario(nome={self.nome}, email={self.email})>"

# =========================
# Tabela de Filmes
# =========================
class Filme(Base):
   __tablename__ = 'filmes'

   id = Column(Integer, primary_key=True)
   titulo = Column(String(200), nullable=False)
   genero = Column(String(50), nullable=False)
   ano = Column(Integer, nullable=False)
   imagem = Column(String(500))  # NOVO CAMPO
   descricao = Column(Text)      # NOVO CAMPO
   duracao = Column(String(50))  # NOVO CAMPO
   diretor = Column(String(100)) # NOVO CAMPO
   elenco = Column(Text)         # NOVO CAMPO
   streaming = Column(String(500)) # NOVO CAMPO

   # Relacionamento com Avaliações
   avaliacoes = relationship("Avaliacao", back_populates="filme", cascade="all, delete-orphan")

   def __repr__(self):
       return f"<Filme(titulo={self.titulo}, ano={self.ano})>"

# =========================
# Tabela de Avaliações
# =========================
class Avaliacao(Base):
   __tablename__ = 'avaliacoes'

   id = Column(Integer, primary_key=True)
   nota = Column(Integer, nullable=False)
   comentario = Column(Text)
   data = Column(DateTime, default=datetime.utcnow)

   usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
   filme_id = Column(Integer, ForeignKey('filmes.id'), nullable=False)

   usuario = relationship("Usuario", back_populates="avaliacoes")
   filme = relationship("Filme", back_populates="avaliacoes")

   def __repr__(self):
       return f"<Avaliacao(usuario_id={self.usuario_id}, filme_id={self.filme_id}, nota={self.nota})>"