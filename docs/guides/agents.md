# Agents — Architecture & Runbook

This document describes the agent layout and how to run them locally using docker-compose.

Repository layout (relevant):
- agents/
  - agent_base.py
  - frontend/web_worker.py
  - background/worker.py
  - scheduler/scheduler.py
  - requirements.txt
- docker-compose.agents.yml
- monitoring/prometheus.yml

Quick start (local)
1. Build and start services:
   docker-compose -f docker-compose.agents.yml up --build -d

2. Verify services:
   - Redis: redis-cli -h localhost ping
   - Web API: curl http://localhost:8080/health
   - Background worker metrics: http://localhost:8001/ (Prometheus metrics)
   - Prometheus UI: http://localhost:9090
   - Grafana: http://localhost:3000

3. Enqueue a job:
   curl -XPOST http://localhost:8080/jobs -H "Content-Type: application/json" -d '{"url":"https://httpbin.org/get"}'

4. Check job status:
   curl http://localhost:8080/jobs/<job_id>

Security notes
- Do NOT set ALLOW_EXTERNAL_REQUESTS=yes in production unless you trust the job payload source.
- Provide secrets (if required) via environment variables or a Secrets Manager (Vault/GitHub Secrets).
- Agents expose minimal ports; use network policy / firewall to restrict access.

Deployment recommendations
- Build and push container images from CI (use the same Dockerfiles).
- Deploy agents as Deployments in Kubernetes with liveness/readiness probes (/health).
- Use HorizontalPodAutoscaler based on custom metrics (queue length exported to Prometheus).
- Use Kubernetes CronJob for scheduled tasks if you prefer k8s-native scheduling.

Observability
- Prometheus scrapes /metrics ports configured in monitoring/prometheus.yml
- Grafana dashboards can visualize:
  - queue length
  - job latency (PROCESS_TIME)
  - job success/failure counts
  - resource usage per agent

Troubleshooting
- If jobs are not running: ensure background-worker has connected to Redis and RQ queue name matches.
- If metrics not scraping: check docker-compose service names match Prometheus static_configs.
- If no metrics: ensure agents start_metrics_server(...) on configured ports.

This is a production-ready baseline; extend the job processing functions (agents.background.worker.process_http_job)
to integrate with your internal model calls, cloud APIs, or data stores. Always keep secrets out of the repository.
