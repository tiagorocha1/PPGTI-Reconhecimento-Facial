from flask import Flask, request, jsonify
import base64
import cv2
import numpy as np
import os
from flask_cors import CORS
from datetime import datetime
import time

app = Flask(__name__)

CORS(app)  # Isso permite todas as origens (*). .


class Pessoa:
    def __init__(self, nome, foto_path):
        self.nome = nome
        self.foto_path = foto_path

def base64_to_image(base64_string):
    image_data = base64.b64decode(base64_string)
    image_array = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    return image


def copiar_arquivo_com_nome_formatado(caminho_arquivo):
    try:
        # Verifica se o arquivo existe
        if not os.path.exists(caminho_arquivo):
            return "O arquivo especificado não existe."

        # Extrai o nome do arquivo do caminho
        nome_arquivo = os.path.basename(caminho_arquivo)

        # Gera a data e hora atual no formato desejado
        data_hora_atual = datetime.now().strftime("%Y%m%d%H%M%S")

        # Constrói o novo nome do arquivo
        novo_nome_arquivo = f"Pessoa-{data_hora_atual}.jpg"

        # Constrói o caminho de destino
        destino = os.path.join("C:\\Fotos_Conhecidas", novo_nome_arquivo)

        # Copia o arquivo para o destino
        shutil.copy(caminho_arquivo, destino)

        return f"Arquivo copiado para {destino}"
    except Exception as e:
        return f"Erro ao copiar o arquivo: {str(e)}"


def detect_and_draw_faces(base64_string, nome):
    # Converte a base64 em imagem
    image = base64_to_image(base64_string)

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    # Desenha um retângulo verde em torno do primeiro rosto detectado (ou em todos os rostos encontrados)
    for (x, y, w, h) in faces:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Define a cor do nome
        if nome == "Desconhecido":
            nome_cor = (0, 0, 255)  # Vermelho
        else:
            nome_cor = (0, 255, 0)  # Verde

        
        nome_tamanho = 2  
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(image, nome, (x, y + h + 20), font, nome_tamanho, nome_cor, 2)

    # Converte a imagem com os retângulos e nomes de volta para base64
    _, encoded_image = cv2.imencode('.jpg', image)
    base64_with_rectangles = base64.b64encode(encoded_image).decode('utf-8')

    return base64_with_rectangles

def reconhecerPessoa(imagem_capturada):

    print("Reconhecendo Pessoas: ")
    pessoas = listar_pessoas_em_diretorio("C:\\Fotos_Conhecidas")

    print("### leitura da imagem")
    # Leitura da imagem capturada

    print(imagem_capturada)

    imagem = cv2.imread(imagem_capturada)
    print("Leu")
    if imagem is None:
        return "Desconhecido"

    # Calcula o histograma da imagem capturada
    histograma_imagem_capturada = cv2.calcHist([imagem], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])

    for pessoa in pessoas:
       
        print("Encontradas: "+pessoa.nome+" - "+pessoa.foto_path)
        foto_pessoa = cv2.imread(pessoa.foto_path)

        if foto_pessoa is None:
            continue

        # Calcula o histograma da imagem da pessoa conhecida
        histograma_pessoa = cv2.calcHist([foto_pessoa], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])

        # Calcula a diferença entre os histogramas usando a distância de Bhattacharyya
        diferenca = cv2.compareHist(histograma_imagem_capturada, histograma_pessoa, cv2.HISTCMP_BHATTACHARYYA)

        if diferenca < 0.5:
            return pessoa.nome

    return "Desconhecido"

def listar_pessoas_em_diretorio(diretorio):
    lista_pessoas = []
    
    for nome_arquivo in os.listdir(diretorio):
        caminho_completo = os.path.join(diretorio, nome_arquivo)
        
        if os.path.isfile(caminho_completo):
            # Extrai o nome do arquivo (sem extensão) como o nome da pessoa
            nome_pessoa = os.path.splitext(nome_arquivo)[0]
            
            pessoa = Pessoa(nome=nome_pessoa, foto_path=caminho_completo)
          
            lista_pessoas.append(pessoa)
    
    return lista_pessoas

def imagemCaptada(image_data):
    try:
        # Converta os dados da imagem em um array NumPy
        nparr = np.frombuffer(image_data, np.uint8)

        # Decodifique a imagem usando OpenCV
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Gere um nome de arquivo exclusivo com timestamp
        timestamp = int(time.time())
        filename = f"_{timestamp}.jpg"
        
        # Crie o caminho completo para a pasta temporária
        temp_folder = "C:\\Fotos_Conhecidas"
        file_path = os.path.join(temp_folder, filename)
        
        # Salve a imagem no caminho completo
        cv2.imwrite(file_path, image)
        
        # Retorne o caminho completo para o arquivo
        return file_path

    except Exception as e:
        return {'error': str(e)}


@app.route('/api/detecta', methods=['POST'])
def detecta():
    try:
        # Obtenha os dados da imagem em base64 a partir do corpo da solicitação
        data = request.json['image_base64']

        # Decodifique a imagem base64 em um array de bytes
        image_data = base64.b64decode(data)

        # Chame a função 'imagemCaptada' para processar a imagem
        caminho_image = imagemCaptada(image_data)

        nome = reconhecerPessoa(caminho_image)

        
        if nome.strip() == "Desconhecido":
            copiar_arquivo_com_nome_formatado(caminho_image)
            print(salvou)
            


        print("Pessoa reconhecida : "+nome)

        return jsonify({"nome": nome, "foto": detect_and_draw_faces(data, nome)})



    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
