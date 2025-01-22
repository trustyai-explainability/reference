# Deploying GuardrailsOrchestrator onto KServe Serverless

## Set your default namespace
```
oc project <GUARDRAILS_NS>
```
## POST'ing the generation endpoint
```
LLM_ROUTE=$(oc get inferenceservice -o jsonpath="{.items[0].status.url}")
LLM_ROUTE=${LLM_ROUTE#https://}
MODEL_ID=$(oc get inferenceservice -o jsonpath="{.items[0].metadata.name}")
TEXT_INPUT="At what temperature does liquid Nitrogen boil?
# Run the curl command with the prompt
grpcurl -insecure -d '{"text": "'"${TEXT_INPUT}"'"}' \
    -H "mm-model-id: ${MODEL_ID}" \
    ${LLM_ROUTE}:443 caikit.runtime.Nlp.NlpService/TextGenerationTaskPredict

```
## GET'ing the orchestrator's info endpoint
```
curl -kv http://localhost:8034/info
```
## POST'ing the orchestrator's classification-with-text-generation endpoint
```
curl -kv -H "Content-Type: application/json" \
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

## Debugging Istio
1. Enable Envoy access logs by adding the following lines to the `data-science-smcp` resource:
    ```
    oc edit smcp data-science-smcp -n istio-system
    ```

    ```
    proxy:
        accessLogging:
        file:
            name: /dev/stdout     #file name
    ```

2. Curl the orchestrator's `/info` endpoint:
    ```
    curl -kv http://localhost:8034/info
    ```

3. Validate that the request was sent to both the detector's and generator's `/health` endpoint:

    * Get logs for the orchestrator's `istio-proxy` container:
        ```
        oc logs -f <ORCHESTRATOR_POD_NAME> -c istio-proxy
        ```
        Expected output:
        ```
        [2024-11-14T21:30:15.466Z] "GET /health HTTP/1.1" 200 - via_upstream - "-" 0 4 20 20 "-" "-" "462680f0-9b89-48bc-b523-6cc720b6613c" "regex-detector-predictor.guardrails-test.svc.cluster.local" "10.131.0.79:8012" outbound|80||regex-detector-predictor-00001.guardrails-test.svc.cluster.local 10.129.2.103:33088 172.30.28.139:80 10.129.2.103:32822 - -
        [2024-11-14T21:30:15.488Z] "POST /grpc.health.v1.Health/Check HTTP/2" 200 - via_upstream - "-" 5 0 7 6 "-" "tonic/0.12.3" "51104f80-0f47-43c1-8319-c2e4f9c52041" "172.30.28.139:80" "10.128.2.65:8081" outbound|80||knative-local-gateway.istio-system.svc.cluster.local 10.129.2.103:59438 172.30.28.139:80 10.129.2.103:32832 - default
        ```

    * Get logs for the detector's `istio-proxy` container:
        ```
        oc logs -f <DETECTOR_POD_NAME> -c istio-proxy
        ```

    * Get logs for the generator's `istio-proxy` container:
        ```
        oc logs -f <GENERATOR_POD_NAME> -c istio-proxy
        ```


4. Check the request authority for both the detector and generator:
    ```
    oc get svc -A | grep 'regex'
    ```

    ```
    oc get svc -A  grep '28.139'
    ```
