# ODH LLM Deployment Notes

## Prereqs
1) ODH is installed on your cluster and a DSC is deployed

## Instructions to get GPU
Copied from Lucas' notes [here.](https://docs.google.com/document/d/1T2oc-KZRMboUVuUSGDZnt3VRZ5s885aDRJGYGMkn_Wo/edit?usp=sharing)
### Get a GPU Worker Node
1) Go to the Openshift cluster console
2) Under <your-cluster> -> Machine pools, click “Add machine pool”
3) Add a name, and in “Compute node instance type” scroll all way down and search for `g4dn.xlarge`
4) Click on Add machine pool

### Install the gpu operators
1) Go to the openshift dashboard
2) In OperatorHub install the following operators:
   1) Node Feature Discovery Operator 
      1) Create Node Feature Discovery CR, the defaults are fine 
      2) Several pods will start in the openshift-nfd (default) namespace. Once all these are up, the nodes will be labeled with a lot of feature flags. At which point you can proceed
   2) NVIDIA GPU Operator
      1) Create GPU ClusterPolicy CR. This will create several pods in the nvidia GPU namespace, they can take a while to come up because they compile the driver. Once they are up, scheduler should have allocatable GPUs

### Accelerator migration
If you already have RHOAI/ODH already deployed, you need to force the migration:

1) Go to the `redhat-ods-applications`/`opendatahub` namespace
2) Go to the Configmaps 
3) Delete the one called `migration-gpu-status` 
4) Now go to Deployments 
5) Click into `rhods-dashboard` / `odh-dashboard` 
6) Go to the replicasets 
7) Delete the the replicaset to force a restart of the pods 
8) Now go to `Search > Resources > AcceleratorProfiles`
9) You should see a resource under the redhat-ods-applications namespace

If not, just install the RHOAI operator and you should be ready to go.

## Authentication Patches for ROSA
```bash
export sa_issuer="$(oc get authentication cluster -o jsonpath --template='{ .spec.serviceAccountIssuer }' -n openshift-authentication)"
export dsci_audience="$(oc get DSCInitialization default-dsci -o jsonpath='{.spec.serviceMesh.auth.audiences[0]}')"
if [[ "z$sa_issuer" != "z" ]] && [[ "$sa_issuer" != "$dsci_audience" ]]
then
  echo “DSCI is updated”
  oc patch DSCInitialization default-dsci --type='json' -p="[{'op': 'replace', 'path': '/spec/serviceMesh/auth/audiences/0', 'value': '$sa_issuer'}]"
fi
```

Then restart your odh-model-controller deployment

## Deploy LLM Storage Container
1) `oc apply -f llm-model-container.yaml`

This downloads the LLM(s) from Huggingface, so can take some time to spin up (5-10 minutes)

## Deploy the LLMs
```bash
oc apply -f vllm_serving_runtime.yaml
oc apply -f isvc.yaml
```

## Set up query parameters
```bash
TOKEN=$(oc create token user-one)
LLM_ROUTE=$(oc get $(oc get ksvc -o name | grep predictor) --template={{.status.url}})
MODEL=$(curl -sk $LLM_ROUTE/v1/models -H "Authorization: Bearer ${TOKEN}" | jq ".data[0].root")
echo $MODEL
```
If this returns the name of your model (in this example, `phi-3`), proceed to the next step. Else, make sure that the model deployment has succesfully completed. You can verify this by looking in the `xyz-predictor` pod in your model namespace, and checking for the following log in the `kserve-container` conainer:
```
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

## Query
```bash
LLM_PROMPT="Hi, what's your name?"
echo $(curl -ks $LLM_ROUTE/v1/completions \
   -H "Authorization: Bearer ${TOKEN}" \
   -H "Content-Type: application/json" \
   -d "{
   \"model\": ${MODEL},
   \"prompt\": \"${LLM_PROMPT}\",
   \"max_tokens\":26,
   \"temperature\": .1
   }" | jq ".choices[0].text")
```
Should return:
```.
Chatbot: Hello! I'm Phi, your AI assistant. How can I help you today?"
```
