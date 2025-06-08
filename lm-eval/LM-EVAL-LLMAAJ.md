# LLM-as-a-Judge Tutorial

## What is LLM-as-a-Judge?

Instead of using basic metrics like ROUGE scores, you can use another AI model to judge your model's outputs. This is useful when you need human-like evaluation.

## When to use it

- No clear right/wrong answers (like creative writing)
- Need to check quality, not just correctness
- Want to measure things like helpfulness or safety

## Setup

First, make sure TrustyAI is installed in your Kubernetes cluster. Then configure it:

```bash
kubectl patch configmap trustyai-service-operator-config -n test --type=merge -p '{
  "data": {
    "lmes-allow-online": "true",
    "lmes-code-execution": "true",
    "lmes-default-batch-size": "4"
  }
}'
```

## What Each Example Does

### Example 1: Standard Benchmark Evaluation
- **What it tests**: Your model answers questions from MT-Bench (a standard benchmark)
- **Who judges**: Mistral-7B model acts as the judge
- **How it works**: 
  1. Your model (flan-t5-base) answers MT-Bench questions
  2. Mistral-7B rates those answers on quality
  3. You get scores showing how well your model performed
- **Good for**: Comparing your model against standard benchmarks

### Example 2: Custom Quality Assessment  
- **What it tests**: Same MT-Bench questions, but with custom evaluation criteria
- **Who judges**: Mistral-7B model with custom instructions
- **How it works**:
  1. Your model (flan-t5-small) answers questions
  2. Mistral-7B rates answers from 1-10 based on helpfulness, accuracy, and detail
  3. Uses custom preprocessing to clean and format the data
- **Good for**: Testing specific quality aspects you care about

## Technical Components Explained

### Example 1 Components
- **`cards.mt_bench.generation.english_single_turn`**: Loads MT-Bench dataset with single-turn conversations
- **`templates.empty`**: No special formatting - uses data as-is
- **`formats.empty`**: No special model formatting
- **`metrics.llm_as_judge.rating.mistral_7b_instruct_v0_2_huggingface_template_mt_bench_single_turn`**: Pre-built metric that uses Mistral-7B to rate answers

### Example 2 Components
- **Card preprocessing steps**:
  - `rename_splits`: Changes "train" split to "test" 
  - `filter_by_condition`: Only keeps single-turn conversations
  - `rename`: Changes field names (model_input → question, etc.)
  - `literal_eval`: Converts string lists to actual lists
  - `copy`: Extracts first item from lists
- **Custom template**: Tells the judge how to rate (1-10 scale, what to look for)
- **`processors.extract_mt_bench_rating_judgment`**: Pulls the numerical rating from judge's response
- **`formats.models.mistral.instruction`**: Formats prompts for Mistral model
- **Custom LLM-as-judge metric**: Uses Mistral-7B with your custom instructions

## Example 1: Basic Evaluation with MT-Bench

This example uses MT-Bench to evaluate how well a model answers questions:

```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
  name: mt-bench-eval
  namespace: test
spec:
  model: hf
  modelArgs:
    - name: pretrained
      value: google/flan-t5-base
  taskList:
    taskRecipes:
      - card:
          name: "cards.mt_bench.generation.english_single_turn"
        template:
          name: "templates.empty"
        format: "formats.empty"
        metrics:
          - name: "metrics.llm_as_judge.rating.mistral_7b_instruct_v0_2_huggingface_template_mt_bench_single_turn"
  logSamples: true
  batchSize: "2"
  allowOnline: true
  allowCodeExecution: true
  pod:
    container:
      env:
        - name: HUGGINGFACE_TOKEN
          valueFrom:
            secretKeyRef:
              name: hf-token-secret
              key: token
      resources:
        limits:
          cpu: '2'
          memory: 16Gi
          nvidia.com/gpu: '1'
        requests:
          cpu: '2'
          memory: 16Gi
          nvidia.com/gpu: '1'
```

## Example 2: Custom Evaluation

This example shows how to create custom evaluation criteria:

