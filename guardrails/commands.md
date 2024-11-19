## POST'ing the generation endpoint 
```
LLM_ROUTE=gpt2-predictor.guardrails-test.cluster.svc.local
curl -kv --data '{
    "model_id": "gpt2",
    "inputs": "At what temperature does Nitrogen boil?"
}' "$LLM_ROUTE/api/v1/task/text-generation" \
    -H "Content-Type: application/json"
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