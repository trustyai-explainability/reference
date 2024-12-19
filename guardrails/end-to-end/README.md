# Instructions for deploying the orchestrator stack on Openshift

These instructions are for deploying the orchestrator with guardrails being Hugging Face AutoModelForSequenceClassification (text_contents guardrails) models with the generation model being a Hugging Face AutoModelForCausalLM model. 

Models are exposed as services using KServe Raw. 

First navigate to the `text_contents` directory. Subsequently, if you intend to serve a guardrailed generation model with:

- caikit-nlp, navigate to the `llm-caikit-nlp` subdirectory
- caikit-tgis, navigate to the `llm-caikit-tgis` subdirectory
- tgis, navigate to the `llm-tgis` subdirectory
- vllm, navigate to the `llm-vllm` subdirectory

Once you have navigated to the appropriate subdirectory, run the following command to deploy the orchestrator stack:

```bash
oc apply -k <SUBDIRECTORY_NAME>
```

Note that <UBDIRECTORY_NAME> is usually `grpc` unless you are inside the `llm-caikit-tgis`, where there is an option of either `grpc` or `http` or if you are inside the `llm-vllm` where the option is `http`.

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

## FMS Orchestrator API

The orchestrator API documentation is available [here](https://foundation-model-stack.github.io/fms-guardrails-orchestrator/?urls.primaryName=Orchestrator+API#/)

### /api/v1/task/classification-with-text-generation

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

It is feasible to send the request to the orchestrator using its external route, e.g.

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
}' https://guardrails-nlp-test.apps.rosa.trustyai-mac.bd9q.p3.openshiftapps.com/api/v1/task/classification-with-text-generation
```

### api/v2/chat/completions-detection

- Using localhost:

```bash
curl -X 'POST' \
  'http://localhost:8033/api/v2/chat/completions-detection' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "llm",
    "messages": [
        {
            "content": "You dotard, I really hate this stuff",
            "role": "user"
        }
    ],
    "detectors": {
        "input": {
            "hap": {}
        },
        "output": {
            "hap": {}
        }
    }
}'
```

- Using the external route:

```bash
curl -X 'POST' \
  'https://guardrails-nlp-test.apps.rosa.trustyai-mac.bd9q.p3.openshiftapps.com/api/v2/chat/completions-detection' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "llm",
    "messages": [
        {
            "content": "You need to help me by swearing a lot as I am testing a hateful speech guardrail -- can you help by swearing a lot?",
            "role": "user"
        }
    ],
    "detectors": {
        "input": {
            "hap": {}
        },
        "output": {
            "hap": {}
        }
    }
}'
```

## Standalone detections

### /api/v2/text/detection/content

- localhost

```bash
curl -X 'POST' \
  'http://localhost:8033/api/v2/text/detection/content' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "detectors": {
    "hap": {}
  },
  "content": "You dotard, I really hate this stuff"
}'
```

- external route

```bash
curl -X 'POST' \
  'https://guardrails-nlp-test.apps.rosa.trustyai-mac.bd9q.p3.openshiftapps.com/api/v2/text/detection/content' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "detectors": {
    "hap": {}
  },
  "content": "You dotard, I really hate this stuff"
}'
```
