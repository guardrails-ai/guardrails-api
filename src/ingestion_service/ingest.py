from flask import Flask, request
from ingestion_client import IngestionClient

app = Flask(__name__)

def create_database(): 
    app = Flask(__name__)
    from database import PostgresPGClient
    client = PostgresPGClient()
    client.initialize(app)

    

    @app.route("/")
    def home():
        return "Hello, Flask!"

    @app.route("/ingest")
    def ingest(articles: list, metadata: dict, validatorId: str, guardId: str, embeddingModel: str):
        ingestionClient = IngestionClient()
        return ingestionClient.ingest(articles, metadata, validatorId, guardId, embeddingModel)
    
    @app.route("/embeddings/<uuid>", methods = ['POST', 'GET', 'DELETE'])
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
          pass #raise an error later
        

    return app

