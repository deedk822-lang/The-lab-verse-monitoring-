# Fueling Generative Content with Keyword Research

This guide implements Cohere's keyword research cookbook to enhance content generation with SEO insights and search demand data.

## Overview

Combine generative AI with keyword research to create content that:
- Aligns with user search intent
- Targets high-traffic keywords
- Groups related keywords into topics
- Generates topic-focused content

## Prerequisites

- Cohere API key ([Get yours here](https://dashboard.cohere.com/api-keys))
- Python 3.8+
- Required packages: `cohere`, `pandas`, `numpy`, `scikit-learn`

## Architecture

```
Keyword Data → Embed (Cohere) → Cluster (KMeans) → Topic Names (Chat) → Content Generation
```

## Setup

1. **Install Dependencies**
```
pip install cohere pandas numpy scikit-learn
```

2. **Set Environment Variables**
```
export COHERE_API_KEY="your-api-key-here"
```

3. **Prepare Keyword Data**
   - Export keywords from Google Keyword Planner
   - Format as CSV with columns: `keyword`, `volume`

## Implementation

See `services/keywordResearchService.py` for the complete implementation.

## Usage Examples

### Python Script
```
from services.keywordResearchService import KeywordResearchService

# Initialize service
kr_service = KeywordResearchService(api_key="your-cohere-api-key")

# Load and process keywords
results = kr_service.process_keywords_from_csv("remote_teams.csv", num_topics=4)

# Generate content ideas
content_ideas = kr_service.generate_content_ideas(results['topic_summary'])
```

### API Endpoint
```
curl -X POST http://localhost:3000/api/keyword-research \
  -H "Content-Type: multipart/form-data" \
  -F "file=@remote_teams.csv" \
  -F "num_topics=4"
```

## Features

- ✅ Keyword embedding with Cohere Embed v4
- ✅ Topic clustering with KMeans
- ✅ Automatic topic naming with Cohere Chat
- ✅ Content idea generation
- ✅ CSV export of results
- ✅ RESTful API integration

## API Reference

### POST `/api/keyword-research`
Upload keywords and get topic clusters

**Request:**
- `file`: CSV file (keyword, volume)
- `num_topics`: Number of topic clusters (default: 4)

**Response:**
```
{
  "topics": [
    {
      "id": 0,
      "name": "Remote Team Management",
      "keywords": ["managing remote teams", "how to manage remote teams"],
      "total_volume": 1260
    }
  ],
  "summary": "Processed 50 keywords into 4 topics"
}
```

## Best Practices

1. **Keyword Selection**: Focus on 50-200 keywords per topic area
2. **Topic Count**: Start with 3-5 topics, adjust based on results
3. **Volume Threshold**: Filter keywords below 100 monthly searches
4. **Update Frequency**: Refresh keyword data monthly

## Integration with Content Creator AI

This module integrates seamlessly with the existing content-creator-ai system:
- Feeds topics into content generation pipeline
- Prioritizes high-volume keyword topics
- Enhances SEO optimization
