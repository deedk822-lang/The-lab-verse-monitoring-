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
