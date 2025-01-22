# Testing Disconnected Images
To emulate a disconnected cluster, you can apply a NetworkPolicy to restrict the egress from
every pod in a namespace. This blocks all outbound network connections from all pods in the namespace.

## Emulating Disconnection
### Disconnect a single namespace
```bash
oc apply -f disconnect.yaml
```

### Reconnect a single namespace
```bash
oc delete -f disconnect.yaml --ignore-not-found
```

### Disconnect all possible namespaces
This will disconnect as many namespaces as is possible without fundamentally breaking the Openshift web console:
```bash
python3 cluster_connector.py disconnect
```

### Reconnect all possible namespaces
This will undo all changes made by the disconnection command:

```bash
python3 cluster_connector.py connect
```

### See which namespaces have emulated disconnection:
```bash
python3 cluster_connector.py check
```

## Testing
The [Dockerfile](Dockerfile) builds a minimal image that provides `curl` and `ping`. A prebuilt version can be deployed via 

`oc apply -f ping-pod.yaml`

This can verify whether the disconnection emulation is successful:

```bash
oc apply -f ping-pod.yaml
oc exec ping-pod -- bash -c "ping -c 3 google.com"
>   PING google.com (142.251.163.102) 56(84) bytes of data.
>   64 bytes from wv-in-f102.1e100.net (142.251.163.102): icmp_seq=1 ttl=55 time=2.83 ms
>   64 bytes from wv-in-f102.1e100.net (142.251.163.102): icmp_seq=2 ttl=55 time=2.63 ms
>   64 bytes from wv-in-f102.1e100.net (142.251.163.102): icmp_seq=3 ttl=55 time=1.94 ms
>
>   --- google.com ping statistics ---
>   3 packets transmitted, 3 received, 0% packet loss, time 2002ms
>   rtt min/avg/max/mdev = 1.941/2.465/2.831/0.380 ms

oc apply -f disconnect.yaml
oc exec -i pods/ping-pod -- bash -s "ping google.com"
>   ping: google.com: Name or service not known
```