import os
import traceback
import logging
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

from src.clients.guard_client import GuardClient
from src.modules.otel_tracer import otel_tracer
from src.modules.otel_logger import otel_logger

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

# resource = Resource(attributes={
#    'service.name': 'validation-loop'
# })
# trace.set_tracer_provider(TracerProvider(resource=resource))
# otlp_span_exporter = OTLPSpanExporter(endpoint='otel-collector:4317', insecure=True)
# span_processor = SimpleSpanProcessor(otlp_span_exporter)
# trace.get_tracer_provider().add_span_processor(span_processor)
# tracer = trace.get_tracer(__name__)

# logger_provider = LoggerProvider(resource=resource)
# set_logger_provider(logger_provider)
# otlp_logs_exporter = OTLPLogExporter(endpoint='otel-collector:4317', insecure=True)
# logger_provider.add_log_record_processor(SimpleLogRecordProcessor(otlp_logs_exporter))
# handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
# logging.root.setLevel(logging.NOTSET)
# # can remove namespace 'open-search' if we want all root logs to go to OpenSearch
# otel_logger = logging.getLogger('otel')
# otel_logger.addHandler(handler)

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

@app.route("/")
def home():
   return "Hello, Flask!"

@app.route("/ingest")
def ingest():
   with otel_tracer.start_as_current_span('foo'):
      otel_logger.info('Guardrails is cool!')
   return 'Done!'

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
