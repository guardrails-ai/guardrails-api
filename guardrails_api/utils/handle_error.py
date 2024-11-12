from functools import wraps
import traceback
from werkzeug.exceptions import HTTPException
from guardrails_api.classes.http_error import HttpError
from guardrails_api.utils.logger import logger
from guardrails.errors import ValidationError


def handle_error(fn):
    @wraps(fn)
    def decorator(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValidationError as validation_error:
            logger.error(validation_error)
            traceback.print_exception(
                type(validation_error), validation_error, validation_error.__traceback__
            )
            resp_body = {"status_code": 400, "detail": str(validation_error)}
            return resp_body, 400
        except HttpError as http_error:
            logger.error(http_error)
            traceback.print_exception(
                type(http_error), http_error, http_error.__traceback__
            )
            resp_body = http_error.to_dict()
            resp_body["status_code"] = http_error.status
            resp_body["detail"] = http_error.message
            return resp_body, http_error.status
        except HTTPException as http_exception:
            logger.error(http_exception)
            traceback.print_exception(http_exception)
            http_error = HttpError(http_exception.code, http_exception.description)
            resp_body = http_error.to_dict()
            resp_body["status_code"] = http_error.status
            resp_body["detail"] = http_error.message

            return resp_body, http_error.status
        except Exception as e:
            logger.error(e)
            traceback.print_exception(e)
            resp_body = HttpError(500, "Internal Server Error").to_dict()
            resp_body["status_code"] = 500
            resp_body["detail"] = "Internal Server Error"
            return resp_body, 500

    return decorator
