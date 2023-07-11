
import openai
import uuid
from models.ingestion_item import IngestionItem
from clients.postgrespg_client import PostgresPGClient

class IngestionClient: 
     def __init__(self):
          self.initialized = True
          self.client = PostgresPGClient()

     def ingest(self, articles: list, metadata: dict, validatorId: str, guardId: str, embeddingModel: str):
        embeddings = self.getOpenAPIEmbeddings(articles, embeddingModel)

        ingestion = IngestionItem(
              id = self.generateIngestionUUID(), 
              embedding=embeddings, 
              data=metadata, 
              guardId=guardId, 
              validatorId=validatorId
          )
        
        self.client.db.session.add(ingestion)
        self.client.db.session.commit()

     def getEmbeddings(self, uuid: str): 
        item = self.getIngestionItem(uuid)
        return self.ingestionItemToDict(item)
     
     def updateEmbeddings(self, uuid: str, articles: list, metadata: dict, validatorId: str, guardId: str, embeddingModel: str): 
        
        ingestionItem = self.getIngestionItem(uuid)
        embeddings = self.getOpenAPIEmbeddings(articles, embeddingModel)
        ingestionItem.data = metadata
        ingestionItem.embedding = embeddings
        ingestionItem.guardId = guardId
        ingestionItem.validatorId = validatorId

        
        self.client.db.session.commit()
        return ingestionItem
        
    
     def deleteEmbeddings(self, uuid): 
        ingestionItem = self.getIngestionItem(uuid)
        self.client.db.session.delete(ingestionItem)
        self.client.db.session.commit()
        return self.ingestionItemToDict(ingestionItem)
     
     def getOpenAPIEmbeddings(articles, embeddingModel='text-embedding-ada-002'): 
      return openai.Embedding.create(input = articles, model=embeddingModel)['data'][0]['embedding']
    
     def getIngestionItem(self, uuid): 
        return self.client.db.session.query(IngestionItem).filter_by(id=uuid).first()

     def generateIngestionUUID():
        return uuid.uuid1()
     
     def ingestionItemToDict(seld, ingestionItem: IngestionItem): 
        return { 
           'id': ingestionItem.id, 
           'guardId': ingestionItem.guardId, 
           'embeddings': ingestionItem.embedding.tolist(), 
           'validatorId': ingestionItem.validatorId, 
           'metadata': ingestionItem.data }