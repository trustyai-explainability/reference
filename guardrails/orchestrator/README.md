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

1. Create a namespace `guardrails-test`
    ```
    TEST_NS=guardrails-test
    oc create ns $TEST_NS
    ```
2. Set your working directory to `guardrails/orchestrator`
    ```
    cd guardrails/orchestrator
    ```

2. Deploy the generator model
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

3. Deploy the guardrails configmap which contains the gateway and regex detector images
    ```
    oc apply -f gorch_cm.yaml -n $TEST_NS
    ```

4. Deploy the orchestrator configmap to specify the generator, detector, and chunker services
    ```
    oc apply -f orchestrator_cm.yaml -n $TEST_NS
    ```

5. Deploy the vLLM gateway configmap to specify the detector arguments
    ```
    oc apply -f vllm_gateway_cm.yaml -n $TEST_NS
    ```

6. Deploy the orchestrator custom resource. This will create a service account, deployment, service, and route object in your namespace.
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

7. Sanity check the health of your detector and generator services.

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
    curl -v http://$GORCH_ROUTE_HEALTH/health
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
    curl -v http://$GORCH_ROUTE_HEALTH/info
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

8. Exit out of the orchestrator container. Run the following command to get inside the gateway container
    ```
    export POD_NAME=gorch-test-55bf5f84d9-dd4vm # Replace this with the name of your guardrails orchestrator pod
    export CONTAINER_NAME=gorch-test-gateway
    oc exec -it -n $TEST_NS $POD_NAME -c $CONTAINER_NAME -- /bin/bash
    ```

9. Query the `/pii/v1/chat/completions` endpoint to perform completions while enabling detections on email and SSN information
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

10. Query the `/passthrough/v1/chat/completions` endpoint to perform completions on while disabling detections
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
