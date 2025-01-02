#!/usr/bin/env bash

wait_for_pod_completion() {
  local yaml_file=$1
  local pod_name=$2
  local namespace=$3
  local timeout=600
  local interval=5
  local elapsed=0


  echo "Applying $yaml_file..."
  oc apply -f "$yaml_file" -n "$namespace"


  echo "Waiting for Pod $pod_name to complete..."
  while true; do
    phase=$(oc get pod "$pod_name" -n "$namespace" -o jsonpath='{.status.phase}')
    if [[ "$phase" == "Succeeded" ]]; then
      echo "Pod $pod_name has completed successfully."
      break
    fi
    if (( elapsed >= timeout )); then
      echo "Timed out waiting for Pod $pod_name to complete."
      exit 1
    fi
    sleep $interval
    elapsed=$((elapsed + interval))
  done
}
