import requests


def has_internet_connection() -> bool:
    try:
        requests.get("https://www.guardrailsai.com/")
        return True
    except requests.ConnectionError:
        return False