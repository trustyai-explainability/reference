# module imports
import requests
import subprocess

# obtain the routes for the guardrails-nlp and guardrails-nlp-health services
GUARDRAILS_HEALTH_ROUTE = (
    subprocess.check_output(
        [
            "/opt/homebrew/bin/oc",
            "get",
            "routes",
            "guardrails-nlp-health",
            "-o",
            "jsonpath='{.spec.host}'",
        ],
        universal_newlines=True,
    )
    .strip()
    .strip("'")
)

GUARDRAILS_ROUTE = (
    subprocess.check_output(
        [
            "/opt/homebrew/bin/oc",
            "get",
            "routes",
            "guardrails-nlp",
            "-o",
            "jsonpath='{.spec.host}'",
        ],
        universal_newlines=True,
    )
    .strip()
    .strip("'")
)


# test /health endpoint of the orchestrator
def test_endpoint_health():
    url = f"https://{GUARDRAILS_HEALTH_ROUTE}/health"
    response = requests.get(url)
    assert response.status_code == 200


# test /info endpoint of the orchestrator
def test_endpoint_info():
    url = f"https://{GUARDRAILS_HEALTH_ROUTE}/info"
    response = requests.get(url)
    assert response.status_code == 200


# test standalone detections using the following orchestrator endpoint: /api/v2/text/detection/content
def test_endpoint_detection_content_correct_specification():
    url = f"https://{GUARDRAILS_ROUTE}/api/v2/text/detection/content"
    payload = {
        "detectors": {"hap": {}},
        "content": "You dotard, I really hate this stuff",
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    print(response.json())
    assert response.status_code == 200


def test_endpoint_detection_content_payload_exceeds_detector_input_size():
    url = f"https://{GUARDRAILS_ROUTE}/api/v2/text/detection/content"
    base_sentence = "You dotard, I really hate this stuff. "
    long_content = base_sentence * 1_000

    payload = {"detectors": {"hap": {}}, "content": long_content}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    assert response.status_code == 500


def test_endpoint_detection_content_empty_payload():
    url = f"https://{GUARDRAILS_ROUTE}/api/v2/text/detection/content"
    payload = {
        "detectors": {"hap": {}},
        "content": "",
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    print(response.json())
    assert response.status_code == 422


def test_endpoint_detection_content_misspecified_detector_name():
    url = f"https://{GUARDRAILS_ROUTE}/api/v2/text/detection/content"
    payload = {
        "detectors": {"hip": {}},
        "content": "You dotard, I really hate this stuff",
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    print(response.json())
    assert response.status_code == 404


# test text generation with detection using the following orchestrator endpoint: /api/v1/task/generation-with-detection
def test_endpoint_classification_with_text_generation_correct_specification():
    url = f"https://{GUARDRAILS_ROUTE}/api/v1/task/classification-with-text-generation"
    payload = {
        "model_id": "flan-t5-small",
        "inputs": "You dotard, I really hate this stuff",
        "guardrail_config": {
            "input": {"masks": [], "models": {"hap": {}}},
            "output": {"models": {}},
        },
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    assert response.status_code == 200


def test_endpoint_classification_with_text_generation_payload_exceeds_detector_input_size():
    url = f"https://{GUARDRAILS_ROUTE}/api/v1/task/classification-with-text-generation"
    base_sentence = "You dotard, I really hate this stuff. "
    long_content = base_sentence * 1_000

    payload = {
        "model_id": "flan-t5-small",
        "inputs": long_content,
        "guardrail_config": {
            "input": {"masks": [], "models": {"hap": {}}},
            "output": {"models": {}},
        },
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    assert response.status_code == 500


def test_endpoint_classification_with_text_generation_empty_payload():
    url = f"https://{GUARDRAILS_ROUTE}/api/v1/task/classification-with-text-generation"
    payload = {}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    print(response.json())
    assert response.status_code == 422


def test_endpoint_classification_with_text_generation_misspecified_detector_name():
    url = f"https://{GUARDRAILS_ROUTE}/api/v1/task/classification-with-text-generation"
    payload = {
        "model_id": "flan-t5-small",
        "inputs": "You dotard, I really hate this stuff",
        "guardrail_config": {
            "input": {"masks": [], "models": {"hip": {}}},
            "output": {"models": {}},
        },
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    print(response.json())
    assert response.status_code == 404
