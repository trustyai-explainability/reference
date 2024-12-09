# LM-Eval

Install a `DataScienceCluster` (DSC) with:

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

or

```shell
oc apply -f resources/dsc.yaml
```

## Testing local models

> 💡 The following will always assume a namespace `test`.

Local models and datasets are available at `quay.io/ruimvieira`, they follow the convention `quay.io/ruimvieira/lmeval-assets-<model>-<dataset>`. Below is a list of available models:

| Name                                                        | Model                             | Dataset                |
|-------------------------------------------------------------|-----------------------------------|------------------------|
| `quay.io/ruimvieira/lmeval-assets-flan-arceasy:latest`      | `google/flan-t5-base`             | allenai/ai2_arc (wnli) |
| `quay.io/ruimvieira/lmeval-assets-granite-arceasy:latest`   | `ibm-granite/granite-7b-instruct` | allenai/ai2_arc (wnli) |
| `quay.io/ruimvieira/lmeval-assets-flan-glue:latest`         | `google/flan-t5-base`             | nyu-mll/glue           |
| `quay.io/ruimvieira/lmeval-assets-flan-20newsgroups:latest` | `google/flan-t5-base`             | SetFit/20_newsgroups   |


### Local model, local datasets and bundled tasks

<details open>

<summary>Details on to deploy an LMEval job with local model, dataset and offline/code execution disabled</summary>

Create a PVC to hold the models and datasets.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: lmeval-data
  namespace: test
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
```

**or** run

```shell
oc apply -f resources/00-pvc.yaml -n test
```

Deploy a Pod that will copy the models and datasets to the PVC:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: "lmeval-downloader"
  namespace: "test"
spec:
  containers:
    - name: downloader
      image: quay.io/ruimvieira/lm-eval-downloader:latest
      command: [ "python", "/app/download.py" ]
      env:
        - name: MODELS
          value: "google/flan-t5-base:flan"
        - name: DATASETS
          value: "allenai/ai2_arc:ARC-Easy"
        - name: DESTINATION_PATH
          value: "/mnt/data"
        - name: HF_HOME
          value: "/mnt/data/hf_home"
      volumeMounts:
        - name: data-volume
          mountPath: /mnt/data
      securityContext:
        allowPrivilegeEscalation: false
        runAsNonRoot: true
        capabilities:
          drop:
            - ALL
        seccompProfile:
          type: RuntimeDefault

  volumes:
    - name: data-volume
      persistentVolumeClaim:
        claimName: "lmeval-data"
  securityContext:
    fsGroup: 1000
  restartPolicy: Never
```

**or** run

```shell
oc apply -f resources/downloader-flan-arceasy.yaml -n test
```

Wait for the Pod to complete.

You can now deploy an LMEval CR like

```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
  name: "lmeval-test"
  namespace: "test"
spec:
  model: hf
  modelArgs:
    - name: pretrained
      value: "/opt/app-root/src/hf_home/flan"
  taskList:
    taskNames:
      - "arc_easy"
  logSamples: true
  offline:
    storage:
      pvcName: "lmeval-data"
```

**or** run

```shell
oc apply -f resources/01-lmeval-local-offline-builtin.yaml -n test
```

Once you're done with the LMEval job, you can delete everything so we can move to the next test.

```shell
oc delete lmevaljob lmeval-test -n test 
oc delete pod lmeval-downloader -n test
oc delete pvc lmeval-data -n test
```

</details>

### Local model, local datasets and unitxt catalog tasks

> 👉 Delete any previous PVC for models and downloader pods.

Create a PVC to hold the model and datasets.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: lmeval-data
  namespace: test
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
```

**or** run

```shell
oc apply -f resources/00-pvc.yaml -n test
```

and the downloader pod:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: "lmeval-downloader"
  namespace: "test"
spec:
  containers:
    - name: downloader
      image: quay.io/ruimvieira/lm-eval-downloader:latest
      command: [ "python", "/app/download.py" ]
      env:
        - name: MODELS
          value: "google/flan-t5-base:flan"
        - name: DATASETS
          value: "SetFit/20_newsgroups"
        - name: DESTINATION_PATH
          value: "/mnt/data"
        - name: HF_HOME
          value: "/mnt/data/hf_home"
      volumeMounts:
        - name: data-volume
          mountPath: /mnt/data
      securityContext:
        allowPrivilegeEscalation: false
        runAsNonRoot: true
        capabilities:
          drop:
            - ALL
        seccompProfile:
          type: RuntimeDefault
  volumes:
    - name: data-volume
      persistentVolumeClaim:
        claimName: "lmeval-data
  securityContext:
    fsGroup: 1000
  restartPolicy: Never
```

