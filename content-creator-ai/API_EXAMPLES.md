# API Examples 📚

Comprehensive examples for using the Content Creator AI API.

## Authentication

All API requests (except `/health` and `/test`) require authentication:

```bash
# Via Header (Recommended)
curl -H "X-API-Key: your-api-key" https://api.example.com/api/content

# Via Query Parameter
curl "https://api.example.com/api/content?api_key=your-api-key"
```

## Basic Examples

### 1. Generate a Simple Article

```bash
curl -X POST http://localhost:3000/api/content \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "topic": "Introduction to Machine Learning",
    "media_type": "text",
    "length": "medium"
  }'
```

### 2. Generate with Specific Provider

```bash
curl -X POST http://localhost:3000/api/content \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "topic": "Cloud computing trends",
    "media_type": "text",
    "provider": "google",
    "enable_research": true
  }'
```

### 3. Generate Image

```bash
curl -X POST http://localhost:3000/api/content \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "topic": "A serene mountain landscape at dawn",
    "media_type": "image",
    "provider": "google",
    "aspect_ratio": "16:9",
    "style": "photorealistic"
  }'
```

## Advanced Examples

### 4. Long-Form SEO-Optimized Article

```bash
curl -X POST http://localhost:3000/api/content \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "topic": "Complete Guide to Node.js Performance Optimization",
    "media_type": "text",
    "provider": "google",
    "audience": "Node.js developers",
    "tone": "technical",
    "length": "long",
    "format": "markdown",
    "enable_research": true,
    "include_seo": true,
    "include_social": true,
    "keywords": ["nodejs", "performance", "optimization", "backend"],
    "cta": "Start optimizing your Node.js apps today!",
    "temperature": 0.7
  }'
```

### 5. Z.AI Thinking Mode for Complex Topics

```bash
curl -X POST http://localhost:3000/api/content \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "topic": "Explain the CAP theorem and its practical implications in distributed systems",
    "media_type": "text",
    "provider": "zai",
    "thinking_mode": true,
    "tone": "technical",
    "length": "long",
    "max_tokens": 8000
  }'
```

### 6. LocalAI for Privacy-Focused Content

```bash
curl -X POST http://localhost:3000/api/content \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "topic": "Internal company newsletter about Q4 results",
    "media_type": "text",
    "provider": "localai",
    "audience": "company employees",
    "tone": "friendly",
    "length": "medium"
  }'
```

### 7. Multimodal Content (Text + Image)

```bash
curl -X POST http://localhost:3000/api/content \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "topic": "The Future of Electric Vehicles",
    "media_type": "multimodal",
    "provider": "google",
    "tone": "professional",
    "length": "medium",
    "aspect_ratio": "16:9",
    "include_seo": true,
    "include_social": true
  }'
```

### 8. Social Media Campaign

```bash
curl -X POST http://localhost:3000/api/content \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "topic": "Announcing our new AI-powered features",
    "media_type": "text",
    "length": "short",
    "tone": "friendly",
    "include_social": true,
    "keywords": ["AI", "innovation", "technology", "launch"],
    "cta": "Try it now!"
  }'
```

### 9. Video Script Generation

```bash
curl -X POST http://localhost:3000/api/content \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "topic": "How to use our product - Tutorial",
    "media_type": "video",
    "provider": "google",
    "duration": 30,
    "aspect_ratio": "16:9"
  }'
```

### 10. Audio/Podcast Script

```bash
curl -X POST http://localhost:3000/api/content \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "topic": "Weekly tech news roundup",
    "media_type": "audio",
    "provider": "openai",
    "voice": "nova",
    "enable_research": true
  }'
```

## JavaScript/Node.js Examples

### Using Axios

```javascript
const axios = require('axios');

async function generateContent() {
  try {
    const response = await axios.post('http://localhost:3000/api/content', {
      topic: 'Getting started with Docker',
      media_type: 'text',
      provider: 'google',
      length: 'medium',
      include_seo: true
    }, {
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'your-api-key'
      }
    });

    console.log('Success!', response.data);
    
    // Access the content
    console.log('Content:', response.data.content.content);
    
    // Access SEO data
    console.log('SEO Title:', response.data.seo.title);
    
    // Check cost
    console.log('Cost: $', response.data.costs.totalCost);
    
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

generateContent();
```

### Using Fetch (Browser/Modern Node)

