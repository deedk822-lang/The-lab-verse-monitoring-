# Advanced Keyword Research with Cohere + Perplexity Deep Search

Combining Cohere's embedding and clustering with Perplexity's deep search for comprehensive keyword research and content strategy.

## Features

- 🔍 **Keyword Clustering**: Group related keywords using Cohere embeddings
- 🧠 **Topic Intelligence**: Generate topic names with Cohere Chat
- 🌐 **Deep Search**: Enrich topics with Perplexity's real-time web research
- 📊 **Competitive Analysis**: Discover trending content and gaps
- ✍️ **Content Briefs**: Auto-generate detailed content outlines
- 📈 **Search Intent**: Understand user intent behind keywords

## Architecture

```
Keywords → Cohere Embed → KMeans Cluster → Cohere Topic Names
    ↓
Perplexity Deep Search → Content Insights → SEO Strategy
```

## Setup

1. **Environment Variables**
```
COHERE_API_KEY=your-cohere-api-key
PERPLEXITY_API_KEY=your-perplexity-api-key
```

2. **Install Dependencies**
```
pip install cohere pandas numpy scikit-learn requests
```

## Usage

### Basic Keyword Research with Deep Search
```
from services.keywordResearchWithPerplexity import EnhancedKeywordResearchService

service = EnhancedKeywordResearchService(
    cohere_key="your-cohere-key",
    perplexity_key="your-perplexity-key"
)

# Process keywords with deep search
results = service.process_keywords_with_deep_search(
    csv_path="remote_teams.csv",
    num_topics=4,
    enable_deep_search=True
)

# Access enriched results
for topic in results['enriched_topics']:
    print(f"\nTopic: {topic['topic_name']}")
    print(f"Search Trends: {topic['perplexity_insights']['current_trends']}")
    print(f"Content Opportunities: {topic['perplexity_insights']['content_gaps']}")
```

### API Endpoint
```
curl -X POST http://localhost:3000/api/keyword-research/deep-search \
  -H "Content-Type: multipart/form-data" \
  -F "file=@keywords.csv" \
  -F "num_topics=4" \
  -F "enable_deep_search=true"
```

## Perplexity Deep Search Capabilities

### 1. Topic Trend Analysis
- Current search trends and interest
- Emerging subtopics
- Seasonal patterns

### 2. Content Gap Analysis
- What competitors are missing
- Underserved user questions
- Fresh angle opportunities

### 3. Search Intent Mapping
- Informational vs transactional intent
- User pain points
- Common questions

### 4. Competitive Landscape
- Top-ranking content analysis
- Content formats that work
- Authority sources

## Response Format

```
{
  "topics": [
    {
      "id": 0,
      "topic_name": "Remote Team Management",
      "keywords": ["managing remote teams", "remote team leadership"],
      "keyword_count": 25,
      "total_volume": 5200,
      "perplexity_insights": {
        "current_trends": "Rising interest in async communication and hybrid work models",
        "content_gaps": [
          "Remote team onboarding processes",
          "Managing timezone differences effectively"
        ],
        "search_intent": "Users seeking practical frameworks and tools",
        "top_questions": [
          "How to build trust in remote teams?",
          "What metrics track remote team productivity?"
        ],
        "recommended_formats": ["How-to guides", "Tool comparisons", "Case studies"]
      },
      "content_brief": {
        "suggested_title": "The Complete Guide to Managing Remote Teams in 2025",
        "outline": ["Introduction", "Communication strategies", "Tools", "Best practices"],
        "target_length": 2500,
        "difficulty": "Intermediate"
      }
    }
  ],
  "summary": {
    "total_keywords": 100,
    "total_volume": 15600,
    "avg_competition": "Medium",
    "recommended_priority": ["Topic 0", "Topic 2"]
  }
}
```

## Best Practices

1. **Deep Search Timing**: Use for top 3-5 topics only (API cost optimization)
2. **Refresh Frequency**: Run monthly for trend updates
3. **Combine Signals**: Use both search volume + Perplexity insights
4. **Content Calendar**: Map topics to publication schedule

## Integration Examples

### Content Calendar Generation
```
calendar = service.generate_content_calendar(
    results['enriched_topics'],
    weeks=12
)
```

### SEO Brief Export
```
service.export_seo_briefs(
    results['enriched_topics'],
    output_dir='content-briefs'
)
```
