# %% module imports
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


def test_json_structure_valid_payload():
    url = f"https://{GUARDRAILS_ROUTE}/api/v2/text/detection/content"
    payload = {
        "detectors": {"hap": {}},
        "content": "You dotard, I really hate this stuff",
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()

    assert "detections" in response_data, "Response does not contain 'detections' key"
    assert isinstance(response_data["detections"], list), "'detections' is not a list"
    assert len(response_data["detections"]) > 0, "No detections returned"


def test_detection_fields():
    url = f"https://{GUARDRAILS_ROUTE}/api/v2/text/detection/content"
    payload = {
        "detectors": {"hap": {}},
        "content": "You dotard, I really hate this stuff",
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    detection = response.json()["detections"][0]
    assert "start" in detection, "Detection does not contain 'start' key"
    assert "end" in detection, "Detection does not contain 'end' key"
    assert "text" in detection, "Detection does not contain 'text' key"
    assert "detection" in detection, "Detection does not contain 'detection' key"
    assert (
        "detection_type" in detection
    ), "Detection does not contain 'detection_type' key"
    assert "score" in detection, "Detection does not contain 'score' key"


def test_detection_field_values():
    url = f"https://{GUARDRAILS_ROUTE}/api/v2/text/detection/content"
    payload = {
        "detectors": {"hap": {}},
        "content": "You dotard, I really hate this stuff",
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    detection = response.json()["detections"][0]

    assert (
        detection["text"] == payload["content"]
    ), "Returned text does not match input content"
    assert (
        detection["detection"] == "sequence_classifier"
    ), f"Unexpected detection: {detection['detection']}"
    assert (
        detection["detection_type"] == "sequence_classification"
    ), f"Unexpected detection type: {detection['detection_type']}"
    assert 0.0 <= detection["score"] <= 1.0, "Score is out of range (0.0 to 1.0)"


def test_score_threshold():
    url = f"https://{GUARDRAILS_ROUTE}/api/v2/text/detection/content"
    payload = {
        "detectors": {"hap": {}},
        "content": "You dotard, I really hate this stuff",
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    detection = response.json()["detections"][0]

    assert detection["score"] > 0.95, f"Score is too low: {detection['score']}"


def test_json_structure():
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
    response_data = response.json()

    # Validate top-level keys
    assert (
        "token_classification_results" in response_data
    ), "Response missing 'token_classification_results' key"
    assert (
        "input_token_count" in response_data
    ), "Response missing 'input_token_count' key"
    assert "warnings" in response_data, "Response missing 'warnings' key"


def test_token_classification_results():
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
    response_data = response.json()

    classification_results = response_data["token_classification_results"]["input"]
    assert isinstance(
        classification_results, list
    ), "'input' in 'token_classification_results' is not a list"
    assert len(classification_results) > 0, "No classification results returned"

    result = classification_results[0]
    assert "start" in result, "Missing 'start' in classification result"
    assert "end" in result, "Missing 'end' in classification result"
    assert "word" in result, "Missing 'word' in classification result"
    assert "entity" in result, "Missing 'entity' in classification result"
    assert "entity_group" in result, "Missing 'entity_group' in classification result"
    assert "score" in result, "Missing 'score' in classification result"
    assert (
        result["word"] == payload["inputs"]
    ), "Returned word does not match input text"
    assert (
        result["entity"] == "sequence_classifier"
    ), f"Unexpected entity: {result['entity']}"
    assert (
        result["entity_group"] == "sequence_classification"
    ), f"Unexpected entity group: {result['entity_group']}"
    assert 0.0 <= result["score"] <= 1.0, "Score is out of range (0.0 to 1.0)"


def test_input_token_count():
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
    response_data = response.json()

    token_count = response_data["input_token_count"]
    assert isinstance(token_count, int), "'input_token_count' is not an integer"


def test_warnings():
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
    response_data = response.json()

    warnings = response_data["warnings"]
    assert isinstance(warnings, list), "'warnings' is not a list"
    assert len(warnings) > 0, "No warnings returned"

    warning = warnings[0]
    assert "id" in warning, "Missing 'id' in warning"
    assert "message" in warning, "Missing 'message' in warning"
    assert (
        warning["id"] == "UNSUITABLE_INPUT"
    ), f"Unexpected warning id: {warning['id']}"
    assert (
        "Unsuitable input detected" in warning["message"]
    ), f"Unexpected warning message: {warning['message']}"
