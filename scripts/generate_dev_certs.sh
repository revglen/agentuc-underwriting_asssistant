#!/usr/bin/env bash
# Generates a self-signed cert for LOCAL DEV ONLY. Browsers/clients will not
# trust this. A real deployment gets its cert from an actual CA (ACM,
# Let's Encrypt/ACME, corporate PKI) at the load balancer or ingress, not
# from this script.
set -euo pipefail

CERT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/certs"
mkdir -p "$CERT_DIR"

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "$CERT_DIR/dev-key.pem" \
  -out "$CERT_DIR/dev-cert.pem" \
  -days 365 \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "Wrote $CERT_DIR/dev-cert.pem and $CERT_DIR/dev-key.pem (dev only, not trusted by browsers)"
