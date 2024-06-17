import os
import json
import flask
from string import Template
from flask import Blueprint
from guardrails_api.open_api_spec import get_open_api_spec
from sqlalchemy import text
from guardrails_api.classes.health_check import HealthCheck
from guardrails_api.clients.postgres_client import PostgresClient, postgres_is_enabled
from guardrails_api.utils.handle_error import handle_error
from guardrails_api.utils.logger import logger


root_bp = Blueprint("root", __name__, url_prefix="/")


@root_bp.route("/")
@handle_error
def home():
    return "Hello, Flask!"


@root_bp.route("/health-check")
@handle_error
def health_check():
    # If we're not using postgres, just return Ok
    if not postgres_is_enabled():
        return HealthCheck(200, "Ok").to_dict()
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
def api_docs():
    api_spec = get_open_api_spec()
    return json.dumps(api_spec)


@root_bp.route("/docs")
@handle_error
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
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css" />
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js" crossorigin></script>
<script>
  window.onload = () => {
    window.ui = SwaggerUIBundle({
      url: '${apiDocUrl}',
      dom_id: '#swagger-ui',
    });
  };
</script>
</body>
</html>""").safe_substitute(apiDocUrl=f"{host}/api-docs")  # noqa

    return flask.render_template_string(swagger_ui)
