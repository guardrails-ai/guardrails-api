from sqlalchemy import Column, String
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from models.base import db




class IngestionItem(db.Model):
     __tablename__ = "embeddings"
     
     id = Column(String, primary_key=True)
     #embedding = Column(Vector(1536), nullable=False)
     embedding = Column(Vector(1536), nullable=True)
     data = Column(String, nullable=False)
     guardId = Column(String, nullable=False)
     validatorId = Column(String, nullable=True)
     

     def __init__(
             self,
             id,
             embedding,
             data, 
             guardId,
             validatorId
     ):
         self.id = id
         self.embedding = embedding
         self.data = data
         self.guardId = guardId
         self.validatorId = validatorId
