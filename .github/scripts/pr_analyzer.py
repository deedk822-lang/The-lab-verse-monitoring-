import os
import re
import sys

# Read the list of changed files from standard input
changed_files = [line.strip() for line in sys.stdin if line.strip()]

# Define the protected paths from AGENTS.md
protected_paths = [
    "config/",
    "scripts/setup-",
    "docker-compose.yml",
    ".github/workflows/",
    "requirements.txt",
    "package.json",
]

# Initialize scoring variables
confidence_score = 100
deduction_reasons = []
protected_paths_found = []

# Check for modifications in protected paths
for file_path in changed_files:
    for protected in protected_paths:
        if file_path.startswith(protected):
            protected_paths_found.append(file_path)
            break

if protected_paths_found:
    confidence_score = 0  # A single protected path violation fails the check
    deduction_reasons.append(
        "Critical error: Modified protected paths. Manual review required."
    )

# Score deductions for code smells, but only if no protected paths were modified
if not protected_paths_found:
    # Rule: Large PR (>15 files)
    if len(changed_files) > 15:
        confidence_score -= 20
        deduction_reasons.append(
            f"(-20) Large pull request: {len(changed_files)} files changed (max is 15)."
        )

    # Rule: Check for TODOs and console.logs in each file's content
    for file_path in changed_files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                # Rule: TODO/FIXME comments (case-insensitive)
                if re.search(r"\b(TODO|FIXME)\b", content, re.IGNORECASE):
                    confidence_score -= 10
                    deduction_reasons.append(
                        f"(-10) TODO/FIXME found in '{file_path}'."
                    )
                # Rule: console.log statements (check for console.log(...))
                if re.search(r"\bconsole\.log\s*\(", content):
                    confidence_score -= 5
                    deduction_reasons.append(
                        f"(-5) `console.log` statement found in '{file_path}'."
                    )
        except FileNotFoundError:
            # The file might have been deleted in the PR, which is fine.
            # No points are deducted in this case.
            pass

# --- Output the results ---
print(f"Jules Governance Analysis")
print(f"-------------------------")
print(f"Confidence Score: {confidence_score}/100")

if deduction_reasons:
    print("\nScore Deductions:")
    for reason in deduction_reasons:
        print(f"- {reason}")

if protected_paths_found:
    print("\nProtected Paths Modified:")
    for path in protected_paths_found:
        print(f"- {path}")

# Exit with a non-zero status code if the score is below the threshold
# This will cause the GitHub Actions step to fail
if confidence_score < 85 or protected_paths_found:
    print("\nConclusion: 🔴 Automated approval failed. Please review the issues.")
    sys.exit(1)
else:
    print("\nConclusion: 🟢 Looks good! Automated checks passed.")
