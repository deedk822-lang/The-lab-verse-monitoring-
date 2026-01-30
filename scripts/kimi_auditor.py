#!/usr/bin/env python3
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime

import openai

# ========================
# CONFIG
# ========================
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY")
if not MOONSHOT_API_KEY:
    raise ValueError("Set MOONSHOT_API_KEY")

BASE_URL = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1")
MODEL = os.getenv("KIMI_MODEL", "kimi-k2-thinking")
WORKSPACE = os.getenv("WORKSPACE", "/workspace/the-lab-verse")
BASE_BRANCH = os.getenv("BASE_BRANCH", "main")
TARGET_BRANCH = os.getenv("TARGET_BRANCH", "feat/hubspot-ollama-integration-9809589759324023108")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "3600"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))
AUTO_APPROVE = os.getenv("AUTO_APPROVE", "false").lower() == "true"  # Set true for full autonomy
TEST_CMD = os.getenv("TEST_CMD", "pytest")  # e.g., "pytest" or "make test"

client = openai.OpenAI(api_key=MOONSHOT_API_KEY, base_url=BASE_URL)


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] KIMI: {msg}")


def get_diff() -> str:
    os.chdir(WORKSPACE)
    subprocess.run(["git", "pull", "--quiet"], check=False)
    result = subprocess.run(
        ["git", "diff", f"origin/{BASE_BRANCH}...HEAD"], capture_output=True, text=True
    )
    diff = result.stdout
    log(f"Diff size: {len(diff) // 1000}k chars")
    return diff if diff else ""


def run_tests() -> bool:
    log("Running tests...")
    result = subprocess.run(TEST_CMD.split(), capture_output=True, text=True)
    if result.returncode == 0:
        log("Tests passed")
        return True
    log(f"Tests failed:\n{result.stdout[-1000:]}{result.stderr[-1000:]}")
    return False


def run_kimi_analysis(diff: str, error_feedback: str = "") -> str | None:
    feedback = f"\nPrevious attempt failed: {error_feedback}" if error_feedback else ""
    prompt = f"""You are a senior security engineer fixing vulnerabilities in changed code.

DIFF ONLY:
{diff[:12000]}{"..." if len(diff) > 12000 else ""}

{feedback}

Output EXACTLY:

### Findings
Markdown summary (or "NO CRITICAL ISSUES")

### Confidence
High/Medium/Low

### Patch
Unified diff fixing ALL issues, or "NO SAFE FIX POSSIBLE"
```diff
...
```"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=8000,
    )
    return response.choices[0].message.content.strip()


def extract_section(raw: str, header: str) -> str:
    match = re.search(rf"### {header}\n(.*?)(###|$)", raw, re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_patch(raw: str) -> str | None:
    match = re.search(r"```diff\n(.*?)\n```", raw, re.DOTALL)
    return match.group(1).strip() if match else None


def apply_patch(patch: str) -> str:  # Returns error or ""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".patch") as f:
        f.write(patch)
        f.flush()
        check = subprocess.run(["git", "apply", "--check", f.name], capture_output=True)
        if check.returncode != 0:
            return f"Patch rejected: {check.stderr.decode()}"
        subprocess.run(["git", "apply", f.name], check=True)
    return ""


def create_pr(findings: str, confidence: str, applied: bool, iteration: int):
    timestamp = int(time.time())
    branch = f"kimi/fix-{timestamp}-i{iteration}"
    status = "Applied" if applied else "Proposed"

    subprocess.run(["git", "checkout", "-b", branch], check=True)
    if applied:
        subprocess.run(["git", "add", "-A"])
        subprocess.run(
            ["git", "commit", "-m", f"🤖 Kimi auto-fix (iteration {iteration})"], check=True
        )

    subprocess.run(["git", "push", "origin", branch, "--force"], check=True)

    body = f"### Kimi Security Audit (Confidence: {confidence})\n\n{findings}\n\n"
    body += (
        f"Fixes {status.lower()} in iteration {iteration}. Tests: {'Passed' if applied else 'N/A'}"
    )

    title = f"🤖 Kimi Security Fix ({confidence} confidence)"
    labels = "kimi,security,auto-fix"
    if not applied:
        labels += ",needs-review"

    subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--title",
            title,
            "--body",
            body,
            "--base",
            TARGET_BRANCH,
            "--head",
            branch,
            "--label",
            labels,
        ],
        check=True,
    )
    log("PR created")


def main():
    log("Kimi Self-Healing Security Agent v4 Activated")

    while True:
        try:
            diff = get_diff()
            if not diff:
                log("No changes")
                time.sleep(CHECK_INTERVAL)
                continue

            error_feedback = ""
            applied = False
            for i in range(1, MAX_ITERATIONS + 1):
                log(f"Iteration {i}/{MAX_ITERATIONS}")
                raw = run_kimi_analysis(diff, error_feedback)
                findings = extract_section(raw, "Findings")
                confidence = extract_section(raw, "Confidence")
                patch = extract_patch(raw)

                print(f"\n{findings}\nConfidence: {confidence}\n")

                if not patch or "NO SAFE FIX" in raw:
                    log("No safe fix possible")
                    break

                apply_error = apply_patch(patch)
                if apply_error:
                    error_feedback = apply_error
                    subprocess.run(["git", "reset", "--hard", "HEAD"], check=True)  # rollback
                    continue

                if run_tests():
                    applied = True
                    break
                else:
                    error_feedback = "Tests failed after patch"
                    subprocess.run(["git", "reset", "--hard", "HEAD"], check=True)

            confirm = "yes" if AUTO_APPROVE else input("\nCreate PR? (yes/no): ").strip().lower()
            if confirm == "yes":
                create_pr(findings, confidence, applied, i)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            log(f"Error: {e}")
            time.sleep(300)


if __name__ == "__main__":
    main()
