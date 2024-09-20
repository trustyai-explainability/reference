FROM python:3.11-slim

RUN python -m venv /tmp/venv &&\
    /tmp/venv/bin/pip install -U "huggingface_hub[cli]"

ENTRYPOINT ["top", "-b"]