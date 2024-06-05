import boto3
import json
import os
from flask import Flask
from sqlalchemy import text
from typing import Tuple
from guardrails_api.models.base import db, INIT_EXTENSIONS


def postgres_is_enabled() -> bool:
    return os.environ.get("PGHOST", None) is not None


class PostgresClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PostgresClient, cls).__new__(cls)
        return cls._instance

    def fetch_pg_secret(self, secret_arn: str) -> dict:
        client = boto3.client("secretsmanager")
        response: dict = client.get_secret_value(SecretId=secret_arn)
        secret_string = response.get("SecretString")
        try:
            secret = json.loads(secret_string)
            return secret
        except Exception:
            pass

    def get_pg_creds(self) -> Tuple[str, str]:
        pg_user = None
        pg_password = None
        pg_password_secret = os.environ.get("PGPASSWORD_SECRET_ARN")
        if pg_password_secret is not None:
            pg_secret = self.fetch_pg_secret(pg_password_secret) or {}
            pg_user = pg_secret.get("username")
            pg_password = pg_secret.get("password")

        pg_user = pg_user or os.environ.get("PGUSER", "postgres")
        pg_password = pg_password or os.environ.get("PGPASSWORD")
        return pg_user, pg_password

    def initialize(self, app: Flask):
        pg_user, pg_password = self.get_pg_creds()
        pg_host = os.environ.get("PGHOST", "localhost")
        pg_port = os.environ.get("PGPORT", "5432")
        pg_database = os.environ.get("PGDATABASE", "postgres")

        pg_endpoint = (
            pg_host
            if pg_host.endswith(
                f":{pg_port}"
            )  # FIXME: This is a cheap check; maybe use a regex instead?
            else f"{pg_host}:{pg_port}"
        )

        conf = f"postgresql://{pg_user}:{pg_password}@{pg_endpoint}/{pg_database}"

        if os.environ.get("NODE_ENV") == "production":
            conf = f"{conf}?sslmode=verify-ca&sslrootcert=global-bundle.pem"

        app.config["SQLALCHEMY_DATABASE_URI"] = conf

        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.secret_key = "secret"
        self.app = app
        self.db = db
        db.init_app(app)
        from guardrails_api.models.guard_item import GuardItem  # NOQA
        from guardrails_api.models.guard_item_audit import (  # NOQA
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
