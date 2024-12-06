# Instructions to deploy the orchestrator stack on Openshift

These instructions are for deploying the orchestrator with guardrails being Hugging Face AutoModelForSequenceClassification models with the generation model being a Hugging Face AutoModelForCausalLM model.

Models are exposed as services using KServe Raw. To serve a guardrailed generation model with caikit-nlp over grpc, run the following command to deploy the orchestrator stack from within the `llm-caikit-nlp/` directory:

```bash
oc apply -k grpc/
```

## Sense-checking the orchestrator output

From within the orchestrator pod, execute the following command to get inside the pod:

```bash
oc exec -it -n test deployments/fms-orchestr8-nlp /bin/bash
```

Then, you can run hit the `/health` endpoint:

```bash
curl -v http://localhost:8034/health
```

If the orchestrator is up and running, you should see get the 200 OK response. In this case, you can also hit the `/info` endpoint:

```bash
curl -v http://localhost:8034/info
```

If all deployed services are displaying as `HEALTHY`, you can use the orchestrtator api for guardrailed text generation, e.g. 

```bash
curl -v -H "Content-Type: application/json" --data '{
    "model_id": "flan-t5-small",
    "inputs": "You dotard, I really hate this stuff",
    "guardrail_config": {
        "input": {
            "masks": [],
            "models": {"hap": {}}
        },
        "output": {
            "models": {}
        }
    }
}' http://localhost:8033/api/v1/task/classification-with-text-generation
```

