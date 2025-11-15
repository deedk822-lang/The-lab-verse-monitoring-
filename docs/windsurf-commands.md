# Live Control Commands for RankYak Universal Bridge (Windsurf)

These commands are designed to be copy/pasted directly into the Windsurf chat interface for live control of the RankYak Universal Bridge.

## 1. Create WordPress post + trigger full distribution

This command sequence first creates a new post on WordPress.com via the MCP and then triggers the full distribution workflow via the RankYak bridge webhook.

```bash
# Step 1: Create WordPress post and save the permalink
@wpcom-mcp create post title="AI Trends 2025" slug="ai-trends-2025" content="<p>Summary of the week.</p>" status="publish" tags=["AI","trends"]

# Step 2: Trigger the full distribution event
@rankyak-bridge trigger event="api/webhook" data={"title":"AI Trends 2025","slug":"ai-trends-2025","content":"<p>Summary of the week.</p>","platforms":"twitter,linkedin,facebook","includeEmail":true}
```

## 2. Emergency stop (if needed)

Use this command to cancel a running workflow instance. The `<run-id>` must be retrieved from the Inngest dashboard.

```bash
@rankyak-bridge cancel run <run-id>
```

## 3. Check status

These commands provide real-time status updates on the GitHub repository and the RankYak bridge workflow.

```bash
# Check the last commit on the main branch
@github show me the last commit on main

# Check the status of a specific workflow run
@rankyak-bridge show status <run-id>
```
