import os
from flask import Flask
from src.models.base import db

class PostgresClient:
    _instance = None
    def __new__(cls):
      if cls._instance is None:
            cls._instance = super(PostgresClient, cls).__new__(cls)
      return cls._instance

    def initialize(self, app: Flask):
        pg_user = os.environ.get('PGUSER', 'postgres')
        pg_password = os.environ.get('PGPASSWORD','undefined')
        pg_host = os.environ.get('PGHOST','localhost')
        pg_port = os.environ.get('PGPORT','5432')
        pg_database = os.environ.get('PGDATABASE','postgres')

        CONF = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
        app.config['SQLALCHEMY_DATABASE_URI'] = CONF

        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.secret_key = 'secret'
        self.app = app
        self.db = db
        db.init_app(app)
        from src.models.guard_item import GuardItem
        with self.app.app_context():
          self.db.create_all()