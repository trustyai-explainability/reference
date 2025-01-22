#!/usr/bin/env bash

set -e

NS="test"

oc apply -f 00-pvc.yaml -n $NS

echo "Waiting for PVC to settle..."
sleep 5

source ./00-wait-completion.sh

wait_for_pod_completion "00-downloader-pod-flan-arceasy.yaml" "lmeval-copy" "$NS"


echo "Deploy LMEval Job"
oc apply -f 00-offline-no-code_cr-local-flan-arceasy.yaml -n $NS