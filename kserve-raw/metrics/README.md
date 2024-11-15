# TrustyAI service metrics with Raw KServe

This tutorial has the steps to install a raw KServe model and to test TrustyAI service with it.

**Important**

The entire tutorial assumes a project named `test` where you deploy the model and TAS. If this is different for your setup, please change it where appropriate.

## DataScienceCluster

Start a `DataScienceCluster` with

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
      devFlags:
        manifests:
          - contextDir: config
            sourcePath: 'overlays/odh'
            uri: "https://github.com/opendatahub-io/kserve/tarball/release-v0.14"
      serving:
        ingressGateway:
          certificate:
            type: OpenshiftDefaultIngress
        managementState: Managed
        name: knative-serving
      
      managementState: Managed
      
      
      
      defaultDeploymentMode: RawDeployment
      
    modelregistry:
      registriesNamespace: odh-model-registries
      managementState: Removed
    trustyai:
      devFlags:
        manifests:
          - contextDir: config
            sourcePath: ''
            uri: 'https://api.github.com/repos/trustyai-explainability/trustyai-service-operator-ci/tarball/operator-75f0c017bfdb6985e469b1baf8b752b70fdcaf86'
      managementState: Managed

    ray:
      managementState: Removed
    kueue:
    
      managementState: Managed
    
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

## Prepare TLS

**Before** deploying the TrustyAI service or models, do the following:

Patch the inference serving `ConfigMap` ob the operator's namespace (`opendatahub` in ODH's case):

```shell
kubectl patch configmap inferenceservice-config \
            -n opendatahub \
            --type=json \
            -p='[{"op": "add", "path": "/data/logger", "value": "{\"image\" : \"quay.io/opendatahub/kserve-agent:latest\",\"memoryRequest\": \"100Mi\",\"memoryLimit\": \"1Gi\",\"cpuRequest\": \"100m\",\"cpuLimit\": \"1\",\"defaultUrl\": \"http://default-broker\",\"caBundle\": \"kserve-logger-ca-bundle\",\"caCertFile\": \"service-ca.crt\",\"tlsSkipVerify\": false}"}]'
```
and create a `ConfigMap` to hold the CA certificate on the **model's** namespace:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kserve-logger-ca-bundle
  namespace: test
  annotations:
    service.beta.openshift.io/inject-cabundle: "true"
data: {}
```

## Deploy model

Deploy a tabular Raw KServe model, for instance, use:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: "aws-connection-minio-data-connection"
  namespace: "test"
  labels:
    opendatahub.io/dashboard: "true"
    opendatahub.io/managed: "true"
  annotations:
    opendatahub.io/connection-type: s3
    openshift.io/display-name: Minio Data Connection
data: #these are dummy values to populate the ODH UI with, and do not correspond to any real AWS credentials
  AWS_ACCESS_KEY_ID: VEhFQUNDRVNTS0VZ
  AWS_DEFAULT_REGION: dXMtc291dGg=
  AWS_S3_BUCKET: bW9kZWxtZXNoLWV4YW1wbGUtbW9kZWxz
  AWS_S3_ENDPOINT: aHR0cDovL21pbmlvOjkwMDA=
  AWS_SECRET_ACCESS_KEY: VEhFU0VDUkVUS0VZ
type: Opaque
---
# Source: odh-kserve-models/templates/03-storage-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: minio
  namespace: "test"
spec:
  ports:
    - name: minio-client-port
      port: 9000
      protocol: TCP
      targetPort: 9000
  selector:
    app: minio
---
# Source: odh-kserve-models/templates/02-storage-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: minio
    maistra.io/expose-route: "true"
  annotations:
    
  name: minio
  namespace: "test"
spec:
  containers:
    - args:
        - server
        - /data1
      env:
        - name: MINIO_ACCESS_KEY
          value: THEACCESSKEY
        - name: MINIO_SECRET_KEY
          value: THESECRETKEY
      image: quay.io/trustyai/modelmesh-minio-examples:latest
      name: minio
---
# Source: odh-kserve-models/templates/04-model_alpha.yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name:  "demo-loan-nn-onnx-alpha"
  namespace: "test"
  annotations:
    openshift.io/display-name:  demo-loan-nn-onnx-alpha
    
  labels:
    opendatahub.io/dashboard: "true"
spec:
  predictor:
    maxReplicas: 1
    minReplicas: 1
    model:
      modelFormat:
        name: onnx
        version: "1"
      resources:
        limits:
          cpu: "2"
          memory: 8Gi
        requests:
          cpu: "1"
          memory: 4Gi
      runtime: ovms-1.x
      storage:
        key: aws-connection-minio-data-connection
        path: ovms/loan_model_alpha
---
# Source: odh-kserve-models/templates/00-ovms-1.x.yaml
apiVersion: serving.kserve.io/v1alpha1
kind: ServingRuntime
metadata:
  name: ovms-1.x
  namespace: "test"
  annotations:
    opendatahub.io/accelerator-name: ""
    opendatahub.io/apiProtocol: REST
    opendatahub.io/recommended-accelerators: '["nvidia.com/gpu"]'
    opendatahub.io/template-display-name: OpenVINO Model Server
    opendatahub.io/template-name: kserve-ovms
    openshift.io/display-name: ovms-1.x
    prometheus.io/path: /metrics
    prometheus.io/port: "8888"
  labels:
    opendatahub.io/dashboard: "true"
spec:
  containers:
    - name: kserve-container
      image: "quay.io/opendatahub/openvino_model_server:stable-nightly-2024-05-26"
      args:
        - --model_name={{.Name}}
        - --port=8001
        - --rest_port=8888
        - --model_path=/mnt/models
        - --file_system_poll_wait_seconds=0
        - --grpc_bind_address=0.0.0.0
        - --rest_bind_address=0.0.0.0
        - --target_device=AUTO
        - --metrics_enable
      ports:
        - containerPort: 8888
          protocol: TCP
      volumeMounts:
        - mountPath: /dev/shm
          name: shm
  multiModel: false
  protocolVersions:
    - v2
    - grpc-v2
  supportedModelFormats:
    - autoSelect: true
      name: openvino_ir
      version: opset13
    - name: onnx
      version: "1"
    - autoSelect: true
      name: tensorflow
      version: "1"
    - autoSelect: true
      name: tensorflow
      version: "2"
    - autoSelect: true
      name: paddle
      version: "2"
    - autoSelect: true
      name: pytorch
      version: "2"
  volumes:
    - emptyDir:
        medium: Memory
        sizeLimit: 2Gi
      name: shm
```

