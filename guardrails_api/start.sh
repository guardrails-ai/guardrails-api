# TODO: Have to pass the config file to this now or it will blow up.
gunicorn --bind 0.0.0.0:8000 --timeout=5 --workers=1 "guardrails_api.app:create_app()"
