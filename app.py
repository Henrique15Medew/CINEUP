from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modelo import Base, Usuario, Filme, Avaliacao
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Necessário para sessões

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db_session = Session()


# ---------------- ROTAS ---------------- #

# Página principal (HOME PÚBLICO)
@app.route('/')
def main():
    return render_template('MAIN.html')


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        success_message = request.args.get('success')

        if request.method == 'POST':
            email = request.form['email']
            senha = request.form['senha']

            usuario = db_session.query(Usuario).filter_by(email=email).first()

            if usuario and usuario.verificar_senha(senha):
                session['usuario_id'] = usuario.id
                session['usuario_nome'] = usuario.nome
                session['usuario_email'] = usuario.email
                session['is_admin'] = usuario.is_admin

                return redirect(url_for('catalogo'))
            else:
                return render_template('login.html', error="Email ou senha incorretos")

        return render_template('login.html', success=success_message)

    except Exception as e:
        db_session.rollback()
        print(f"Erro no login: {e}")
        return render_template('login.html', error="Erro interno no sistema")


# REGISTER (CADASTRO) - VALIDAÇÃO FORTE DE E-MAIL DUPLICADO
@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            print("=== TENTATIVA DE REGISTRO ===")

            nome = request.form.get('nome')
            email = request.form.get('email')
            senha = request.form.get('senha')

            print(f"Dados recebidos: Nome={nome}, Email={email}")

            if not nome or not email or not senha:
                return render_template('register.html', error="Todos os campos são obrigatórios.")

            # 🔒 VALIDAÇÃO FORTE - Verificar email duplicado (case insensitive)
            email_normalizado = email.lower().strip()

            # Buscar todos os usuários e verificar manualmente (approach mais seguro)
            todos_usuarios = db_session.query(Usuario).all()
            email_ja_existe = False

            for usuario in todos_usuarios:
                if usuario.email.lower().strip() == email_normalizado:
                    email_ja_existe = True
                    break

            if email_ja_existe:
                print(f"❌ TENTATIVA DE CADASTRO DUPLICADO: {email}")
                return render_template('register.html', error="Este e-mail já está cadastrado. Use outro e-mail.")

            if len(senha) < 4:
                return render_template('register.html', error="A senha deve ter pelo menos 4 caracteres.")

            novo_usuario = Usuario(nome=nome, email=email, is_admin=False)
            novo_usuario.set_senha(senha)

            db_session.add(novo_usuario)
            db_session.commit()

            # Loga o usuário automaticamente
            session['usuario_id'] = novo_usuario.id
            session['usuario_nome'] = novo_usuario.nome
            session['usuario_email'] = novo_usuario.email
            session['is_admin'] = novo_usuario.is_admin

            print(f"✅ USUÁRIO REGISTRADO E LOGADO: {novo_usuario.nome}")
            print("🔀 REDIRECIONANDO PARA CATÁLOGO...")

            return redirect(url_for('catalogo'))

        return render_template('register.html')

    except Exception as e:
        db_session.rollback()
        print(f"❌ ERRO NO CADASTRO: {e}")
        return render_template('register.html', error="Erro interno no cadastro")


# CATÁLOGO (PÁGINA PRINCIPAL APÓS LOGIN)
@app.route('/catalogo')
def catalogo():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    return render_template('catalogo.html',
                           usuario_nome=session['usuario_nome'],
                           is_admin=session.get('is_admin', False))


