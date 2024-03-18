npx @redocly/cli bundle --dereferenced --output ./open-api-spec.json --ext json ./open-api-spec.yml

docker build \
    -f Dockerfile.dev \
    --progress=plain \
    --no-cache \
    --build-arg CACHEBUST="$(date)" \
    --build-arg GITHUB_TOKEN="$GITHUB_TOKEN" \
    -t "guardrails-api:dev" .;