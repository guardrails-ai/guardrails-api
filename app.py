import os
import traceback
from flask import Flask, request
from sqlalchemy import text
from src.classes.health_check import HealthCheck
from src.classes.http_error import HttpError
from flask_sqlalchemy import SQLAlchemy
from src.classes.validation_output import ValidationOutput
from swagger_ui import api_doc
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import SimpleLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opensearchpy import OpenSearch

import guardrails as gd
import openai
# For integration with otel-instrumentors package
# from otel_instrumentors import (
#    otel_logger, 
#    otel_meter, 
#    metric_reader,
#    otel_tracer
# ) 

from src.clients.guard_client import GuardClient
from src.modules.otel_tracer import otel_tracer
from src.modules.otel_logger import otel_logger
from src.modules.otel_meter import otel_meter, metric_reader

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

# DELETE ME: OpenSearch client example for telemetry api
client = OpenSearch(
   ['opensearch-node1', 'opensearch-node2'],
   use_ssl=True,
   # no verify SSL certificates
   verify_certs=False,
   # don't show warnings about ssl certs verification
   ssl_show_warn=False,
   # http_compress = True,
   http_auth = ('admin', 'admin'),
   # ssl_assert_hostname = False,
)

# can we add metadata?
# one counter per user id and one global
ingest_counter = otel_meter.create_counter('ingest')

# t-SNE for vector projections

@app.route("/")
def home():
   return "Hello, Flask!"

# DELETE ME: test route and function
@app.route("/ingest")
def ingest():

   doctors_notes = """49 y/o Male with chronic macular rash to face & hair, worse in beard, eyebrows & nares.
Itchy, flaky, slightly scaly. Moderate response to OTC steroid cream"""
   guard = gd.Guard.from_rail('getting_started.rail')

   # Set your OpenAI API key
   os.environ["OPENAI_API_KEY"] = "INSERT"
   
   with otel_tracer.start_as_current_span('guard'):
      # Wrap the OpenAI API call with the `guard` object
      guard(
         openai.Completion.create,
         prompt_params={"doctors_notes": doctors_notes},
         engine="text-davinci-003",
         max_tokens=1024,
         temperature=0.3,
      )
      
      # Example log
      otel_logger.info('Guardrails is cool!')

      # Example metric, this doesn't reset
      ingest_counter.add(1)
      metric_reader.collect()

   return 'Done!'

# DELETE ME: example query for telemetry api
@app.route("/get-trace")
def getTrace():
   query = {
      'size': 5,
      'query': {
         'match': {
            'traceGroup': 'foo'
         }
      }
   }
   response = client.search(body=query, index='')
   return response

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
      # Add telemetry here
      return ValidationOutput(True, result, guard.state.all_histories).to_dict()
    except HttpError as http_error:
       print(e)
       traceback.print_exception(http_error)
       return http_error.to_dict(), http_error.status
    except Exception as e:
       print(e)
       traceback.print_exception(e)
       return HttpError(500, 'Internal Server Error').to_dict(), 500
