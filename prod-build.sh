docker build \
    -f Dockerfile.prod \
    --progress=plain \
    --no-cache \
    --build-arg CACHEBUST="$(date)" \
    -t "guardrails-api:prod" .;