# AVALIAR FILMES
@app.route('/avaliar/<int:filme_id>', methods=['POST'])
def avaliar_filme(filme_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    try:
        nota = request.form['nota']
        comentario = request.form.get('comentario', '')

        print(f"🎬 AVALIAÇÃO RECEBIDA - Filme ID: {filme_id}, Usuário: {session['usuario_id']}")
        print(f"📝 Nota: {nota}, Comentário: {comentario}")

        # Verificar se o usuário já avaliou este filme
        avaliacao_existente = db_session.query(Avaliacao).filter_by(
            usuario_id=session['usuario_id'],
            filme_id=filme_id
        ).first()

        if avaliacao_existente:
            # Atualizar avaliação existente
            avaliacao_existente.nota = nota
            avaliacao_existente.comentario = comentario
            print(f"✅ Avaliação atualizada: ID {avaliacao_existente.id}")
        else:
            # Criar nova avaliação
            nova_avaliacao = Avaliacao(
                nota=nota,
                comentario=comentario,
                usuario_id=session['usuario_id'],
                filme_id=filme_id
            )
            db_session.add(nova_avaliacao)
            print(f"✅ Nova avaliação criada para o filme {filme_id}")

        db_session.commit()
        return redirect(url_for('catalogo', success="Avaliação salva com sucesso!"))

    except Exception as e:
        db_session.rollback()
        print(f"❌ Erro ao avaliar filme: {e}")
        return redirect(url_for('catalogo', error="Erro ao salvar avaliação"))


# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------------- ROTAS ADMIN (MANTIDAS) ----------------

# Gerenciar usuários (admin) - VALIDAÇÃO FORTE DE E-MAIL DUPLICADO
@app.route('/usuarios', methods=['GET', 'POST'])
def usuarios():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return "Acesso negado! Somente admin pode gerenciar usuários."

    try:
        if request.method == 'POST':
            nome = request.form['nome']
            email = request.form['email']
            senha = request.form['senha']
            is_admin = request.form.get('is_admin') == 'true'

            # 🔒 VALIDAÇÃO FORTE - Verificar email duplicado (case insensitive)
            email_normalizado = email.lower().strip()

            # Buscar todos os usuários e verificar manualmente
            todos_usuarios = db_session.query(Usuario).all()
            email_ja_existe = False

            for usuario in todos_usuarios:
                if usuario.email.lower().strip() == email_normalizado:
                    email_ja_existe = True
                    break

            if email_ja_existe:
                usuarios = db_session.query(Usuario).all()
                return render_template('USUARIOS.html',
                                       usuarios=usuarios,
                                       error="Este e-mail já está cadastrado. Use outro e-mail.")

            # Criar novo usuário
            novo_usuario = Usuario(nome=nome, email=email, is_admin=is_admin)
            novo_usuario.set_senha(senha)

            db_session.add(novo_usuario)
            db_session.commit()

            usuarios = db_session.query(Usuario).all()
            return render_template('USUARIOS.html',
                                   usuarios=usuarios,
                                   success="Usuário cadastrado com sucesso!")

        # GET - Mostrar lista de usuários
        usuarios = db_session.query(Usuario).all()
        return render_template('USUARIOS.html', usuarios=usuarios)

    except Exception as e:
        db_session.rollback()
        print(f"Erro em /usuarios: {e}")
        usuarios = db_session.query(Usuario).all()
        return render_template('USUARIOS.html',
                               usuarios=usuarios,
                               error="Erro interno no sistema")


# Tornar usuário admin
@app.route('/usuarios/tornar-admin/<int:usuario_id>', methods=['POST'])
def tornar_admin(usuario_id):
    if 'usuario_id' not in session or not session.get('is_admin'):
        return "Acesso negado!"

    try:
        usuario = db_session.query(Usuario).get(usuario_id)
        if usuario:
            usuario.is_admin = True
            db_session.commit()

        return redirect(url_for('usuarios'))
    except Exception as e:
        db_session.rollback()
        print(f"Erro ao tornar admin: {e}")
        return redirect(url_for('usuarios'))


# Excluir usuário
@app.route('/usuarios/excluir/<int:usuario_id>', methods=['POST'])
def excluir_usuario(usuario_id):
    if 'usuario_id' not in session or not session.get('is_admin'):
        return "Acesso negado!"

    try:
        # Não permitir excluir a si mesmo
        if usuario_id == session['usuario_id']:
            usuarios = db_session.query(Usuario).all()
            return render_template('USUARIOS.html',
                                   usuarios=usuarios,
                                   error="Você não pode excluir sua própria conta!")

        usuario = db_session.query(Usuario).get(usuario_id)
        if usuario:
            db_session.delete(usuario)
            db_session.commit()

        return redirect(url_for('usuarios'))
    except Exception as e:
        db_session.rollback()
        print(f"Erro ao excluir usuário: {e}")
        return redirect(url_for('usuarios'))


# Adicionar filmes (admin)
@app.route('/filmes', methods=['GET', 'POST'])
def filmes():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return "Acesso negado! Somente admin pode adicionar filmes."

    if request.method == 'POST':
        titulo = request.form['titulo']
        genero = request.form['genero']
        ano = request.form['ano']
        imagem = request.form['imagem']
        descricao = request.form.get('descricao', '')
        duracao = request.form.get('duracao', '')
        diretor = request.form.get('diretor', '')
        elenco = request.form.get('elenco', '')
        streaming = request.form.get('streaming', '#')

        novo_filme = Filme(
            titulo=titulo,
            genero=genero,
            ano=ano,
            imagem=imagem,
            descricao=descricao,
            duracao=duracao,
            diretor=diretor,
            elenco=elenco,
            streaming=streaming
        )
        db_session.add(novo_filme)
        db_session.commit()
        return redirect(url_for('crud'))

    return render_template('FILMES.html')


# CRUD de filmes (admin)
@app.route('/crud')
def crud():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return "Acesso negado!"

    filmes = db_session.query(Filme).all()
    return render_template('CRUD.html', filmes=filmes)


# Editar filme (admin)
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_filme(id):
    if 'usuario_id' not in session or not session.get('is_admin'):
        return "Acesso negado!"

    filme = db_session.query(Filme).get(id)
    if request.method == 'POST':
        filme.titulo = request.form['titulo']
        filme.genero = request.form['genero']
        filme.ano = request.form['ano']
        filme.imagem = request.form['imagem']
        filme.descricao = request.form.get('descricao', '')
        filme.duracao = request.form.get('duracao', '')
        filme.diretor = request.form.get('diretor', '')
        filme.elenco = request.form.get('elenco', '')
        filme.streaming = request.form.get('streaming', '#')

        db_session.commit()
        return redirect(url_for('crud'))

    return render_template('FILMES.html', filme=filme)


# Deletar filme (admin)
@app.route('/delete/<int:id>')
def delete_filme(id):
    if 'usuario_id' not in session or not session.get('is_admin'):
        return "Acesso negado!"

    filme = db_session.query(Filme).get(id)
    db_session.delete(filme)
    db_session.commit()
    return redirect(url_for('crud'))


@app.route('/api/minhas-avaliacoes')
def api_minhas_avaliacoes():
    if 'usuario_id' not in session:
        return jsonify([])

    try:
        avaliacoes = db_session.query(Avaliacao).filter_by(usuario_id=session['usuario_id']).all()
        return jsonify([{
            'id': a.id,
            'filme_id': a.filme_id,
            'nota': a.nota,
            'comentario': a.comentario,
            'data': a.data.isoformat() if a.data else None
        } for a in avaliacoes])
    except Exception as e:
        print(f"Erro ao carregar avaliações: {e}")
        return jsonify([])


# SINCRONIZAR FILMES DO FRONTEND COM O BANCO
@app.route('/sync-filmes', methods=['POST'])
def sync_filmes():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return {"error": "Acesso negado"}, 403

    try:
        filmes_data = request.json.get('filmes', [])

        for filme_data in filmes_data:
            # Verificar se o filme já existe
            filme_existente = db_session.query(Filme).filter_by(
                titulo=filme_data['title'],
                ano=filme_data['year']
            ).first()

            if not filme_existente:
                novo_filme = Filme(
                    titulo=filme_data['title'],
                    genero=filme_data['genre'],
                    ano=filme_data['year']
                )
                db_session.add(novo_filme)
                print(f"✅ Filme adicionado: {filme_data['title']} ({filme_data['year']})")

        db_session.commit()
        return {"success": "Filmes sincronizados com sucesso"}, 200

    except Exception as e:
        db_session.rollback()
        print(f"❌ Erro ao sincronizar filmes: {e}")
        return {"error": "Erro ao sincronizar filmes"}, 500


# API PARA BUSCAR FILMES
@app.route('/api/filmes')
def api_filmes():
    try:
        filmes = db_session.query(Filme).all()
        return jsonify([{
            'id': f.id,
            'titulo': f.titulo,
            'genero': f.genero,
            'ano': f.ano
        } for f in filmes])
    except Exception as e:
        print(f"Erro ao carregar filmes: {e}")
        return jsonify([])


# CRIAR FILMES PADRÃO
@app.route('/criar-filmes-padrao')
def criar_filmes_padrao():
    try:
        filmes_padrao = [
            {"titulo": "Oppenheimer", "genero": "Drama Histórico", "ano": 2023},
            {"titulo": "Interestelar", "genero": "Ficção Científica", "ano": 2014},
            {"titulo": "Avatar: O Caminho da Água", "genero": "Ficção Científica", "ano": 2022},
            {"titulo": "Duna: Parte 2", "genero": "Ficção Científica", "ano": 2024},
            {"titulo": "Homem-Aranha: Sem Volta para Casa", "genero": "Ação", "ano": 2021},
            {"titulo": "The Batman", "genero": "Ação", "ano": 2022},
            {"titulo": "Vingadores: Ultimato", "genero": "Ação", "ano": 2019},
            {"titulo": "John Wick 4", "genero": "Ação", "ano": 2023}
        ]

        filmes_criados = 0
        for filme_data in filmes_padrao:
            filme_existente = db_session.query(Filme).filter_by(
                titulo=filme_data["titulo"],
                ano=filme_data["ano"]
            ).first()

            if not filme_existente:
                novo_filme = Filme(
                    titulo=filme_data["titulo"],
                    genero=filme_data["genero"],
                    ano=filme_data["ano"]
                )
                db_session.add(novo_filme)
                filmes_criados += 1
                print(f"✅ Filme criado: {filme_data['titulo']}")

        db_session.commit()
        return f"✅ {filmes_criados} filmes criados com sucesso!"

    except Exception as e:
        db_session.rollback()
        return f"❌ Erro ao criar filmes: {e}"


# API PARA BUSCAR TODOS OS FILMES (COM DADOS REAIS)
@app.route('/api/filmes-completos')
def api_filmes_completos():
    try:
        filmes = db_session.query(Filme).all()

        filmes_formatados = []
        for filme in filmes:
            # Se o filme não tem imagem, usar fallback baseado no título
            imagem = filme.imagem
            if not imagem:
                # Fallback para filmes conhecidos
                filmes_imagens = {
                    "Oppenheimer": "https://br.web.img3.acsta.net/c_310_420/pictures/23/05/08/10/29/0695770.jpg",
                    "Interestelar": "https://br.web.img3.acsta.net/c_310_420/pictures/14/10/31/20/39/476171.jpg",
                    "O Silêncio Dos inocentes": "https://br.web.img2.acsta.net/c_310_420/medias/nmedia/18/92/91/32/20224832.jpg",
                    "Avatar: O Caminho da Água": "https://br.web.img2.acsta.net/c_310_420/pictures/22/05/09/16/16/3197518.jpg",
                    "Duna: Parte 2": "https://br.web.img3.acsta.net/c_310_420/pictures/23/05/26/17/47/1900372.jpg",
                    "Homem-Aranha: Sem Volta para Casa": "https://br.web.img3.acsta.net/c_310_420/pictures/21/11/08/16/02/3963914.png",
                    "The Batman": "https://br.web.img2.acsta.net/c_310_420/pictures/22/03/02/19/26/3666027.jpg",
                    "Vingadores: Ultimato": "https://br.web.img2.acsta.net/c_310_420/pictures/19/04/26/17/30/2428965.jpg",
                    "John Wick 4": "https://br.web.img2.acsta.net/c_310_420/pictures/22/12/05/09/07/2007563.jpg"
                }
                imagem = filmes_imagens.get(filme.titulo,
                                            "https://via.placeholder.com/300x450/2a2a2a/ffffff?text=Sem+Imagem")

            filmes_formatados.append({
                'id': filme.id,
                'title': filme.titulo,
                'genre': filme.genero,
                'year': filme.ano,
                'duration': filme.duracao or "120 min",
                'rating': 4.0,
                'ratingCount': len(filme.avaliacoes),
                'description': filme.descricao or f"Descrição do filme {filme.titulo}.",
                'image': imagem,
                'streaming': filme.streaming or "#",
                'director': filme.diretor or "Diretor não informado",
                'cast': filme.elenco or "Elenco não informado"
            })

        return jsonify(filmes_formatados)
    except Exception as e:
        print(f"Erro ao carregar filmes completos: {e}")
        return jsonify([])


# ATUALIZAR FILMES EXISTENTES COM IMAGENS E INFORMAÇÕES
@app.route('/atualizar-filmes-existente')
def atualizar_filmes_existente():
    if 'usuario_id' not in session or not session.get('is_admin'):
        return "Acesso negado! Somente admin pode atualizar filmes."

    try:
        # Dados completos para os filmes existentes
        filmes_info = {
            "Oppenheimer": {
                "imagem": "https://br.web.img3.acsta.net/c_310_420/pictures/23/05/08/10/29/0695770.jpg",
                "descricao": "A história do físico J. Robert Oppenheimer e seu papel no desenvolvimento da bomba atômica durante a Segunda Guerra Mundial.",
                "duracao": "180 min",
                "diretor": "Christopher Nolan",
                "elenco": "Cillian Murphy, Emily Blunt, Matt Damon",
                "streaming": "https://www.primevideo.com/detail/0LTLQ7P1ASD8E1S6FKHTGLX4B6"
            },
            "Interestelar": {
                "imagem": "https://br.web.img3.acsta.net/c_310_420/pictures/14/10/31/20/39/476171.jpg",
                "descricao": "Um grupo de exploradores viaja através de um buraco de minhoca no espaço na tentativa de garantir a sobrevivência da humanidade.",
                "duracao": "169 min",
                "diretor": "Christopher Nolan",
                "elenco": "Matthew McConaughey, Anne Hathaway, Jessica Chastain",
                "streaming": "https://www.netflix.com/br/title/70305903"
            },
            "O Silêncio Dos inocentes": {
                "imagem": "https://br.web.img2.acsta.net/c_310_420/medias/nmedia/18/92/91/32/20224832.jpg",
                "descricao": "Uma jovem agente do FBI recorre a um assassino canibal preso para ajudá-la a capturar outro serial killer.",
                "duracao": "118 min",
                "diretor": "Jonathan Demme",
                "elenco": "Jodie Foster, Anthony Hopkins, Scott Glenn",
                "streaming": "https://www.netflix.com/br/title/60000986"
            },
            "Avatar: O Caminho da Água": {
                "imagem": "https://br.web.img2.acsta.net/c_310_420/pictures/22/05/09/16/16/3197518.jpg",
                "descricao": "Jake Sully vive com sua nova família no planeta Pandora. Quando uma ameaça familiar retorna, Jake deve travar uma guerra difícil.",
                "duracao": "192 min",
                "diretor": "James Cameron",
                "elenco": "Sam Worthington, Zoe Saldana, Sigourney Weaver",
                "streaming": "https://www.disneyplus.com/pt-br/movies/avatar-o-caminho-da-agua/6k4dKe0WpoL3"
            },
            "Duna: Parte 2": {
                "imagem": "https://br.web.img3.acsta.net/c_310_420/pictures/23/05/26/17/47/1900372.jpg",
                "descricao": "Paul Atreides se une a Chani e aos Fremen enquanto busca vingança contra os conspiradores que destruíram sua família.",
                "duracao": "166 min",
                "diretor": "Denis Villeneuve",
                "elenco": "Timothée Chalamet, Zendaya, Rebecca Ferguson",
                "streaming": "https://www.max.com/br/pt/movies/duna-2/8a0a3d77-dune2"
            },
            "Homem-Aranha: Sem Volta para Casa": {
                "imagem": "https://br.web.img3.acsta.net/c_310_420/pictures/21/11/08/16/02/3963914.png",
                "descricao": "Peter Parker pede ajuda ao Doutor Estranho para que todos esqueçam sua identidade, mas o feitiço dá errado.",
                "duracao": "148 min",
                "diretor": "Jon Watts",
                "elenco": "Tom Holland, Zendaya, Benedict Cumberbatch",
                "streaming": "https://www.netflix.com/br/title/81492908"
            },
            "The Batman": {
                "imagem": "https://br.web.img2.acsta.net/c_310_420/pictures/22/03/02/19/26/3666027.jpg",
                "descricao": "Batman investiga o submundo de Gotham City quando um assassino sádico deixa para trás um rastro de pistas enigmáticas.",
                "duracao": "176 min",
                "diretor": "Matt Reeves",
                "elenco": "Robert Pattinson, Zoë Kravitz, Paul Dano",
                "streaming": "https://www.max.com/br/pt/movies/the-batman/4b45b05a-617d-49b6-b4e3-6edc21b67b75"
            },
            "Vingadores: Ultimato": {
                "imagem": "https://br.web.img2.acsta.net/c_310_420/pictures/19/04/26/17/30/2428965.jpg",
                "descricao": "Os Vingadores restantes precisam encontrar uma maneira de recuperar seus aliados para um confronto final com Thanos.",
                "duracao": "181 min",
                "diretor": "Anthony e Joe Russo",
                "elenco": "Robert Downey Jr., Chris Evans, Scarlett Johansson",
                "streaming": "https://www.disneyplus.com/pt-br/movies/avengers-endgame/aRbVJUb2h2Rf"
            },
            "John Wick 4": {
                "imagem": "https://br.web.img2.acsta.net/c_310_420/pictures/22/12/05/09/07/2007563.jpg",
                "descricao": "John Wick descobre um caminho para derrotar a Alta Cúpula. Mas antes que possa ganhar sua liberdade, Wick deve enfrentar um novo inimigo.",
                "duracao": "169 min",
                "diretor": "Chad Stahelski",
                "elenco": "Keanu Reeves, Donnie Yen, Bill Skarsgård",
                "streaming": "https://www.primevideo.com/detail/John-Wick-4/0JGHF1M6S8P8T3I8SHCLYRT3A9"
            }
        }

        filmes_atualizados = 0
        filmes = db_session.query(Filme).all()

        for filme in filmes:
            if filme.titulo in filmes_info:
                info = filmes_info[filme.titulo]

                # Atualizar apenas se estiver vazio
                if not filme.imagem:
                    filme.imagem = info["imagem"]
                if not filme.descricao:
                    filme.descricao = info["descricao"]
                if not filme.duracao:
                    filme.duracao = info["duracao"]
                if not filme.diretor:
                    filme.diretor = info["diretor"]
                if not filme.elenco:
                    filme.elenco = info["elenco"]
                if not filme.streaming or filme.streaming == "#":
                    filme.streaming = info["streaming"]

                filmes_atualizados += 1
                print(f"✅ Filme atualizado: {filme.titulo}")

        db_session.commit()
        return f"✅ {filmes_atualizados} filmes atualizados com sucesso!"

    except Exception as e:
        db_session.rollback()
        return f"❌ Erro ao atualizar filmes: {e}"


# ROTA PARA LIMPAR USUÁRIOS DUPLICADOS (APENAS PARA DEBUG)
@app.route('/limpar-duplicados')
def limpar_duplicados():
    if not session.get('is_admin'):
        return "Acesso negado"

    try:
        # Encontrar e-mails duplicados
        todos_usuarios = db_session.query(Usuario).all()
        emails_vistos = set()
        usuarios_para_remover = []

        for usuario in todos_usuarios:
            email_normalizado = usuario.email.lower().strip()
            if email_normalizado in emails_vistos:
                usuarios_para_remover.append(usuario)
            else:
                emails_vistos.add(email_normalizado)

        # Remover duplicatas
        for usuario in usuarios_para_remover:
            db_session.delete(usuario)
            print(f"❌ Removido usuário duplicado: {usuario.email}")

        db_session.commit()
        return f"✅ {len(usuarios_para_remover)} usuários duplicados removidos!"

    except Exception as e:
        db_session.rollback()
        return f"❌ Erro ao limpar duplicados: {e}"


if __name__ == '__main__':
    app.run(debug=True)