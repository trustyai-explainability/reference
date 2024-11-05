## Istio

What is a Sevice Mesh ?
Service Mesh addresses challenges with deploying 

OpenShift Router (HAProxy) -> reads OpenShift Route and sends to istio-ingressgateway -> reads virtual-service -> sends traffic to public service -> (if scaled to zero) activator -> private service -> target pod
