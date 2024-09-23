## Deploying a Guardrails Detector

### Convert model to Caikit format
1. Fork and clone this repository

2. Set your working directory to `reference/llm-deployment/caikit/`
    ```
    cd reference/llm-deployment/caikit/
    ```
3. Bootstrap your LLM using the Caikit-NLP SequenceClassification module
    ```
    python bootstrap_model.py -m=<model_name_or_path> -o=<output_path>
    ```

### Setup MinIO Storage
1. Create new namespace `minio`
    ```
    MINIO_NS=minio
    oc new-project $MINIO_NS
    ```

2. Apply MinIO files to `minio` namespace
    ```
    oc apply -f minio.yaml -n ${MINIO_NS}
    oc apply -f minio-secret.yaml -n ${MINIO_NS}
    oc apply -f minio-serviceaccount.yaml -n ${MINIO_NS}
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

3. Deploy the MinIO data connection and service account
    ```
    oc apply -f minio-secret.yaml -n ${TEST_NS}
    oc create -f minio-serviceaccount.yaml -n ${TEST_NS}
    ```

4. Deploy the inference service
    ```
    oc apply -f caikit-isvc.yaml
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
        ISVC_URL + "/api/v1/task/text-classification",
        json={
            "model_id": MODEL_ID,
            "inputs": TEXT
        },
        verify=False
        )
    response.json()
    ```