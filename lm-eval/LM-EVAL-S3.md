# LMEval S3 support

Start by creating a `DataScienceCluster` with the appropriate TrustyAI devFlag:

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
            managementState: Removed
            defaultDeploymentMode: RawDeployment
        modelregistry:
            registriesNamespace: odh-model-registries
            managementState: Removed
        trustyai:
            devFlags:
                manifests:
                    - contextDir: config
                      sourcePath: ""
                      uri: "https://github.com/ruivieira/trustyai-service-operator/tarball/test/s3"
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

Once this is available, create a MinIO storage and service:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
    name: minio-pvc
    namespace: test
spec:
    accessModes:
        - ReadWriteOnce
    resources:
        requests:
            storage: 10Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
    name: minio
    namespace: test
spec:
    replicas: 1
    selector:
        matchLabels:
            app: minio
    template:
        metadata:
            labels:
                app: minio
        spec:
            containers:
                - name: minio
                  image: minio/minio:latest
                  args:
                      - server
                      - /data
                      - --console-address
                      - ":9001"
                  env:
                      - name: MINIO_ROOT_USER
                        value: "minioadmin"
                      - name: MINIO_ROOT_PASSWORD
                        value: "minioadmin"
                  ports:
                      - containerPort: 9000
                      - containerPort: 9001
                  volumeMounts:
                      - name: minio-storage
                        mountPath: "/data"
            volumes:
                - name: minio-storage
                  persistentVolumeClaim:
                      claimName: minio-pvc
MANIFEST:
---
apiVersion: v1
kind: Service
metadata:
    name: minio-service
    namespace: test
spec:
    selector:
        app: minio
    ports:
        - protocol: TCP
          port: 9000
          targetPort: 9000
    type: NodePort
```

Once the MinIO deployment is ready, deploy the pod below. This will copy the
assets (model and dataset) to the MinIO storage (under the `models` bucket).

```yaml
apiVersion: v1
kind: Pod
metadata:
    name: copy-to-minio
    namespace: test
spec:
    restartPolicy: Never
    volumes:
        - name: shared-data
          emptyDir: {}
    initContainers:
        - name: copy-data
          image: quay.io/ruimvieira/lmeval-assets-flan-arceasy:latest
          command: ["/bin/sh", "-c"]
          args:
              - |
                    cp -r /mnt/data /shared
          volumeMounts:
              - name: shared-data
                mountPath: /shared
    containers:
        - name: minio-uploader
          image: minio/mc:latest
          command: ["/bin/sh", "-c"]
          args:
              - |
                    mc alias set myminio http://minio-service:9000 minioadmin minioadmin &&
                    mc mb --ignore-existing myminio/models &&
                    mc cp --recursive /shared/data/ myminio/models
          volumeMounts:
              - name: shared-data
                mountPath: /shared
```

(_Optional_) Once the pod is completed, you can verify the files are in MinIO by
first forwarding the service:

```sh
kubectl port-forward svc/minio-service -n test 9000:9000 &
```

Creating an alias:

```sh
mc alias set myminio http://localhost:9000 minioadmin minioadmin
```

And list the contents of the `models` bucket:

```sh
mc ls myminio/models
```

You should see a directory for `flan` and `datasets`, at the minimum.

(_End optional_)

You can now deploy a `Secret` with the MinIO connection details, for the LMEval
job:

```yaml
apiVersion: v1
kind: Secret
metadata:
    name: "s3-secret"
    namespace: test
    labels:
        opendatahub.io/dashboard: "true"
        opendatahub.io/managed: "true"
    annotations:
        opendatahub.io/connection-type: s3
        openshift.io/display-name: "Minio Data Connection - LMEval"
data:
    AWS_ACCESS_KEY_ID: bWluaW9hZG1pbg== # "minioadmin"
    AWS_DEFAULT_REGION: dXMtc291dGg= # "us-south"
    AWS_S3_BUCKET: bW9kZWxz # "models"
    AWS_S3_ENDPOINT: aHR0cDovL21pbmlvLXNlcnZpY2U6OTAwMA== # "http://minio-service:9000"
    AWS_SECRET_ACCESS_KEY: bWluaW9hZG1pbg== # "minioadmin"
type: Opaque
```

Finally, deploy the following LMEval job:

```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
    name: evaljob-sample
spec:
    allowOnline: false
    model: hf
    modelArgs:
        - name: pretrained
          value: /opt/app-root/src/hf_home/flan
    taskList:
        taskNames:
            - arc_easy
    logSamples: true
    offline:
        storage:
            s3:
                accessKeyId:
                    name: s3-secret
                    key: AWS_ACCESS_KEY_ID
                secretAccessKey:
                    name: s3-secret
                    key: AWS_SECRET_ACCESS_KEY
                bucket:
                    name: s3-secret
                    key: AWS_S3_BUCKET
                endpoint:
                    name: s3-secret
                    key: AWS_S3_ENDPOINT
                region:
                    name: s3-secret
                    key: AWS_DEFAULT_REGION
                path: ""
                verifySSL: false
```

The job should proceed successfully, with an indication at the start of the logs
that the assets are being downloaded from S3.
