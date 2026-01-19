# AI Talent Scout v7: Setup and Operations Guide

This document outlines the setup requirements and operational flow for the fully autonomous, multi-platform, zero-touch recruiting intelligence system.

## 1. HubSpot Setup Requirements

To enable the Talent Scout, the following configurations must be in place within your HubSpot portal.

### 1.1. Custom Properties on Contact Objects

Navigate to `Settings > Properties` and create the following custom properties for your Contact objects:

-   **`github_handle`**
    -   **Type:** Single-line text
    -   **Description:** Stores the candidate's GitHub username (e.g., "jules-the-engineer").
-   **`linkedin_url`**
    -   **Type:** Single-line text
    -   **Description:** Stores the full URL to the candidate's public LinkedIn profile.
-   **`audit_status`**
    -   **Type:** Dropdown select
    -   **Description:** Tracks the state of the AI audit.
    -   **Options:**
        -   `Pending` (Default state to trigger an audit)
        -   `Audited` (Set automatically after a successful audit)
        -   `Skipped` (Optional state for manual overrides)

### 1.2. HubSpot Private App Token Scopes

The system requires a HubSpot Private App with a token that has the following scopes enabled:

-   `crm.objects.contacts.read` (To find candidates pending audit)
-   `crm.objects.contacts.write` (To update the `audit_status` after completion)
-   `crm.objects.notes.read` (To check for existing notes for duplicate prevention)
-   `crm.objects.notes.write` (To post the audit findings as a note)
-   `timeline` (Required for associating the note with the contact)

## 2. Third-Party Service Requirements

### 2.1. GitHub Token

The system requires a GitHub Personal Access Token (PAT) with read-only access to public user information. No special permissions are needed.

### 2.2. Proxycurl API Key

The system uses Proxycurl to reliably audit public LinkedIn profiles. You will need an API key from Proxycurl.
-   **Website:** https://nubela.co/proxycurl

## 3. Environment Variables

The GitHub Actions workflow requires the following secrets to be configured in your repository's settings (`Settings > Secrets and variables > Actions`):

-   `HUBSPOT_PRIVATE_APP_TOKEN`: The token from your HubSpot Private App.
-   `GITHUB_TOKEN`: Your GitHub Personal Access Token.
-   `PROXYCURL_KEY`: Your API key from Proxycurl.

## 4. Operational Flow (Zero-Touch Process)

The entire system is designed to be fully autonomous. The workflow is as follows:

1.  **Candidate Entry:** A recruiter adds a new candidate to HubSpot.
2.  **Trigger Audit:** The recruiter populates the `github_handle` and optionally the `linkedin_url` properties, then sets the `Audit_Status` to `Pending`.
3.  **Scheduled Execution:** The `talent_scout.py` script runs automatically every day at 08:00 SAST (06:00 UTC) via the GitHub Actions workflow.
4.  **Candidate Discovery:** The script queries HubSpot for all contacts with `Audit_Status` set to "Pending" and a `github_handle`.
5.  **Duplicate Prevention:** Before auditing, the script checks if an "AI Talent Scout" note already exists for the candidate. If so, it skips the audit, updates the status to "Audited", and moves to the next candidate.
6.  **Multi-Platform Audit:** For each new candidate, the script audits their public profiles on both GitHub and LinkedIn.
7.  **Combined Verdict:** The system generates a single, combined verdict (`VERIFIED_BUILDER`, `NUANCED_POTENTIAL`, or `GHOST_DEVELOPER`) based on the signals from both platforms.
8.  **Post Note:** A detailed, formatted note containing the combined verdict, evidence from both platforms, and a final recommendation is posted to the candidate's HubSpot timeline.
9.  **Update Status:** The script updates the candidate's `Audit_Status` property to "Audited".

This cycle ensures that every new candidate is automatically audited across multiple platforms without any further manual intervention, providing the recruiting team with a constant stream of verified, actionable, and duplicate-free intelligence.
