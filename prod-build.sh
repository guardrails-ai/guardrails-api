curl https://raw.githubusercontent.com/guardrails-ai/guardrails-api-client/main/service-specs/guardrails-service-spec.yml -o ./open-api-spec.yml

# Dereference API Spec to JSON
npx @redocly/cli bundle --dereferenced --output ./open-api-spec.json --ext json ./open-api-spec.yml

# Copy Lambda Layer and convert to extension
# if [ ! -d "opentelemetry-lambda-layer" ]; then
#   curl $(aws lambda get-layer-version-by-arn --arn arn:aws:lambda:us-east-1:184161586896:layer:opentelemetry-collector-arm64-0_2_0:1 --query 'Content.Location' --output text) --output otel-collector.zip
#   unzip otel-collector.zip -d ./opentelemetry-lambda-layer
#   rm otel-collector.zip
# fi

docker build \
    -f Dockerfile.prod \
    --progress=plain \
    --build-arg CACHEBUST="$(date)" \
    --no-cache \
    -t "guardrails-api:prod" .;
