#!/bin/bash

MODEL_NAME="${MODEL_NAME:-google/flan-t5-base}"
CARD="${CARD:-cards.wnli}"
TEMPLATE="${TEMPLATE:-templates.classification.multi_class.relation.default}"
GPU="${GPU:-false}"

TMP_YAML=$(mktemp /tmp/lmeval_job.XXXXXX.yaml)

BASE_YAML="
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
  name: \"evaljob-sample\"
spec:
  allowOnline: true
  model: hf
  modelArgs:
    - name: pretrained
      value: \"{{MODEL_NAME}}\"
  taskList:
    taskRecipes:
      - card:
          name: \"{{CARD}}\"
        template: \"{{TEMPLATE}}\"
  logSamples: true
"

if [[ "$GPU" == "true" ]]; then
  GPU_SECTION="
  pod:
    container:
      resources:
        limits:
          cpu: '1'
          memory: 8Gi
          nvidia.com/gpu: '1'
        requests:
          cpu: '1'
          memory: 8Gi
          nvidia.com/gpu: '1'
"
  YAML_CONTENT="${BASE_YAML}${GPU_SECTION}"
else
  YAML_CONTENT="${BASE_YAML}"
fi

echo "$YAML_CONTENT" | sed \
  -e "s|{{MODEL_NAME}}|$MODEL_NAME|g" \
  -e "s|{{CARD}}|$CARD|g" \
  -e "s|{{TEMPLATE}}|$TEMPLATE|g" > "$TMP_YAML"

echo "Generated YAML file:"
cat "$TMP_YAML"

kubectl apply -f "$TMP_YAML"

rm "$TMP_YAML"
