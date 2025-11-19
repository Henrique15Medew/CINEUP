import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from modelo import Base, Usuario, Filme, Avaliacao

# Carrega variáveis do .env
load_dotenv()

# Configuração do banco
DATABASE_URL = os.getenv("DATABASE_URL")


def atualizar_estrutura_banco(engine):
    """Atualiza a estrutura do banco sem apagar dados"""
    try:
        print("🔄 Verificando estrutura do banco...")
        inspector = inspect(engine)

        # Verificar se a tabela filmes existe
        if 'filmes' not in inspector.get_table_names():
            print("❌ Tabela 'filmes' não existe. Criando todas as tabelas...")
            Base.metadata.create_all(engine)
            return True

        # Verificar colunas da tabela filmes
        colunas_existentes = [col['name'] for col in inspector.get_columns('filmes')]
        print(f"📋 Colunas existentes na tabela filmes: {colunas_existentes}")

        colunas_necessarias = ['imagem', 'descricao', 'duracao', 'diretor', 'elenco', 'streaming']
        colunas_faltantes = [col for col in colunas_necessarias if col not in colunas_existentes]

        if colunas_faltantes:
            print(f"🔧 Adicionando colunas faltantes: {colunas_faltantes}")
            with engine.begin() as conn:
                for coluna in colunas_faltantes:
                    try:
                        if coluna == 'imagem':
                            conn.execute(text(f"ALTER TABLE filmes ADD {coluna} VARCHAR(500)"))
                        elif coluna == 'streaming':
                            conn.execute(text(f"ALTER TABLE filmes ADD {coluna} VARCHAR(500)"))
                        elif coluna in ['descricao', 'elenco']:
                            conn.execute(text(f"ALTER TABLE filmes ADD {coluna} TEXT"))
                        else:
                            conn.execute(text(f"ALTER TABLE filmes ADD {coluna} VARCHAR(100)"))
                        print(f"✅ Coluna {coluna} adicionada")
                    except Exception as e:
                        print(f"⚠️ Erro ao adicionar coluna {coluna}: {e}")
            return True
        else:
            print("✅ Todas as colunas já existem")
            return True

    except Exception as e:
        print(f"❌ Erro ao verificar estrutura: {e}")
        return False


def criar_banco_e_tabelas():
    try:
        print("Conectando ao banco de dados SQL Server...")
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)

        # Testa a conexão
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Conexão com SQL Server estabelecida")

        # Atualizar estrutura do banco
        if not atualizar_estrutura_banco(engine):
            print("❌ Falha ao atualizar estrutura do banco")
            return False

        # Cria sessão
        Session = sessionmaker(bind=engine)
        session = Session()

        # Verifica se o admin já existe
        admin_existente = session.query(Usuario).filter_by(email="admin@cineup.com").first()

        if not admin_existente:
            print("👤 Criando usuário administrador...")
            admin = Usuario(
                nome="Administrador",
                email="admin@cineup.com",
                is_admin=True
            )
            admin.set_senha("admin123")
            session.add(admin)
            session.commit()
            print("✅ Usuário admin criado: admin@cineup.com / admin123")
        else:
            print("✅ Usuário admin já existe")

        # Mostra total de usuários e filmes
        total_usuarios = session.query(Usuario).count()
        total_filmes = session.query(Filme).count()
        print(f"📊 Total de usuários no sistema: {total_usuarios}")
        print(f"🎬 Total de filmes no sistema: {total_filmes}")

        session.close()
        return True

    except Exception as e:
        print(f"❌ Erro ao configurar banco: {e}")
        return False


if __name__ == "__main__":
    print("=== ATUALIZAÇÃO DO BANCO DE DADOS CINEUP ===")
    print(f"📁 Banco: {DATABASE_URL.split('/')[-1].split('?')[0]}")
    print("=" * 50)

    if criar_banco_e_tabelas():
        print("\n🎉 Atualização concluída com sucesso!")
        print("📋 Estrutura do banco atualizada:")
        print("   - Tabela 'filmes' agora tem campos: imagem, descricao, duracao, diretor, elenco, streaming")
        print("\n🔑 Credenciais do Admin:")
        print("   📧 Email: admin@cineup.com")
        print("   🔐 Senha: admin123")
        print("\n🚀 Agora você pode adicionar filmes com imagens!")
    else:
        print("\n💥 Falha na atualização do banco!")