You should a raw KServe model deployed:

```text
$ oc get pods -n test

NAME                                                 READY   STATUS    RESTARTS   AGE
demo-loan-nn-onnx-alpha-predictor-86dccb5467-r87c7   1/1     Running   0          97s
minio                                                1/1     Running   0          98s

```

## Deploy TrustyAI service

Now deploy the TrustyAI service

```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: TrustyAIService
metadata:
  name: trustyai-service
  namespace: test
spec:
  storage:
    format: PVC
    folder: /inputs
    size: 1Gi
  data:
    filename: data.csv
    format: CSV
  metrics:
    schedule: 5s
```

After the deployments are finished, check that the logger is correctly setup.
With:

```shell
oc get inferenceservice demo-loan-nn-onnx-alpha -n test -o jsonpath='{.spec.predictor.logger}'
```

You should get something similar to

```json
{"mode":"all","url":"https://trustyai-service.test.svc.cluster.local"}
```

The model shouldn't have a route, so create a simple one for testing purposes:

```yaml
kind: Route
apiVersion: route.openshift.io/v1
metadata:
  name: model
  namespace: test
  labels:
    app: isvc.demo-loan-nn-onnx-alpha-predictor
    app.kubernetes.io/managed-by: Helm
    component: predictor
    opendatahub.io/dashboard: 'true'
    serving.kserve.io/inferenceservice: demo-loan-nn-onnx-alpha
spec:
  to:
    kind: Service
    name: demo-loan-nn-onnx-alpha-predictor
  tls: null
  port:
    targetPort: 9081
  alternateBackends: []
```

Make a note of the model's url as you'll be using it next.

## Inferences

Perform a simple inference:

```shell
curl -kv -H "Authorization: Bearer BOGUS_TOKEN" -H "Content-Type: application/json" -d '{
        "inputs": [
        {
            "name": "customer_data_input",
            "shape": [1, 11],
            "datatype": "FP64",
            "data": [
            [
                0.0, 202500.0, 1.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 8861.0, 889.0
            ]
            ]
        }
        ]
    }' http://<MODEL_URL>/v2/models/demo-loan-nn-onnx-alpha/infer
```

You should get a response similar to

```json
{
  "model_name": "demo-loan-nn-onnx-alpha",
  "model_version": "1",
  "outputs": [
    {
      "name": "predict",
      "shape": [
        1
      ],
      "datatype": "INT64",
      "data": [
        1
      ]
    }
  ]
}
```

Check on the TrustyAI service logs that the payload was registered:

```text
2024-11-15 09:35:00,128 INFO [org.kie.tru.ser.dat.rec.KServeInferencePayloadReconciler] (executor-thread-1) Reconciling partial input and output, id=0a8d5a82-8f26-42e2-98b0-1d07734232ca
2024-11-15 09:35:00,128 INFO [org.kie.tru.ser.dat.rec.KServeInferencePayloadReconciler] (executor-thread-1) Reconciling KServe payloads id = 0a8d5a82-8f26-42e2-98b0-1d07734232ca
2024-11-15 09:35:00,230 INFO [org.kie.tru.ser.dat.sto.fla.PVCStorage] (executor-thread-1) Starting PVC storage consumer:
2024-11-15 09:35:00,231 INFO [org.kie.tru.ser.dat.sto.fla.PVCStorage] (executor-thread-1) PVC data locations: data=/inputs/*-data.csv, metadata=/inputs/*-metadata.json
```