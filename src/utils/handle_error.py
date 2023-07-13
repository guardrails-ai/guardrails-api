from functools import wraps
import traceback
from src.classes.http_error import HttpError

def handle_error(fn):
    @wraps(fn)
    def decorator(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except HttpError as http_error:
          print(http_error)
          traceback.print_exception(http_error)
          return http_error.to_dict(), http_error.status
        except Exception as e:
          print(e)
          traceback.print_exception(e)
          return HttpError(500, 'Internal Server Error').to_dict(), 500

    return decorator