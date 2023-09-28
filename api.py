from flask import Flask, request, jsonify, Response, redirect
import sqlite3, requests, os, gzip, threading
from datetime import datetime, timedelta
from markdown import markdown

app = Flask(__name__)

url = 'https://storage.covid19datahub.io/latest.db.gz'

# Nome do arquivo onde você salvará o banco de dados compactado
gz_file = './files/latest.db.gz'
db_file = './files/latest.db'
camposBasicos = ['timeseries.id', 'date']

# Variável global para controlar o status de download
download_in_progress = False

# Semáforo para garantir que apenas uma solicitação inicie o download por vez
download_lock = threading.Lock()

# Função para fazer o download do arquivo se a data de modificação no servidor for mais recente
def need_to_download_file(filename):
    # Check if the folder exists
    if not os.path.exists('files'):
        # If it doesn't exist, create it
        os.makedirs('files')

    if not os.path.exists(filename):
        return True
    else:
        local_last_modified_date = datetime.fromtimestamp(os.path.getmtime(filename))
        one_day_ago = datetime.now() - timedelta(days=1)

        if local_last_modified_date <= one_day_ago:
            return True
        else:
            print("O arquivo local já está atualizado.")

    return False  # Retorna False para indicar que o arquivo não foi baixado agora

def download_file(url, filename):
    print("Fazendo o download do arquivo...")
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            file.write(response.content)
        print("Download concluído com sucesso.")
        return True  # Retorna True para indicar que o arquivo foi baixado agora
    else:
        print("Falha no download do arquivo.")

# Função para descompactar o arquivo
def extract_database(gz_filename, db_filename):
    try:
        with gzip.open(gz_filename, 'rb') as gz_file:
            with open(db_filename, 'wb') as db_file:
                db_file.write(gz_file.read())
        print(f"Arquivo {db_filename} descompactado com sucesso.")
    except Exception as e:
        print(f"Erro ao descompactar o arquivo: {str(e)}")


def constroi_consulta(campos, level, location, start_date, end_date, limit):
    consulta = 'SELECT '
    for campo in campos:
        consulta += campo + ', '
    consulta = consulta[:-2] # remove a ultima virgula
    consulta += ' FROM location LEFT JOIN timeseries ON location.id = timeseries.id WHERE '
    if level:
        consulta += 'administrative_area_level=' + str(level) + ' AND '
    if location:
        consulta += 'administrative_area_level_' + str(level) + '="' + location + '" AND '
    if start_date:
        consulta += 'date >= "' + start_date + '" AND '
    if end_date:
        consulta += 'date <= "' + end_date + '" AND '
    consulta = consulta[:-5] # remove o ultimo AND
    if limit:
        consulta += ' LIMIT ' + str(limit)
    return consulta

@app.before_request
def check_download():
    global download_in_progress

    if request.path != '/api/status' and request.path != '/api/consultar':
        return

    with download_lock:
        if not download_in_progress and need_to_download_file(gz_file):
            download_in_progress = True

            def generate():
                global download_in_progress

                if download_file(url, gz_file):
                    extract_database(gz_file, db_file)
                    download_in_progress = False
                    yield 'Download concluído!\n'
                else:
                    download_in_progress = False
                    yield 'Falha no download!\n'

            return Response(generate(), content_type='text/plain')
        elif download_in_progress:
            return 'Download em andamento...', 503  # Retorne código 503 para indicar que o serviço está indisponível temporariamente

@app.route('/api/status', methods=['GET'])
def status():
    global download_in_progress

    if download_in_progress:
        return 'Download em andamento...', 503
    else:
        return 'Download concluído!', 200

# Rota para consultar todos os registros na tabela
@app.route('/api/consultar', methods=['GET'])
def consultar_todos():
    level = request.args.get('level')
    location = request.args.get('location')
    start_date = request.args.get('start_date')  # Parâmetro 'start_date' na URL
    end_date = request.args.get('end_date')  # Parâmetro 'end_date' na URL
    campos = request.args.getlist('campos[]') + camposBasicos  # Parâmetro 'campos' na URL

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        consulta = constroi_consulta(campos, level, location, start_date, end_date, 3650)

        # Construa a consulta SQL para unir as tabelas location e timeseries e filtrar por datas. juntar campos
        cursor.execute(consulta)  # Substitua "tabela" pelo nome da tabela em seu banco de dados

        data = cursor.fetchall()
        conn.close()

        resultados_json = []
        for row in data:
            resultado_dict = {}
            for i, campo in enumerate(campos):
                if campo == "timeseries.id":
                    resultado_dict["id"] = row[i]
                else:
                    resultado_dict[campo] = row[i]
            resultados_json.append(resultado_dict)

        return jsonify(resultados_json)
    except Exception as e:
        return str(e), 500

# Função para ler e converter o conteúdo do arquivo readme.md em HTML
def read_and_convert_readme():
    with open('readme.md', 'r', encoding='utf-8') as readme_file:
        markdown_content = readme_file.read()
        html_content = markdown(markdown_content)
    return html_content


# Rota para exibir o conteúdo do arquivo readme.md em HTML
@app.route('/api', methods=['GET'])
def display_readme():
    readme_html = read_and_convert_readme()
    return Response(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>API Documentation</title>
            <!-- Link to Bootstrap CSS -->
            <link
                rel="stylesheet"
                href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css"
            />
            <meta charset="UTF-8">
        </head>
        <body>
            <div class="container mt-5">
                <div class="jumbotron">
                    <div class="lead">
                        {readme_html}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """,
        content_type='text/html',
    )

# Rota para redirecionar da raiz '/' para '/api'
@app.route('/')
def root():
    return redirect('/api')

if __name__ == '__main__':
    app.run(debug=True)
