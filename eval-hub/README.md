# EvalHub Deployment Guide

EvalHub is a REST API service for running LLM evaluations using various evaluation providers (lm-evaluation-harness, RAGAS, Garak, etc.).

## Quick Deployment

### Prerequisites

- OpenShift cluster with TrustyAI Service Operator installed
- Namespace with the necessary permissions

### Setup Variables

Set your desired namespace:

```bash
export NAMESPACE=test
```

### 1. Create a Custom Namespace

```bash
oc new-project $NAMESPACE
```

> **Note**: This step is optional if you want to use an existing namespace. Just ensure your `$NAMESPACE` variable points to the correct namespace.

### 2. Create Required Secret

EvalHub requires an OpenAI API key for some evaluation providers:

```bash
oc create secret generic openai-secret \
  --from-literal=api-key=your-openai-api-key-here \
  -n $NAMESPACE
```

### 3. Deploy EvalHub CR

Create an `evalhub.yaml` file:

```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: EvalHub
metadata:
  name: my-evalhub
  namespace: test
spec:
  replicas: 1
  env:
    - name: LOG_LEVEL
      value: DEBUG
    - name: OPENAI_API_KEY
      valueFrom:
        secretKeyRef:
          name: openai-secret
          key: api-key
```

Apply the CR:

```bash
oc apply -f evalhub.yaml -n $NAMESPACE
```

### 4. Verify Deployment

Check that EvalHub is running:

```bash
oc get evalhubs -n $NAMESPACE
oc get pods -n $NAMESPACE
```

Wait for the status to show `Ready: True`:

```bash
oc get evalhubs my-evalhub -n $NAMESPACE -o jsonpath='{.status.ready}'
```

### 5. Setup API Access

Export the route URL and authentication token:

```bash
# Export the route URL (external access)
export EVALHUB_ROUTE=$(oc get route my-evalhub -n $NAMESPACE -o jsonpath='{.spec.host}')

# Export authentication token
export TOKEN=$(oc whoami -t)
```

> **Note**: If no route exists, you can use port-forward: `oc port-forward -n $NAMESPACE svc/my-evalhub 8443:8443`

### 6. Test the API

```bash
# Health check
curl -k -H "Authorization: Bearer $TOKEN" "https://$EVALHUB_ROUTE/api/v1/health"

# List available providers
curl -k -H "Authorization: Bearer $TOKEN" "https://$EVALHUB_ROUTE/api/v1/evaluations/providers"

# List available benchmarks
curl -k -H "Authorization: Bearer $TOKEN" "https://$EVALHUB_ROUTE/api/v1/evaluations/benchmarks"
```

## Running an LMEval Benchmark

Here's a complete example of how to run an LMEval benchmark using the EvalHub API:

### 1. Run Multiple Benchmarks (Asynchronous)

```bash
# Start async evaluation with multiple benchmarks
EVAL_RESPONSE=$(curl -k -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": {
      "url": "http://vllm-server:8000",
      "name": "my-llm-model"
    },
    "benchmarks": [
      {
        "id": "toxigen",
        "provider_id": "lm_evaluation_harness",
        "config": {
          "limit": 10
        }
      },
      {
        "id": "arc_easy",
        "provider_id": "lm_evaluation_harness",
        "config": {
          "limit": 10
        }
      }
    ],
    "timeout_minutes": 120
  }' \
  "https://$EVALHUB_ROUTE/api/v1/evaluations/jobs")

# Extract evaluation ID from response
EVAL_ID=$(echo $EVAL_RESPONSE | jq -r '.resource.id')
echo "Evaluation ID: $EVAL_ID"
```

### 2. Check Evaluation Status

```bash
# Check status of running evaluation
curl -k -H "Authorization: Bearer $TOKEN" \
  "https://$EVALHUB_ROUTE/api/v1/evaluations/jobs/$EVAL_ID"
```

### 3. List All Evaluations

```bash
# List all evaluations with summary view
curl -k -H "Authorization: Bearer $TOKEN" \
  "https://$EVALHUB_ROUTE/api/v1/evaluations/jobs?summary=true&limit=10"

# List only completed evaluations
curl -k -H "Authorization: Bearer $TOKEN" \
  "https://$EVALHUB_ROUTE/api/v1/evaluations/jobs?status_filter=completed"
```

### 4. Cancel a Running Evaluation

```bash
# Cancel evaluation if needed
curl -k -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "https://$EVALHUB_ROUTE/api/v1/evaluations/jobs/$EVAL_ID"
```

### Available LMEval Benchmarks

The default LMEval provider supports these benchmarks:
- `arc_challenge` - ARC (AI2 Reasoning Challenge)
- `hellaswag` - HellaSwag commonsense reasoning
- `mmlu` - Massive Multitask Language Understanding
- `truthfulqa` - TruthfulQA factual accuracy

### Common Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `num_fewshot` | Number of few-shot examples | Provider default |
| `batch_size` | Evaluation batch size | 8 |
| `limit` | Maximum number of examples to evaluate | All |
| `device` | Device to run on (cpu, cuda) | Auto-detect |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `OPENAI_API_KEY` | OpenAI API key for evaluations | Required |
| `MAX_CONCURRENT_EVALUATIONS` | Maximum parallel evaluations | 10 |
| `DEFAULT_TIMEOUT_MINUTES` | Default evaluation timeout | 60 |

### Custom Configuration

You can customize the evaluation providers and benchmarks by mounting custom configuration. See the [EvalHub documentation](../../eval-hub/README.md) for details.

## Cleanup

### Delete EvalHub CR

To remove the EvalHub deployment:

```bash
# Delete the EvalHub CR (this will clean up all related resources)
oc delete evalhubs my-evalhub -n $NAMESPACE
```

This will automatically clean up:
- Deployment and pods
- Service
- Route (if exists)
- ConfigMaps
- ServiceAccount and ClusterRoleBinding
- TLS Secret (managed by OpenShift)

### Optional: Delete Namespace and Secrets

If you want to completely clean up:

```bash
# Delete the OpenAI secret (optional)
oc delete secret openai-secret -n $NAMESPACE
```

> **Note**: The TrustyAI Service Operator uses finalizers to ensure proper cleanup of all resources when the EvalHub CR is deleted.

## Troubleshooting

### Common Issues

1. **Pod not starting**: Check if the OpenAI secret exists and has the correct key
2. **RBAC errors**: Ensure the TrustyAI Service Operator has proper permissions
3. **Route not accessible**: Verify OpenShift Route configuration for external access

### Debug Commands

```bash
# Check CR status
oc describe evalhubs my-evalhub -n $NAMESPACE

# Check pod logs
oc logs -n $NAMESPACE -l app=eval-hub

# Check controller logs
oc logs -n opendatahub deployment/trustyai-service-operator-controller-manager
```