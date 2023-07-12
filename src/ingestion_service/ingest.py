from flask import Flask, request
from clients.ingestion_client import IngestionClient

app = Flask(__name__)

def create_database(): 
    app = Flask(__name__)
    from clients.postgrespg_client import PostgresPGClient
    client = PostgresPGClient()
    client.initialize(app)

    

    @app.route("/")
    def home():
        return "Hello, Flask!"

    @app.route("/ingest", methods = ['POST'])
    def ingest():
        if(request.method == 'POST'):
            payload = request.json
            ingestionClient = IngestionClient()
            return ingestionClient.ingest(**payload)
        else: 
           pass
    
    @app.route("/embeddings/<uuid>", methods = ['PUT', 'GET', 'DELETE'])
    def embeddings(uuid: str):
       print(uuid)
       ingestionClient = IngestionClient()
       if request.method == 'GET':
        return ingestionClient.getEmbeddings(uuid)
       elif request.method == 'PUT': 
        payload = request.json
        return ingestionClient.updateEmbeddings(uuid, **payload)
       elif request.method == 'DELETE': 
          return ingestionClient.deleteEmbeddings(uuid)
       else: 
          pass #to-do raise an error
        

    return app

