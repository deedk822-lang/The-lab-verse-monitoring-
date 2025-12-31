# Kimi Autonomous Security Auditor v4

This directory contains the scripts for the Kimi Autonomous Security Auditor v4, a self-healing security agent.

## `kimi_auditor_v4.py`

This is the main Python script that performs the security audit. It is designed to be run from the root of the repository.

### Features

-   **Diff-Based Context**: Analyzes only the changes between branches for maximum precision and efficiency.
-   **Automated Test Gate**: Runs the test suite after applying a patch and rolls back on failure.
-   **Iterative Refinement Loop**: Feeds back errors to Kimi for a refined patch (up to 3 attempts).
-   **Configurable Autonomy**: Can be configured to run in a fully autonomous mode.
-   **Rich PRs with Evidence**: Creates detailed pull requests with findings and confidence scores.

### Configuration

The script is configured entirely through environment variables. To configure the auditor, follow these steps:

1.  **Copy the example environment file:**

    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file:**

    Open the newly created `.env` file and fill in the required values under the "Kimi Autonomous Security Auditor v4" section. At a minimum, you must provide your `MOONSHOT_API_KEY`.

    The following variables are available:

    -   `MOONSHOT_API_KEY`: **(Required)** Your API key for the Moonshot/Kimi service.
    -   `TARGET_BRANCH`: The branch you want to analyze.
    -   `BASE_BRANCH`: The base branch to compare against.
    -   `AUTO_APPROVE`: Set to `"true"` to enable fully autonomous operation.
    -   `MAX_ITERATIONS`: The maximum number of times Kimi should attempt to refine a patch.
    -   `TEST_CMD`: The command to run your test suite.
    -   `MOONSHOT_BASE_URL`: The base URL for the Moonshot API.
    -   `KIMI_MODEL`: The model to use for the analysis.
    -   `WORKSPACE`: The path to the repository.

## `run_audit_v4.sh`

This is a convenience script that demonstrates how to set the required environment variables and run the auditor.

### Usage

1.  Open `scripts/run_audit_v4.sh` and replace the placeholder `sk-your-key-here` with your actual Moonshot/Kimi API key.
2.  (Optional) Customize the other environment variables in the script as needed.
3.  Run the script from the root of the repository:

    ```bash
    bash scripts/run_audit_v4.sh
    ```
