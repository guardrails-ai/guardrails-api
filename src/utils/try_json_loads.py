import json


def try_json_loads(val):
    try:
        string_val = json.loads(val, default=str)
        return string_val
    except:
        return val