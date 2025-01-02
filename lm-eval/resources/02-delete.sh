#!/usr/bin/env bash

NS="test"

oc delete pod lmeval-copy -n $NS
sleep 5
oc delete lmevaljob lmeval-test -n $NS
sleep 5
oc delete pvc lmeval-data -n $NS