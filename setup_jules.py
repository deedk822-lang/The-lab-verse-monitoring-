#!/usr/bin/env python3
"""Jules Auto-Merge System Setup Script

This script initializes the complete Jules autonomous merge system.
Run this script to set up all necessary configuration files and workflows.

Usage:
    python3 setup_jules.py
"""

import os
import sys

# --- Configuration Content ---
CONFIG_YAML = """version: 2.1

agent:
  name: "Jules-DevOps-Agent"
  repository: "deedk822-lang/The-lab-verse-monitoring-"

automation:
  # Minimum confidence score (0-100) required for auto-merge
  min_confidence_score: 85
  
  # Maximum number of files changed before human review is forced
  max_file_churn: 15
  
  # Automatically attempt to rebase branches that are behind main
  auto_rebase: true

protected_paths:
  # Regex patterns for sensitive areas (Modifying these = Automatic Block)
  - "^config/"
  - "^scripts/setup-"
  - "docker-compose.*\\\\.yml$"
  - "^\\\\.github/workflows/"
  - "requirements.*\\\\.txt$"
  - "package.*\\\\.json$"

scoring:
  # Points deducted from 100
  todo_comment_penalty: 10
  console_log_penalty: 5
  large_pr_penalty: 20  # Applied if > 500 lines changed
"""

AGENTS_MD = """# 🤖 Jules Protocol & Directives

## 🧠 Agent Identity

**Jules** is the autonomous DevOps guardian for the `deedk822-lang` ecosystem.

**Role:** Guardian of Main Branch Integrity.

## 🎮 Human Interaction (ChatOps)

Humans can control Jules by commenting on Pull Requests:

| Command | Action |
|---------|--------|
| `@jules merge` | **Override:** Force merge (Bypasses confidence checks). |
| `@jules rebase` | **Heal:** Updates the PR branch with latest `main` changes. |
| `@jules report` | **Analyze:** Re-runs the confidence assessment. |
| `@jules pause` | **Emergency:** Blocks all automation on the specific PR. |

## ⛔ Immediate Stop Conditions

Jules will **block auto-merge** if:

1. **Protected Path Modified:** Any change to `.github/`, `config/`, or infrastructure.
2. **Confidence < 85%:** Code smell detection (TODOs, console logs, large diffs).
3. **Merge Conflicts:** Standard git conflicts.

## 🟢 Success Criteria (Auto-Merge)

1. Status Checks: ✅ **Pass**
2. Confidence Score: 📊 **>= 85**
3. Protected Paths: 🛡️ **Untouched**
"""

# --- File Generation Logic ---
def create_file(path, content):
    """Create a file with the given content, creating directories as needed."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created: {path}")

def main():
    """Main setup function."""
    print("🤖 Initializing Jules Agent Structure...")
    print("="*50)
    
    try:
        # Check if we're in a git repository
        if not os.path.exists('.git'):
            print("❌ Error: Not in a git repository root!")
            print("   Please run this script from the repository root.")
            sys.exit(1)
        
        # Create all files
        create_file(".jules/config.yml", CONFIG_YAML)
        create_file("AGENTS.md", AGENTS_MD)
        create_file(".jules/logs/.gitkeep", "")
        
        print("="*50)
        print("\n🎉 Jules setup complete!")
        print("\n📋 Next steps:")
        print("   1. Review generated files")
        print("   2. Run: git status")
        print("   3. Run: git add .jules/ AGENTS.md")
        print("   4. Run: git commit -m 'feat: add Jules auto-merge system'")
        print("   5. Run: git push")
        print("\n⚠️  Don't forget to:")
        print("   - Set up branch protection rules in GitHub")
        print("   - Enable workflow permissions (read and write)")
        print("   - Review AGENTS.md for protocol details")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
