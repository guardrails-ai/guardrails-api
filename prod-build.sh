# Setup unpublished api client
echo "Building api client..."
# Speed things up for local testing
# bash build-sdk.sh

# Copy Lambda Layer and convert to extension
if [ ! -d "opentelemetry-lambda-layer" ]; then
  curl $(aws lambda get-layer-version-by-arn --arn arn:aws:lambda:us-east-1:184161586896:layer:opentelemetry-collector-arm64-0_2_0:1 --query 'Content.Location' --output text) --output otel-collector.zip
  unzip otel-collector.zip -d ./opentelemetry-lambda-layer
  rm otel-collector.zip
fi

docker build \
    -f Dockerfile.prod \
    --progress=plain \
    -t "guardrails-api:prod" .;
    # --no-cache \
    # --build-arg CACHEBUST="$(date)" \