# LM-Eval

## Table of contents

- [Creating a `DataScienceCluster`](#creating-a-datasciencecluster)
- [Testing local mode (offline)](#testing-local-mode-offline)

   - [Local model, local datasets and builtin tasks](#local-model-local-datasets-and-builtin-tasks)
   - [Local model, local datasets and unitxt catalog tasks](#local-model-local-datasets-and-unitxt-catalog-tasks)
   - [Local model, local datasets and unitxt custom tasks](#local-model-local-datasets-and-unitxt-custom-tasks)

- [Testing local mode (online)](#testing-local-mode-online)

   - [Online model and datasets, no code execution](#online-model-and-datasets-no-code-execution)
   - [Online model and datasets, no code execution, unitxt](#online-model-and-datasets-no-code-execution-unitxt)
   - [Online with code execution](#online-with-code-execution)

- [Testing vLLM (offline)](#testing-vllm-offline)
- [Testing vLLM (online)](#testing-vllm-online)

   - [Remote model, local dataset with builtin tasks](#remote-model-local-dataset-with-builtin-tasks)
   - [Remote model, local dataset with unitxt catalog tasks](#remote-model-local-dataset-with-unitxt-catalog-tasks)

- [Disconnected testing](#disconnected-testing)
- [Model authentication](#model-authentication)

## Pre-flight

Some of these examples require the `gomplate` tool. It is a simple tool to
render Go templates from the CLI. Installation instructions available
[here](https://docs.gomplate.ca/installing/).

After installing it, check a successful installation by running:

```sh {"interactive":"false"}
echo "Hello, {{.Env.NAME}}" | NAME="LMEval" gomplate
```

You should see

```text
Hello, LMEval
```

## Creating a `DataScienceCluster`

Install a `DataScienceCluster` (DSC) with:

```sh
oc apply -f resources/dsc.yaml
```

Change the TrustyAI `devFlag` as needed.

<details>

<summary>Example <code>DataScienceCluster</code></summary>

```yaml
apiVersion: datasciencecluster.opendatahub.io/v1
kind: DataScienceCluster
metadata:
  name: default-dsc
  labels:
    app.kubernetes.io/created-by: opendatahub-operator
    app.kubernetes.io/instance: default
    app.kubernetes.io/managed-by: kustomize
    app.kubernetes.io/name: datasciencecluster
    app.kubernetes.io/part-of: opendatahub-operator
spec:
  components:
    codeflare:
      managementState: Removed
    kserve:
      serving:
        ingressGateway:
          certificate:
            type: OpenshiftDefaultIngress
        managementState: Managed
        name: knative-serving
      managementState: Managed
      defaultDeploymentMode: Serverless
    modelregistry:
      registriesNamespace: odh-model-registries
      managementState: Removed
    trustyai:
      devFlags:
        manifests:
          - contextDir: config
            sourcePath: ""
            uri: "https://github.com/ruivieira/trustyai-service-operator/tarball/test/lmeval"
      managementState: Managed
    ray:
      managementState: Removed
    kueue:
      managementState: Removed
    workbenches:
      managementState: Removed
    dashboard:
      managementState: Managed
    modelmeshserving:
      managementState: Managed
    datasciencepipelines:
      managementState: Removed
    trainingoperator:
      managementState: Removed
```

</details>

LMEval works in several modes, all of which can be combined. The supported modes
are:

- **Local** vs **Remote**

   - In **Local** mode, artifacts are run from the pod (models, datasets,
      tokenizers, etc)
   - In **Remote**, the model is located somewhere else (e.g. a vLLM deployment)

- **Online** vs **Offline**

   - In **Online** mode, artifacts are fetched from a remote server (typically
      HuggingFace) if not present locally
   - In **Offline** mode, the artifacts must be present locally, otherwise the
      evaluation will fail

- **Code execution** vs **No code execution**

   - In **Code execution**, LMEval can run external code needed to setup the
      evaluation (i.e. prepare a dataset, etc)
   - In **No Code Execution**, no scripts are ran

- **Builtin** vs **unitxt**

   - In **Builtin** mode, the tasks used are the ones bundled with LMEval
   - In **unitxt** mode, the tasks used are either from the unitxt catalog, or
      custom ones

These modes can be combined (e.g. we can have remote, offline + builtin or
local, online + unitxt). In this document we'll try to capture some examples of
every combination.

> NOTE: By default online mode and code execution are not allowed by the operator, even when specified in the LMEval Job CR.
>
> To allow these modes follow the instructions below

To allow online mode and code execution, first patch the TrustyAI operator `ConfigMap`:

```sh {"interactive":"false","promptEnv":"never"}
kubectl patch configmap trustyai-service-operator-config -n opendatahub \
--type merge -p '{"data":{"lmes-allow-online":"true","lmes-allow-code-execution":"true"}}'

```

Then restart the TrustyAI operator with

```sh {"interactive":"false","promptEnv":"never"}
kubectl rollout restart deployment trustyai-service-operator-controller-manager -n opendatahub
```

## Testing local mode (offline)

> 💡 The following will always assume a namespace `test`.

Local models and datasets are available at `quay.io/ruimvieira`, they follow the
convention `quay.io/ruimvieira/lmeval-assets-<model>-<dataset>`. Below is a list
of available models:

| Name                                                        | Model                             | Dataset                |
| ----------------------------------------------------------- | --------------------------------- | ---------------------- |
| `quay.io/ruimvieira/lmeval-assets-flan-arceasy:latest`      | `google/flan-t5-base`             | allenai/ai2_arc (wnli) |
| `quay.io/ruimvieira/lmeval-assets-granite-arceasy:latest`   | `ibm-granite/granite-7b-instruct` | allenai/ai2_arc (wnli) |
| `quay.io/ruimvieira/lmeval-assets-flan-glue:latest`         | `google/flan-t5-base`             | nyu-mll/glue           |
| `quay.io/ruimvieira/lmeval-assets-flan-20newsgroups:latest` | `google/flan-t5-base`             | SetFit/20_newsgroups   |

### Builtin tasks

🚀 Create a PVC to hold the models and datasets.

```sh {"interactive":"false"}
oc apply -f resources/pvc.yaml -n test
```

🚀 Deploy a Pod that will copy the models and datasets to the PVC:

```sh {"interactive":"false"}
oc apply -f resources/disconnected-flan-arceasy.yaml -n test
```

⏱️ Wait for the Pod to complete.

🚀 You can now deploy an LMEval CR with the following command (if you don't have
GPU, use `GPU=false`):

```sh {"interactive":"false"}
cat resources/cr-local-builtin.yaml | MODEL_NAME="/opt/app-root/src/hf_home/flan" TASK_NAME="arc_easy" GPU=true gomplate | \
oc apply -n test -f -
```

Once you're done with the LMEval job, you can delete the everything so we can
move to the next test.

```sh {"interactive":"false","promptEnv":"never"}
kubectl delete all --selector=lmevaltests=vllm -n test
kubectl delete lmevaljob lmeval-test -n test
```

### unitxt

> 👉 Delete any previous PVC for models and downloader pods.

Create a PVC to hold the model and datasets.

```sh {"interactive":"false","promptEnv":"never"}
oc apply -f resources/pvc.yaml -n test
```

and the downloader pod:

```sh {"interactive":"false","promptEnv":"never"}
oc apply -f resources/downloader-flan-20newsgroups.yaml -n test
# OR
# oc apply -f resources/disconnected-flan-glue.yaml -n test
```

Once the copying has finished, you can deploy the `LMEvalJob` CR now with

```sh {"interactive":"false"}
cat resources/cr-local-unitxt.yaml | \
MODEL_NAME="/opt/app-root/src/hf_home/flan" CARD="cards.20_newsgroups_short" TEMPLATE="templates.classification.multi_class.title" GPU=true \
gomplate | \
oc apply -n test -f -
```

> __🐌 WARNING__: If not using GPU acceleration, look into the LMEval log and
> wait a couple of minutes for the first inference. This will be _very slow_, so
> if after a few inferences you're happy this is progressing with no errors, you
> can stop here.

Once you are finished, you can tear down this setup by deleting the LMEval job

```sh {"interactive":"false"}
oc delete lmevaljob lmeval-test -n test
```

and the assets:

```sh {"interactive":"false","mimeType":""}
oc delete pod lmeval-downloader -n test
oc delete pvc lmeval-data -n test
```

### unitxt (custom)

> 👉 Delete any previous PVC for models and downloader pods.

Create a PVC to hold the model and datasets.

```sh {"interactive":"false"}
oc apply -f resources/pvc.yaml -n test
```

and the downloader pod:

```sh {"interactive":"false"}
oc apply -f resources/downloader-flan-20newsgroups.yaml -n test
```

Once the copying has finished, you can deploy the `LMEvalJob` CR now with

```sh {"interactive":"false"}
cat resources/cr-local-unitxt-custom.yaml | \
MODEL_NAME="/opt/app-root/src/hf_home/flan" ONLINE=false GPU=true gomplate | \
oc apply -n test -f -
```

> __🐌 WARNING__: If not using GPU acceleration, look into the LMEval log and
> wait a couple of minutes for the first inference. This will be _very slow_, so
> if after a few inferences you're happy this is progressing with no errors, you
> can stop here.

Once you are finished, you can tear down this setup by deleting the LMEval job

```sh {"interactive":"false"}
oc delete lmevaljob lmeval-test -n test
```

and the assets:

```sh {"interactive":"false","mimeType":""}
oc delete pod lmeval-downloader -n test
oc delete pvc lmeval-data -n test
```

## Testing local mode (online)

### Builtin tasks

For this example, we use a script. This script allows to deploy a specific model
and builtin task by using the env var `MODEL_NAME`, `TASK_NAME` and whether to
use GPUs with `GPU=true` or `false`. If no model or task name is set, it will
default ones.

Some combinations of models/tasks to try:

- Models:

   - `google/flan-t5-base`
   - `facebook/opt-1.3b`
   - `EleutherAI/gpt-neo-1.3B`
   - `mosaicml/mpt-7b`

- Tasks:

   - `arc_easy`

As an example:

```sh {"interactive":"false","promptEnv":"never"}
cat resources/cr-local-builtin.yaml | MODEL_NAME="google/flan-t5-base" ONLINE=true TASK_NAME="arc_easy" GPU=true gomplate | \
oc apply -n test -f -
```

Once finished, this LMEval job can be deleted with

```sh {"interactive":"false"}
oc delete lmevaljob lmeval-test -n test
```

### unitxt

For this example, we use a script. This script allows to deploy a specific model
and unitxt card and template by using the env var `CARD`, `TEMPLATE` and whether
to use GPUs with `GPU=true` or `false`. If no model or task name is set, it will
default ones.

Some combinations of models/tasks to try:

- Models:

   - `google/flan-t5-base`
   - `facebook/opt-1.3b`
   - `EleutherAI/gpt-neo-1.3B`
   - `mosaicml/mpt-7b`

- Cards/Templates:

   - card: `cards.20_newsgroups_short`, template:
      `templates.classification.multi_class.title`
   - card: `cards.hellaswag`, template:
      `templates.completion.multiple_choice.all`

As an example:

```sh {"interactive":"false","promptEnv":"never"}
MODEL_NAME="google/flan-t5-base" CARD="cards.20_newsgroups_short" \
TEMPLATE="templates.classification.multi_class.title" GPU=true \
./resources/lmeval-job-local-online-unitxt.sh
```

Once finished, this LMEval job can be deleted with

```sh {"interactive":"false","promptEnv":"never"}
oc delete lmevaljob lmeval-test -n test
```

### unitxt (custom)

You can try to use models from the previous section. The script to deploy custom
`unitxt` tasks takes the arguments:

- `MODEL_NAME`
- `ONLINE`
- `GPU`

Example:

```sh {"interactive":"false"}
cat resources/cr-local-unitxt-custom.yaml | \
MODEL_NAME="google/flan-t5-base" ONLINE=true GPU=true gomplate  | \
kubectl apply -n test -f -
```

```sh {"interactive":"false"}
oc delete lmevaljob lmeval-test -n test
```

Once finished, this LMEval job can be deleted with

## Testing vLLM (offline)

### Remote model, offline, local dataset with bundled tasks

> This example, assumes no authentication for the vLLM model. However, it will
> work the same **with** authentication, the only change needed is to add
> `security.opendatahub.io/enable-auth: 'true'` to the `InferenceService
> annotations. An example will be given at the end.
>
> This can be done by setting `AUTH=true` when applying the `InferenceService`.

> 👉 Delete any previous PVC for models and downloader pods.

As with the other "offline" examples, start by creating the PVC and pods that
populate that PVC. i.e.:

```sh {"interactive":"false","promptEnv":"never"}
oc apply -f resources/pvc.yaml -n test
```

and then

```sh {"interactive":"false","promptEnv":"never"}
oc apply -f resources/disconnected-flan-arceasy.yaml -n test
```

The installation of the vLLM storage resources takes the following env vars as
configuration:

- `MODEL_REPO`, this is a HuggingFace model repo of the model to deploy, e.g.
   `google/flan-t5-base`
- `MODEL_NAME`, this is the name you want to register the model with (e.g.
   `flan`), this will be used to create the endpoint and address the model

Example:

Set the `MODEL_NAME`

```sh {"interactive":"false","name":"MODEL_NAME","promptEnv":"never"}
export MODEL_NAME="phi-3" && echo -n "${MODEL_NAME}"
```

And the `MODEL_REPO`

```sh {"interactive":"false","name":"MODEL_REPO","promptEnv":"never"}
export MODEL_REPO="microsoft/Phi-3-mini-4k-instruct" && echo -n "${MODEL_REPO}"
```

```sh {"interactive":"false","promptEnv":"never"}
cat resources/vllm-storage.template.yaml | \
MODEL_NAME="$MODEL_NAME" MODEL_REPO="$MODEL_REPO" gomplate | \
kubectl apply -n test -f -
```

Once the minio pod is running, deploy the inference service with (<u>make sure
the name matches `MODEL_NAME` used above</u>). Without authentication:

```sh {"interactive":"false","promptEnv":"never"}
# Without authentication
cat resources/vllm-serving.template.yaml | \
MODEL_NAME="$MODEL_NAME" AUTH="false" gomplate | \
kubectl apply -n test -f -
```

Alternatively, **with** authentication:

```sh
# With authentication
cat resources/vllm-serving.template.yaml | \
MODEL_NAME="$MODEL_NAME" AUTH="true" gomplate | \
kubectl apply -n test -f -
```

Once vLLM is running, get the model's URL with (here we will assume
`MODEL_NAME="phi-3`)

```sh {"interactive":"false","name":"MODEL_URL","promptEnv":"never"}
export MODEL_URL=$(oc get isvc $MODEL_NAME -n test -o jsonpath='{.status.url}') && \
echo -n ${MODEL_URL}
```

Get the model's id with

```sh {"interactive":"false","name":"MODEL_ID","promptEnv":"never"}
export MODEL_ID=$(curl -ks "${MODEL_URL}/v1/models" | jq -r '.data[0].id') && \
echo -n ${MODEL_ID}
```

Get the model's token with

```sh {"interactive":"false","name":"SECRET_NAME","promptEnv":"never"}
export SECRET_NAME=$(oc get secrets -n test -o custom-columns=NAME:.metadata.name | grep user-one-token) && \
echo -n ${SECRET_NAME}
```

Try a request with

```sh {"interactive":"false","promptEnv":"never"}
curl -ks $MODEL_URL/v1/chat/completions\
   -H "Content-Type: application/json" \
   -d "{
    \"model\": \"${MODEL_ID}\",
    \"messages\": [{\"role\": \"user\", \"content\": \"How are you?\"}],
   \"temperature\":0
   }"
```

You get a response similar to

```json
{
  "id": "chat-cc6f917e706048fd9596ed1a32325f65",
  "object": "chat.completion",
  "created": 1733166202,
  "model": "phi-3",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": " I'm doing well. How about you? How may I help you today?",
        "tool_calls": []
      },
      "logprobs": null,
      "finish_reason": "stop",
      "stop_reason": 32007
    }
  ],
  "usage": {
    "prompt_tokens": 7,
    "total_tokens": 25,
    "completion_tokens": 18
  }
}
```

We can now deploy the CR:

```sh {"interactive":"false","promptEnv":"never"}
cat resources/vllm-cr.template.yaml | \
TASK_NAME="arc_easy" MODEL_NAME="$MODEL_ID" \
URL="$MODEL_URL" TOKENIZER_NAME="/opt/app-root/src/hf_home/flan" \
SECRET_NAME="$SECRET_NAME" OFFLINE="true" gomplate | \
kubectl apply -n test -f -
```

```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
  name: "lmeval-test"
  namespace: "test"
  labels:
    lmevaltests: "vllm"
spec:
  model: local-completions
  taskList:
    taskNames:
      - "arc_easy"
  logSamples: true
  batchSize: "1"
  modelArgs:
    - name: model
      value: "phi-3" # <- replace with your MODEL_ID
    - name: base_url
      value: "https://phi-3-test.apps.<...>.openshiftapps.com/v1/completions" # <- replace with your MODEL_URL/v1/completions
    - name: num_concurrent
      value: "1"
    - name: max_retries
      value: "3"
    - name: tokenized_requests
      value: "False"
    - name: tokenizer
      value: "/opt/app-root/src/hf_home/flan"
  offline:
    storage:
      pvcName: "lmeval-data"
  pod:
    container:
      env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: "user-one-token-8ppxt" # replace with your Secret name
              key: token
```

### Internal services

If you want to an internal endpoint, first get the service's internal endpoint
usin the `<MODEL_NAME>.<NAMESPACE>.svc.cluster.local` syntax, i.e., for the
previous example:

```sh {"interactive":"false","name":"MODEL_URL","promptEnv":"never"}
export MODEL_URL="https://${MODEL_NAME}.test.svc.cluster.local" && \
echo -n ${MODEL_URL}
```

The LMEval Job CR will be similar, with a couple of changes, namely:

- The endpoint
- Passing a CA cert location

For this example the root CA included in the pod can used. e.g.

```sh {"interactive":"false","promptEnv":"never"}
cat resources/vllm-cr.template.yaml | \
TASK_NAME="arc_easy" MODEL_NAME="$MODEL_ID" \
URL="$MODEL_URL" TOKENIZER_NAME="/opt/app-root/src/hf_home/flan" \
SECRET_NAME="$SECRET_NAME" OFFLINE="true" CERT="true" gomplate | \
kubectl apply -n test -f -
```

This will generate a CR similar to:

```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
  name: "lmeval-test"
  namespace: "test"
spec:
  model: local-completions
  taskList:
    taskNames:
      - "arc_easy"
  logSamples: true
  batchSize: "1"
  modelArgs:
    - name: model
      value: "phi-3" # <- replace with your MODEL_ID
    - name: base_url
      value: "https://phi-3.test.svc.cluster.local/v1/completions" # <- replace with your MODEL_URL/v1/completions
    - name: num_concurrent
      value: "1"
    - name: max_retries
      value: "3"
    - name: tokenized_requests
      value: "False"
    - name: tokenizer
      value: "/opt/app-root/src/hf_home/granite"
    - name: verify_certificate
      value: "/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt" # <- Add the root cert
  offline:
    storage:
      pvcName: "lmeval-data"
  pod:
    container:
      env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: "user-one-token-hm4gb" # replace with your Secret name
              key: token
```

🗑️ Once you are done, you can delete LMEval Job with:

```sh
oc delete lmevaljob lmeval-test -n test
```

🗑️ Or delete all the above resources with:

```sh {"interactive":"false","promptEnv":"never"}
kubectl delete all --selector=lmevaltests=vllm -n test
```

### Remote model with unitxt catalog tasks

> 👉 Delete any previous PVC for models and downloader pods.

## Testing vLLM (online)

### Remote model, local dataset with builtin tasks

> This example, assumes no authentication for the vLLM model. However, it will
> work the same **with** authentication, the only change needed is to add
> `security.opendatahub.io/enable-auth: 'true'` to the `InferenceService
> annotations. An example will be given at the end.
>
> This can be done by setting `AUTH=true` when applying the `InferenceService`.

> 👉 Delete any previous PVC for models and downloader pods.

To automate the installation of a vLLM model use the following command. This
script takes the following env vars as configuration:

- `MODEL_REPO`, this is a HuggingFace model repo of the model to deploy, e.g.
   `google/flan-t5-base`
- `MODEL_NAME`, this is the name you want to register the model with (e.g.
   `flan`), this will be used to create the endpoint and address the model

Example:

Set the `MODEL_NAME`

```sh {"interactive":"false","name":"MODEL_NAME","promptEnv":"never"}
export MODEL_NAME="phi-3" && echo -n "${MODEL_NAME}"
```

And the `MODEL_REPO`

```sh {"interactive":"false","name":"MODEL_REPO","promptEnv":"never"}
export MODEL_REPO="microsoft/Phi-3-mini-4k-instruct" && echo -n "${MODEL_REPO}"
```

```sh {"interactive":"false","name":"","promptEnv":"never"}
cat resources/vllm-storage.template.yaml | \
MODEL_NAME="$MODEL_NAME" MODEL_REPO="$MODEL_REPO" gomplate | \
kubectl apply -n test -f -
```

Once the minio pod is running, deploy the inference service with (<u>make sure
the name matches `MODEL_NAME` used above</u>). Without authentication:

```sh {"interactive":"false","promptEnv":"never"}
# Without authentication
cat resources/vllm-serving.template.yaml | \
MODEL_NAME="$MODEL_NAME" AUTH="false" gomplate | \
kubectl apply -n test -f -
```

Alternatively, **with** authentication:

```sh {"interactive":"false","promptEnv":"never"}
# With authentication
cat resources/vllm-serving.template.yaml | \
MODEL_NAME="$MODEL_NAME" AUTH="true" gomplate | \
kubectl apply -n test -f -
```

Once vLLM is running, het the model's URL with (here we will assume
`MODEL_NAME="phi-3`)

```sh {"interactive":"false","mimeType":"text/plain","name":"MODEL_URL","promptEnv":"never","terminalRows":"1"}
export MODEL_URL=$(oc get isvc $MODEL_NAME -n test -o jsonpath='{.status.url}') && \
echo -n ${MODEL_URL}
```

Get the model's id with

```sh {"interactive":"false","mimeType":"text/plain","name":"MODEL_ID","terminalRows":"1"}
export MODEL_ID=$(curl -ks "${MODEL_URL}/v1/models" | jq -r '.data[0].id') && \
echo -n ${MODEL_ID}
```

Get the model's token with

```sh {"interactive":"false","mimeType":"text/plain","name":"SECRET_NAME","terminalRows":"1"}
export SECRET_NAME=$(oc get secrets -n test -o custom-columns=NAME:.metadata.name | grep user-one-token) && \
echo -n ${SECRET_NAME}
```

Try a request with

```sh {"interactive":"false"}
curl -ks $MODEL_URL/v1/chat/completions\
   -H "Content-Type: application/json" \
   -d "{
    \"model\": \"${MODEL_ID}\",
    \"messages\": [{\"role\": \"user\", \"content\": \"How are you?\"}],
   \"temperature\":0
   }"
```

You get a response similar to

```json {"excludeFromRunAll":"true"}
{
  "id": "chat-cc6f917e706048fd9596ed1a32325f65",
  "object": "chat.completion",
  "created": 1733166202,
  "model": "phi-3",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": " I'm doing well. How about you? How may I help you today?",
        "tool_calls": []
      },
      "logprobs": null,
      "finish_reason": "stop",
      "stop_reason": 32007
    }
  ],
  "usage": {
    "prompt_tokens": 7,
    "total_tokens": 25,
    "completion_tokens": 18
  }
}
```

We can now deploy the CR using a script that needs:

- `TASK_NAME`, the name of the builtin task to deploy
- `MODEL_NAME`, the model's short name (eg `phi-3`)
- `URL`, the vLLM's endpoint, e.g.
   `https://phi-3-test.apps.<...>.openshiftapps.com`
- `TOKENIZER_NAME`, the repo name of the tokenizer, e.g. `google/flan-t5-base`
- `SECRET_NAME`, the name of the secret to use for authentication

Example:

```sh {"interactive":"false"}
cat resources/vllm-cr.template.yaml | \
TASK_NAME="arc_easy" MODEL_NAME="$MODEL_ID" URL="$MODEL_URL" \
TOKENIZER_NAME="google/flan-t5-base" \
SECRET_NAME="$SECRET_NAME" gomplate | \
kubectl apply -n test -f -
```

🗑️ Once you are done, you delete the LMEval with

```sh {"interactive":"false"}
oc delete lmevaljob lmeval-test -n test
```

🗑️ If you want to delete all the vLLM resources also use

```sh
kubectl delete all --selector=lmevaltests=vllm -n test
```

### Remote model, local dataset with unitxt catalog tasks

> 👉 Delete any previous PVC for models and downloader pods.

### Internal services

If you want to an internal endpoint, first get the service's internal endpoint
usin the `<MODEL_NAME>.<NAMESPACE>.svc.cluster.local` syntax, i.e., for the
previous example:

```sh {"interactive":"false","name":"MODEL_URL","promptEnv":"never"}
export MODEL_URL="https://${MODEL_NAME}.test.svc.cluster.local" && \
echo -n ${MODEL_URL}
```

The LMEval Job CR will be similar, with a couple of changes, namely:

- The endpoint
- Passing a CA cert location

For this example the root CA included in the pod can used. e.g.

```sh {"interactive":"false","promptEnv":"never"}
cat resources/vllm-cr.template.yaml | \
TASK_NAME="arc_easy" MODEL_NAME="$MODEL_ID" \
URL="$MODEL_URL" TOKENIZER_NAME="google/flan-t5-base" \
SECRET_NAME="$SECRET_NAME" OFFLINE="false" CERT="true" gomplate | \
kubectl apply -n test -f -
```

This will generate a CR similar to:

```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
  name: "lmeval-test"
  namespace: "test"
spec:
  model: local-completions
  taskList:
    taskNames:
      - "arc_easy"
  logSamples: true
  batchSize: "1"
  modelArgs:
    - name: model
      value: "phi-3" # <- replace with your MODEL_ID
    - name: base_url
      value: "https://phi-3.test.svc.cluster.local/v1/completions" # <- replace with your MODEL_URL/v1/completions
    - name: num_concurrent
      value: "1"
    - name: max_retries
      value: "3"
    - name: tokenized_requests
      value: "False"
    - name: tokenizer
      value: "/opt/app-root/src/hf_home/granite"
    - name: verify_certificate
      value: "/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt" # <- Add the root cert
  offline:
    storage:
      pvcName: "lmeval-data"
  pod:
    container:
      env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: "user-one-token-hm4gb" # replace with your Secret name
              key: token
```

🗑️ Once you are done, you can delete LMEval Job with:

```sh {"interactive":"false","promptEnv":"never"}
oc delete lmevaljob lmeval-test -n test
```

🗑️ Or delete all the above resources with:

```sh {"interactive":"false","promptEnv":"never"}
kubectl delete all --selector=lmevaltests=vllm -n test
```

### KServe Raw

In the previous example, we've used KServe Serverless. To use KServe Raw, first you would need to redeploy your `DataScienceCluster` in order to support KServe Raw.
Once that's done, the steps would be similar to KServe Serverless, with some small changes.

We start by setting the `MODEL_NAME`, as in the Serverless case:

```sh {"interactive":"false","name":"MODEL_NAME","promptEnv":"never"}
export MODEL_NAME="phi-3" && echo -n "${MODEL_NAME}"
```

And the `MODEL_REPO`

```sh {"interactive":"false","name":"MODEL_REPO","promptEnv":"never"}
export MODEL_REPO="microsoft/Phi-3-mini-4k-instruct" && echo -n "${MODEL_REPO}"
```

```sh {"interactive":"false","name":"","promptEnv":"never"}
cat resources/vllm-storage.template.yaml | \
MODEL_NAME="$MODEL_NAME" MODEL_REPO="$MODEL_REPO" gomplate | \
kubectl apply -n test -f -
```

Once the minio pod is running, deploy the inference service with (<u>make sure
the name matches `MODEL_NAME` used above</u>). Without authentication:

```sh {"interactive":"false","promptEnv":"never"}
# Without authentication
cat resources/vllm-serving.template.yaml | \
MODEL_NAME="$MODEL_NAME" AUTH="false" RAW="true" gomplate | \
kubectl apply -n test -f -
```

Alternatively, **with** authentication:

```sh {"interactive":"false","promptEnv":"never"}
# With authentication
cat resources/vllm-serving.template.yaml | \
MODEL_NAME="$MODEL_NAME" AUTH="true" gomplate | \
kubectl apply -n test -f -
```

Once vLLM is running, het the model's URL with (here we will assume
`MODEL_NAME="phi-3`)

```sh {"interactive":"false","mimeType":"text/plain","name":"MODEL_URL","promptEnv":"never","terminalRows":"1"}
export MODEL_URL=$(oc get isvc ${MODEL_NAME} -n test -o jsonpath='{.status.address.url}' | cut -d'/' -f3)  && \
echo -n ${MODEL_URL}
```

Get the model's token with

```sh {"interactive":"false","mimeType":"text/plain","name":"SECRET_NAME","terminalRows":"1"}
export SECRET_NAME=$(oc get secrets -n test -o custom-columns=NAME:.metadata.name | grep user-one-token) && \
echo -n ${SECRET_NAME}
```

We can now deploy the CR using a script that needs:

- `TASK_NAME`, the name of the builtin task to deploy
- `MODEL_NAME`, the model's short name (eg `phi-3`)
- `URL`, the vLLM's endpoint, e.g.
   `https://phi-3-test.apps.<...>.openshiftapps.com`
- `TOKENIZER_NAME`, the repo name of the tokenizer, e.g. `google/flan-t5-base`
- `SECRET_NAME`, the name of the secret to use for authentication

Example:

```sh {"interactive":"false"}
cat resources/vllm-cr.template.yaml | \
TASK_NAME="arc_easy" MODEL_NAME="$MODEL_NAME" \
MODEL_URL="http://${MODEL_URL}:8080" TOKENIZER_NAME="google/flan-t5-base" \
SECRET_NAME="$SECRET_NAME" OFFLINE="false" CERT="true" gomplate | \
kubectl apply -n test -f -
```

🗑️ Once you are done, you delete the LMEval with

```sh {"interactive":"false"}
oc delete lmevaljob lmeval-test -n test
```

🗑️ If you want to delete all the vLLM resources also use

```sh {"interactive":"false","promptEnv":"never"}
kubectl delete all --selector=lmevaltests=vllm -n test
```

## Disconnected testing

> The following images must be available in your disconnected cluster
>
> - `quay.io/ruimvieira/lmeval-assets-flan-arceasy:latest`
> - `quay.io/ruimvieira/lmeval-assets-flan-20newsgroups:latest`

Install a `DataScienceCluster` as

```sh
oc apply -f resources/dsc.yaml
```

### Testing local models, builtin tasks

Install the image containing the necessary model and dataset, by first creating
a PVC:

```sh
oc apply -f resources/pvc.yaml -n test
```

And then the LMEval assets downloader:

```sh
oc apply -f resources/disconnected-flan-arceasy.yaml -n test
```

Run the local LMEval with

```sh
oc apply -f resources/01-lmeval-local-offline-builtin.yaml -n test
```

Once you're done with the LMEval job, you can delete everything so we can move
to the next test.

```sh
oc delete lmevaljob lmeval-test -n test
oc delete pod lmeval-copy -n test
oc delete pvc lmeval-data -n test
```

### Testing local models, builtin tasks

> NOTE: This example works with authentication turned off for the vLLM model. At
> the end of this guide, steps on how to use authenticated models will be
> provided.

Install the image containing the necessary model and dataset, by first creating
a PVC:

```sh
oc apply -f resources/pvc.yaml -n test
```

And then the LMEval assets downloader:

```sh
oc apply -f resources/disconnected-flan-20newsgroups.yaml -n test
```

Run the local LMEval with

```sh
oc apply -f resources/01-lmeval-local-offline-unitxt.yaml -n test
```

Once you're done with the LMEval job, you can delete everything so we can move
to the next test.

```sh
oc delete lmevaljob lmeval-test -n test
oc delete pod lmeval-copy -n test
oc delete pvc lmeval-data -n test
```

### Testing remote models, builtin tasks

Start by install vLLM model server as in
[the previous section](#remote-model-local-dataset-with-bundled-tasks).

Install the image containing the necessary model and dataset, by first creating
a PVC:

```sh
oc apply -f resources/pvc.yaml -n test
```

And then the LMEval assets downloader:

```sh
oc apply -f resources/disconnected-flan-arceasy.yaml -n test
```

Get the vLLM model endpoint by using

```sh
export MODEL_URL=$(oc get isvc phi-3 -n test -o jsonpath='{.status.url}')
```

and the model id with

```sh
export MODEL_ID=$(curl -ks "$MODEL_URL/v1/models" | jq -r '.data[0].id')
```

Replace the URL in `02-lmeval-remote-offline-builtin.yaml`, e.g.

```sh
MODEL_URL=$(oc get isvc phi-3 -n test -o jsonpath='{.status.url}') && \
MODEL_ID=$(curl -ks "$MODEL_URL/v1/models" | jq -r '.data[0].id') && \
sed -e "s|\${MODEL_ID}|${MODEL_ID}|g" -e "s|\${MODEL_URL}|${MODEL_URL}|g" resources/02-lmeval-remote-offline-builtin.yaml | oc apply -n test -f -
```

```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
  name: "lmeval-test"
  namespace: "test"
spec:
  model: local-completions
  modelArgs:
    - name: model
      value: ${MODEL_ID} # <--- replace with your MODEL_ID
    - name: base_url
      value: "${MODEL_URL}/v1/completions" # <--- replace with your MODEL_URL
    - name: num_concurrent
      value: "1"
    - name: max_retries
      value: "3"
    - name: tokenized_requests
      value: "False"
    - name: tokenizer
      value: /opt/app-root/src/hf_home/flan
  taskList:
    taskNames:
      - "arc_easy"
  logSamples: true
  offline:
    storage:
      pvcName: "lmeval-data"
```

Once you're done with the LMEval job, you can delete everything so we can move
to the next test.

```sh
oc delete lmevaljob lmeval-test -n test
oc delete pod lmeval-copy -n test
oc delete pvc lmeval-data -n test
```

### Testing local models, builtin tasks

> NOTE: This example works with authentication turned off for the vLLM model. At
> the end of this guide, steps on how to use authenticated models will be
> provided.

Install the image containing the necessary model and dataset, by first creating
a PVC:

```sh
oc apply -f resources/pvc.yaml -n test
```

And then the LMEval assets downloader:

```sh
oc apply -f resources/disconnected-flan-20newsgroups.yaml -n test
```

Run the local LMEval with

```sh
oc apply -f resources/01-lmeval-local-offline-unitxt.yaml -n test
```

Once you're done with the LMEval job, you can delete everything so we can move
to the next test.

```sh
oc delete lmevaljob lmeval-test -n test
oc delete pod lmeval-copy -n test
oc delete pvc lmeval-data -n test
```

### Testing remote models, unitxt tasks

_(If not running a vLLM model already, start it as in
[the previous section](#remote-model-local-dataset-with-bundled-tasks).)_

Install the image containing the necessary model and dataset, by first creating
a PVC:

```sh
oc apply -f resources/pvc.yaml -n test
```

And then the LMEval assets downloader:

```sh
oc apply -f resources/disconnected-flan-20newsgroups.yaml -n test
```

Get the vLLM model endpoint by using

```sh
export MODEL_URL=$(oc get isvc phi-3 -n test -o jsonpath='{.status.url}')
```

and the model id with

```sh
export MODEL_ID=$(curl -ks "$MODEL_URL/v1/models" | jq -r '.data[0].id')
```

Replace the URL in `02-lmeval-remote-offline-unitxt.yaml`, e.g.

```sh
MODEL_URL=$(oc get isvc phi-3 -n test -o jsonpath='{.status.url}') && \
MODEL_ID=$(curl -ks "$MODEL_URL/v1/models" | jq -r '.data[0].id') && \
sed -e "s|\${MODEL_ID}|${MODEL_ID}|g" -e "s|\${MODEL_URL}|${MODEL_URL}|g" resources/02-lmeval-remote-offline-unitxt.yaml | oc apply -n test -f -
```

Once you're done with the LMEval job, you can delete everything so we can move
to the next test.

```sh
oc delete lmevaljob lmeval-test -n test
oc delete pod lmeval-copy -n test
oc delete pvc lmeval-data -n test
```

## Model authentication

### Testing local models, builtin tasks

_(If not running a vLLM model already, start it as in
[the previous section](#remote-model-local-dataset-with-bundled-tasks).)_

Install the image containing the necessary model and dataset, by first creating
a PVC:

```sh
oc apply -f resources/pvc.yaml -n test
```

And then the LMEval assets downloader:

```sh
oc apply -f resources/disconnected-flan-arceasy.yaml -n test
```

Get the vLLM model endpoint by using

```sh
oc get ksvc phi-3-predictor -n test -o jsonpath='{.status.url}'
```

Get the token with

```sh
NAME=$(oc get secrets --no-headers -o custom-columns=":metadata.name" -n test | grep "^user-one-token") && \
export TOKEN=$(oc get secret -n test $NAME -o jsonpath='{.data.token}' | base64 --decode)
```

and the model id with

```sh
export MODEL_ID=$(curl -ks -H "Authorization: Bearer $TOKEN" "$MODEL_URL/v1/models" | jq -r '.data[0].id')
```

Replace the URL in `02-lmeval-remote-offline-unitxt.yaml`, e.g.

```sh
MODEL_URL=$(oc get ksvc "phi-3-predictor" -n test -o jsonpath='{.status.url}') && \
TOKEN_NAME=$(oc get secrets --no-headers -o custom-columns=":metadata.name" -n test | grep "^user-one-token") && \
MODEL_ID=$(curl -ks -H "Authorization: Bearer ${TOKEN}" "${MODEL_URL}/v1/models" | jq -r '.data[0].id') && \
sed -e "s|\${MODEL_ID}|${MODEL_ID}|g" \
  -e "s|\${MODEL_URL}|${MODEL_URL}|g" \
  -e "s|\${TOKEN_NAME}|${TOKEN_NAME}|g" \
  resources/03-lmeval-remote-auth-offline-builtin.yaml | \
  oc apply -n test -f -
```

Once you're done with the LMEval job, you can delete everything so we can move
to the next test.

```sh
oc delete lmevaljob lmeval-test -n test
oc delete pod lmeval-copy -n test
oc delete pvc lmeval-data -n test
```

### Testing remote models, unitxt tasks

_(If not running a vLLM model already, start it as in
[the previous section](#remote-model-local-dataset-with-bundled-tasks).)_

Install the image containing the necessary model and dataset, by first creating
a PVC:

```sh
oc apply -f resources/pvc.yaml -n test
```

And then the LMEval assets downloader:

```sh
oc apply -f resources/disconnected-flan-20newsgroups.yaml -n test
```

Get the vLLM model endpoint by using

```sh
oc get ksvc phi-3-predictor -n test -o jsonpath='{.status.url}'
```

Get the token with

```sh
NAME=$(oc get secrets --no-headers -o custom-columns=":metadata.name" -n test | grep "^user-one-token") && \
export TOKEN=$(oc get secret -n test $NAME -o jsonpath='{.data.token}' | base64 --decode)
```

and the model id with

```sh
export MODEL_ID=$(curl -ks -H "Authorization: Bearer $TOKEN" "$MODEL_URL/v1/models" | jq -r '.data[0].id')
```

Replace the URL in `02-lmeval-remote-offline-unitxt.yaml`, e.g.

```sh
MODEL_URL=$(oc get ksvc "phi-3-predictor" -n test -o jsonpath='{.status.url}') && \
TOKEN_NAME=$(oc get secrets --no-headers -o custom-columns=":metadata.name" -n test | grep "^user-one-token") && \
MODEL_ID=$(curl -ks -H "Authorization: Bearer ${TOKEN}" "${MODEL_URL}/v1/models" | jq -r '.data[0].id') && \
sed -e "s|\${MODEL_ID}|${MODEL_ID}|g" \
  -e "s|\${MODEL_URL}|${MODEL_URL}|g" \
  -e "s|\${TOKEN_NAME}|${TOKEN_NAME}|g" \
  resources/03-lmeval-remote-auth-offline-unitxt.yaml | \
  oc apply -n test -f -
```

Once you're done with the LMEval job, you can delete everything so we can move
to the next test.

```sh
oc delete lmevaljob lmeval-test -n test
oc delete pod lmeval-copy -n test
oc delete pvc lmeval-data -n test
```

## Resource limits

> To create resource limits for an LMEval Job use the following example from
> [local model (online)]

🚀 As an example, create the LMEval Job CR:

```sh {"interactive":"false","promptEnv":"never"}
cat resources/cr-local-builtin.yaml | MODEL_NAME="google/flan-t5-base" ONLINE=true TASK_NAME="arc_easy" GPU=true gomplate | \
oc apply -n test -f -
```

🔎 By using the GPU mode, some CPU and memory limits are already set. You can
simply run

```sh {"interactive":"false","promptEnv":"never"}
kubectl get pod lmeval-test -n test -o jsonpath="{.spec.containers[*].resources.limits}"
```

and verify the limits are set.

⏱️ Once finished, this LMEval job can be deleted with

```sh {"interactive":"false","promptEnv":"never"}
oc delete lmevaljob lmeval-test -n test
```
