#!/bin/bash

callerIdentity=$(aws sts get-caller-identity);
accountId=$(jq -r .Account <<< $callerIdentity);
imageName="${IMAGE_NAME:-validation-service}";
repoName="${ECR_REPO_NAME:-guardrails-validation-service-test}";
commitSha=$(git rev-parse HEAD);
region="${AWS_DEFAULT_REGION:-us-east-1}";
defaultEcrEndpoint="${accountId}.dkr.ecr.${region}.amazonaws.com";
ecrEndpoint="${ECR_ENDPOINT:-$defaultEcrEndpoint}"
ecrImageUrl="${ecrEndpoint}/${repoName}";

# Setup unpublished api client
echo "Building api client..."
bash build-sdk.sh

echo "Performing docker build"
docker login -u AWS -p $(aws ecr get-login-password --region $region) $ecrEndpoint;

docker buildx build \
  --platform linux/arm64 \
  --progress plain \
  -f Dockerfile.prod \
  -t "$imageName:$commitSha" \
  -t "$imageName:latest" . \
  || exit 1;

docker image tag "$imageName:$commitSha" "$ecrImageUrl:$commitSha";
docker image tag "$imageName:$version" "$ecrImageUrl:$version";
docker image tag "$imageName:latest" "$ecrImageUrl:latest";

echo "Publishing to ECR"
docker push $ecrImageUrl --all-tags;