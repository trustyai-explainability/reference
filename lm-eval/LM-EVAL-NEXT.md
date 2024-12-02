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
      managementState: Removed
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
      image: "quay.io/ruimvieira/lmeval-assets-flan-arceasy:latest" # Your UBI8-based image
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