# LM-Eval For ODH-vLLM Models (disconnected)

> !IMPORTANT For the remainder of this tutorial, we will assume you have set
> your work project as active e.g. `oc project test`.

Create a `DataScienceCluster` like

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
                      uri: "https://github.com/trustyai-explainability/trustyai-service-operator/tarball/main"
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

or run

```sh
oc apply -f resources/disconnected-dsc.yaml
```

Once the DSC has installed all the operators, install the GPU-enabled vLLM with

```yaml
---
apiVersion: v1
kind: ServiceAccount
metadata:
    name: user-one
---
apiVersion: v1
kind: Secret
metadata:
    name: aws-connection-phi-3-data-connection
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
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
    name: vllm-models-claim
spec:
    accessModes:
        - ReadWriteOnce
    volumeMode: Filesystem
    resources:
        requests:
            storage: 300Gi
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
    name: user-one-view
subjects:
    - kind: ServiceAccount
      name: user-one
      namespace: "<YOUR TEST NAMESPACE>" # <- Replace!
roleRef:
    apiGroup: rbac.authorization.k8s.io
    kind: ClusterRole
    name: view
---
apiVersion: v1
kind: Service
metadata:
    name: "minio-phi3"
spec:
    ports:
        - name: minio-client-port
          port: 9000
          protocol: TCP
          targetPort: 9000
    selector:
        app: "minio-phi3"
---
apiVersion: apps/v1
kind: Deployment
metadata:
    name: phi3-minio-container # <--- change this
labels:
    app: "minio-phi3" # <--- change this to match label on the pod
spec:
    replicas: 1
    selector:
        matchLabels:
            app: "minio-phi3" # <--- change this to match label on the pod
    template: # => from here down copy and paste the pods metadata: and spec: sections
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
---
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
    name: phi-3
    labels:
        opendatahub.io/dashboard: "true"
    annotations:
        openshift.io/display-name: phi-3
        security.opendatahub.io/enable-auth: "true"
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
---
apiVersion: serving.kserve.io/v1alpha1
kind: ServingRuntime
metadata:
    name: "vllm-runtime-phi-3"
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

or

```sh
oc apply -f resources/disconnected-vllm.yaml
```

## Create offline model and dataset storage

Create a PVC with

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
    name: "models-pvc"
spec:
    accessModes:
        - ReadWriteOnce
    resources:
        requests:
            storage: 50Gi
```

or

```sh
oc apply -f resources/disconnected-pvc.yaml
```

It will be `pending`, until you attach it, this is expected.

### Download models and datasets from HuggingFace

Create a downloader pod. This pod fetches the required models and datasets, and
saves them to the PVC.

```yaml
apiVersion: v1
kind: Pod
metadata:
    name: model-dataset-download-pod
spec:
    containers:
        - name: downloader
          image: quay.io/ruimvieira/lmeval-offline-downloader:latest
          volumeMounts:
              - mountPath: /mnt/cache
                name: cache-storage
          resources:
              requests:
                  memory: "4Gi"
                  cpu: "2"
              limits:
                  memory: "8Gi"
                  cpu: "4"
          env:
              - name: HF_HOME
                value: /mnt/cache
              - name: HF_DATASETS_CACHE
                value: /mnt/cache
    volumes:
        - name: cache-storage
          persistentVolumeClaim:
              claimName: models-pvc
    restartPolicy: Never
```

or

```sh
oc apply -f resources/disconnected-downloader.yaml
```

Next, run the offline `LMEvalJob` with this CR. Remember to replace your token
name with the secret named `user-one-...` and to use the actual URL. The URL can
be retrieved as

```
oc get ksvc
```

```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
    name: "evaljob-sample"
spec:
    model: local-completions
    taskList:
        taskNames:
            - "arc_easy"
    logSamples: true
    batchSize: "auto"
    modelArgs:
        - name: model
          value: "phi-3"
        - name: base_url
          value: "<MODEL_URL>/v1/completions" # <- Replace with actual url!
        - name: num_concurrent
          value: "1"
        - name: max_retries
          value: "3"
        - name: tokenized_requests
          value: "False"
        - name: tokenizer
          value: "/opt/app-root/src/hf_home/distilgpt2"
    offline:
        storage:
            pvcName: "models-pvc"
    pod:
        container:
            env:
                - name: OPENAI_API_KEY
                  valueFrom:
                      secretKeyRef:
                          name: "user-one-token-dpmfv" # <- Replace with actual token!
                          key: token
                - name: HF_HOME
                  value: /opt/app-root/src/hf_home
                - name: HF_DATASETS_CACHE
                  value: /opt/app-root/src/hf_home
```
