docker build \
    -f Dockerfile.enterprise \
    --progress=plain \
    --no-cache \
    --build-arg CACHEBUST="$(date)" \
    -t "guardrails-api-enterprise:latest" .;