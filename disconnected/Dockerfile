FROM registry.access.redhat.com/ubi9/ubi-minimal
RUN microdnf -y update && microdnf -y install sudo iputils hostname findutils less nano && microdnf clean all
CMD ["tail", "-f", "/dev/null"]