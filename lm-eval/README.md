# LM-Eval For ODH-vLLM Models

## Other guides

- [Using S3 storage with LMEval](LM-EVAL-S3.md)
- [LLM-as-a-Judge](LM-EVAL-LLMAAJ.md)

## Install ODH
Until LMEval is merged onto main, you'll need to use a devflag to get access to LM-Eval. A DSC has been provided [here](dsc.yaml).

## Deploy Model
Follow the instructions in [the vLLLM deployment guide](../llm-deployment/vllm/README.md).

## Define your LMEvalJob CR


#### Model Args
* `base_url` should be set to the route/service URL of your model. Make sure to include the `/v1/completions` endpoint in the URL.
* `tokenizer` should match the path to your model on Huggingface. E.g., for granite, use `ibm-granite/granite-7b-instruct` and for Phi-3, use `microsoft/Phi-3-mini-4k-instruct`.
#### Secret Ref
`envSecrets.secretRef` should point to a secret that contains a token that can authenticate to your model. `secretRef.name` should be
the secret's name in the namespace, while `secretRef.key` should point at the token's key within the secret. 

If you followed this instructions in the vLLM deployment guide, then
* `secretRef.name` can equal the output of`oc get secrets -o custom-columns=SECRET:.metadata.name --no-headers | grep user-one-token`
* `secretRef.key` should equal `token`

#### Task List
Pick some tasks to run!

#### Batch Size
The LMEval Controller may not correctly assign a sensible default batch size (PR incoming), so set this to `1` for safety.


```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
  name: evaljob
spec:
  model: local-completions
  taskList:
    taskNames:
      - mmlu
  logSamples: true
  batchSize: 1
  modelArgs:
    - name: model
      value: granite
    - name: base_url
      value: $ROUTE_TO_MODEL/v1/completions
    - name: num_concurrent
      value:  "1"
    - name: max_retries
      value:  "3"
    - name: tokenized_requests
      value: "False"
    - name: tokenizer
      value: ibm-granite/granite-7b-instruct
 env:
   - name: OPENAI_TOKEN
     valueFrom:
          secretKeyRef:
            name: <secret-name>
            key: token
```

## Run
Then, apply this CR into the same namespace as your model. You should see a pod spin up in your 
model namespace called `evaljob`. In the pod terminal, you can see the output via `tail -f output/stderr.log`
