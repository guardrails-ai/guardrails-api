from flask import Flask, request, abort
from swagger_ui import api_doc
from flask_cors import CORS
from src.auth import authenticate_user

app = Flask(__name__)
CORS(app)


@app.before_request
def check_auth_token():
    if request.path in ("/", "/health-check"):
        return

    token = request.headers.get("authorization")
    user = authenticate_user(token)

    if user is None:
        abort(401)
    request.__setattr__("user", user)


def create_app():
    api_doc(
        app,
        config_path="./open-api-spec.yml",
        url_prefix="/docs",
        title="GuardRails API Docs",
    )

    from src.clients import PostgresClient

    pg_client = PostgresClient()
    pg_client.initialize(app)

    from src.blueprints import root_bp, guards_bp, railspec_templates_bp

    app.register_blueprint(root_bp)
    app.register_blueprint(guards_bp)
    app.register_blueprint(railspec_templates_bp)

    return app
