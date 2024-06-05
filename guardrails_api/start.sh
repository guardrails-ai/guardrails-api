export APP_ENVIRONMENT=local
export PYTHONUNBUFFERED=1
export LOGLEVEL="INFO"
export GUARDRAILS_LOG_LEVEL="INFO"
export GUARDRAILS_PROCESS_COUNT=1
export SELF_ENDPOINT=http://localhost:8000
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# TODO: Include the bundled api spec in the published package
curl https://raw.githubusercontent.com/guardrails-ai/guardrails-api-client/main/service-specs/guardrails-service-spec.yml -o ./open-api-spec.yml
npx @redocly/cli bundle --dereferenced --output ./open-api-spec.json --ext json ./open-api-spec.yml

gunicorn --bind 0.0.0.0:8000 --timeout=5 --threads=10 "app:create_app()"
