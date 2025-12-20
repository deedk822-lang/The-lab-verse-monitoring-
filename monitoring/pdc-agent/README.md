# Grafana PDC Agent

This directory contains the Kubernetes configuration for the Grafana PDC Agent.

## Setup

1.  **Create the Kubernetes Secret:**

    The `secret.yaml.example` file is a template for the Kubernetes secret. To create the actual secret, you need to copy the example file and replace the placeholder value with your `GCLOUD_PDC_SIGNING_TOKEN`.

    ```bash
    # 1. Copy the example file
    cp secret.yaml.example secret.yaml

    # 2. Get your GCLOUD_PDC_SIGNING_TOKEN and base64 encode it
    echo -n "YOUR_GCLOUD_PDC_SIGNING_TOKEN" | base64

    # 3. Open secret.yaml and replace the value of 'token' with your base64 encoded token.
    ```

    **IMPORTANT:** Do not commit the `secret.yaml` file to version control. It should be treated as a sensitive file.

2.  **Deploy the Agent:**

    Once you have created the `secret.yaml` file, you can deploy the agent using the following command:

    ```bash
    kubectl apply -f secret.yaml
    kubectl apply -f deployment.yaml
    ```
