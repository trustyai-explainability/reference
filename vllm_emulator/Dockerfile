FROM registry.access.redhat.com/ubi8:8.10-1020

COPY *.py app/
COPY requirements.txt app/
COPY bigrams.json app/

WORKDIR app

# install python
RUN dnf install -y jq python3.11 python3.11-devel python3.11-pip unzip && \
    dnf clean all && \
    pip3 install -r requirements.txt

EXPOSE 8000
CMD ["fastapi", "run", "vllm_emulator.py"]