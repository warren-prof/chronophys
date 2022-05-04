import socket
import os
from flask import Flask, request


def get_address() :
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 1))
    local_ip_address = s.getsockname()[0]
    return local_ip_address

def start_server(self):
    local_ip_address = get_address()
    FOLDER = 'videos_recues'
    os.makedirs(FOLDER, exist_ok=True)

    app = Flask(__name__)

    @app.route('/', methods=['GET', 'POST'])
    def index():

        if request.method == 'GET':
            return '''
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>Importation de vidéo | ChronoPhys</title>

                <style>
                body {
                    font-family: Arial, Helvetica, sans-serif;
                }
                </style>
            </head>
            <body>
                <header></header>
                <main>
                <h2>Importer une vidéo sur ChronoPhys</h2>
                <form enctype="multipart/form-data" action="" method="POST">
                    <p>
                    Veuillez enregistrer une vidéo en cliquant sur le bouton suivant :
                    </p>
                    <input type="hidden" name="MAX_FILE_SIZE" value="8000000" />
                    <input
                    type="file"
                    name="image"
                    id="image"
                    accept="video/*"
                    capture="environment"
                    /><br />
                    <p style="color: rgb(230, 66, 66); font-style: italic">
                    On veillera à ce que la vidéo ne soit pas trop longue (< 10 secondes)
                    afin d'éviter des temps de transfert trop longs.
                    </p>
                    <input type="submit" value="Envoyer la vidéo" />
                </form>
                </main>
                <footer></footer>
            </body>
            </html>
            '''
        
        filename = ""
        if request.method == 'POST':
            for field, data in request.files.items():
                print('field:', field)
                print('filename:', data.filename)
                if data.filename:
                    data.save(os.path.join(FOLDER, data.filename))
                    filename = data.filename
            self.video.emit(filename)
            return '''
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>Importation de vidéo | ChronoPhys</title>

                <style>
                body {
                    font-family: Arial, Helvetica, sans-serif;
                }
                </style>
            </head>
            <body>
                <header></header>
                <main>
                <h2>Importer une vidéo sur ChronoPhys</h2>
                <form enctype="multipart/form-data" action="" method="POST">
                    
                    <p style="color: rgb(26, 112, 52); font-style: italic">
                    La vidéo a bien été transférée vers ChronoPhys. Vous pouvez retourner sur le logiciel et cliquer sur "Ok".
                
                </form>
                </main>
                <footer></footer>
            </body>
            </html>
            '''


    app.run(host=local_ip_address, port=8080)