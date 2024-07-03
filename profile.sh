#!/bin/bash

# Run this the first time
# pip install "gunicorn[gthread]"
# pip install opentelemetry-distro
# opentelemetry-bootstrap -a install

export OTEL_PYTHON_TRACER_PROVIDER=sdk_tracer_provider
export OTEL_SERVICE_NAME=guardrails-api
export OTEL_TRACES_EXPORTER=otlp
export OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST="Accept-Encoding,User-Agent,Referer"
export OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE="Last-Modified,Content-Type"
export OTEL_METRICS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

export APP_ENVIRONMENT=local
export PYTHONUNBUFFERED=1
export LOGLEVEL="INFO"
export GUARDRAILS_LOG_LEVEL="INFO"
export HOST=http://localhost
export PORT=8000
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

opentelemetry-instrument gunicorn --bind 0.0.0.0:8000 --timeout=5 --threads=10 'guardrails_api.app:create_app("sample.env", "sample_config.py")'