import pymysql
from flask import Flask, request, render_template, redirect, url_for, session

app = Flask(__name__)

# Configurações de conexão
host = "localhost"
user = "root"
password = "12052007"  # Coloque a senha se tiver, ou deixe vazio se não tiver
database = "edulaa"

# Definir uma chave secreta para sessões
app.secret_key = 'sua_chave_secreta_aqui'  # Substitua por uma chave real

# Função para conectar ao banco de dados
def connect_db():
    return pymysql.connect(host=host, user=user, password=password, database=database)

# Página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        tipo = request.form['tipo']  # "user" ou "professor"
        matricula_cpf = request.form['matricula_cpf']
        senha = request.form['senha']
        
        connection = connect_db()
        cursor = connection.cursor()
        
        if tipo == 'user':
            query = "SELECT * FROM user WHERE matricula = %s AND senha = %s"
            cursor.execute(query, (matricula_cpf, senha))
        elif tipo == 'professor':
            query = "SELECT * FROM professores WHERE cpf = %s AND senha = %s"
            cursor.execute(query, (matricula_cpf, senha))

        user = cursor.fetchone()
        connection.close()

        if tipo == 'professor':
            session['id'] = user[0]  # ID do professor
            session['nome'] = user[1]
            session['tipo_usuario'] = 'professor'
            return redirect(url_for('area_professor'))
        elif tipo == 'user':
            session['iduser'] = user[0]  # ID do aluno
            session['nome'] = user[3]
            session['tipo_usuario'] = 'user'
            return redirect(url_for('area_user'))

    
    return render_template('login.html')

# Página inicial após login (Área do Usuário)
@app.route('/area_user')
def area_user():
    if 'nome' in session:
        nome = session['nome']
        return render_template('area_user.html', nome=nome)  # Passa o nome para o template
    return redirect(url_for('login'))  # Redireciona para o login se não estiver logado

    
@app.route('/provas_disponiveis')
def provas_disponiveis():
    if 'iduser' not in session:
        return redirect(url_for('login'))  # Redireciona para o login se não estiver logado
    
    connection = connect_db()
    cursor = connection.cursor()

    # Buscar todas as provas associadas ao aluno logado
    cursor.execute("""
        SELECT p.id, p.nome, p.descricao, p.tipo
        FROM provas p
        JOIN provas_alunos pa ON p.id = pa.prova_id
        WHERE pa.aluno_id = %s
    """, (session['iduser'],))
    
    provas = cursor.fetchall()  # Recupera as provas associadas ao aluno
    connection.close()

    return render_template('provas_disponiveis.html', provas=provas)

# Página inicial após login (Área do Professor)
@app.route('/area_professor')
def area_professor():
    if 'nome' in session:
        nome = session['nome']
        return render_template('area_professor.html', nome=nome)  # Passa o nome para o template
    return redirect(url_for('login'))  # Redireciona para o login se não estiver logado

# Página de cadastro de usuário
@app.route('/cadastro_user', methods=['GET', 'POST'])
def cadastro_user():
    if request.method == 'POST':
        nome = request.form['nome']
        matricula = request.form['matricula']
        senha = request.form['senha']
        
        connection = connect_db()
        cursor = connection.cursor()
        query = "INSERT INTO user (nome, matricula, senha) VALUES (%s, %s, %s)"
        cursor.execute(query, (nome, matricula, senha))
        connection.commit()
        connection.close()

        return redirect(url_for('login'))
    
    return render_template('cadastro_user.html')

# Página de cadastro de professor
@app.route('/cadastro_professor', methods=['GET', 'POST'])
def cadastro_professor():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        senha = request.form['senha']
        
        connection = connect_db()
        cursor = connection.cursor()
        query = "INSERT INTO professores (nome, cpf, senha) VALUES (%s, %s, %s)"
        cursor.execute(query, (nome, cpf, senha))
        connection.commit()
        connection.close()

        return redirect(url_for('login'))
    
    return render_template('cadastro_professor.html')

# Página de logout


@app.route('/forum', methods=['GET', 'POST'])
def forum():
    if 'nome' not in session:
        return redirect(url_for('login'))  # Redireciona para o login se o usuário não estiver logado
    
    connection = connect_db()
    cursor = connection.cursor()

    # Se for um POST, significa que um novo tópico está sendo criado
    if request.method == 'POST':
        titulo = request.form['titulo']
        conteudo = request.form['conteudo']
        nome_usuario = session['nome']  # Recupera o nome do usuário logado
        
        query = "INSERT INTO forum (titulo, conteudo, autor) VALUES (%s, %s, %s)"
        cursor.execute(query, (titulo, conteudo, nome_usuario))
        connection.commit()

    # Consulta os tópicos existentes no fórum
    cursor.execute("SELECT titulo, conteudo, autor FROM forum ORDER BY id DESC")
    topicos = cursor.fetchall()  # Recupera todos os tópicos do fórum

    connection.close()
    return render_template('forum.html', topicos=topicos)








