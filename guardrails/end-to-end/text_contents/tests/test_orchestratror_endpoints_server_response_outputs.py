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
