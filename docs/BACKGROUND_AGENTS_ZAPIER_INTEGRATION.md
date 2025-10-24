# 🤖 Background Agents to Zapier Integration Guide

## Overview

This guide explains how to connect your Lab-Verse background agents to Zapier for automated workflow orchestration. Your system already has sophisticated AI orchestration capabilities, and this guide shows how to extend them to work with Zapier's automation platform.

## 🏗️ Current Architecture

Your system includes:
- **Background Agents**: Located in `lab_verse/` directory with orchestrator and agent management
- **AI Orchestration**: n8n workflows for intelligent model selection and routing
- **Zapier Integration**: GitHub Actions webhook that triggers Zapier workflows
- **Monitoring**: Prometheus and Grafana for system observability

## 🔗 Integration Methods

### Method 1: Direct Webhook Integration (Recommended)

Create a webhook endpoint that background agents can call to trigger Zapier workflows directly.

#### Step 1: Create Background Agent Webhook Endpoint

```javascript
// src/routes/backgroundAgentWebhook.js
import express from 'express';
import axios from 'axios';
import logger from '../utils/logger.js';

const router = express.Router();

// Webhook endpoint for background agents to trigger Zapier
router.post('/background-agent-webhook', async (req, res) => {
  try {
    const { 
      agentId, 
      action, 
      data, 
      priority = 'normal',
      zapierWebhookUrl 
    } = req.body;

    // Validate required fields
    if (!agentId || !action || !data) {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'agentId, action, and data are required'
      });
    }

    // Prepare payload for Zapier
    const zapierPayload = {
      agent_id: agentId,
      action: action,
      data: data,
      priority: priority,
      timestamp: new Date().toISOString(),
      source: 'background_agent',
      metadata: {
        processing_time: Date.now(),
        agent_version: process.env.AGENT_VERSION || '1.0.0'
      }
    };

    // Send to Zapier webhook
    const zapierResponse = await axios.post(zapierWebhookUrl, zapierPayload, {
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Lab-Verse-Background-Agent/1.0'
      },
      timeout: 10000
    });

    logger.info('Background agent webhook triggered successfully', {
      agentId,
      action,
      zapierStatus: zapierResponse.status
    });

    res.json({
      success: true,
      message: 'Background agent webhook triggered successfully',
      zapier_response: zapierResponse.data,
      agent_id: agentId
    });

  } catch (error) {
    logger.error('Background agent webhook failed', {
      error: error.message,
      agentId: req.body.agentId,
      action: req.body.action
    });

    res.status(500).json({
      success: false,
      error: 'Failed to trigger Zapier webhook',
      message: error.message
    });
  }
});

export default router;
```

#### Step 2: Update Background Agent to Use Webhook

```python
# lab_verse/agents.py
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("background_agent")

class BackgroundAgent:
    def __init__(self, agent_id: str, zapier_webhook_url: str):
        self.agent_id = agent_id
        self.zapier_webhook_url = zapier_webhook_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def trigger_zapier_workflow(self, action: str, data: Dict[Any, Any], priority: str = "normal"):
        """Trigger a Zapier workflow from background agent"""
        try:
            payload = {
                "agent_id": self.agent_id,
                "action": action,
                "data": data,
                "priority": priority,
                "timestamp": asyncio.get_event_loop().time(),
                "source": "background_agent"
            }

            async with self.session.post(
                self.zapier_webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Zapier workflow triggered successfully: {action}")
                    return result
                else:
                    logger.error(f"Failed to trigger Zapier workflow: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error triggering Zapier workflow: {e}")
            return None

    async def process_and_trigger(self, task_data: Dict[Any, Any]):
        """Process task and trigger appropriate Zapier workflow"""
        # Your background processing logic here
        processed_data = await self.process_task(task_data)
        
        # Determine action based on processing results
        if processed_data.get("requires_ai_processing"):
            action = "ai_content_generation"
        elif processed_data.get("requires_notification"):
            action = "send_notification"
        elif processed_data.get("requires_data_sync"):
            action = "sync_data"
        else:
            action = "general_processing"

        # Trigger Zapier workflow
        return await self.trigger_zapier_workflow(action, processed_data)

    async def process_task(self, task_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """Your background task processing logic"""
        # Implement your specific background processing here
        return task_data

# Updated Swarm class to use background agents
class Swarm:
    def __init__(self, zapier_webhook_url: str):
        self.zapier_webhook_url = zapier_webhook_url
        self.agents = []

    async def run(self):
        """Run swarm with Zapier integration"""
        print("Swarm is running with Zapier integration...")
        
        # Create background agents
        async with BackgroundAgent("swarm_agent_1", self.zapier_webhook_url) as agent:
            # Process tasks and trigger Zapier workflows
            result = await agent.process_and_trigger({"task": "example"})
            
        await asyncio.sleep(1)
        return {"result": "success", "zapier_triggered": True}

async def launch_swarm(cfg):
    zapier_webhook_url = cfg.get("zapier_webhook_url", "http://localhost:3000/api/background-agent-webhook")
    return Swarm(zapier_webhook_url)
```

