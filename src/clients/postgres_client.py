import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class PostgresClient:
    def __init__(self, app: Flask):
        pg_user = os.environ.get('PGUSER', 'postgres')
        pg_password = os.environ.get('PGPASSWORD','undefined')
        pg_host = os.environ.get('PGHOST','localhost')
        pg_port = os.environ.get('PGPORT','5432')
        pg_database = os.environ.get('PGDATABASE','postgres')

        CONF = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
        app.config['SQLALCHEMY_DATABASE_URI'] = CONF

        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.secret_key = 'secret'
        self.db = SQLAlchemy(app)
        with app.app_context():
            self.db.create_all()

class GuardItem(Base):
    __tablename__ = "guards"
    # TODO: Make primary key a composite between guard.name and the guard owner's userId from w/e auth system is implemented
    name = Column(String, primary_key=True)
    railspec = Column(JSONB, nullable=False)
    num_reasks = Column(Integer, nullable=True)
    # owner = Column(String, nullable=False)

    def __init__(
            self,
            name,
            railspec,
            num_reasks
            # owner = None
    ):
        self.name = name
        self.railspec = railspec
        self.num_reasks = num_reasks
        # self.owner = owner