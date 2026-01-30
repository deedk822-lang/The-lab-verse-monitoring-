#!/usr/bin/env bash

# S1: Generate RSA keys for JWT signing
set -e

mkdir -p secrets

echo "Generating RSA keys for JWT..."
openssl genrsa -out secrets/jwt-private-key.pem 2048
openssl rsa -in secrets/jwt-private-key.pem -pubout -out secrets/jwt-public-key.pem

# Secure the private key
chmod 600 secrets/jwt-private-key.pem

echo "✓ JWT keys generated in secrets/"