### Method 2: n8n Workflow Integration

Extend your existing n8n workflows to handle background agent triggers.

#### Step 1: Create Background Agent n8n Workflow

```json
{
  "meta": {
    "instanceId": "background-agent-zapier-integration"
  },
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "background-agent-trigger",
        "options": {
          "rawBody": true
        }
      },
      "id": "background-agent-webhook",
      "name": "Background Agent Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 2,
      "position": [240, 300]
    },
    {
      "parameters": {
        "mode": "runOnceForAllItems",
        "jsCode": "const input = $input.first().json;\nconst agentId = input.agent_id;\nconst action = input.action;\nconst data = input.data;\nconst priority = input.priority || 'normal';\n\n// Route to appropriate Zapier webhook based on action\nlet zapierWebhookUrl = '';\n\nswitch (action) {\n  case 'ai_content_generation':\n    zapierWebhookUrl = 'https://hooks.zapier.com/hooks/catch/24571038/uio32zw/';\n    break;\n  case 'send_notification':\n    zapierWebhookUrl = 'https://hooks.zapier.com/hooks/catch/24571038/notification/';\n    break;\n  case 'sync_data':\n    zapierWebhookUrl = 'https://hooks.zapier.com/hooks/catch/24571038/sync/';\n    break;\n  default:\n    zapierWebhookUrl = 'https://hooks.zapier.com/hooks/catch/24571038/general/';\n}\n\nreturn [{\n  json: {\n    ...input,\n    zapier_webhook_url: zapierWebhookUrl,\n    processed_at: new Date().toISOString()\n  }\n}];"
      },
      "id": "action-router",
      "name": "Action Router",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [460, 300]
    },
    {
      "parameters": {
        "url": "={{ $json.zapier_webhook_url }}",
        "sendBody": true,
        "specifyHeaders": true,
        "headers": {
          "parameters": [
            {
              "name": "Content-Type",
              "value": "application/json"
            },
            {
              "name": "User-Agent",
              "value": "Lab-Verse-Background-Agent/1.0"
            }
          ]
        },
        "bodyParametersUi": {
          "parameter": [
            {
              "name": "agent_id",
              "value": "={{ $json.agent_id }}"
            },
            {
              "name": "action",
              "value": "={{ $json.action }}"
            },
            {
              "name": "data",
              "value": "={{ $json.data }}"
            },
            {
              "name": "priority",
              "value": "={{ $json.priority }}"
            },
            {
              "name": "timestamp",
              "value": "={{ $json.timestamp }}"
            }
          ]
        },
        "options": {
          "response": {
            "response": {
              "neverError": true,
              "responseFormat": "json"
            }
          },
          "timeout": 30000
        }
      },
      "id": "zapier-webhook",
      "name": "Zapier Webhook",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [680, 300]
    }
  ],
  "connections": {
    "Background Agent Webhook": {
      "main": [
        [
          {
            "node": "Action Router",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Action Router": {
      "main": [
        [
          {
            "node": "Zapier Webhook",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

### Method 3: Event-Driven Integration

Use your existing monitoring system to trigger Zapier workflows based on agent events.

#### Step 1: Create Event Listener

```javascript
// src/services/backgroundAgentEventService.js
import EventEmitter from 'events';
import axios from 'axios';
import logger from '../utils/logger.js';

class BackgroundAgentEventService extends EventEmitter {
  constructor() {
    super();
    this.zapierWebhooks = {
      'agent.completed': 'https://hooks.zapier.com/hooks/catch/24571038/completed/',
      'agent.error': 'https://hooks.zapier.com/hooks/catch/24571038/error/',
      'agent.started': 'https://hooks.zapier.com/hooks/catch/24571038/started/',
      'agent.data_processed': 'https://hooks.zapier.com/hooks/catch/24571038/processed/'
    };
    
    this.setupEventHandlers();
  }

