# Containerizing a MinIO Storage Bucket

## Prereqs
1) Quay.io account
2) Podman
3) Locally stored model

## Instructions to containerize MinIO
1. Replace `<LOCAL_MODEL_PATH>` in `Dockerfile.minio` with your local model path

2. Replace `<OUTPUT_MODEL_PATH>` in `Dockerfile.minio` with your desired model path in your MinIO bucket. **It cannot point directly to the model's folder**

3. Define your Quay credentials
    ```bash
    QUAY_USER=<QUAY_USERNAME>
    REPO_NAME=<QUAY_REPOSITORY_NAME>
    IMAGE_TAG=<IMAGE_TAG>
    ```

4. Build the container image
    ```
    podman build -t quay.io/${QUAY_USERNAME}/{REPO_NAME}:${IMAGE_TAG} ./minio/Dockerfile.minio
    ```

5. Push the container image to Quay.io
    ```
    podman push quay.io/${QUAY_USERNAME}/{REPO_NAME}:${IMAGE_TAG}
    ```

### Deploy MinIO image on OpenShift
1. Create a new project `minio`
    ```bash
    MINIO_NS=minio
    oc new-project ${MINIO_NS}
    ```

2. Replace `<QUAY_IMG>` in `minio.yaml` with your Quay image

3. Define a secret access key, create new MinIO specs with the secret access key, and apply them to the `minio` namespace
    ```bash
    SECRET_ACCESS_KEY=$(openssl rand -hex 32)

    sed "s/<accesskey>/$ACCESS_KEY_ID/g"  ./llm-deployment/minio/minio.yaml | sed "s+<secretkey>+$SECRET_ACCESS_KEY+g" | tee ./llm-deployment/minio/minio-current.yaml | oc -n ${MINIO_NS} apply -f -

    sed "s/<accesskey>/$ACCESS_KEY_ID/g" ./llm-deployment/minio/minio-secret.yaml | sed "s+<secretkey>+$SECRET_ACCESS_KEY+g" |sed "s/<minio_ns>/$MINIO_NS/g" | tee ./llm-deployment/minio/minio-secret-current.yaml | oc -n ${MINIO_NS} apply -f -
    ```

4. Create a new project to deploy your model in
    ```bash
    MODEL_NS=model
    oc new-project ${MODEL_NS}
    ```

5. Apply `minio-secret-current.yaml` and `serviceaccount-minio-current.yaml` to you model namespace
    ```bash
    oc apply -f ${BASE_DIR}/minio-secret-current.yaml -n ${TEST_NS}
    oc apply -f ${BASE_DIR}/serviceaccount-minio-current.yaml -n ${TEST_NS}
    ```