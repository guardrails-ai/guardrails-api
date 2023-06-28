import os
import traceback
from flask import Flask, request
from sqlalchemy import text
from src.classes.health_check import HealthCheck
from src.classes.http_error import HttpError
from flask_sqlalchemy import SQLAlchemy
from src.classes.validation_output import ValidationOutput
from swagger_ui import api_doc

from src.clients.guard_client import GuardClient
app = Flask(__name__)
api_doc(app, config_path='./open-api-spec.yml', url_prefix='/docs', title='GuardRails API Docs')

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
      # Make sure we're connected to the database and can run queries
      query = text("SELECT count(datid) FROM pg_stat_activity;")
      response = db.session.execute(query).all()
      print('response: ', response)
      # There's probably a better way to serialize these classes built into Flask
      return HealthCheck(200, 'Ok').to_dict()
    except Exception as e:
       print(e)
       return HttpError(500, 'Internal Server Error').to_dict()

@app.route("/guards/<guard_id>/validate", methods = ['POST'])
def validate(guard_id: str):
    try:
      if request.method != 'POST':
         raise HttpError(405, 'Method Not Allowed', '/guards/<guard_id>/validate only supports the POST method. You specified %s'.format(request.method))
      payload = request.data.decode() 
      guardClient = GuardClient()
      guard = guardClient.get_guard(guard_id)
      result = guard.parse(payload)
      return ValidationOutput(True, result, guard.state.all_histories).to_dict()
    except HttpError as http_error:
       print(e)
       traceback.print_exception(http_error)
       return http_error.to_dict(), http_error.status
    except Exception as e:
       print(e)
       traceback.print_exception(e)
       return HttpError(500, 'Internal Server Error').to_dict(), 500
