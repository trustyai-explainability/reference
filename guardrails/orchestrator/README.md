# Getting Started with GuardrailsOrchestrator

**Prequisites:**
* An OpenShift Cluster with [**KServe Raw Deployment**](https://access.redhat.com/solutions/7078183) configured

* In the DSC, set the following `devFlag` for the TrustyAI component
    ```
    trustyai:
        devFlags:
            manifests:
                - contextDir: config
                  sourcePath: ''
                  uri:  https://github.com/trustyai-explainability/trustyai-service-operator/tarball/main
    managementState: Managed

* **Optionally**, enable metrics and tracing by following the steps in Configuring OpenTelemetry

1. Create a namespace `guardrails-test`
    ```
    TEST_NS=guardrails-test
    oc create ns $TEST_NS
    ```

2. Set your working directory to `guardrails/orchestrator`
    ```
    cd guardrails/orchestrator
    ```

## Configuring OpenTelemetry
1. From the OperatorHub install the Red Hat OpenShift distributed tracing platform

2. Create a Jaegar instance in your namespace using the default values

3. Once the instance is up and running, check the service and route
    ```
    oc get svc -n $TEST_NS | grep jaeger
    ```

3. Navigate back to OperatorHub and install the Red Hat build of OpenTelemetry

4. Create an OpenTelemetryCollector instance

    ```
    apiVersion: opentelemetry.io/v1beta1
    kind: OpenTelemetryCollector
    metadata:
    name: fms-otel-collector
    spec:
      observability:
        metrics: {}
      deploymentUpdateStrategy: {}
      config: # Ref https://opentelemetry.io/docs/collector/configuration/#basics
        connectors:
          spanmetrics:
            metrics_flush_interval: 15s
        exporters:
          debug: {}
          otlp:
            endpoint: 'my-jaeger-collector-headless.gorch-test.svc.cluster.local:4317' # jaeger-all-in-one collector headless service created by Jaeger operator
            tls:
              insecure: true
          prometheus:
            add_metric_suffixes: false
            endpoint: '0.0.0.0:8889' # prometheus service endpoint can be specified here
            resource_to_telemetry_conversion:
              enabled: true
        processors:
          batch:
            send_batch_size: 10000
            timeout: 10s
          memory_limiter:
            check_interval: 1s
            limit_percentage: 75
            spike_limit_percentage: 15
        receivers:
          otlp: # exported traces and metrics can be sent to port 4317/4318 of the OTEL collector service
            protocols:
              grpc:
                endpoint: 'localhost:4317' # These are default OTEL_EXPORTER_OTLP_ENDPOINT values for grpc/http
              http:
                endpoint: 'localhost:4318'
        service:
          pipelines:
            metrics:
              exporters:
                - debug
                - prometheus
              processors:
                - memory_limiter
                - batch
              receivers:
                - otlp
                - spanmetrics
            traces:
              exporters:
                - debug
                - otlp
                - spanmetrics
              processors:
                - memory_limiter
                - batch
              receivers:
                - otlp
      ```
5. Before moving on to the next section, sanity check the readiness of the OpenTelemetry instance

    * Check pod readiness
      ```
      oc get pods -n $TEST_NS | grep otel
      ```

      Expected output:
      ```
      fms-otel-collector-collector-7cd88d4ff-l8dbh   1/1     Running   0          30m
      ```

    * Check the pod's logs
      ```
      oc logs -f fms-otel-collector-collector-7cd88d4ff-l8dbh -n $TEST_NS
      ```

    Expected output:
      ```
      2025-02-25T15:53:51.086Z	info	service@v0.113.0/service.go:166	Setting up own telemetry...
      2025-02-25T15:53:51.086Z	warn	service@v0.113.0/service.go:221	service::telemetry::metrics::address is being deprecated in favor of service::telemetry::metrics::readers
      2025-02-25T15:53:51.086Z	info	telemetry/metrics.go:70	Serving metrics	{"address": "0.0.0.0:8888", "metrics level": "Normal"}
      2025-02-25T15:53:51.086Z	info	builders/builders.go:26	Development component. May change in the future.	{"kind": "exporter", "data_type": "metrics", "name": "debug"}
      2025-02-25T15:53:51.086Z	info	memorylimiter@v0.113.0/memorylimiter.go:151	Using percentage memory limiter	{"kind": "processor", "name": "memory_limiter", "pipeline": "metrics", "total_memory_mib": 31632, "limit_percentage": 75, "spike_limit_percentage": 15}
      2025-02-25T15:53:51.087Z	info	memorylimiter@v0.113.0/memorylimiter.go:75	Memory limiter configured	{"kind": "processor", "name": "memory_limiter", "pipeline": "metrics", "limit_mib": 23724, "spike_limit_mib": 4744, "check_interval": 1}
      2025-02-25T15:53:51.087Z	info	spanmetricsconnector@v0.113.0/connector.go:110	Building spanmetrics connector	{"kind": "connector", "name": "spanmetrics", "exporter_in_pipeline": "traces", "receiver_in_pipeline": "metrics"}
      2025-02-25T15:53:51.087Z	info	builders/builders.go:26	Development component. May change in the future.	{"kind": "exporter", "data_type": "traces", "name": "debug"}
      2025-02-25T15:53:51.099Z	info	service@v0.113.0/service.go:238	Starting otelcol...	{"Version": "0.113.0", "NumCPU": 8}
      2025-02-25T15:53:51.099Z	info	extensions/extensions.go:39	Starting extensions...
      2025-02-25T15:53:51.099Z	warn	internal@v0.113.0/warning.go:40	Using the 0.0.0.0 address exposes this server to every network interface, which may facilitate Denial of Service attacks.	{"kind": "exporter", "data_type": "metrics", "name": "prometheus", "documentation": "https://github.com/open-telemetry/opentelemetry-collector/blob/main/docs/security-best-practices.md#safeguards-against-denial-of-service-attacks"}
      2025-02-25T15:53:51.099Z	info	otlpreceiver@v0.113.0/otlp.go:112	Starting GRPC server	{"kind": "receiver", "name": "otlp", "data_type": "traces", "endpoint": "localhost:4317"}
      2025-02-25T15:53:51.100Z	info	otlpreceiver@v0.113.0/otlp.go:169	Starting HTTP server	{"kind": "receiver", "name": "otlp", "data_type": "traces", "endpoint": "localhost:4318"}
      2025-02-25T15:53:51.101Z	info	spanmetricsconnector@v0.113.0/connector.go:204	Starting spanmetrics connector	{"kind": "connector", "name": "spanmetrics", "exporter_in_pipeline": "traces", "receiver_in_pipeline": "metrics"}
      2025-02-25T15:53:51.101Z	info	service@v0.113.0/service.go:261	Everything is ready. Begin running and processing data.
      ```

## Deploying GuardrailsOrchestrator

1. Deploy the generator model
    ```
    oc apply -k ./generator -n $TEST_NS
    ```

    Sanity check the readiness of the generator pod:
    ```
    oc get pods -n $TEST_NS
    ```

    Expected output:
    ```
    NAME                                       READY   STATUS    RESTARTS   AGE
    llm-container-deployment-bd4d9d898-gdhkz   1/1     Running    0         154m
    llm-predictor-5d54c877d5-8mvbm             1/1     Running    0         126m
    ```

2. Deploy the vLLM configmap which contains the gateway and regex detector images
    ```
    oc apply -f vllm_images_cm.yaml -n $TEST_NS
    ```

3. Deploy the orchestrator configmap to specify the generator, detector, and chunker services
    ```
    oc apply -f orchestrator_cm.yaml -n $TEST_NS
    ```

4. Deploy the vLLM gateway configmap to specify the detector arguments
    ```
    oc apply -f detectors_cm.yaml -n $TEST_NS
    ```

5. Deploy the orchestrator custom resource. This will create a service account, deployment, service, and route object in your namespace.

    * **If you've installed OpenTelemetry in the previous section**
      ```
      oc apply -f orchestrator_otel_cr.yaml
      ```

    ```
    oc apply -f orchestrator_cr.yaml -n $TEST_NS
    ```

   Sanity check the readiness of the orchestrator pod:
   ```
   oc get pods -n $TEST_NS
   ```

   Expected output:
   ```
   NAME                                       READY   STATUS    RESTARTS   AGE
   gorch-test-55bf5f84d9-dd4vm                3/3     Running   0          3h53m
   llm-container-deployment-bd4d9d898-52r5j   1/1     Running   0          3h53m
   llm-predictor-5d54c877d5-rbdms             1/1     Running   0          57m
   ```

6. Sanity check the health of your detector and generator services.

    Run the following command to get inside the orchestrator container
    ```
    export POD_NAME=gorch-test-55bf5f84d9-dd4vm # Replace this with the name of your guardrails orchestrator pod
    export CONTAINER_NAME=gorch-test
    oc exec -it -n $TEST_NS $POD_NAME -c $CONTAINER_NAME -- /bin/bash
    ```

    **Alternatively,** you can query the external route
    ```
    GORCH_ROUTE_HEALTH=$(oc get routes gorch-test-health -o jsonpath='{.spec.host}')
    ```

    a) Query the `/health` endpoint:
    ```
    curl -v http://localhost:8034/health
    ```

    **or**
    ```
    curl -v https://$GORCH_ROUTE_HEALTH/health
    ```


    Expected output:
    ```
    *   Trying ::1:8034...
    * connect to ::1 port 8034 failed: Connection refused
    *   Trying 127.0.0.1:8034...
    * Connected to localhost (127.0.0.1) port 8034 (#0)
    > GET /health HTTP/1.1
    > Host: localhost:8034
    > User-Agent: curl/7.76.1
    > Accept: */*
    >
    * Mark bundle as not supporting multiuse
    < HTTP/1.1 200 OK
    < content-type: application/json
    < content-length: 36
    < date: Fri, 31 Jan 2025 14:04:25 GMT
    <
    * Connection #0 to host localhost left intact
    {"fms-guardrails-orchestr8":"0.1.0"}
    ```

    b) Query the `/info` endpoint:
    ```
    curl -v http://localhost:8034/info
    ```

      **or**
    ```
    curl -v https://$GORCH_ROUTE_HEALTH/info
    ```

    Expected output:

    ```
    *   Trying ::1:8034...
    * connect to ::1 port 8034 failed: Connection refused
    *   Trying 127.0.0.1:8034...
    * Connected to localhost (127.0.0.1) port 8034 (#0)
    > GET /info HTTP/1.1
    > Host: localhost:8034
    > User-Agent: curl/7.76.1
    > Accept: */*
    >
    * Mark bundle as not supporting multiuse
    < HTTP/1.1 200 OK
    < content-type: application/json
    < content-length: 82
    < date: Fri, 31 Jan 2025 14:05:10 GMT
    <
    * Connection #0 to host localhost left intact
    {"services":{"chat_generation":{"status":"HEALTHY"},"regex":{"status":"HEALTHY"}}}
    ```

7. Exit out of the orchestrator container. Run the following command to get inside the gateway container
    ```
    export POD_NAME=gorch-test-55bf5f84d9-dd4vm # Replace this with the name of your guardrails orchestrator pod
    export CONTAINER_NAME=gorch-test-gateway
    oc exec -it $POD_NAME -c $CONTAINER_NAME -- /bin/bash
    ```

8. Query the `/pii/v1/chat/completions` endpoint to perform completions while enabling detections on email and SSN information
    ```
    curl localhost:8090/pii/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "llm",
        "messages": [
            {
                "role": "user",
                "content": "say hello to me at someemail@somedomain.com"
            },
            {
                "role": "user",
                "content": "btw here is my social 123456789"
            }
        ]
    }'
    ```

    Expected output:
    ```
    Object {
        "choices": Array [],
        "created": Number(1738705923),
        "detections": Object {
            "input": Array [
                Object {
                    "message_index": Number(1),
                    "results": Array [
                        Object {
                            "detection": String("SocialSecurity"),
                            "detection_type": String("pii"),
                            "detector_id": String("regex"),
                            "end": Number(31),
                            "score": Number(1.0),
                            "start": Number(22),
                            "text": String("123456789"),
                        },
                    ],
                },
            ],
        },
        "id": String("71b080689abf47099c7fb5424aced478"),
        "model": String("llm"),
        "object": String(""),
        "usage": Object {
            "completion_tokens": Number(0),
            "prompt_tokens": Number(0),
            "total_tokens": Number(0),
        },
        "warnings": Array [
            Object {
                "message": String("Unsuitable input detected. Please check the detected entities on your input and try again with the unsuitable input removed."),
                "type": String("UNSUITABLE_INPUT"),
            },
        ],
    }
    ```

9. Query the `/passthrough/v1/chat/completions` endpoint to perform completions on while disabling detections
    ```
    curl localhost:8090/passthrough/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "llm",
        "messages": [
            {
                "role": "user",
                "content": "say hello to me at someemail@somedomain.com"
            },
            {
                "role": "user",
                "content": "btw here is my social 123456789"
            }
        ]
    }'
    ```

    Expected output:
    ```
    Object {
        "choices": Array [
            Object {
                "finish_reason": String("stop"),
                "index": Number(0),
                "logprobs": Null,
                "message": Object {
                    "content": String("Hello! I hope this message finds you well. Is there anything specific you'd like to talk about or ask about at this moment? I'm here to help in a variety of topics and to assist you with any questions you may have. Let me know if you need anything at all."),
                    "role": String("assistant"),
                    "tool_calls": Array [],
                },
            },
        ],
        "created": Number(1738705088),
        "id": String("cmpl-ba79ba95af1d4f8684203f3c59531f44"),
        "model": String("llm"),
        "object": String("chat.completion"),
        "usage": Object {
            "completion_tokens": Number(59),
            "prompt_tokens": Number(61),
            "total_tokens": Number(120),
        },
    }
    ```

10. Proceed to the next section if you've configured OpenTelemetry

## Observing Jaeger traces
1. Change your perspective from `Administrator` to `Developer`

2. Navigate to `Topology` and click on the Jaeger url

3. Under Service, select `jaeger-all-in-one` and click on the `Find Traces` button