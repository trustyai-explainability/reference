# LM-Eval

Install a DataScienceCluster (DSC) with:

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
            sourcePath: ''
            uri: 'https://github.com/ruivieira/trustyai-service-operator/tarball/lmeval-hardened-test-qe'
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

## Testing

The following will always assume a namespace `test`.

### Local model with local datasets

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

Deploy a Pod that will copy the models and datasets to the PVC:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: lmeval-copy
  namespace: "test"
spec:
  securityContext:
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: data
      image: "quay.io/ruimvieira/lmeval-assets-flan-arceasy:latest"
      command:
        ["/bin/sh", "-c", "cp -r /mnt/data/. /mnt/pvc/ && tail -f /dev/null"]
      securityContext:
        runAsUser: 1000
        runAsNonRoot: true
        allowPrivilegeEscalation: false
        capabilities:
          drop:
            - ALL
      volumeMounts:
        - mountPath: /mnt/pvc
          name: pvc-volume
  restartPolicy: Never
  volumes:
    - name: pvc-volume
      persistentVolumeClaim:
        claimName: "lmeval-data"
```

You can check that the copy has finished by running

```shell
oc exec -it lmeval-copy -n test -- du /mnt/data -h
```

The result should be similar to

```text
1.4M	/mnt/data/datasets/allenai___ai2_arc/ARC-Easy/0.0.0/210d026faf9955653af8916fad021475a3f00453
1.4M	/mnt/data/datasets/allenai___ai2_arc/ARC-Easy/0.0.0
1.4M	/mnt/data/datasets/allenai___ai2_arc/ARC-Easy
1.4M	/mnt/data/datasets/allenai___ai2_arc
1.4M	/mnt/data/datasets
3.9G	/mnt/data/flan
0	/mnt/data/modules/datasets_modules
0	/mnt/data/modules
3.9G	/mnt/data

```

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

### Remote model with local datasets

If you have any PVC or download Pods from previous tests, delete them.

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
```

and deploy the downloader pod:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: lmeval-copy
  namespace: "test"
spec:
  securityContext:
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: data
      image: "quay.io/ruimvieira/lmeval-assets-granite-arceasy:latest"
      command:
        ["/bin/sh", "-c", "cp -r /mnt/data/. /mnt/pvc/ && tail -f /dev/null"]
      securityContext:
        runAsUser: 1000
        runAsNonRoot: true
        allowPrivilegeEscalation: false
        capabilities:
          drop:
            - ALL
      volumeMounts:
        - mountPath: /mnt/pvc
          name: pvc-volume
  restartPolicy: Never
  volumes:
    - name: pvc-volume
      persistentVolumeClaim:
        claimName: "lmeval-data"
```

When it's finished, you should see something like

```text
1.4M	/mnt/data/datasets/allenai___ai2_arc/ARC-Easy/0.0.0/210d026faf9955653af8916fad021475a3f00453
1.4M	/mnt/data/datasets/allenai___ai2_arc/ARC-Easy/0.0.0
1.4M	/mnt/data/datasets/allenai___ai2_arc/ARC-Easy
1.4M	/mnt/data/datasets/allenai___ai2_arc
1.4M	/mnt/data/datasets
848K	/mnt/data/granite/model-card
13G	/mnt/data/granite
13G	/mnt/data
```

Deploy the vLLM model.
Start by creating a service account

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
    opendatahub.io/dashboard: 'true'
    opendatahub.io/managed: 'true'
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
  name: phi3-minio-container # <--- change this
  namespace: "test"
labels:
    app: "minio-phi3" # <--- change this to match label on the pod
spec:
  replicas: 1
  selector:
    matchLabels:
      app: "minio-phi3"  # <--- change this to match label on the pod
  template: # => from here down copy and paste the pods metadata: and spec: sections
    metadata:
      labels:
        app: "minio-phi3"
        maistra.io/expose-route: 'true'
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
              # model="ibm-granite/granite-7b-instruct"
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
              value:  THEACCESSKEY
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

Finally, create the `InferenceService`:

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

```shell
```shell
curl -ks $MODEL_URL/v1/chat/completions\
   -H "Content-Type: application/json" \
   -d "{
    \"model\": \"$MODEL_ID\",
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