  setupEventHandlers() {
    this.on('agent.completed', this.handleAgentCompleted.bind(this));
    this.on('agent.error', this.handleAgentError.bind(this));
    this.on('agent.started', this.handleAgentStarted.bind(this));
    this.on('agent.data_processed', this.handleDataProcessed.bind(this));
  }

  async handleAgentCompleted(data) {
    await this.triggerZapierWebhook('agent.completed', {
      agent_id: data.agentId,
      status: 'completed',
      result: data.result,
      processing_time: data.processingTime,
      timestamp: new Date().toISOString()
    });
  }

  async handleAgentError(data) {
    await this.triggerZapierWebhook('agent.error', {
      agent_id: data.agentId,
      status: 'error',
      error: data.error,
      timestamp: new Date().toISOString()
    });
  }

  async handleAgentStarted(data) {
    await this.triggerZapierWebhook('agent.started', {
      agent_id: data.agentId,
      status: 'started',
      task: data.task,
      timestamp: new Date().toISOString()
    });
  }

  async handleDataProcessed(data) {
    await this.triggerZapierWebhook('agent.data_processed', {
      agent_id: data.agentId,
      status: 'data_processed',
      data_size: data.dataSize,
      processing_time: data.processingTime,
      timestamp: new Date().toISOString()
    });
  }

  async triggerZapierWebhook(eventType, payload) {
    try {
      const webhookUrl = this.zapierWebhooks[eventType];
      if (!webhookUrl) {
        logger.warn(`No Zapier webhook configured for event: ${eventType}`);
        return;
      }

      const response = await axios.post(webhookUrl, payload, {
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'Lab-Verse-Background-Agent/1.0'
        },
        timeout: 10000
      });

      logger.info(`Zapier webhook triggered for ${eventType}`, {
        status: response.status,
        agent_id: payload.agent_id
      });

    } catch (error) {
      logger.error(`Failed to trigger Zapier webhook for ${eventType}`, {
        error: error.message,
        agent_id: payload.agent_id
      });
    }
  }
}

export default new BackgroundAgentEventService();
```

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Background Agent Zapier Integration
ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/24571038/uio32zw/
ZAPIER_AI_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/24571038/ai/
ZAPIER_NOTIFICATION_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/24571038/notification/
ZAPIER_SYNC_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/24571038/sync/

# Background Agent Settings
AGENT_VERSION=1.0.0
BACKGROUND_AGENT_ENABLED=true
ZAPIER_INTEGRATION_ENABLED=true
```

### Update Docker Compose

Add the background agent service to your `docker-compose.yml`:

```yaml
services:
  background-agent:
    build: .
    command: python -m lab_verse.orchestrator
    environment:
      - ZAPIER_WEBHOOK_URL=${ZAPIER_WEBHOOK_URL}
      - ZAPIER_INTEGRATION_ENABLED=${ZAPIER_INTEGRATION_ENABLED}
      - AGENT_VERSION=${AGENT_VERSION}
    depends_on:
      - n8n
      - postgres
    volumes:
      - ./lab_verse:/app/lab_verse
      - ./config:/app/config
    networks:
      - lab-verse-network
```

## 📊 Monitoring and Analytics

### Prometheus Metrics

Add these metrics to track background agent to Zapier integration:

```javascript
// src/metrics/backgroundAgentMetrics.js
import { register, Counter, Histogram, Gauge } from 'prom-client';

const backgroundAgentRequests = new Counter({
  name: 'background_agent_zapier_requests_total',
  help: 'Total number of background agent requests to Zapier',
  labelNames: ['agent_id', 'action', 'status']
});

const backgroundAgentResponseTime = new Histogram({
  name: 'background_agent_zapier_response_time_seconds',
  help: 'Response time for background agent Zapier requests',
  labelNames: ['agent_id', 'action']
});

const backgroundAgentErrors = new Counter({
  name: 'background_agent_zapier_errors_total',
  help: 'Total number of background agent Zapier errors',
  labelNames: ['agent_id', 'error_type']
});

const activeBackgroundAgents = new Gauge({
  name: 'background_agents_active',
  help: 'Number of active background agents',
  labelNames: ['agent_type']
});

export {
  backgroundAgentRequests,
  backgroundAgentResponseTime,
  backgroundAgentErrors,
  activeBackgroundAgents
};
```

