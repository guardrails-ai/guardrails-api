from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

INIT_EXTENSIONS = """
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
"""