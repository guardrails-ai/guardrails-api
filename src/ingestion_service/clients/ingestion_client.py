
import openai
import uuid
from models.ingestion_item import IngestionItem
from clients.postgrespg_client import PostgresPGClient

class IngestionClient: 
     def __init__(self):
          self.initialized = True
          self.client = PostgresPGClient()

     def ingest(self, articles: list, metadata: str, validatorId: str, guardId: str, articleId: str, chunkId: str, embeddingModel: str):
        embeddings = self.getOpenAPIEmbeddings(articles, embeddingModel)

        ingestion = IngestionItem(
              id = self.generateIngestionUUID(), 
              embedding=embeddings, 
              data=metadata, 
              guardId=guardId, 
              validatorId=validatorId,
              articleId=articleId, 
              chunkId=chunkId

          )
        
        self.client.db.session.add(ingestion)
        self.client.db.session.commit()

        return self.ingestionItemToDict(ingestion)

     def getEmbeddings(self, uuid: str): 
        item = self.getIngestionItem(uuid)
        return self.ingestionItemToDict(item)
     
     def getEmbeddingsForGaurd(self, gaurdId: str): 
        #to-do 
        pass
     
     def updateEmbeddings(self, uuid: str, articles: list, metadata: str, validatorId: str, guardId: str, articleId: str, chunkId: str, embeddingModel: str): 
        
        ingestionItem = self.getIngestionItem(uuid)
        openai_embeddings = self.getOpenAPIEmbeddings(articles, embeddingModel)
        
   
        ingestionItem.data = metadata
        ingestionItem.embedding = openai_embeddings
        ingestionItem.guardId = guardId
        ingestionItem.validatorId = validatorId 
        ingestionItem.articleId = articleId
        ingestionItem.chunkId = chunkId


        self.client.db.session.commit()
        return self.ingestionItemToDict(ingestionItem)
        
     def deleteEmbeddings(self, uuid): 
        ingestionItem = self.getIngestionItem(uuid)
        self.client.db.session.delete(ingestionItem)
        self.client.db.session.commit()
        return self.ingestionItemToDict(ingestionItem)
     
     def getOpenAPIEmbeddings(self, articles, embeddingModel='text-embedding-ada-002'): 
      openai.api_key = ''
      return openai.Embedding.create(input = articles, model=embeddingModel)['data'][0]['embedding']
    
     def getIngestionItem(self, uuid): 
        return self.client.db.session.query(IngestionItem).filter_by(id=uuid).first()

     def generateIngestionUUID(self):
        return str(uuid.uuid1())
     
     def ingestionItemToDict(self, ingestionItem: IngestionItem): 
        return { 
           'id': ingestionItem.id, 
           'guardId': ingestionItem.guardId, 
           'embeddings': ingestionItem.embedding.tolist(), 
           'validatorId': ingestionItem.validatorId, 
           'metadata': ingestionItem.data, 
           'articleId': ingestionItem.articleId, 
           'chunkId': ingestionItem.chunkId
           }