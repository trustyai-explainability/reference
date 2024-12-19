#!/bin/bash

set -e

TASK_NAME="${TASK_NAME:-arc_easy}"
MODEL_NAME="${MODEL_NAME:-phi-3}"
URL="${URL:-https://phi-3-test.apps.<...>.openshiftapps.com/v1/completions}"
TOKENIZER_NAME="${TOKENIZER_NAME:-google/flan-t5-base}"
SECRET_NAME="${SECRET_NAME:-user-one-token-hm4gb}"
NAMESPACE="${NAMESPACE:-test}"

TMP_YAML=$(mktemp /tmp/lmeval_job.XXXXXX.yaml)

cat <<EOF > "$TMP_YAML"
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
  name: "lmeval-test"
  namespace: "$NAMESPACE"
  labels:
    lmevaltests: "vllm"
spec:
  allowOnline: true
  model: local-completions
  taskList:
    taskNames:
      - "$TASK_NAME"
  logSamples: true
  batchSize: "1"
  modelArgs:
    - name: model
      value: "$MODEL_NAME"
    - name: base_url
      value: "${URL}/v1/completions"
    - name: num_concurrent
      value: "1"
    - name: max_retries
      value: "3"
    - name: tokenized_requests
      value: "False"
    - name: tokenizer
      value: "$TOKENIZER_NAME"
  pod:
    container:
      env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: "$SECRET_NAME"
              key: token
EOF

echo "Generated YAML file:"
cat "$TMP_YAML"

echo "Deploying the LMEvalJob..."
kubectl apply -f "$TMP_YAML" -n test

rm "$TMP_YAML"

echo "LMEvalJob deployed successfully!"