```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
  name: custom-eval
  namespace: test
spec:
  allowOnline: true
  allowCodeExecution: true
  model: hf
  modelArgs:
    - name: pretrained
      value: google/flan-t5-small
  taskList:
    taskRecipes:
      - card:
          custom: |
            {
                "__type__": "task_card",
                "loader": {
                    "__type__": "load_hf",
                    "path": "OfirArviv/mt_bench_single_score_gpt4_judgement",
                    "split": "train"
                },
                "preprocess_steps": [
                    {
                        "__type__": "rename_splits",
                        "mapper": {
                            "train": "test"
                        }
                    },
                    {
                        "__type__": "filter_by_condition",
                        "values": {
                            "turn": 1
                        },
                        "condition": "eq"
                    },
                    {
                        "__type__": "filter_by_condition",
                        "values": {
                            "reference": "[]"
                        },
                        "condition": "eq"
                    },
                    {
                        "__type__": "rename",
                        "field_to_field": {
                            "model_input": "question",
                            "score": "rating",
                            "category": "group",
                            "model_output": "answer"
                        }
                    },
                    {
                        "__type__": "literal_eval",
                        "field": "question"
                    },
                    {
                        "__type__": "copy",
                        "field": "question/0",
                        "to_field": "question"
                    },
                    {
                        "__type__": "literal_eval",
                        "field": "answer"
                    },
                    {
                        "__type__": "copy",
                        "field": "answer/0",
                        "to_field": "answer"
                    }
                ],
                "task": "tasks.response_assessment.rating.single_turn",
                "templates": [
                    "templates.response_assessment.rating.mt_bench_single_turn"
                ]
            }
        template:
          ref: response_assessment.rating.mt_bench_single_turn
        format: formats.models.mistral.instruction
        metrics:
        - ref: llmaaj_metric
    custom:
      templates:
        - name: response_assessment.rating.mt_bench_single_turn
          value: |
            {
                "__type__": "input_output_template",
                "instruction": "Please act as an impartial judge and evaluate the quality of the response provided by an AI assistant to the user question displayed below. Your evaluation should consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of the response. Begin your evaluation by providing a short explanation. Be as objective as possible. After providing your explanation, you must rate the response on a scale of 1 to 10 by strictly following this format: \"[[rating]]\", for example: \"Rating: [[5]]\".\n\n",
                "input_format": "[Question]\n{question}\n\n[The Start of Assistant's Answer]\n{answer}\n[The End of Assistant's Answer]",
                "output_format": "[[{rating}]]",
                "postprocessors": [
                    "processors.extract_mt_bench_rating_judgment"
                ]
            }
      tasks:
        - name: response_assessment.rating.single_turn
          value: |
            {
                "__type__": "task",
                "input_fields": {
                    "question": "str",
                    "answer": "str"
                },
                "outputs": {
                    "rating": "float"
                },
                "metrics": [
                    "metrics.spearman"
                ]
            }
      metrics:
        - name: llmaaj_metric
          value: |
            {
                "__type__": "llm_as_judge",
                "inference_model": {
                    "__type__": "hf_pipeline_based_inference_engine",
                    "model_name": "mistralai/Mistral-7B-Instruct-v0.2",
                    "max_new_tokens": 256,
                    "use_fp16": true
                },
                "template": "templates.response_assessment.rating.mt_bench_single_turn",
                "task": "rating.single_turn",
                "format": "formats.models.mistral.instruction",
                "main_score": "mistral_7b_instruct_v0_2_huggingface_template_mt_bench_single_turn"
            }
  logSamples: true
  pod:
    container:
      env:
        - name: HF_TOKEN
          valueFrom:
            secretKeyRef:
              name: hf-token-secret
              key: token
      resources:
        limits:
          cpu: '2'
          memory: 16Gi
```

## How to run

1. Save your YAML to a file (e.g., `eval.yaml`)
2. Create the secret for your HuggingFace token:
   ```bash
   kubectl create secret generic hf-token-secret --from-literal=token=YOUR_TOKEN -n test
   ```
3. Apply the evaluation job:
   ```bash
   kubectl apply -f eval.yaml
   ```
4. Check the results:
   ```bash
   kubectl logs -f job/mt-bench-eval -n test
   ```

## Tips

- Start with smaller models to test your setup
- Use `batchSize: "1"` if you have memory issues
- Check logs if something fails
- The judge model needs to be powerful enough to give good ratings

