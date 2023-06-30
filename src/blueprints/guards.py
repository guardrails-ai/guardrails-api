from flask import Blueprint, request
from src.classes.guard_struct import GuardStruct
from src.classes.http_error import HttpError
from src.classes.validation_output import ValidationOutput
from src.clients.guard_client import GuardClient
from src.utils.handle_error import handle_error

guardsBp = Blueprint('guards', __name__, url_prefix="/guards")

@guardsBp.route("/", methods = ['GET', 'POST'])
@handle_error
def guards():
    guardClient = GuardClient()
    if request.method == 'GET':
        guards = guardClient.get_guards()
        return [g.to_dict() for g in guards]
    elif request.method == 'POST':
        payload = request.json
        guard = GuardStruct.from_request(payload)
        new_guard = guardClient.create_guard(guard)
        return new_guard.to_dict()
    else:
        raise HttpError(405, 'Method Not Allowed', '/guards only supports the GET and POST methods. You specified %s'.format(request.method))

@guardsBp.route("/<guard_name>", methods = ['PUT', 'DELETE'])
@handle_error
def guard(guard_name: str):
    guardClient = GuardClient()
    if request.method == 'PUT':
        payload = request.json
        guard = GuardStruct.from_request(payload)
        updated_guard = guardClient.update_guard(guard_name, guard)
        return updated_guard.to_dict()
    elif request.method == 'DELETE':
        guard = guardClient.delete_guard(guard_name)
        return guard.to_dict()
    else:
        raise HttpError(405, 'Method Not Allowed', '/guard/<guard_name> only supports the PUT and DELETE methods. You specified %s'.format(request.method))

@guardsBp.route("/<guard_name>/validate", methods = ['POST'])
@handle_error
def validate(guard_name: str):
    if request.method != 'POST':
        raise HttpError(405, 'Method Not Allowed', '/guards/<guard_name>/validate only supports the POST method. You specified %s'.format(request.method))
    payload = request.data.decode()
    guardClient = GuardClient()
    guard = guardClient.get_guard(guard_name)
    result = guard.parse(payload)
    return ValidationOutput(True, result, guard.state.all_histories).to_dict()