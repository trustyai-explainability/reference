#!/bin/bash

MODEL_NAME="${MODEL_NAME:-google/flan-t5-base}"
GPU="${GPU:-false}"

# Generate the custom card YAML content
CUSTOM_CARD=$(cat <<EOF
{
  "__type__": "task_card",
  "loader": {
    "__type__": "load_hf",
    "path": "SetFit/20_newsgroups",
    "streaming": true
  },
  "preprocess_steps": [
    {
      "__type__": "filter_by_condition",
      "values": {
        "text": ""
      },
      "condition": "ne"
    },
    {
      "__type__": "filter_by_expression",
      "expression": "len(text.split()) < 543"
    },
    {
      "__type__": "split_random_mix",
      "mix": {
        "train": "train[90%]",
        "validation": "train[10%]",
        "test": "test"
      }
    },
    {
      "__type__": "rename",
      "field_to_field": {
        "label_text": "label"
      }
    },
    {
      "__type__": "map_instance_values",
      "mappers": {
        "label": {
          "alt.atheism": "atheism",
          "comp.graphics": "computer graphics",
          "comp.os.ms-windows.misc": "microsoft windows",
          "comp.sys.ibm.pc.hardware": "pc hardware",
          "comp.sys.mac.hardware": "mac hardware",
          "comp.windows.x": "windows x",
          "misc.forsale": "for sale",
          "rec.autos": "cars",
          "rec.motorcycles": "motorcycles",
          "rec.sport.baseball": "baseball",
          "rec.sport.hockey": "hockey",
          "sci.crypt": "cryptography",
          "sci.electronics": "electronics",
          "sci.med": "medicine",
          "sci.space": "space",
          "soc.religion.christian": "christianity",
          "talk.politics.guns": "guns",
          "talk.politics.mideast": "middle east",
          "talk.politics.misc": "politics",
          "talk.religion.misc": "religion"
        }
      }
    },
    {
      "__type__": "set",
      "fields": {
        "classes": [
          "atheism",
          "computer graphics",
          "microsoft windows",
          "pc hardware",
          "mac hardware",
          "windows x",
          "for sale",
          "cars",
          "motorcycles",
          "baseball",
          "hockey",
          "cryptography",
          "electronics",
          "medicine",
          "space",
          "christianity",
          "guns",
          "middle east",
          "politics",
          "religion"
        ]
      }
    }
  ],
  "task": "tasks.classification.multi_class.topic_classification",
  "templates": "templates.classification.multi_class.all",
  "__tags__": {
    "region": "us"
  },
  "__description__": "This is a version of the 20 newsgroups dataset that is provided in Scikit-learn. From the Scikit-learn docs: \\n\"The 20 newsgroups dataset comprises around 18000 newsgroups posts on 20 topics split in two subsets: one for training (or development) and the other one for testing (or for performance evaluation). The split between the train and test set is based upon a message posted before and after a specific date.\"\nSee the full description on the dataset page: https://huggingface.co/datasets/SetFit/20_newsgroups."
}
EOF
)

# Temporary YAML file
TMP_YAML=$(mktemp /tmp/lmeval_job.XXXXXX.yaml)

# Base YAML content
BASE_YAML=$(cat <<EOF
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
  name: evaljob-sample
spec:
  allowOnline: true
  allowCodeExecution: true
  model: hf
  modelArgs:
    - name: pretrained
      value: "${MODEL_NAME}"
  taskList:
    taskRecipes:
      - template: "templates.classification.multi_class.title"
        card:
          custom: |
            ${CUSTOM_CARD}
  logSamples: true
EOF
)

# Add GPU resources if GPU is true
if [[ "$GPU" == "true" ]]; then
  GPU_SECTION=$(cat <<EOF
  pod:
    container:
      resources:
        limits:
          cpu: '1'
          memory: 8Gi
          nvidia.com/gpu: '1'
        requests:
          cpu: '1'
          memory: 8Gi
          nvidia.com/gpu: '1'
      env:
        - name: HF_HUB_VERBOSITY
          value: "debug"
        - name: UNITXT_DEFAULT_VERBOSITY
          value: "debug"
EOF
)
else
  GPU_SECTION=$(cat <<EOF
  pod:
    container:
      resources:
        limits:
          cpu: '1'
          memory: 8Gi
        requests:
          cpu: '1'
          memory: 8Gi
      env:
        - name: HF_HUB_VERBOSITY
          value: "debug"
        - name: UNITXT_DEFAULT_VERBOSITY
          value: "debug"
EOF
)
fi

# Combine YAML parts
echo "${BASE_YAML}" > "$TMP_YAML"
if [[ "$GPU" == "true" ]]; then
  echo "${GPU_SECTION}" >> "$TMP_YAML"
fi
echo "Generated YAML file:"
cat "$TMP_YAML"

kubectl apply -f "$TMP_YAML" -n test

rm "$TMP_YAML"
