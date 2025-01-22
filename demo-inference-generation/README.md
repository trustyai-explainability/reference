# TrustyAI Demo Inference Generator
When spinning up TrustyAI to use the demo-loan-nn-onnx-alpha and demo-loan-nn-onnx-beta models, you can deploy this pod into your namespace to automatically send inferences to the models. This will send a random set of 5 inferences every 30 seconds to both the alpha and beta models indefinitely.


## Build
`podman build -t SOMETHING .`

## Deploy
`oc apply -f inference_generator.yaml`