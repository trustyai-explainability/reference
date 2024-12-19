#!/bin/bash

MODEL_NAME="${MODEL_NAME:-default-model-name}"
NAMESPACE="test"

TEMPLATE_FILE="resources/vllm-serving.template.yaml"

OUTPUT_FILE=$(mktemp /tmp/inferenceservice.XXXXXX.yaml)

if [[ ! -f "$TEMPLATE_FILE" ]]; then
  echo "Error: Template file $TEMPLATE_FILE does not exist."
  exit 1
fi

sed -e "s|{{MODEL_NAME}}|$MODEL_NAME|g" "$TEMPLATE_FILE" > "$OUTPUT_FILE"

echo "Generated YAML file:"
cat "$OUTPUT_FILE"

echo "Deploying the InferenceService..."
kubectl apply -f "$OUTPUT_FILE" -n "$NAMESPACE"

rm "$OUTPUT_FILE"

echo "InferenceService for MODEL_NAME=$MODEL_NAME deployed successfully in namespace $NAMESPACE."
