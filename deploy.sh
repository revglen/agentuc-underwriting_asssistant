#!/usr/bin/env bash
# Builds mcp-servers, api, ui images -> loads into Minikube -> deploys ->
# port-forwards -> prints URLs to open.
#
# Run from the project root (where Dockerfile.mcp / Dockerfile.api /
# Dockerfile.ui and k8s/ live).
set -euo pipefail

echo "==> 1/6 checking minikube is running"
#minikube status > /dev/null || { echo "FAIL: minikube is not running. Run: minikube start --driver=docker"; exit 1; }
minikube status > /dev/null || { echo "minikube not running, starting..."; minikube start --driver=docker || { echo "FAIL: minikube start failed"; exit 1; }; }

echo "==> 2/6 building images"
docker build -f Dockerfile.mcp -t underwriting-assistant-mcp-servers:latest .
docker build -f Dockerfile.api -t underwriting-assistant-api:latest .
docker build -f Dockerfile.ui  -t underwriting-assistant-ui:latest .

echo "==> 3/6 loading images into minikube"
minikube image load underwriting-assistant-mcp-servers:latest
minikube image load underwriting-assistant-api:latest
minikube image load underwriting-assistant-ui:latest

echo "==> 4/6 TLS secret"
if [ ! -f certs/dev-cert.pem ] || [ ! -f certs/dev-key.pem ]; then
    echo "    dev cert not found, generating"
    ./scripts/generate_dev_certs.sh
fi
if kubectl get secret underwriting-tls-certs > /dev/null 2>&1; then
    echo "    secret already exists, skipping create"
else
    kubectl create secret generic underwriting-tls-certs \
        --from-file=dev-cert.pem=./certs/dev-cert.pem \
        --from-file=dev-key.pem=./certs/dev-key.pem
fi

echo "==> 5/6 deploying (mcp-servers before api, api before ui)"
kubectl apply -f k8/prometheus-configmap.yaml
kubectl apply -f k8/mcp-servers.yaml
kubectl apply -f k8/prometheus.yaml
kubectl apply -f k8/grafana.yaml
kubectl apply -f k8/api.yaml
kubectl apply -f k8/ui.yaml

echo "    waiting for pods to be ready (this can take a few minutes on first run)"
kubectl wait --for=condition=Ready pod -l app=mcp-servers --timeout=180s
kubectl wait --for=condition=Ready pod -l app=api --timeout=180s
kubectl wait --for=condition=Ready pod -l app=ui --timeout=180s
kubectl wait --for=condition=Ready pod -l app=prometheus --timeout=120s
kubectl wait --for=condition=Ready pod -l app=grafana --timeout=120s

echo "==> 6/6 opening port-forwards"
pkill -f "port-forward service/underwriting-api" 2>/dev/null || true
pkill -f "port-forward service/ui" 2>/dev/null || true
pkill -f "port-forward service/prometheus" 2>/dev/null || true
pkill -f "port-forward service/grafana" 2>/dev/null || true
sleep 1

nohup kubectl port-forward service/underwriting-api 8443:8443 > /tmp/pf-api.log 2>&1 &
disown
nohup kubectl port-forward service/ui 8501:8501 > /tmp/pf-ui.log 2>&1 &
disown
nohup kubectl port-forward service/prometheus 9090:9090 > /tmp/pf-prometheus.log 2>&1 &
disown
nohup kubectl port-forward service/grafana 3000:3000 > /tmp/pf-grafana.log 2>&1 &
disown
sleep 2

echo
echo "==> done. open:"
echo "    UI:         http://localhost:8501"
echo "    API docs:   https://localhost:8443/docs   (self-signed cert)"
echo "    Prometheus: http://localhost:9090"
echo "    Grafana:    http://localhost:3000  (admin / admin)"
echo
echo "port-forwards are running in the background (logs: /tmp/pf-*.log)."
echo "to stop them: pkill -f 'port-forward service/'"