### Grafana Dashboard

Create a Grafana dashboard to monitor background agent to Zapier integration:

```json
{
  "dashboard": {
    "title": "Background Agents Zapier Integration",
    "panels": [
      {
        "title": "Background Agent Requests to Zapier",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(background_agent_zapier_requests_total[5m])",
            "legendFormat": "{{agent_id}} - {{action}}"
          }
        ]
      },
      {
        "title": "Background Agent Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(background_agent_zapier_response_time_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Background Agent Errors",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(background_agent_zapier_errors_total[5m])",
            "legendFormat": "{{agent_id}} - {{error_type}}"
          }
        ]
      }
    ]
  }
}
```

## 🚀 Usage Examples

### Example 1: AI Content Generation

```python
# Background agent triggers AI content generation via Zapier
async def generate_content_workflow():
    async with BackgroundAgent("content_agent", ZAPIER_WEBHOOK_URL) as agent:
        # Process content request
        content_data = {
            "topic": "AI and Machine Learning",
            "target_audience": "developers",
            "content_type": "blog_post",
            "word_count": 1000
        }
        
        # Trigger Zapier workflow for AI content generation
        result = await agent.trigger_zapier_workflow(
            action="ai_content_generation",
            data=content_data,
            priority="high"
        )
        
        return result
```

### Example 2: Data Synchronization

```python
# Background agent triggers data sync via Zapier
async def sync_data_workflow():
    async with BackgroundAgent("sync_agent", ZAPIER_WEBHOOK_URL) as agent:
        # Process sync request
        sync_data = {
            "source": "database",
            "destination": "external_api",
            "data_type": "user_profiles",
            "batch_size": 100
        }
        
        # Trigger Zapier workflow for data synchronization
        result = await agent.trigger_zapier_workflow(
            action="sync_data",
            data=sync_data,
            priority="normal"
        )
        
        return result
```

### Example 3: Notification System

```python
# Background agent triggers notifications via Zapier
async def notification_workflow():
    async with BackgroundAgent("notification_agent", ZAPIER_WEBHOOK_URL) as agent:
        # Process notification request
        notification_data = {
            "recipients": ["user@example.com"],
            "message": "Your background task has completed",
            "notification_type": "email",
            "priority": "normal"
        }
        
        # Trigger Zapier workflow for notifications
        result = await agent.trigger_zapier_workflow(
            action="send_notification",
            data=notification_data,
            priority="normal"
        )
        
        return result
```

## 🔒 Security Considerations

1. **Webhook Authentication**: Use webhook secrets to authenticate requests
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **Data Validation**: Validate all data before sending to Zapier
4. **Error Handling**: Implement proper error handling and retry logic
5. **Monitoring**: Monitor all webhook calls for security issues

## 🧪 Testing

### Test Background Agent Integration

```bash
# Test background agent webhook
curl -X POST http://localhost:3000/api/background-agent-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test_agent",
    "action": "ai_content_generation",
    "data": {"topic": "test", "content": "test content"},
    "priority": "normal"
  }'
```

### Test n8n Workflow

```bash
# Test n8n background agent workflow
curl -X POST http://localhost:5678/webhook/background-agent-trigger \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test_agent",
    "action": "ai_content_generation",
    "data": {"topic": "test", "content": "test content"},
    "priority": "normal"
  }'
```

## 📝 Next Steps

1. **Choose Integration Method**: Select the method that best fits your needs
2. **Set Up Zapier Workflows**: Create corresponding workflows in Zapier
3. **Configure Webhooks**: Set up webhook URLs and authentication
4. **Test Integration**: Test the complete flow from background agents to Zapier
5. **Monitor Performance**: Set up monitoring and alerting
6. **Scale**: Optimize and scale based on usage patterns

## 🤝 Support

For questions or issues with background agent to Zapier integration:

- **Issues**: [GitHub Issues](https://github.com/deedk822-lang/The-lab-verse-monitoring-/issues)
- **Discussions**: [GitHub Discussions](https://github.com/deedk822-lang/The-lab-verse-monitoring-/discussions)
- **Documentation**: Check the `/docs` directory for detailed guides

---

**Built with ❤️ for the Lab-Verse community**