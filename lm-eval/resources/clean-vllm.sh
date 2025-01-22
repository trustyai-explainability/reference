#!/bin/bash

UNIQUE_LABEL_KEY="lmevaltests"
UNIQUE_LABEL_VALUE="vllm"

RESOURCE_TYPES=(
  "serviceaccount"
  "secret"
  "rolebinding"
  "service"
  "deployment"
  "servingruntime.serving.kserve.io"
  "persistentvolumeclaim"
)

NAMESPACE="test"

echo "Deleting resources with label ${UNIQUE_LABEL_KEY}=${UNIQUE_LABEL_VALUE} in namespace ${NAMESPACE}..."
for RESOURCE_TYPE in "${RESOURCE_TYPES[@]}"; do
  kubectl delete "${RESOURCE_TYPE}" --selector="${UNIQUE_LABEL_KEY}=${UNIQUE_LABEL_VALUE}" --namespace="${NAMESPACE}"
done

echo "All resources with label ${UNIQUE_LABEL_KEY}=${UNIQUE_LABEL_VALUE} have been deleted."
