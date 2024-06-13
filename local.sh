export APP_ENVIRONMENT=local
# export NODE_ENV=production
export AWS_PROFILE=dev
export AWS_DEFAULT_REGION=us-east-1
export PGPORT=5432
export PGDATABASE=postgres
export PGHOST=localhost
export PGUSER=${PGUSER:-postgres}
export PGPASSWORD=${PGPASSWORD:-changeme}

# export AWS_EXECUTION_ENV=AWS_ECS_Fargate

export PYTHONUNBUFFERED=1
export OTEL_PYTHON_TRACER_PROVIDER=sdk_tracer_provider
export OTEL_SERVICE_NAME=guardrails-api
export OTEL_TRACES_EXPORTER=otlp #,console
export OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST="Accept-Encoding,User-Agent,Referer"
export OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE="Last-Modified,Content-Type"
export OTEL_METRICS_EXPORTER=none #otlp #,console

# export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
# export OTEL_EXPORTER_OTLP_ENDPOINT=https://hty0gc1ok3.execute-api.us-east-1.amazonaws.com
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

export OTEL_SDK_DISABLED=true

# export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://hty0gc1ok3.execute-api.us-east-1.amazonaws.com/v1/traces
# export OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=https://hty0gc1ok3.execute-api.us-east-1.amazonaws.com/v1/metrics
# export OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=https://hty0gc1ok3.execute-api.us-east-1.amazonaws.com/v1/logs
export LOGLEVEL="INFO"
export GUARDRAILS_LOG_LEVEL="INFO"
export GUARDRAILS_PROCESS_COUNT=1
export SELF_ENDPOINT=http://localhost:8000
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
export HF_API_KEY=${HF_TOKEN}

# For running https locally
# mkdir -p ~/certificates
# if [ ! -f ~/certificates/local.key ]; then
#     openssl req  -nodes -new -x509  -keyout ~/certificates/local.key -out ~/certificates/local.cert
# fi



# For running https locally
# gunicorn --keyfile ~/certificates/local.key --certfile ~/certificates/local.cert --bind 0.0.0.0:8000 --timeout=5 --threads=10 "app:create_app()"
gunicorn --bind 0.0.0.0:8000 --timeout=5 --threads=10 "app:create_app()"
