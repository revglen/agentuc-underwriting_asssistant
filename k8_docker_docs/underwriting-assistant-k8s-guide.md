# Underwriting Assistant — Docker & Kubernetes (Minikube) Reference

Ubuntu/Linux, Docker driver. Two source-of-truth notes before anything else:

- **Installation section**: standard, official install commands. Not run in
  this session — verify against the official docs if a version pins below
  goes stale.
- **Everything from "Building the images" onward**: exact commands actually
  run and verified together in this conversation, against this project.

---

## 1. Installation

### 1.1 Docker
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# run docker without sudo
sudo usermod -aG docker $USER
newgrp docker

docker --version
docker compose version
```

### 1.2 kubectl
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version --client
```

### 1.3 Minikube
```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
minikube version
```

### 1.4 Verify everything
```bash
docker --version
kubectl version --client
minikube version
```

---

## 2. Starting the environment

```bash
# start Docker daemon if not already running
sudo systemctl start docker
sudo systemctl status docker

# start minikube (Docker driver)
minikube start --driver=docker

# confirm
minikube status
kubectl cluster-info
```

### Ollama, needs to be reachable from containers
```bash
# check what it's bound to - must show *:11434 or 0.0.0.0:11434, not 127.0.0.1
ss -ltnp | grep 11434

# if it's loopback-only, fix it:
OLLAMA_HOST=0.0.0.0 nohup ollama serve > /tmp/ollama.log 2>&1 &
disown
# or, for a persistent fix (systemd service):
#   sudo systemctl stop ollama
#   sudo mkdir -p /etc/systemd/system/ollama.service.d
#   sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null <<'EOF'
#   [Service]
#   Environment="OLLAMA_HOST=0.0.0.0"
#   EOF
#   sudo systemctl daemon-reload
#   sudo systemctl restart ollama
```

---

## 3. Building the images (Docker Compose path)

```bash
# build + start MCP servers, Prometheus, Grafana
docker compose -f docker-compose.monitoring.yml up -d --build mcp-servers prometheus grafana

# build + start the API (once its service is in the compose file)
docker compose -f docker-compose.monitoring.yml up -d --build api

# force a clean rebuild, ignoring cached layers (use when a fix "isn't taking")
docker compose -f docker-compose.monitoring.yml build --no-cache api
docker compose -f docker-compose.monitoring.yml build --no-cache mcp-servers

# check running containers
docker compose -f docker-compose.monitoring.yml ps

# view logs
docker compose -f docker-compose.monitoring.yml logs mcp-servers
docker compose -f docker-compose.monitoring.yml logs api -f      # -f = follow, live
docker compose -f docker-compose.monitoring.yml logs api --previous
```

---

## 4. Loading images into Minikube

Local images aren't in any registry — Minikube needs them loaded directly,
and the deployment YAML needs `imagePullPolicy: Never` so it doesn't try to
pull them from anywhere.

```bash
docker images   # confirm the exact tags to load

minikube image load underwriting-assistant-mcp-servers:latest
minikube image load underwriting-assistant-api:latest

# verify Ollama is reachable from inside minikube's network
minikube ssh -- curl -s -o /dev/null -w "%{http_code}\n" http://host.minikube.internal:11434/api/tags
```

---

## 5. Kubernetes secrets and config

```bash
# TLS cert/key as a Secret (never bake private keys into an image)
kubectl create secret generic underwriting-tls-certs \
  --from-file=dev-cert.pem=./certs/dev-cert.pem \
  --from-file=dev-key.pem=./certs/dev-key.pem

# verify
kubectl get secret underwriting-tls-certs
```

Prometheus config is applied as a ConfigMap via `k8s/prometheus-configmap.yaml`
in the next step (not a separate manual command).

---

## 6. Deploying to Kubernetes

Apply in this order — `mcp-servers` before `api`, since `api` depends on it
being reachable:

```bash
kubectl apply -f k8s/prometheus-configmap.yaml
kubectl apply -f k8s/mcp-servers.yaml
kubectl apply -f k8s/prometheus.yaml
kubectl apply -f k8s/grafana.yaml
kubectl apply -f k8s/api.yaml
```

If you've edited a file after an earlier `apply` and env vars from a Service
name collision (or anything else) forces a pod recreate:
```bash
kubectl rollout restart deployment/mcp-servers
kubectl rollout restart deployment/api
```

---

## 7. Verifying the deployment

```bash
kubectl get pods
kubectl get pods -w              # watch live until everything is Running 1/1
kubectl get deployments
kubectl get services

# logs
kubectl logs -l app=mcp-servers
kubectl logs -l app=api
kubectl logs <pod-name> --previous   # the last attempt, if it's crash-looping

# deep inspect a pod that won't come up at all
kubectl describe pod <pod-name>
```

