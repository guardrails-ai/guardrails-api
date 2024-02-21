export APP_ENVIRONMENT=local
export AWS_PROFILE=dev
export AWS_DEFAULT_REGION=us-east-1
export PGPORT=5432
export PGDATABASE=postgres
export PGHOST=localhost
export PGUSER=${PGUSER:-postgres}
export PGPASSWORD=${PGPASSWORD:-changeme}
export OTEL_SERVICE_NAME=guardrails-api
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_TRACES_EXPORTER=otlp #,console
export OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST="Accept-Encoding,User-Agent,Referer"
export OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE="Last-Modified,Content-Type"
export OTEL_METRICS_EXPORTER=otlp #,console
export PYTHONUNBUFFERED=1
export LOGLEVEL=INFO
export GUARDRAILS_PROCESS_COUNT=1
opentelemetry-instrument gunicorn --bind 0.0.0.0:8000 --timeout=5 --threads=10 "app:create_app()"