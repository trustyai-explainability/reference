FROM registry.access.redhat.com/ubi8:8.10-1020

ARG OC_CLI_URL=https://mirror.openshift.com/pub/openshift-v4/amd64/clients/ocp/4.14.33/openshift-client-linux.tar.gz

# install python
RUN dnf install -y jq python3.11 python3.11-devel python3.11-pip unzip && \
    dnf clean all && \
    pip3 install requests

# install oc
ADD ${OC_CLI_URL} oc-cli.tar.gz
RUN tar -C /usr/local/bin -xvf oc-cli.tar.gz && \
    chmod +x /usr/local/bin/oc

# run code
COPY main.py .
CMD ["python3", "main.py"]