**or** run

```shell
oc apply -f resources/downloader-flan-20newsgroups.yaml -n test
```

Once the copying has finished, you can deploy the `LMEvalJob` CR now with

```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
  name: "lmeval-test"
  namespace: "test"
spec:
  model: hf
  modelArgs:
    - name: pretrained
      value: "/opt/app-root/src/hf_home/flan"
  taskList:
    taskRecipes:
      - card:
          name: "cards.20_newsgroups_short"
        template: "templates.classification.multi_class.title"
  logSamples: true
  offline:
    storage:
      pvcName: "lmeval-data"
```

**or** run

```shell
oc apply -f resources/01-lmeval-local-offline-unitxt.yaml
```

> **🐌 WARNING**: Look into the LMEval log and wait a couple of minutes for the first inference. This will be _very slow_, so if after a few inferences you're happy this is progressing with no errors, you can stop here.

Once you are finished, you can tear down this setup with

```shell
oc delete lmevaljob lmeval-test -n test 
oc delete pod lmeval-downloader -n test
oc delete pvc lmeval-data -n test
```

### Local model, local datasets and unitxt custom tasks

TBD

## Testing vLLM

### Remote model, local dataset with bundled tasks

> This example, assumes no authentication for the vLLM model. However, it will
> work the same **with** authentication, the only change needed is to add
> `security.opendatahub.io/enable-auth: 'true'` to the `InferenceService
> annotations. An example will be given at the end.

> 👉 Delete any previous PVC for models and downloader pods.

Create a new PVC, as in the previous section:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: lmeval-data
  namespace: test
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
````

**or** run

```shell
oc apply -f resources/00-pvc.yaml -n test
```

and deploy the downloader pod:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: "lmeval-downloader"
  namespace: "test"
spec:
  containers:
    - name: downloader
      image: quay.io/ruimvieira/lm-eval-downloader:latest
      command: [ "python", "/app/download.py" ]
      env:
        - name: MODELS
          value: "google/flan-t5-base:flan"
        - name: DATASETS
          value: "allenai/ai2_arc:ARC-Easy"
        - name: DESTINATION_PATH
          value: "/mnt/data"
        - name: HF_HOME
          value: "/mnt/data/hf_home"
      volumeMounts:
        - name: data-volume
          mountPath: /mnt/data
      securityContext:
        allowPrivilegeEscalation: false
        runAsNonRoot: true
        capabilities:
          drop:
            - ALL
        seccompProfile:
          type: RuntimeDefault

  volumes:
    - name: data-volume
      persistentVolumeClaim:
        claimName: "lmeval-data"
  restartPolicy: Never
```

**or** run

```shell
oc apply -f resources/downloader-flan-arceasy.yaml -n test
```

When it's finished, deploy the vLLM model. 
Start by deploying the storage with:

```shell
oc apply -f resources/02-vllm-storage.yaml
```

This will create the following resources:
A service account:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: user-one
  namespace: "test"
```

and a `Secret`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: aws-connection-phi-3-data-connection
  namespace: "test"
  labels:
    opendatahub.io/dashboard: "true"
    opendatahub.io/managed: "true"
  annotations:
    opendatahub.io/connection-type: s3
    openshift.io/display-name: Minio Data Connection - Phi3
data:
  AWS_ACCESS_KEY_ID: VEhFQUNDRVNTS0VZ
  AWS_DEFAULT_REGION: dXMtc291dGg=
  AWS_S3_BUCKET: bGxtcw==
  AWS_S3_ENDPOINT: aHR0cDovL21pbmlvLXBoaTM6OTAwMA==
  AWS_SECRET_ACCESS_KEY: VEhFU0VDUkVUS0VZ
type: Opaque
```

