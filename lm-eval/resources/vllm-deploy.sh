#!/bin/bash

MODEL_REPO="${MODEL_REPO:-default-repo-url}"
MODEL_NAME="${MODEL_NAME:-default-model-name}"
NAMESPACE="test"

TEMPLATE_FILE="resources/vllm-storage.template.yaml"

TMP_DEPLOYMENT_FILE=$(mktemp /tmp/deployment.XXXXXX.yaml)

if [[ ! -f "$TEMPLATE_FILE" ]]; then
  echo "Error: Template file $TEMPLATE_FILE does not exist."
  exit 1
fi

sed -e "s|{{MODEL_REPO}}|$MODEL_REPO|g" \
    -e "s|{{MODEL_NAME}}|$MODEL_NAME|g" \
    "$TEMPLATE_FILE" > "$TMP_DEPLOYMENT_FILE"

echo "Generated YAML file:"
cat "$TMP_DEPLOYMENT_FILE"

echo "Applying the deployment to Kubernetes..."
kubectl apply -f "$TMP_DEPLOYMENT_FILE" -n "$NAMESPACE"

rm "$TMP_DEPLOYMENT_FILE"

echo "Deployment applied successfully."
