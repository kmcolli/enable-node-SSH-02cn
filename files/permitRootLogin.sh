#!/bin/bash
kubectl exec -i $1 -n kube-system -- bash -c "sed -i 's/PermitRootLogin no/PermitRootLogin yes/g' /host/etc/ssh/sshd_config"
sleep 5
kubectl exec -i $1 -n kube-system -- bash -c  "./systemutil -service sshd.service restart"
sleep 5