Create a PVC to hold the model:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: vllm-models-claim
  namespace: "test"
spec:
  accessModes:
    - ReadWriteOnce
  volumeMode: Filesystem
  # storageClassName: gp3-csi
  resources:
    requests:
      storage: 300Gi
```

and the RBAC:

```yaml
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: user-one-view
  namespace: "test"
subjects:
  - kind: ServiceAccount
    name: user-one
    namespace: "test"
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: view
```

Create a `Service`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: "minio-phi3"
  namespace: "test"
spec:
  ports:
    - name: minio-client-port
      port: 9000
      protocol: TCP
      targetPort: 9000
  selector:
    app: "minio-phi3"
```

and the deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: phi3-minio-container
  namespace: "test"
  labels:
    app: "minio-phi3"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: "minio-phi3"
  template:
    metadata:
      labels:
        app: "minio-phi3"
        maistra.io/expose-route: "true"
      name: "minio-phi3"
    spec:
      volumes:
        - name: model-volume
          persistentVolumeClaim:
            claimName: vllm-models-claim
      initContainers:
        - name: download-model
          image: quay.io/rgeada/llm_downloader:latest
          securityContext:
            fsGroup: 1001
          command:
            - bash
            - -c
            - |
                model="microsoft/Phi-3-mini-4k-instruct"
                echo "starting download"
                /tmp/venv/bin/huggingface-cli download $model --local-dir /mnt/models/llms/$(basename $model)
                echo "Done!"
          resources:
            limits:
              memory: "2Gi"
              cpu: "2"
          volumeMounts:
            - mountPath: "/mnt/models/"
              name: model-volume
      containers:
        - args:
            - server
            - /models
          env:
            - name: MINIO_ACCESS_KEY
              value: THEACCESSKEY
            - name: MINIO_SECRET_KEY
              value: THESECRETKEY
          image: quay.io/trustyai/modelmesh-minio-examples:latest
          name: minio
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop:
                - ALL
            seccompProfile:
              type: RuntimeDefault
          volumeMounts:
            - mountPath: "/models/"
              name: model-volume
```

Wait for the minio container to finish, and finally, create the `InferenceService`:

```shell
oc apply -f resources/02-vllm-serving.yaml -n test
```

This will create:

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: phi-3
  namespace: "test"
  labels:
    opendatahub.io/dashboard: "true"
  annotations:
    openshift.io/display-name: phi-3
    serving.knative.openshift.io/enablePassthrough: "true"
    sidecar.istio.io/inject: "true"
    sidecar.istio.io/rewriteAppHTTPProbers: "true"
spec:
  predictor:
    maxReplicas: 1
    minReplicas: 1
    model:
      modelFormat:
        name: vLLM
      name: ""
      resources:
        limits:
          cpu: "1"
          memory: "8Gi"
          nvidia.com/gpu: "1"
        requests:
          cpu: "1"
          memory: "8Gi"
          nvidia.com/gpu: "1"
      runtime: "vllm-runtime-phi-3"
      storage:
        key: aws-connection-phi-3-data-connection
        path: Phi-3-mini-4k-instruct
    tolerations:
      - effect: NoSchedule
        key: nvidia.com/gpu
        operator: Exists
```

and the `ServingRuntime`

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: ServingRuntime
metadata:
  name: "vllm-runtime-phi-3"
  namespace: "test"
  annotations:
    openshift.io/display-name: vLLM ServingRuntime for KServe - Phi-3
    opendatahub.io/template-display-name: vLLM ServingRuntime for KServe - Phi-3
    opendatahub.io/recommended-accelerators: '["nvidia.com/gpu"]'
  labels:
    opendatahub.io/dashboard: "true"
