# Deploying Guardrails Orchestrator onto KServe RawDeployment

## Prequisites
- ODH 2.20
- NodeFeatureDiscovery (NFD) Operator installed
- NVIDIA GPU Operator installed

## Set KServe to RawDeployment Mode
1. Disable Red Hat OpenShift ServiceMesh by editing the DSCI:
    ```
    oc edit dsci -n redhat-ods-operator
    ```

2. Set the `managementState` for the `serviceMesh` component to `Removed`

3. Save the changes

4. Create an DSC with the following KServe configurations:
    ```
    kserve:
    defaultDeploymentMode: RawDeployment
    managementState: Managed
    serving:
      managementState: Removed
      name: knative-serving
    ```
## Deploy a Generator Service
1. Deploy the model container

2. Deploy the following `caikit-nlp` ServingRuntime:
    ```
    oc apply -f caikit-nlp_sr.yaml -n guardrails-test
    ```

3. Validate that the generator endpoint works
    ```
    curl -kv --data '{
        "model_id": "'"${MODEL_ID}"'",
        "inputs": "'"$1"'"
    }' "$LLM_ROUTE/api/v1/task/text-generation" \
        -H "Authorization: Bearer ${SA_TOKEN}" \
        -H "Content-Type: application/json"
    ```

## Deploy a Regex Detector Service
1. Create a namespace `guardrails-test`:
    ```
    oc create ns guardrails-test
    ```

2. Deploy the Caikit-NLP ServingRuntime
    ```
    oc apply -f caikit-standalone_sr.yaml -n guardrails-test
    ```

3. Deploy the following `regex-detector` InferenceService. Take note that the `serving.kserve.io/deploymentMode` in the annotations is set to `RawDeployment`
    ```
    oc apply -f regex-detector_isvc.yaml -n guardrails-test
    ```

4. Ensure that the generator and detector pods are up and running
    ```
    oc get pods -n guardrails-test
    ```

    Expected output:
    ```
    NAME                                        READY   STATUS    RESTARTS   AGE
    regex-detector-predictor-7b78b7bcb4-68sw7   1/1     Running   0          4h9m
    ```

## Deploy the Orchestrator
1. Create the `ConfigMap`, `Deployment`, `Service`, and `Route` objects
    ```
    oc apply -f orchestrator.yaml -n guardrails-test
    ```

2. On OpenShift, navigate to your `guardrails-test` namespace

3. Click on **Workloads** > **Pods** on the side bar and then select the `orchestrator` pod

4. Within the pod's terminal run the following commands to test the generator and detector endpoints

* To test the generator's `api/v1/text/text-generation`:
    - Retrieve the generator hostname
        ```
        LLM_HOSTNAME=$(oc get isvc -n)
        ```
    - Query the `api/v1/text/text-generation` endpoint:
        ```
        curl -kv  -d '{
            "model_id": "'"${MODEL_ID}"'",
            "inputs": "At what temp does Nitrogen boil?"
        }' "$LLM_ROUTE:8080/api/v1/task/text-generation"     -H "Content-Type: application/json"
        ```

* To test the detector's `api/v1/text/contents` endpoint:
    - Retreive the detector hostname
        ```
        DETECTOR_HOSTNAME=$(oc get isvc regex-detector -o jsonpath='{.status.url}')
        ```
    - Query the `api/v1/text/contents` endpoint
        ```
        curl -X POST "http://127.0.0.1:8000/api/v1/text/contents" \
        -H "Content-Type: application/json" \
        -H "detector-id: has_regex_match" \
        -d '{
            "contents": ["My email address is xx@domain.com and zzz@hotdomain.co.uk"],
            "regex_pattern": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
        }'
        ```

5. Test the orchestrator service