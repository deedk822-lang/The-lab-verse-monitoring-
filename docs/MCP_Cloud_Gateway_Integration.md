# MCP Cloud Gateway Integration

## Overview
This API integrates with **CData MCP Cloud** at `https://mcp.cloud.cdata.com/mcp` for
enterprise-grade service routing.

## Supported Services
1.  **HuggingFace** - AI model discovery and deployment
2.  **SocialPilot** - Social media management
3.  **Unito** - Task synchronization
4.  **WordPress.com** - Content publishing

## Setup

### 1. Sign up for CData MCP Cloud
Visit: https://mcp.cloud.cdata.com

### 2. Configure Services
In the CData Console:
- Add HuggingFace server (paste `HF_API_TOKEN`)
- Add SocialPilot server (paste `SOCIALPILOT_ACCESS_TOKEN`)
- Add Unito server (paste `UNITO_ACCESS_TOKEN`)
- Add WordPress.com server (paste `WORDPRESS_COM_OAUTH_TOKEN`)

### 3. Get Your API Key
Copy your MCP Gateway API key from the Console.

### 4. Update Environment
The following variables should be added to your `.env` file:
```env
MCP_GATEWAY_URL=https://mcp.cloud.cdata.com/mcp
CDATA_MCP_API_KEY=mcpc_your_actual_key_here
MCP_TENANT_ID=your_tenant_id
MCP_API_PORT=8001
```

### 5. Deploy
The MCP Gateway runs as a separate Python service. You can start it using uvicorn:
```bash
cd src/mcp_api
source ../../venv_mcp/bin/activate
uvicorn main:app --host 0.0.0.0 --port $MCP_API_PORT
```

## API Endpoints

### Generic MCP Call
```bash
POST /mcp/call
Content-Type: application/json
X-API-Key: your-api-key
{
"service": "huggingface",
"tool": "list_models",
"arguments": {}
}
```

### HuggingFace - Search Models
```bash
POST /mcp/huggingface/search
X-API-Key: your-api-key
{
"query": "text-generation",
"limit": 10
}
```

### SocialPilot - Post to Social Media
```bash
POST /mcp/socialpilot/post
X-API-Key: your-api-key
{
"content": "Check out our new AI API!",
"platforms": ["twitter", "linkedin"],
"schedule_time": "2024-12-01T10:00:00Z"
}
```

### Unito - Sync Tasks
```bash
POST /mcp/unito/sync
X-API-Key: your-api-key
{
"source": "asana",
"destination": "jira",
"filters": {"project": "Engineering"}
}
```

### WordPress - Publish Post
```bash
POST /mcp/wordpress/post
X-API-Key: your-api-key
{
"title": "New Blog Post",
"content": "This is the content of the post.",
"site_id": "your-wordpress-site-id",
"status": "publish"
}
```
