# Production Checklist – RankYak Universal Bridge

This document is the single source of truth for the RankYak → GitHub → WordPress → Asana + 28-platform bridge with Windsurf MCP control.

## Final, Production-Ready Checklist

| Step                | Status | Command / URL                                                                    | Notes                                     |
| :------------------ | :----- | :------------------------------------------------------------------------------- | :---------------------------------------- |
| 1. Vercel Deploy    | ✅     | `curl -sSL https://raw.githubusercontent.com/rankyak/one-click-bridge/main/deploy.sh` | One-liner deploys `api/webhook.js` + deps |
| 2. Webhook URL      | ✅     | `https://<name>.vercel.app/api/inngest`                                          | Copy from `vercel ls`                     |
| 3. RankYak Webhook  | ✅     | Settings → Integrations → Webhooks                                               | Paste URL + secret                        |
| 4. WordPress.com MCP| ✅     | `@wpcom-mcp connect`                                                             | OAuth in Windsurf chat                    |
| 5. GitHub MCP       | ✅     | `@github connect`                                                                | OAuth in Windsurf chat                    |
| 6. Inngest Workflow | ✅     | `npx inngest-cli@latest dev`                                                     | Local dashboard at `http://localhost:8288`  |
| 7. Grafana Embed    | ✅     | `app/dashboard/page.tsx`                                                         | Iframe to `https://dimakatsomoleli.grafana.net` |
| 8. Secrets Audit    | ✅     | Remove manual WP credentials                                                     | Keep only OAuth + bridge secrets          |
| 9. Test Pipeline    | ✅     | One-liner in Windsurf chat                                                       | See below                                 |
| 10. Live Commands   | ✅     | Saved in repo `docs/windsurf-commands.md`                                        | Copy/paste library                        |

## Quick Health Check

The following `curl` command can be used to perform a quick health check on the Inngest webhook endpoint.

```bash
curl -X POST https://<your-vercel-host>/api/inngest \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: $(gh secret get RANKYAK_WEBHOOK_SECRET)" \
  -d '{"title": "Health Check", "slug": "health-check", "content": "<p>OK</p>", "tags": ["test"]}'
