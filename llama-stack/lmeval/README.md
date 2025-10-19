# How to Run LMEval Jobs via the Llama Stack Operator

## Setup
1. Install ODH Operator 2.35.0+ and all prerequisite operators to deploy a model on GPU.

2. Enable KServe Raw Deployment mode in the DSCI:
    ```
    oc apply -f dsci.yaml
    ```

3. Deploy ODH with TrustyAI and Llama Stack components enabled in the DSC:
    ```
    oc apply -f dsc.yaml
    ```

4. Create a namespace for your project:
    ```
    MODEL_NS=<model_namespace>
    oc new-project ${MODEL_NS}
    ```

5. Grant the Llama Stack operator permissions to deploy resources in your namespace:
    ```
    oc apply -f role.yaml
    ```

6. Deploy a Phi-3 model to run evaluations on:
    ```
    oc apply -f ../vllm/model-container.yaml
    oc apply -f ../vllm/phi3.yaml
    ```

## Create a LlamaStackDistribution Instance
7. This LlamaStackDistribution instance is configured to deploy an LMEval job using custom Llama Stack image. Define the following environmental variables:
    ```
    export VLLM_URL=<location_of_model_service>
    export INFERENCE_MODEL=<inference_model_name>
    export VLLM_API_TOKEN="fake"
    export TRUSTYAI_LM_EVAL_NAMESPACE=${MODEL_NS}
    ```

8. Deploy the LlamaStackDistribution instance:
    ```
    oc apply -f lls.yaml
    ```

9. Ensure that the LLS pods are up and running:
    ```
    oc get pods | grep lls
    ```

10. Port forward the LLS pod to 8321:
    ```
    oc port-forward $(oc get pods -o name | grep lls) 8321:8321
    ```

## Running an LMEval Job
11. Open a new terminal to start running evaluations with LMEval.

12. Retrieve your HF API token and define the following environment variable:
    ```
    export HF_TOKEN=<hf_api_token>
    ```

13. Register `arc-easy` or any other LMEval task dataset as a benchmark:
    ```
    BENCHMARK_ID=trustyai_lmeval::arc_easy

    curl -X POST http://localhost:8321/v1/eval/benchmarks \
    -H "Content-Type: application/json" \
    -d '{
        "benchmark_id": ${BENCHMARK_ID},
        "dataset_id": ${BENCHMARK_ID},
        "scoring_functions": ["string"],
        "provider_benchmark_id": "string",
        "provider_id": "trustyai_lmeval",
        "metadata": {
        "tokenized_requests": false,
        "tokenizer": "google/flan-t5-small",
        "env": {
            "HF_TOKEN": ${HF_TOKEN}
        }
        }
    }'
    ```

14. Run an evaluation job and save the job id as an environment variable:
    ```
    JOB_ID=$(curl -X POST http://localhost:8321/v1alpha/eval/benchmarks/${BENCHMARK_ID}/jobs \
    -H "Content-Type: application/json" \
    -d '{
        "benchmark_config": {
        "eval_candidate": {
            "type": "model",
            "model": "phi3",
            "sampling_params": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 256
            }
        },
        "num_examples": 10
        }
    }' | jq -r '.job_id // empty')
    ```

15. Wait for the job status to report back as `completed`:
    ```
    while true; do
        STATUS_RESP=$(curl -s -X GET "http://localhost:8321/v1/eval/benchmarks/${BENCHMARK_ID}/jobs/${JOB_ID}")

        # Extract status field
        if command -v jq &> /dev/null; then
            JOB_STATUS=$(echo "$STATUS_RESP" | jq -r '.status // empty')
        fi

        # Check if job is complete
        if [ "$JOB_STATUS" = "failed" ] || [ "$JOB_STATUS" = "completed" ]; then
            echo "Job ended with status: $JOB_STATUS"
        break
        fi
    done
    ```

16. Retrieve the results of the evaluation job:
    ```
    curl -s -X GET "http://localhost:8321/v1/eval/benchmarks/${BENCHMARK_ID}/jobs/${JOB_ID}/result"
    ```