```javascript
async function generateContent() {
  const response = await fetch('http://localhost:3000/api/content', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'your-api-key'
    },
    body: JSON.stringify({
      topic: 'Web development best practices',
      media_type: 'text',
      length: 'medium'
    })
  });

  const data = await response.json();
  
  if (data.success) {
    console.log('Content generated!');
    console.log(data.content.content);
  } else {
    console.error('Error:', data.message);
  }
}
```

## Python Examples

### Using Requests

```python
import requests
import json

def generate_content():
    url = 'http://localhost:3000/api/content'
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': 'your-api-key'
    }
    
    data = {
        'topic': 'Introduction to Python',
        'media_type': 'text',
        'provider': 'google',
        'length': 'medium',
        'tone': 'friendly',
        'include_seo': True,
        'include_social': True
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        print('Success!')
        print('Content:', result['content']['content'])
        print('Cost: $', result['costs']['totalCost'])
    else:
        print('Error:', response.json())

generate_content()
```

## Response Examples

### Successful Text Generation Response

```json
{
  "success": true,
  "requestId": "abc-123-def-456",
  "content": {
    "type": "text",
    "content": "# Introduction to AI\n\nArtificial Intelligence...",
    "format": "markdown",
    "research": "Recent developments in AI include...",
    "sources": ["https://example.com/ai-news"],
    "usage": {
      "research": {
        "inputTokens": 50,
        "outputTokens": 200
      },
      "content": {
        "inputTokens": 150,
        "outputTokens": 800
      }
    },
    "totalCost": 0.0125,
    "provider": "google"
  },
  "seo": {
    "title": "Introduction to AI - A Comprehensive Guide",
    "metaDescription": "Learn about Artificial Intelligence, its applications, and future impact...",
    "keywords": ["ai", "artificial", "intelligence", "machine", "learning"],
    "ogTags": {
      "og:title": "Introduction to AI",
      "og:description": "Learn about Artificial Intelligence...",
      "og:type": "article"
    },
    "structuredData": {
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "Introduction to AI"
    },
    "readabilityScore": {
      "score": 78,
      "level": "Fairly Easy"
    }
  },
  "social": {
    "twitter": {
      "text": "Introduction to AI: Learn the basics! #AI #MachineLearning #Tech",
      "length": 65
    },
    "linkedin": {
      "text": "🚀 Introduction to AI\n\nLearn about Artificial Intelligence...\n\n#AI #Technology"
    }
  },
  "metadata": {
    "topic": "Introduction to AI",
    "audience": "general audience",
    "tone": "professional",
    "language": "en",
    "mediaType": "text",
    "provider": "google",
    "fromCache": false
  },
  "costs": {
    "totalCost": 0.0125,
    "breakdown": {
      "provider": "google",
      "mediaType": "text",
      "totalCost": 0.0125
    }
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Error Response

```json
{
  "success": false,
  "requestId": "abc-123",
  "error": "Validation failed",
  "details": [
    "topic is required",
    "media_type must be one of: text, image, video, audio, multimodal"
  ]
}
```

## Webhook Integration

### n8n Workflow Example

```json
{
  "nodes": [
    {
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:3000/api/content",
        "method": "POST",
        "headerParameters": {
          "parameters": [
            {
              "name": "X-API-Key",
              "value": "your-api-key"
            }
          ]
        },
        "bodyParameters": {
          "parameters": [
            {
              "name": "topic",
              "value": "={{$json.topic}}"
            },
            {
              "name": "media_type",
              "value": "text"
            }
          ]
        }
      }
    }
  ]
}
```

## Rate Limiting

The API implements rate limiting. Default: 100 requests per minute.

```bash
# Headers in response:
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1642248600
```

When rate limit is exceeded:

```json
{
  "success": false,
  "error": "Too many requests",
  "message": "Rate limit exceeded. Please try again later."
}
```

## Best Practices

1. **Use caching**: Enable Redis for frequently requested content
2. **Monitor costs**: Check `/api/stats` regularly
3. **Handle errors**: Implement retry logic with exponential backoff
4. **Set timeouts**: API calls may take 10-60 seconds
5. **Use appropriate providers**:
   - Google: Real-time research, multimodal
   - Z.AI: Cost-efficient, long content
   - LocalAI: Privacy, offline
   - OpenAI: High quality, reliable

## Support

For more examples and documentation, visit the [README.md](./README.md).
