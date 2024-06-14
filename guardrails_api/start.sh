export APP_ENVIRONMENT=local
export PYTHONUNBUFFERED=1
export LOGLEVEL="INFO"
export GUARDRAILS_LOG_LEVEL="INFO"
export GUARDRAILS_PROCESS_COUNT=1
export SELF_ENDPOINT=http://localhost:8000
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

gunicorn --bind 0.0.0.0:8000 --timeout=5 --threads=10 "guardrails_api.app:create_app()"
