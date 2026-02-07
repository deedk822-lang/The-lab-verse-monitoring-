# Generate Ads Example

This script demonstrates how to use the Bria API to generate advertisements.

## Prerequisites

- Node.js installed
- `axios` package installed (`npm install axios`)

## Usage

1.  **Set your API Token:**

    You need to set your Bria API token as an environment variable. Replace `your_real_token` with your actual token.

    ```bash
    export BRIA_API_TOKEN=your_real_token
    ```

2.  **Run the script:**

    Execute the script from the root of the repository.

    ```bash
    node examples/generate-ads.js
    ```

The script will send a request to the Bria API and print the response to the console.

---

## Autogen Opik Weather Example

This script demonstrates how to use `autogen` and `opik` to create a simple AI agent that can get the weather.

## Prerequisites

- Python 3 installed
- Required packages installed:
  ```bash
  pip install -U "autogen-agentchat" "autogen-ext[openai]" opik opentelemetry-sdk opentelemetry-instrumentation-openai opentelemetry-exporter-otlp
  ```

## Usage

1.  **Set your OpenAI API Key:**

    The script uses the OpenAI GPT-4o model. You need to set your OpenAI API key as an environment variable.

    ```bash
    export OPENAI_API_KEY="your_api_key"
    ```

2.  **Run the script:**

    Execute the script from the root of the repository.

    ```bash
    python examples/autogen_opik_weather.py
    ```
The script will run, and you will be prompted to configure Opik for telemetry. It will then ask the agent for the weather in New York and print the conversation.
