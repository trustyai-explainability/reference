# Getting Started with GuardrailsOrchestrator

**Prequisites:**
* An OpenShift Cluster with KServe RawDeployment configured

* In the DSC, set the following `devFlag` for the TrustyAI component
    ```
    trustyai:
    devFlags:
        manifests:
            - contextDir: config
        sourcePath: ''
        uri: https://github.com/trustyai-explainability/trustyai-service-operator/tarball/dev/guardrails-orch-merge
    managementState: Managed
    ```

1. Create a namespace `guardrails-test`
    ```
    TEST_NS=guardrails-test
    oc create ns $TEST_NS
    ```
2. Deploy the generator model into your namespace

    ```
    oc apply -k guardrails/generator -n $TEST_NS
    ```


3. Deploy the `regex-detector` detector model into your namespace
    ```
    oc apply -k guardrails/detector -n $TEST_NS
    ```

4. Sanity check the readiness of your inference services
    ```
    oc get isvc -n $TEST_NS
    ```

    Expected output:
    ```
    NAME             URL                                                      READY   PREV   LATEST   PREVROLLEDOUTREVISION   LATESTREADYREVISION   AGE
    gpt2             https://gpt2-guardrails-raw-test.example.com             True                                                                  35d
    regex-detector   https://regex-detector-guardrails-raw-test.example.com   True                                                                  39d
    ```

5. Deploy the config map spec which references the orchestrator container image into your namespace

    ```
    oc apply -f configmap.yaml -n $TEST_NS
    ```

6. Define your GuardrailsOrchestrator CR
    ```
    apiVersion: trustyai.opendatahub.io/v1alpha1
    kind: GuardrailsOrchestrator
    metadata:
        name: gorch-sample
    spec:
        detectors:
            - chunkerName: whole_doc_chunker
            defaultThreshold: '0.5'
            name: regex-detector
            service:
                hostname: regex-detector-predictor.guardrails-test-serverless.svc.cluster.local
                port: 80
            type: hap-en
        generator:
            provider: nlp
            service:
            hostname: gpt2-predictor.guardrails-test-serverless.svc.cluster.local
            port: 80
        replicas: 1
    ```

7. Apply the CR into your namespace. This will create a ConfigMap, ServiceAccount, Deployment, Service, and external Route in your namespace.
