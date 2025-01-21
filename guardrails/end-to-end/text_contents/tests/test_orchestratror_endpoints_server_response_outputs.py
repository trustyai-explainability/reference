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
