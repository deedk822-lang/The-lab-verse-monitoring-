---
description: Run a full system diagnostic
argument-hint: [service-to-check]
allowed-tools: ["mcp__plugin_dev-ops-suite_system-doctor__*", "Bash"]
---

# 🩺 Initializing System Doctor...

$IF($1,
  User reported issue with: $1.
  1. Initialize `system-doctor` agent.
  2. Check status of $1 service specifically.
  3. Check system resource usage.
  ,
  1. Initialize `system-doctor` agent.
  2. Perform full system health scan (CPU, Memory, Disk).
  3. Check Docker status default.
)

Report findings immediately.
