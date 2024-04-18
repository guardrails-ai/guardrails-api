curl https://raw.githubusercontent.com/guardrails-ai/guardrails-api-client/main/service-specs/guardrails-service-spec.yml -o ./open-api-spec.yml

npx @redocly/cli bundle --dereferenced --output ./open-api-spec.json --ext json ./open-api-spec.yml

docker build \
    -f Dockerfile.lite \
    --progress=plain \
    --no-cache \
    --build-arg CACHEBUST="$(date)" \
    --build-arg GITHUB_TOKEN="$GITHUB_TOKEN" \
    --build-arg HF_TOKEN="$HF_TOKEN" \
    -t "guardrails-api:dev" .;