@app.route('/criar_prova', methods=['GET', 'POST'])
def criar_prova():
    # Verifica se o usuário está autenticado e se é professor
    if 'id' not in session or session.get('tipo_usuario') != 'professor':
        return redirect(url_for('login'))

    connection = connect_db()
    cursor = connection.cursor()

    # Buscar os alunos para seleção
    cursor.execute("SELECT iduser, nome FROM user")
    alunos = cursor.fetchall()
    
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        tipo = request.form['tipo']
        alunos_selecionados = request.form.getlist('alunos')

        query = "INSERT INTO provas (nome, descricao, tipo) VALUES (%s, %s, %s)"
        cursor.execute(query, (nome, descricao, tipo))
        prova_id = cursor.lastrowid  # Pega o ID da prova criada

        # Associa a prova aos alunos selecionados
        for aluno_id in alunos_selecionados:
            cursor.execute("INSERT INTO provas_alunos (prova_id, aluno_id) VALUES (%s, %s)", (prova_id, aluno_id))

        connection.commit()
        connection.close()
        
        return redirect(url_for('area_professor'))

    return render_template('criar_prova.html', alunos=alunos)




@app.route('/responder_prova/<int:prova_id>', methods=['GET', 'POST'])
def responder_prova(prova_id):
    if 'iduser' not in session:
        return redirect(url_for('login'))

    connection = connect_db()
    cursor = connection.cursor()

    # Buscar a prova
    cursor.execute("""
        SELECT provas.id, provas.nome, provas.descricao, provas.tipo
        FROM provas
        JOIN provas_alunos ON provas.id = provas_alunos.prova_id
        WHERE provas.id = %s AND provas_alunos.aluno_id = %s
    """, (prova_id, session['iduser']))
    
    prova = cursor.fetchone()

    if not prova:
        return "Você não tem permissão para acessar esta prova."

    if request.method == 'POST':
        resposta = request.form['resposta']
        tipo_resposta = prova[3]  # 'aberta' ou 'multipla'
        alternativa_selecionada = request.form.get('alternativa', '')

        cursor.execute("INSERT INTO respostas (prova_id, aluno_id, resposta, tipo_resposta, alternativa_selecionada) VALUES (%s, %s, %s, %s, %s)", 
                       (prova_id, session['iduser'], resposta, tipo_resposta, alternativa_selecionada))
        connection.commit()
        connection.close()

        return redirect(url_for('area_user'))

    connection.close()
    return render_template('responder_prova.html', prova=prova)



@app.route('/ver_respostas/<int:prova_id>')
def ver_respostas(prova_id):
    if 'professor_id' not in session:
        return redirect(url_for('login'))

    connection = connect_db()
    cursor = connection.cursor()

    # Buscar as respostas da prova específica
    cursor.execute("""
        SELECT user.nome, respostas.resposta, respostas.tipo_resposta, respostas.alternativa_selecionada
        FROM respostas
        JOIN user ON respostas.aluno_id = user.iduser
        WHERE respostas.prova_id = %s
    """, (prova_id,))

    respostas = cursor.fetchall()
    connection.close()

    return render_template('ver_respostas.html', respostas=respostas)


@app.route('/ver_provas')
def ver_provas():
    if 'iduser' not in session:
        return redirect(url_for('login'))

    connection = connect_db()
    cursor = connection.cursor()

    # Buscar as provas disponíveis para o aluno logado
    cursor.execute("""
        SELECT p.id, p.nome, p.descricao, p.tipo
        FROM provas p
        JOIN provas_alunos pa ON p.id = pa.prova_id
        WHERE pa.aluno_id = %s
    """, (session['iduser'],))
    
    provas = cursor.fetchall()
    connection.close()

    return render_template('ver_provas.html', provas=provas)





# Página inicial
@app.route('/')
def inicio():
    return render_template('INICIO.html')


@app.route('/chat')
def chat():
    if 'nome' in session:
        nome = session['nome']
        return render_template('chat.html', nome=nome)  # Passa o nome para o template
    return redirect(url_for('login'))  # Redireciona para o login se não estiver logado

@app.route('/logout')
def logout():
    session.clear()  # Limpa os dados da sessão
    return redirect(url_for('login'))  # Redireciona para a página de login

if __name__ == "__main__":
    app.run(debug=True)