spec:
  annotations:
    prometheus.io/path: /metrics
    prometheus.io/port: "8080"
    openshift.io/display-name: vLLM ServingRuntime for KServe - Phi-3
  labels:
    opendatahub.io/dashboard: "true"
  containers:
    - args:
        - "--port=8080"
        - "--model=/mnt/models"
        - "--served-model-name=phi-3"
        - "--dtype=float16"
        - "--enforce-eager"
      command:
        - python
        - "-m"
        - vllm.entrypoints.openai.api_server
      env:
        - name: HF_HOME
          value: /tmp/hf_home
      image: "quay.io/opendatahub/vllm:stable-849f0f5"
      name: kserve-container
      ports:
        - containerPort: 8080
          protocol: TCP
      volumeMounts:
        - mountPath: /dev/shm
          name: shm
  multiModel: false
  supportedModelFormats:
    - autoSelect: true
      name: vLLM
  volumes:
    - emptyDir:
        medium: Memory
        sizeLimit: 2Gi
      name: shm
```

Get the model's URL with

```shell
export MODEL_URL=$(oc get isvc phi-3 -n test -o jsonpath='{.status.url}')
```

Get the model's id with

```shell
export MODEL_ID=$(curl -ks "$MODEL_URL/v1/models" | jq -r '.data[0].id')
```

Try a request with

````shell
```shell
curl -ks $MODEL_URL/v1/chat/completions\
   -H "Content-Type: application/json" \
   -d "{
    \"model\": \"$MODEL_ID\",
    \"messages\": [{\"role\": \"user\", \"content\": \"How are you?\"}],
   \"temperature\":0
   }"
````

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
      value: "https://phi-3-test.apps.<...>.openshiftapps.com/v1/completions" # <- replace with your MODEL_URL/v1/completions
    - name: num_concurrent
      value: "1"
    - name: max_retries
      value: "3"
    - name: tokenized_requests
      value: "False"
    - name: tokenizer
      value: "/opt/app-root/src/hf_home/granite"
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

Once you are done, you delete the LMEval with

```shell

```

### Remote model with unitxt catalog tasks

> 👉 Delete any previous PVC for models and downloader pods.

## Testing online, no code execution

### Online model and datasets, no code execution

For this example, we simply need the following CR:

```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
  name: "lmeval-test"
  namespace: "test"
spec:
  allowOnline: true
  model: hf
  modelArgs:
    - name: pretrained
      value: "google/flan-t5-base"
  taskList:
    taskNames:
      - "arc_easy"
  logSamples: true
```

### Online model and datasets, no code execution, unitxt

For this example, we simply need the following CR:

```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
  name: "lmeval-test"
  namespace: "test"
spec:
  allowOnline: true
  model: hf
  modelArgs:
    - name: pretrained
      value: "google/flan-t5-base"
  taskList:
    taskRecipes:
      - card:
          name: "cards.wnli"
        template: "templates.classification.multi_class.relation.default"
  logSamples: true
```

## Testing online with code execution

## Disconnected testing

> The following images must be available in your disconnected cluster
> * `quay.io/ruimvieira/lmeval-assets-flan-arceasy:latest`
> * `quay.io/ruimvieira/lmeval-assets-flan-20newsgroups:latest`

Install a `DataScienceCluster` as

```shell
oc apply -f resources/dsc.yaml
```


### Testing local models, builtin tasks


Install the image containing the necessary model and dataset, by first creating a PVC:

```shell
oc apply -f resources/00-pvc.yaml -n test
```

And then the LMEval assets downloader:

```shell
oc apply -f resources/disconnected-flan-arceasy.yaml -n test
```

Run the local LMEval with

```shell
oc apply -f resources/01-lmeval-local-offline-builtin.yaml -n test
```

Once you're done with the LMEval job, you can delete everything so we can move to the next test.

```shell
oc delete lmevaljob lmeval-test -n test 
oc delete pod lmeval-copy -n test
oc delete pvc lmeval-data -n test
```

### Testing local models, unitxt tasks

Install the image containing the necessary model and dataset, by first creating a PVC:

```shell
oc apply -f resources/00-pvc.yaml -n test
```

And then the LMEval assets downloader:

```shell
oc apply -f resources/disconnected-flan-20newsgroups.yaml -n test
```

Run the local LMEval with

```shell
oc apply -f resources/01-lmeval-local-offline-unitxt.yaml -n test
```

Once you're done with the LMEval job, you can delete everything so we can move to the next test.

```shell
oc delete lmevaljob lmeval-test -n test 
oc delete pod lmeval-copy -n test
oc delete pvc lmeval-data -n test
```
