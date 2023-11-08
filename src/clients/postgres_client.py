import boto3
import os
from flask import Flask
from sqlalchemy import text
from src.models.base import db, INIT_EXTENSIONS


class PostgresClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PostgresClient, cls).__new__(cls)
        return cls._instance
    
    def fetch_pg_secret(self, secret_arn: str) -> str:
        client = boto3.client('secretsmanager')
        response: dict = client.get_secret_value(
            SecretId=secret_arn
        )
        return response.get('SecretString')


    def initialize(self, app: Flask):
        pg_user = os.environ.get("PGUSER", "postgres")
        pg_password = os.environ.get("PGPASSWORD")
        pg_password_secret = os.environ.get("PGPASSWORD_SECRET_ARN")
        if pg_password is None and pg_password_secret is not None:
            pg_password = self.fetch_pg_secret(pg_password_secret)
        pg_host = os.environ.get("PGHOST", "localhost")
        pg_port = os.environ.get("PGPORT", "5432")
        pg_database = os.environ.get("PGDATABASE", "postgres")

        conf = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
        app.config["SQLALCHEMY_DATABASE_URI"] = conf

        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.secret_key = "secret"
        self.app = app
        self.db = db
        db.init_app(app)
        from src.models.guard_item import GuardItem  # NOQA
        from src.models.guard_item_audit import (  # NOQA
            GuardItemAudit,
            AUDIT_FUNCTION,
            AUDIT_TRIGGER,
        )

        with self.app.app_context():
            self.db.session.execute(text(INIT_EXTENSIONS))
            self.db.create_all()
            self.db.session.execute(text(AUDIT_FUNCTION))
            self.db.session.execute(text(AUDIT_TRIGGER))
            self.db.session.commit()
