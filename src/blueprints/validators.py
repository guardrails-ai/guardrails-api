from typing import List
from flask import Blueprint, request
from src.classes.http_error import HttpError
from src.utils.handle_error import handle_error
from src.utils.gather_request_metrics import gather_request_metrics

validators_bp = Blueprint("validators", __name__, url_prefix="/validators")

def list_validators() -> List[str]:
  import guardrails.hub
  import validators
  from guardrails.validator_base import validators_registry
  validator_ids = validators_registry.keys()
  return list(validator_ids)

@validators_bp.route("/")
@handle_error
@gather_request_metrics
def get_validators():
    if request.method == "GET":
        return list_validators()
    else:
        raise HttpError(
            405,
            "Method Not Allowed",
            "/guard/<guard_name> only supports the GET, PUT, and DELETE methods."
            " You specified {request_method}".format(
                request_method=request.method
            ),
        )