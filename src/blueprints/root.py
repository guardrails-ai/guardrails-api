import os
import json
import flask
from string import Template
from flask import Blueprint
from sqlalchemy import text
from src.classes.health_check import HealthCheck
from src.clients.postgres_client import PostgresClient
from src.utils.handle_error import handle_error
from src.utils.gather_request_metrics import gather_request_metrics
from src.utils.logger import logger

# from src.modules.otel_logger import logger

root_bp = Blueprint("root", __name__, url_prefix="/")
cached_api_spec = None


@root_bp.route("/")
@handle_error
@gather_request_metrics
def home():
    return "Hello, Flask!"


@root_bp.route("/health-check")
@handle_error
@gather_request_metrics
def health_check():
    # Make sure we're connected to the database and can run queries
    pg_client = PostgresClient()
    query = text("SELECT count(datid) FROM pg_stat_activity;")
    response = pg_client.db.session.execute(query).all()
    # # This works with otel logging
    # logger.info(f"response: {response}")
    # As does this
    logger.info("response: %s", response)
    # # This throws an error
    # print("response: ", response)
    return HealthCheck(200, "Ok").to_dict()


@root_bp.route("/api-docs")
@handle_error
@gather_request_metrics
def api_docs():
    global cached_api_spec
    if not cached_api_spec:
        print("API spec is not cached!")
        print("Loading from file...")
        with open('./open-api-spec.json') as api_spec_file:
            cached_api_spec = json.loads(api_spec_file.read())
            
    return json.dumps(cached_api_spec)


@root_bp.route("/docs")
@handle_error
@gather_request_metrics
def docs():
    host = os.environ.get("SELF_ENDPOINT", "http://localhost:8000")
    swagger_ui = Template("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta
    name="description"
    content="SwaggerUI"
  />
  <title>SwaggerUI</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui.css" />
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui-bundle.js" crossorigin></script>
<script nonce="{{ csp_nonce() }}">
  window.onload = () => {
    window.ui = SwaggerUIBundle({
      url: '${apiDocUrl}',
      dom_id: '#swagger-ui',
    });
  };
</script>
</body>
</html>""").safe_substitute(apiDocUrl=f"{host}/api-docs")
    
    return flask.render_template_string(swagger_ui)