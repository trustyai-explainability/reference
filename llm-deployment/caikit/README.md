## Deploying a Guardrails Generator

### Convert model to Caikit format
1. Fork and clone this repository

2. Set your working directory to `reference/llm-deployment/caikit/`
    ```
    cd reference/llm-deployment/caikit/
    ```
3. Bootstrap your LLM using the Caikit-NLP TextGeneration module
    ```
    python bootstrap_model.py -m=<model_name_or_path> -o=<output_path>
    ```

### Deploy LLM with Caikit Standalone Serving Runtime
1. Create new test namespace
    ```
    TEST_NS=<test_namespace>
    oc new-project ${TEST_NS}
    ```

2. Deploy serving runtime
    ```
    oc apply -f caikit-servingruntime.yaml -n ${TEST_NS}
    ```

3. Replace <MODEL_NAMESPACE> in `minio-secret.yaml` with the name of your test namespace

4. Deploy the MinIO data connection and service account
    ```
    oc apply -f minio.yaml -n ${TEST-NS}
    oc apply -f minio-secret.yaml -n ${TEST_NS}
    oc create -f minio-serviceaccount.yaml -n ${TEST_NS}
    ```

4. Deploy the inference service
    ```
    oc apply -f caikit-isvc.yaml -n ${TEST-NS}
    ```

5. Sanity check to make sure the inference service's `READY` state is `True`
    ```
    ISVC_NAME=hap-classification-model
    oc get isvc ${ISVC_NAME} -n ${TEST_NS}
    ```

### Make an inference request
    ```Python
    TEXT = "At what temperature does liquid Nitrogen boil?"
    MODEL_ID=""granite-hap-caikit"

    response = requests.post(
        ISVC_URL + "/api/v1/task/text-generation",
        json={
            "model_id": MODEL_ID,
            "inputs": TEXT
        },
        verify=False
        )
    response.json()
    ```