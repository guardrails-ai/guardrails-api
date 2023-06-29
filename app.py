import traceback
from flask import Flask, request
from sqlalchemy import text
from src.classes.health_check import HealthCheck
from src.classes.http_error import HttpError
from flask_sqlalchemy import SQLAlchemy
from src.classes.validation_output import ValidationOutput
from swagger_ui import api_doc
from functools import wraps

from src.clients.postgres_client import PostgresClient

def handle_error(fn):
    @wraps(fn)
    def decorator(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except HttpError as http_error:
          print(e)
          traceback.print_exception(http_error)
          return http_error.to_dict(), http_error.status
        except Exception as e:
          print(e)
          traceback.print_exception(e)
          return HttpError(500, 'Internal Server Error').to_dict(), 500

    return decorator

from src.clients.guard_client import GuardClient
app = Flask(__name__)
api_doc(app, config_path='./open-api-spec.yml', url_prefix='/docs', title='GuardRails API Docs')

# TODO: put this inside of a singleton getter/refresher to handle stale connections
pg = PostgresClient(app)
db = pg.db

@app.route("/")
@handle_error
def home():
    return "Hello, Flask!"

@app.route("/health-check")
@handle_error
def healthCheck():
    # Make sure we're connected to the database and can run queries
    query = text("SELECT count(datid) FROM pg_stat_activity;")
    response = db.session.execute(query).all()
    print('response: ', response)
    # There's probably a better way to serialize these classes built into Flask
    return HealthCheck(200, 'Ok').to_dict()

@app.route("/guards", methods = ['GET', 'POST'])
@handle_error
def guards():
    guardClient = GuardClient()
    if request.method == 'GET':
        guards = guardClient.get_guards(db)
        return [g.to_dict() for g in guards]
    elif request.method == 'POST':
        payload = request.json
        guard = guardClient.post_guard(payload, db)
        return guard.to_dict()
    else:
        raise HttpError(405, 'Method Not Allowed', '/guards only supports the GET and POST methods. You specified %s'.format(request.method))

@app.route("/guards/<guard_name>", methods = ['GET', 'POST'])
@handle_error
def guard(guard_name: str):
    guardClient = GuardClient()
    if request.method == 'PUT':
        payload = request.json
        guards = guardClient.put_guard(guard_name, payload, db)
        return [g.to_dict() for g in guards]
    elif request.method == 'DELETE':
        guard = guardClient.delete_guard(guard_name, db)
        return guard.to_dict()
    else:
        raise HttpError(405, 'Method Not Allowed', '/guard/<guard_name> only supports the PUT and DELETE methods. You specified %s'.format(request.method))

@app.route("/guards/<guard_name>/validate", methods = ['POST'])
@handle_error
def validate(guard_name: str):
    if request.method != 'POST':
        raise HttpError(405, 'Method Not Allowed', '/guards/<guard_name>/validate only supports the POST method. You specified %s'.format(request.method))
    payload = request.data.decode()
    guardClient = GuardClient()
    guard = guardClient.get_guard(guard_name)
    result = guard.parse(payload)
    return ValidationOutput(True, result, guard.state.all_histories).to_dict()

