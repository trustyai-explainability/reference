# Deploying GuardrailsOrchestrator onto KServe RawDeployment

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
    ```
    oc apply -f gpt2.yaml -n guardrails-test
    ```
2. Deploy the following Caikit Standalone ServingRuntime:
    ```
    oc apply -f generator/caikit-standalone-sr.yaml -n guardrails-test
    ```
3. Add the following `annotation` to `generator/gpt2-isvc.yaml` to use KServe in RawDeployment mode:
    ```
    serving.kserve.io/deploymentMode: RawDeployment
    ```
4. Deploy the following InferenceService:
    ```
    oc apply -f generator/gpt2-isvc.yaml -n guardrails-test
    ```

5. Ensure that the InferenceService's `READY` state is set to `True`
    ```
    oc get isvc/gpt2 -n guardrails-test
    ```
    Expected output:
    ```
    NAME   URL                                        READY   PREV   LATEST   PREVROLLEDOUTREVISION   LATESTREADYREVISION   AGE
    gpt2   https://gpt2-guardrails-test.example.com   TRUE                                                                 3d18h
    ```

## Deploy a Regex Detector Service
1. Create a namespace `guardrails-test`:
    ```
    oc create ns guardrails-test
    ```

2. Add the following `annotation` to `detector/regex-detector-isvc.yaml` to use KServe in RawDeployment mode:
    ```
    serving.kserve.io/deploymentMode: RawDeployment
    ```

3. Deploy the InferenceService
    ```
    oc apply -f detector/regex-detector_isvc.yaml -n guardrails-test
    ```

4. Ensure that the generator and detector InferenceService's `READY` state is set to `True`:
    ```
    oc get isvc -n guardrails-test
    ```

    Expected output:
    ```
    NAME             URL                                                  READY   PREV   LATEST   PREVROLLEDOUTREVISION   LATESTREADYREVISION   AGE
    gpt2             https://gpt2-guardrails-test.example.com             False                                                                 3d18h
    regex-detector   https://regex-detector-guardrails-test.example.com   True                                                                  4d23h
    ```

## Deploy the Orchestrator
1. Create the `ConfigMap`, `Deployment`, `Service`, and `Route` objects for the orchestrator
    ```
    oc apply -f orchestrator.yaml -n guardrails-test
    ```

2. On OpenShift, navigate to your `guardrails-test` namespace

3. Click on **Workloads** > **Pods** on the side bar and then select the `orchestrator` pod

4. Within the pod's terminal run the following commands to test the generator and detector endpoints

    *  Validate that the generator endpoint works

        - Retrieve the generator ISVC route
            ```
            GEN_ROUTE=$(oc get isvc gpt2 -o jsonpath='{.status.address.url}' |cut -d'/' -f3)
            ```

        - `POST` the `api/v1/task/text-generation` endpoint
            ```
            curl -kv --data '{
                "model_id": "gpt-2",
                "inputs": "At what temperature does Nitrogen boil?"
            }' "$GEN_ROUTE/api/v1/task/text-generation" \
                -H "Content-Type: application/json"
            ```

    * Validate that detector's endpoint wokrks
        - Retrieve the detector ISVC route
            ```
            DETECTOR_ROUTE=$(oc get isvc regex-detector -o jsonpath='{.status.address.url}')
            ```
        - `POST` the `api/v1/text/contents` endpoint
            ```
            curl -X POST "$DETECTOR_ROUTE/api/v1/text/contents" \
            -H "Content-Type: application/json" \
            -H "detector-id: has_regex_match" \
            -d '{
                "contents": ["My email address is xx@domain.com and zzz@hotdomain.co.uk"],
                "regex_pattern": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
            }'
            ```

5. Test the orchestrator service
* Check the `/health` endpoint
    ```
    curl -v http://localhost:8034/health
    ```

* Send a request
    ```
     curl -v -H "Content-Type: application/json" \H "Content-Type: application/json" \
    --data '{
        "model_id": "gpt2",
        "inputs": "dummy input",
        "guardrail_config": {
            "input": {
                "masks": [],
                "models": {}
            },
            "output": {
                "models": {}
            }
        }
    }' http://localhost:8033/api/v1/task/classification-with-text-generation
    ```

