from functools import wraps
import traceback
from werkzeug.exceptions import HTTPException
from guardrails_api.classes.http_error import HttpError
from guardrails_api.utils.logger import logger


def handle_error(fn):
    @wraps(fn)
    def decorator(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except HttpError as http_error:
            logger.error(http_error)
            traceback.print_exception(http_error)
            return http_error.to_dict(), http_error.status
        except HTTPException as http_exception:
            logger.error(http_exception)
            traceback.print_exception(http_exception)
            http_error = HttpError(http_exception.code, http_exception.description)
            return http_error.to_dict(), http_error.status
        except Exception as e:
            logger.error(e)
            traceback.print_exception(e)
            return HttpError(500, "Internal Server Error").to_dict(), 500

    return decorator
