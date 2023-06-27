import os
from flask import Flask
from sqlalchemy import text
from src.classes.health_check import HealthCheck
from src.classes.http_error import HttpError
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)

pg_user = os.environ.get('PGUSER', 'postgres')
pg_password = os.environ.get('PGPASSWORD','undefined')
pg_host = os.environ.get('PGHOST','localhost')
pg_port = os.environ.get('PGPORT','5432')
pg_database = os.environ.get('PGDATABASE','postgres')

CONF = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
app.config['SQLALCHEMY_DATABASE_URI'] = CONF

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret'
db = SQLAlchemy(app)


@app.route("/")
def home():
    return "Hello, Flask!"

@app.route("/health-check")
def healthCheck():
    try:
      query = '''SELECT 1 FROM DUAL;'''
      response = db.session.query(text(query))
      print(response)
      return HealthCheck(200, 'Ok').toDict()
    except Exception as e:
       print(e)
       return HttpError(500, 'Internal Server Error').toDict()
