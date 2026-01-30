#!/usr/bin/env bash

# S2: Generate TLS Certificates for PostgreSQL
set -e

mkdir -p certs/postgres

echo "Generating self-signed TLS certificates for PostgreSQL..."
openssl req -new -x509 -days 365 -nodes -text -out certs/postgres/server.crt \
  -keyout certs/postgres/server.key -subj "/CN=postgres"

# PostgreSQL requires strict permissions on the key
chmod 600 certs/postgres/server.key
cp certs/postgres/server.crt certs/postgres/ca.crt

echo "✓ Certificates generated in certs/postgres/"
