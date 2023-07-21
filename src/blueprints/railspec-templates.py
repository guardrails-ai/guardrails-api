from flask import Blueprint, request
from src.classes.railspec_template_struct import RailspecTemplateStruct
from src.classes.http_error import HttpError
from src.classes.validation_output import ValidationOutput
from src.clients.railspec_template_client import RailspecClient
from src.utils.handle_error import handle_error

railspec_templates_bp = Blueprint("railspec-templates", __name__, url_prefix="/railspec-templates")


@railspec_templates_bp.route("/", methods=["GET", "POST"])
@handle_error
def railspec_templates():
    railspec_client = RailspecClient()
    if request.method == "GET":
        railspec_templates = railspec_client.get_railspec_templates()
        return [r.to_response() for r in railspec_templates]
    elif request.method == "POST":
        payload = request.json
        railspec = RailspecTemplateStruct.from_request(payload)
        new_railspec = railspec_client.create_railspec(railspec)
        return new_railspec.to_response()
    else:
        raise HttpError(
            405,
            "Method Not Allowed",
            "/railspec-templates only supports the GET and POST methods. You specified"
            " {request_method}".format(request_method=request.method),
        )


@railspec_templates_bp.route("/<railspec_name>", methods=["GET", "PUT", "DELETE"])
@handle_error
def railspec(railspec_name: str):
    railspec_client = RailspecClient()
    if request.method == "GET":
        as_of_query = request.args.get("asOf")
        railspec = railspec_client.get_railspec(railspec_name, as_of_query)
        return railspec.to_response()
    elif request.method == "PUT":
        payload = request.json
        railspec = RailspecTemplateStruct.from_request(payload)
        updated_railspec = railspec_client.upsert_railspec(railspec_name, railspec)
        return updated_railspec.to_response()
    elif request.method == "DELETE":
        railspec = railspec_client.delete_railspec(railspec_name)
        return railspec.to_response()
    else:
        raise HttpError(
            405,
            "Method Not Allowed",
            "/railspec-template/<railspec_name> only supports the GET, PUT, and DELETE methods."
            " You specified {request_method}".format(
                request_method=request.method
            ),
        )
