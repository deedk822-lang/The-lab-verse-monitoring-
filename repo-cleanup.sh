#!/bin/bash
# Renames files with spaces and organizes the repository structure
set -e

echo "🧹 Starting Repository Organization..."

# 1. Create Standard Directories
mkdir -p docs/snippets docs/guides docs/archive scripts/legacy docs/concepts docs/examples

# 2. Fix "Bad" Filenames (Copy-paste artifacts)
# We move these to docs/snippets or scripts/legacy and rename them to be safe.

move_and_rename() {
    if [ -f "$1" ]; then
        echo "Moving '$1' -> '$2'"
        mv "$1" "$2"
    fi
}

# Documentation/Notes Artifacts
move_and_rename "Action (ci) snippet" "docs/snippets/ci-action.txt"
move_and_rename "Browser_automation and web_search" "docs/guides/browser-automation.md"
move_and_rename "Complete Deployment ConfigurationCode " "docs/guides/deployment-config.md"
move_and_rename "Configure connector  .env" "docs/snippets/connector-env-setup.md"
move_and_rename "cp .env.example .env" "docs/snippets/env-setup-command.md"
move_and_rename "Create the API routes in your Next.js app" "docs/guides/nextjs-api-routes.md"
move_and_rename "Docker compose YAML" "docs/snippets/docker-compose-example.yaml"
move_and_rename "Fallback_chain" "docs/concepts/fallback-chain.md"
move_and_rename "git init" "docs/snippets/git-init-note.md"
move_and_rename "Groq_voice" "docs/concepts/groq-voice.md"
move_and_rename "Improved HuggingFace Gateway with Retry Logic " "docs/concepts/hf-gateway-logic.md"
move_and_rename "MCP Gateway Test SuiteCode " "docs/snippets/mcp-gateway-test.md"
move_and_rename "Mistral-yalm" "docs/snippets/mistral-config.yaml"
move_and_rename "MPC+connector" "docs/concepts/mpc-connector.md"
move_and_rename "Python. venv" "docs/snippets/python-venv-setup.md"
move_and_rename "Re run validation script" "docs/snippets/rerun-validation-note.md"
move_and_rename "Routes utility" "docs/concepts/routes-utility.md"
move_and_rename "Script's" "docs/archive/scripts-notes.md"
move_and_rename "Smoke test" "docs/guides/smoke-testing.md"
move_and_rename "Start MCP server" "docs/guides/start-mcp.md"
move_and_rename "start LOCALAI" "docs/guides/start-localai.md"
move_and_rename "Test scripts end to end" "docs/guides/e2e-testing.md"
move_and_rename "TS example" "docs/examples/typescript-example.ts"
move_and_rename "Untitled File 2025-12-02 02_34_59.py" "scripts/legacy/untitled_script_20251202.py"
move_and_rename "Use Groq in Main Gateway" "docs/guides/groq-gateway.md"

# 3. Consolidate Documentation
if [ -d "doc" ]; then
    echo "Merging 'doc/' into 'docs/'..."
    cp -r doc/* docs/ 2>/dev/null || true
    rm -rf doc
fi

# 4. Cleanup Root Scripts (Move to scripts/ folder)
# We exclude critical root files like package.json, docker-compose.yml
for file in *.sh *.py *.js; do
    # Skip specific config files or entry points that MUST be in root
    if [[ "$file" == "package.json" ]] || \
       [[ "$file" == "docker-compose.yml" ]] || \
       [[ "$file" == "Dockerfile" ]] || \
       [[ "$file" == "next.config.js" ]] || \
       [[ "$file" == "tailwind.config.ts" ]] || \
       [[ "$file" == "tsconfig.json" ]] || \
       [[ "$file" == "vercel.json" ]] || \
       [[ "$file" == "security-cleanup.sh" ]] || \
       [[ "$file" == "repo-cleanup.sh" ]]; then
        continue
    fi

    # Move Python scripts to scripts/python
    if [[ "$file" == *.py ]]; then
        mkdir -p scripts/python
        mv "$file" "scripts/python/$file"
    fi

    # Move Shell scripts to scripts/shell
    if [[ "$file" == *.sh ]]; then
        mkdir -p scripts/shell
        mv "$file" "scripts/shell/$file"
    fi

    # Move JS scripts (if they look like utilities) to scripts/js
    if [[ "$file" == *.js ]] && [[ "$file" != "next.config.js" ]] && [[ "$file" != "postcss.config.js" ]]; then
        mkdir -p scripts/js
        mv "$file" "scripts/js/$file"
    fi
done

# 5. Consolidate Duplicate Readmes/Guides
mkdir -p docs/deployment docs/reports docs/guides
mv DEPLOYMENT_*.md docs/deployment/ 2>/dev/null || true
mv *_REPORT.md docs/reports/ 2>/dev/null || true
mv *_SUMMARY.md docs/reports/ 2>/dev/null || true
mv *_GUIDE.md docs/guides/ 2>/dev/null || true
mv QUICKSTART*.md docs/guides/ 2>/dev/null || true

echo "✅ Repository organization complete. Structure is now clean."
