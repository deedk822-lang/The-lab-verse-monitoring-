# Kimi Autonomous Security Auditor

This directory contains the script for the Kimi Autonomous Security Auditor.

## `kimi_auditor.py`

This is the main Python script that performs the security audit. It is designed to be run from the root of the repository.

### Configuration

The script is configured entirely through environment variables. To configure the auditor, follow these steps:

1.  **Copy the example environment file:**

    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file:**

    Open the newly created `.env` file and fill in the required values under the "Kimi Autonomous Security Auditor" section. At a minimum, you must provide your `MOONSHOT_API_KEY`.

    The following variables are available:

    -   `MOONSHOT_API_KEY`: **(Required)** Your API key for the Moonshot/Kimi service.
    -   `TARGET_BRANCH`: The branch you want to analyze.
    -   `BASE_BRANCH`: The base branch to compare against.
    -   `AUTO_FIX`: Set to `"true"` to enable the script to automatically apply patches and create pull requests.
    -   `MOONSHOT_BASE_URL`: The base URL for the Moonshot API.
    -   `KIMI_MODEL`: The model to use for the analysis.
    -   `WORKSPACE`: The path to the repository.

### Usage

Once you have configured your `.env` file, you can run the auditor from the root of the repository:

```bash
python3 scripts/kimi_auditor.py
```