---

## 8. Accessing the services

Two ways — pick one per session, don't mix:

**A. `kubectl port-forward`** (simplest, matches how you've been testing all along)
```bash
kubectl port-forward service/underwriting-api 8443:8443 &
kubectl port-forward service/prometheus 9090:9090 &
kubectl port-forward service/grafana 3000:3000 &
```

**B. `minikube service --url`** (needs its own terminal open the whole time on the Docker driver)
```bash
minikube service underwriting-api --url
minikube service prometheus --url
minikube service grafana --url
```

---

## 9. Testing

The API serves **HTTPS only** (dev cert) — always `https://`, always `-k`.

```bash
# synchronous evaluation (blocks until the orchestrator finishes)
curl -k -X POST https://localhost:8443/applications/evaluate \
  -H "Content-Type: application/json" \
  -d '{"applicant_id":"applicant-1","requested_amount":20000,"months_of_statements":6}'

# async: submit, get a job_id back immediately
curl -k -s -X POST https://localhost:8443/applications/evaluate/async \
  -H "Content-Type: application/json" \
  -d '{"applicant_id":"applicant-1","requested_amount":20000,"months_of_statements":6}'

# async: poll with that job_id
curl -k -s https://localhost:8443/applications/evaluate/async/PASTE_JOB_ID_HERE

# capture + poll in one go
JOB_ID=$(curl -k -s -X POST https://localhost:8443/applications/evaluate/async \
  -H "Content-Type: application/json" \
  -d '{"applicant_id":"applicant-1","requested_amount":20000,"months_of_statements":6}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")
curl -k -s https://localhost:8443/applications/evaluate/async/$JOB_ID

# health check
curl -k https://localhost:8443/health

# smoke test the MCP servers directly (outside k8s, local process)
PYTHONPATH=src python3 src/script/mcp_smoke_test.py credit_bureau
PYTHONPATH=src python3 src/script/mcp_smoke_test.py bank_statement_parser
PYTHONPATH=src python3 src/script/mcp_smoke_test.py policy_rules_engine

# standalone orchestrator test, bypassing the API entirely
PYTHONPATH=src python3 src/script/agent_test.py applicant-1 20000 6
```

---

## 10. Stopping / teardown

### Kubernetes — remove just the app, keep the cluster running
```bash
kubectl delete -f k8s/api.yaml
kubectl delete -f k8s/mcp-servers.yaml
kubectl delete -f k8s/prometheus.yaml
kubectl delete -f k8s/grafana.yaml
kubectl delete -f k8s/prometheus-configmap.yaml
kubectl delete secret underwriting-tls-certs

# confirm nothing's left
kubectl get all
```

### Minikube — stop the cluster (state preserved, fast to resume)
```bash
minikube stop
```

### Minikube — fully delete the cluster (nuclear option, next start rebuilds it)
```bash
minikube delete
```

### Docker Compose stack
```bash
docker compose -f docker-compose.monitoring.yml down          # stop + remove containers
docker compose -f docker-compose.monitoring.yml down --volumes # also remove volumes (e.g. grafana-data)
```

### Docker — general cleanup
```bash
docker container prune     # remove stopped containers
docker image prune         # remove dangling (untagged) images
docker image prune -a      # remove all unused images, not just dangling
docker system prune        # containers + networks + dangling images + build cache
docker system prune -a --volumes   # aggressive - be careful on a shared machine
```

### Docker — stop the daemon entirely
```bash
sudo systemctl stop docker
```

---

## Quick troubleshooting index

| Symptom | Likely cause | Where covered |
|---|---|---|
| `no configuration file provided: not found` | missing `-f docker-compose.monitoring.yml` on the command | §3 |
| `All connection attempts failed` from a tool call | Ollama unreachable from the container | §2 (Ollama section), §4 |
| Container `NameError` on import | missing `import asyncio` in `metrics.py` | project history |
| `ValueError: invalid literal for int()` mentioning `tcp://...` | Kubernetes auto-injected `<SERVICE>_PORT` collided with a same-named setting | §6 — rename the Service, add `enableServiceLinks: false` |
| `curl: (52) Empty reply from server` | using `http://` against an HTTPS-only port | §9 — always `https://` + `-k` |
| Pod `CrashLoopBackOff` | `kubectl logs <pod> --previous` and `kubectl describe pod <pod>` | §7 |
| `structured_response` is `None` / decision missing | local model wrote prose instead of calling the structured-output tool | project history — retry-with-nudge logic in `applications.py` |
