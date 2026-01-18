#!/bin/bash
# scripts/test_setup.sh
# Comprehensive test setup script

set -e

echo "Setting up and running tests..."

# Install dependencies
echo "Installing dependencies..."
npm install

# Run linting
echo "Running linter..."
npm run lint

# Run tests
echo "Running tests..."
npm test

# Build the application
echo "Building application..."
npm run build

# Test Docker build
echo "Testing Docker build..."
docker build -t test-build .

# Test Alibaba Cloud connectivity
echo "Testing Alibaba Cloud CLI..."
if command -v aliyun &> /dev/null; then
    echo "Alibaba Cloud CLI is installed"
    aliyun --version
else
    echo "Alibaba Cloud CLI not found - installing..."
    curl -LO https://aliyuncli.alicdn.com/aliyun-cli-linux-latest-amd64.tgz
    tar xzvf aliyun-cli-linux-latest-amd64.tgz
    sudo mv aliyun /usr/local/bin/
    aliyun --version
fi

# Test Hugging Face connectivity
echo "Testing Hugging Face connectivity..."
if python3 -c "import huggingface_hub; print('Hugging Face SDK available')" &> /dev/null; then
    echo "Hugging Face SDK is available"
else
    echo "Installing Hugging Face SDK..."
    pip3 install huggingface_hub
fi

# Test security scanner
echo "Testing security scanner..."
python3 scripts/alibaba_cloud_security_scan.py

echo "All tests passed successfully!"
