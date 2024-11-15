# LM-Eval For ODH-vLLM Models

These are the instructions to setup `LMEvalJob`s on OpenShift/ODH.
For the instructions on how to run LMEval on disconnected clusters see [here](OFFLINE.md)

## Install ODH

Until LMEval is merged onto main, you'll need to use a devflag to get access to LM-Eval. A DSC has been provided [here](dsc.yaml).

## Deploy Model

Follow the instructions in [the vLLLM deployment guide](../llm-deployment/vllm/README.md).

Store the namespace used, since we will refer to it as a variable throughout. Eg.

```sh
export NAMESPACE=test
```

You should also make a note of the model's URL and name:

```sh
oc get isvc -n $NAMESPACE
```

This should return something along

```text
NAME    URL                                                                   READY   PREV   LATEST   PREVROLLEDOUTREVISION   LATESTREADYREVISION     AGE
phi-3   https://phi-3-test.<redacted>.com   True           100                              phi-3-predictor-00001   11h
```

Store this as the `MODEL_URL`:

```sh
export MODEL_URL="https://phi-3-test.<redacted>.com"
```

Finally get the model's name (assuming you just have one model deployed):

```sh
export MODEL_ID=$(curl -s $MODEL/v1/models | jq -r '.data[0].id')
```

## Define your LMEvalJob CR

#### Model Args

* `model` should match the name with which the model is deployed on vLLM. This will be the previous `$MODEL_ID`
* `base_url` should be set to the route/service URL of your model that you defined in `$MODEL_URL`. Make sure to include the `/v1/completions` endpoint in the URL, i.e. `$MODEL_URL/v1/completions`
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

The LMEval Controller may not correctly assign a sensible default batch size (PR incoming), so set this to `1` for safety (although `auto` is better suited for vLLM specifically).

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
  batchSize: "auto"
  modelArgs:
    - name: model
      value: $MODEL_ID
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
