Deploy the VAAL AI Empire backend from this repository/branch:

Repo: https://github.com/deedk822-lang/The-lab-verse-monitoring-.git
Branch: feat/atlassian-jsm-integration-16960019842766473640

Goals:
1) Provision a Linux host (Ubuntu 22.04 recommended) and open ports 22, 80, 443, 8000, 9090.
2) Install Docker + Docker Compose.
3) Clone the repo and run `sudo bash install.sh`.
4) Ensure `.env` is configured with `KIMIAPIKEY` (from the user-provided KIMI_API_KEY).
5) Start the stack and verify:
   - GET /health returns 200
   - POST /api/llm/generate returns a valid response
   - GET /api/usage/stats returns a valid response
6) Validate CLI commands: vaal-dashboard, vaal-logs, vaal-status.

Important:
- The docker-compose stack expects `KIMIAPIKEY` in its environment.
- After install, run the scripts under `scripts/` for automated checks.
