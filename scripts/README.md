# Kimi Autonomous Security Auditor

This directory contains the scripts for the Kimi Autonomous Security Auditor.

## `kimi_auditor.py`

This is the main Python script that performs the security audit. It is designed to be run from the root of the repository.

### Configuration

The script is configured entirely through environment variables. The following variables are required:

-   `MOONSHOT_API_KEY`: Your API key for the Moonshot/Kimi service.

The following variables are optional and have default values:

-   `MOONSHOT_BASE_URL`: The base URL for the Moonshot API. Defaults to `https://api.moonshot.ai/v1`.
-   `KIMI_MODEL`: The model to use for the analysis. Defaults to `kimi-k2-thinking`.
-   `WORKSPACE`: The path to the repository. Defaults to the current directory.
-   `BASE_BRANCH`: The base branch to compare against. Defaults to `main`.
-   `TARGET_BRANCH`: The branch to analyze. Defaults to `HEAD`.
-   `AUTO_FIX`: Set to `true` to automatically apply patches and create pull requests. Defaults to `false`.

## `run_audit.sh`

This is a convenience script that demonstrates how to set the required environment variables and run the auditor.

### Usage

1.  Open `scripts/run_audit.sh` and replace the placeholder `sk-your-key-here` with your actual Moonshot/Kimi API key.
2.  (Optional) Customize the other environment variables in the script as needed.
3.  Run the script from the root of the repository:

    ```bash
    bash scripts/run_audit.sh
    ```
