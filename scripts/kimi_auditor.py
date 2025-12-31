#!/usr/bin/env python3
import os
import subprocess
import time
from datetime import datetime
import openai
import tempfile

# ========================
# CONFIG (Env Vars)
# ========================
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY")
if not MOONSHOT_API_KEY:
    raise ValueError("Set MOONSHOT_API_KEY")

BASE_URL = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1")  # .ai global / .cn China
MODEL = os.getenv("KIMI_MODEL", "kimi-k2-thinking")  # 2025 flagship reasoning model
WORKSPACE = os.getenv("WORKSPACE", ".")
BASE_BRANCH = os.getenv("BASE_BRANCH", "main")
TARGET_BRANCH = os.getenv("TARGET_BRANCH", "HEAD")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "3600"))

client = openai.OpenAI(api_key=MOONSHOT_API_KEY, base_url=BASE_URL)

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] KIMI: {msg}")

def get_changed_files() -> list[str]:
    os.chdir(WORKSPACE)
    subprocess.run(["git", "pull", "--quiet"], check=False)
    result = subprocess.run(
        ["git", "diff", "--name-only", f"origin/{BASE_BRANCH}...{TARGET_BRANCH}"],
        capture_output=True, text=True
    )
    files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    log(f"Detected {len(files)} changed files")
    return files

def build_context(files: list[str]) -> str:
    context = ""
    for file_path in files[:8]:  # Balanced for context length
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            context += f"\n\n=== {file_path} ===\n{content[:5000]}"
    return context

def run_kimi_analysis(context: str) -> str | None:
    if not context:
        return None

    prompt = f"""You are a senior security auditor for The Lab Verse project.
Analyze changed files for CRITICAL/HIGH security vulnerabilities ONLY.

{context}

Output EXACTLY in this format:

### Findings
Markdown list of issues (or "NO CRITICAL ISSUES")

### Proposed Fix
If safe auto-fixes possible: a COMPLETE unified diff patch fixing ALL issues.
\`\`\`diff
diff --git a/file.py b/file.py
...
\`\`\`

If no safe fixes: "NO SAFE AUTO-FIX POSSIBLE"
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,  # Deterministic for patches
        max_tokens=8000
    )
    return response.choices[0].message.content.strip()

def extract_patch(raw: str) -> str | None:
    if "```diff" not in raw:
        return None
    start = raw.find("```diff") + 7
    end = raw.find("```", start)
    return raw[start:end].strip() if end != -1 else None

def apply_patch(patch: str) -> bool:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
        f.write(patch)
        patch_file = f.name

    check = subprocess.run(["git", "apply", "--check", patch_file], capture_output=True)
    os.unlink(patch_file)

    if check.returncode != 0:
        log("Patch check failed (conflicts or invalid)")
        return False

    subprocess.run(["git", "apply", patch_file], check=True)
    return True

def create_fix_branch_and_pr(findings_md: str, applied: bool):
    timestamp = int(time.time())
    branch = f"kimi/fix-{timestamp}"

    subprocess.run(["git", "checkout", "-b", branch], check=True)
    if applied:
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(["git", "commit", "-m", "🤖 Kimi auto-fix: security vulnerabilities"], check=True)

    subprocess.run(["git", "push", "origin", branch, "--force"], check=True)

    title = "🤖 Kimi Security Fixes (Auto-Applied)" if applied else "🤖 Kimi Security Audit (Review Needed)"
    body = f"Automated audit on {TARGET_BRANCH}:\n\n{findings_md}\n\n{'Fixes auto-applied — please review!' if applied else 'No safe auto-fix — manual review required.'}"

    pr_cmd = ["gh", "pr", "create", "--title", title, "--body", body,
              "--base", TARGET_BRANCH, "--head", branch,
              "--label", "kimi,security,auto-fix"]

    result = subprocess.run(pr_cmd, capture_output=True, text=True)
    if result.returncode == 0:
        log(f"✅ PR created: {result.stdout.strip()}")
    else:
        log(f"❌ PR failed: {result.stderr.strip()}")

def main():
    log("🚀 Kimi Autonomous Security Auditor v3 Activated (with Fix Automation)")
    log(f"Monitoring vs origin/{BASE_BRANCH}")

    files = get_changed_files()
    if not files:
        log("No changes")
        return

    context = build_context(files)
    raw = run_kimi_analysis(context)

    if not raw:
        log("No analysis")
        return

    findings_start = raw.find("### Findings")
    findings_md = raw[findings_start:].split("### Proposed Fix")[0].strip() if findings_start != -1 else "Parse failed"

    log("🔍 Analysis complete")
    print(findings_md)

    patch = extract_patch(raw)
    if patch and "NO SAFE AUTO-FIX" not in raw:
        log("✅ Safe patch generated")
        confirm = os.getenv("AUTO_FIX", "false").lower()
        if confirm == "true":
            applied = apply_patch(patch)
            create_fix_branch_and_pr(findings_md, applied)
        else:
            create_fix_branch_and_pr(findings_md, False)
    else:
        log("No auto-fix possible")
        create_fix_branch_and_pr(findings_md, False)

if __name__ == "__main__":
    main()
