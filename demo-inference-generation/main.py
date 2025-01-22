import requests
import random
import logging
import time
import subprocess


def generate_row():
    row = {}
    row["Number of Children"] = random.randint(0, 5)
    row["Total Income"] = random.randint(50_000, 500_000)
    row["Number of Total Family Members"] = random.randint(0, 7)
    row["Is Male-Identifying?"] = random.randint(0, 1)
    row["Owns Car?"] = random.randint(0, 1)
    row["Owns Realty?"] = random.randint(0, 1)
    row["Is Partnered?"] = random.randint(0, 1)
    row["Is Employed?"] = random.randint(0, 1)
    row["Live with Parents?"] = random.randint(0, 1)
    row["Age"] = random.randint(18 * 365, 100 * 365)
    row["Length of Employment?"] = random.randint(0, 50 * 365)
    row = {k: float(v) for k, v in row.items()}
    return row


def format_to_json(rows):
    row_to_array = [list(row.values()) for row in rows]
    return {
        "inputs": [
            {"name": "customer_data_input",
             "shape": [len(rows), 11],
             "datatype": "FP64",
             "data": row_to_array
             }
        ]
    }


# get model routes
models = ["demo-loan-nn-onnx-alpha", "demo-loan-nn-onnx-beta"]
urls = []
for model in models:
    base_route = subprocess.check_output(
        ["oc", "get", "inferenceservice", model, "-o", "jsonpath='{.status.url}'"]
    ).decode().replace("'", "")
    urls.append(base_route+"/v2/models/{}/versions/1/infer".format(model))

token = subprocess.check_output(['oc', 'whoami', '-t']).decode().strip().replace("'", "")

if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger('Payload Generator')
    logger.setLevel(logging.INFO)

    logger.info("Using the following URL for model alpha:\n" + urls[0])
    logger.info("Using the following URL for model beta:\n" + urls[1])

    print(token)
    headers = {"Authorization": "Bearer " + token}

    while True:
        rows = [generate_row() for _ in range(5)]
        json_payload = format_to_json(rows)
        for model_idx, url in enumerate(urls):
            response = requests.post(url, headers=headers, json=json_payload, verify=False)

            if response.status_code == 200:
                logger.info("✅ Posted {} payloads to {}".format(len(rows), models[model_idx]))
            else:
                logger.error("❌ Error posting payloads to {}: ".format(models[model_idx], response.content))
        time.sleep(30)
