# Semantic Search and RAG for Vaal AI Empire

Advanced semantic search and Retrieval-Augmented Generation (RAG) using Cohere embeddings for intelligent content discovery and question answering.

## 🎯 Features

- **🔍 Semantic Search**: Find relevant content based on meaning, not just keywords
- **🧠 RAG (Retrieval-Augmented Generation)**: Generate grounded responses with citations
- **📊 Content Clustering**: Organize large document collections automatically
- **🎨 Similarity Search**: Find similar documents in your corpus
- **⚡ Multiple Backends**: Annoy (local) or Elasticsearch (production)
- **🔄 Reranking**: Improve search results with Cohere's rerank model
- **💰 Cost Optimized**: Mock mode for development, efficient API usage

## 🏗️ Architecture

```
Documents → [Cohere Embeddings] → Vector Index
                                        ↓
Query → [Embed] → [Search] → [Rerank] → Top Results
                                              ↓
                                    [Cohere Chat API]
                                              ↓
                                    Grounded Response + Citations
```

## 📋 Prerequisites

1. **Python 3.9+**
2. **Cohere API Key** ([get one here](https://cohere.com))
3. **Optional**: Annoy for fast search (`pip install annoy`)
4. **Optional**: UMAP for visualization (`pip install umap-learn`)

## 🚀 Quick Start

### Install Dependencies

```bash
pip install cohere numpy annoy scikit-learn
```

### Basic Usage

```python
from services.semantic_search_rag import SemanticSearchService, RAGService

# 1. Semantic Search
search = SemanticSearchService()

documents = [
    {"id": 1, "text": "Python programming tutorial", "title": "Learn Python"},
    {"id": 2, "text": "JavaScript web development", "title": "Web Dev"},
    {"id": 3, "text": "Machine learning with Python", "title": "ML Guide"}
]

search.build_index(documents, text_field="text")
results = search.search("Python machine learning", top_k=2)

for result in results:
    print(f"{result['title']}: {result['similarity_score']:.3f}")

# 2. RAG (Retrieval-Augmented Generation)
rag = RAGService()

rag.index_documents(documents, text_field="text")
response = rag.generate_response("What is machine learning?")

print(f"Response: {response['response']}")
print(f"Citations: {len(response['citations'])}")
```

## 📚 Core Services

### 1. SemanticSearchService

Semantic search using Cohere embeddings and vector similarity.

```python
from services.semantic_search_rag import SemanticSearchService

service = SemanticSearchService(
    cohere_key="your-key",
    backend="annoy",  # or "elasticsearch"
    embedding_model="embed-v4.0"
)

# Build index
service.build_index(documents, text_field="text")

# Search
results = service.search("query", top_k=10)

# Find similar documents
similar = service.find_similar(document_id=0, top_k=5)
```

**Key Methods:**
- `embed_texts(texts)` - Generate embeddings
- `build_index(documents)` - Build search index
- `search(query, top_k)` - Semantic search
- `find_similar(doc_id, top_k)` - Find similar docs

### 2. RAGService

Retrieval-Augmented Generation with citations.

```python
from services.semantic_search_rag import RAGService

service = RAGService(
    cohere_key="your-key",
    chat_model="command-a-03-2025",
    rerank_model="rerank-english-v3.0"
)

# Index knowledge base
service.index_documents(documents, text_field="text")

# Generate grounded response
response = service.generate_response(
    query="What is your pricing?",
    top_k=10,
    use_rerank=True,
    rerank_top_n=5
)

print(response['response'])  # AI-generated answer
print(response['citations'])  # Citations with sources
print(response['documents'])  # Source documents
```

**Key Methods:**
- `index_documents(documents)` - Index knowledge base
- `rerank_documents(query, docs)` - Rerank results
- `generate_response(query)` - RAG with citations
- `hybrid_search_rag(query)` - Hybrid search + RAG

### 3. ContentClusteringService

Organize documents into topic clusters.

```python
from services.semantic_search_rag import ContentClusteringService

service = ContentClusteringService()

result = service.cluster_documents(
    documents,
    n_clusters=5,
    text_field="text"
)

# Access clustered documents
for doc in result['documents']:
    print(f"Cluster {doc['cluster']}: {doc['cluster_keywords']}")

# Visualize clusters (requires UMAP)
viz_data = service.visualize_clusters(documents)
```

**Key Methods:**
- `cluster_documents(docs, n_clusters)` - Cluster documents
- `visualize_clusters(docs)` - 2D visualization data

## 🔧 CLI Usage

The CLI tool provides easy access to all features:

### Index Documents

```bash
python scripts/semantic_search_cli.py index documents.json \
  --output search_index.ann \
  --text-field text
```

### Search

```bash
python scripts/semantic_search_cli.py search documents.json \
  "machine learning tutorials" \
  --top-k 5 \
  --output results.json
```

### RAG Query

```bash
python scripts/semantic_search_cli.py rag documents.json \
  "How do I learn Python?" \
  --rerank \
  --rerank-top-n 5
```

### Cluster Documents

```bash
python scripts/semantic_search_cli.py cluster documents.json \
  --n-clusters 8 \
  --output clusters.json
```

### Find Similar Documents

```bash
python scripts/semantic_search_cli.py similar documents.json 0 \
  --top-k 5
```

## 📊 Document Format

Your JSON documents should have this structure:

```json
[
  {
    "id": 1,
    "text": "Main content here",
    "title": "Document Title",
    "metadata": {"author": "John", "date": "2024-01-01"}
  },
  {
    "id": 2,
    "text": "More content",
    "title": "Another Document"
  }
]
```

**Required fields:**
- `text` (or specify with `--text-field`)

**Optional fields:**
- `title` - Document title
- `id` - Unique identifier
- Any other metadata you want to preserve

## 🎨 Use Cases

### 1. Client Content Library Search

```python
# Index all client content
from services.semantic_search_rag import SemanticSearchService
from core.database import Database

db = Database()
search = SemanticSearchService()

# Get client content
clients = db.get_active_clients()
documents = []
for client in clients:
    # Load client's content history
    documents.extend(load_client_content(client['id']))

search.build_index(documents)

# Search across all content
results = search.search("social media posts about marketing")
```

### 2. Knowledge Base Q&A

```python
# Build internal knowledge base
from services.semantic_search_rag import RAGService

rag = RAGService()

# Index documentation
docs = [
    {
        "text": "Vaal AI Empire offers social media management for R600/month",
        "title": "Pricing"
    },
    {
        "text": "We generate 20 posts per month in Afrikaans and English",
        "title": "Services"
    }
]

rag.index_documents(docs)

# Answer client questions
response = rag.generate_response("What are your monthly rates?")
```

### 3. Content Recommendation

```python
# Find similar content for recommendations
search = SemanticSearchService()
search.build_index(all_posts)

# Get recommendations for a post
current_post_id = 42
similar_posts = search.find_similar(current_post_id, top_k=5)

# Send to client
send_recommendations(client_id, similar_posts)
```

### 4. Content Organization

```python
# Automatically organize large content libraries
from services.semantic_search_rag import ContentClusteringService

clustering = ContentClusteringService()

result = clustering.cluster_documents(
    all_blog_posts,
    n_clusters=10
)

# Group by cluster
for cluster_id in range(10):
    cluster_docs = [d for d in result['documents'] if d['cluster'] == cluster_id]
    keywords = result['cluster_keywords'][cluster_id]

    print(f"Topic {cluster_id}: {', '.join(keywords)}")
    print(f"  {len(cluster_docs)} documents")
```

## ⚙️ Configuration

### Environment Variables

```bash
# Required
COHERE_API_KEY=your-cohere-key

# Optional
COHERE_EMBED_MODEL=embed-v4.0
COHERE_CHAT_MODEL=command-a-03-2025
COHERE_RERANK_MODEL=rerank-english-v3.0
SEARCH_BACKEND=annoy  # or elasticsearch
```

### Mock Mode

All services work in mock mode without API keys for development:

```python
# Automatically uses mock mode if COHERE_API_KEY not set
service = SemanticSearchService()  # Works without API key
service.available  # False (mock mode)

# Still functional!
service.build_index(documents)
results = service.search("query")  # Returns mock results
```

## 🧪 Testing

Run comprehensive tests:

```bash
# All tests
python tests/test_semantic_search_rag.py

# Specific test class
python -m pytest tests/test_semantic_search_rag.py::TestRAGService -v

# With coverage
pytest tests/test_semantic_search_rag.py --cov=services/semantic_search_rag
```

**Test Coverage:**
- ✅ Semantic search (10 tests)
- ✅ RAG service (8 tests)
- ✅ Content clustering (6 tests)
- ✅ Integration tests (4 tests)
- **Total: 28+ tests**

## 📈 Performance

### Benchmarks

| Operation | Documents | Time | Memory |
|-----------|-----------|------|--------|
| Index building | 1,000 | ~5s | ~100MB |
| Index building | 10,000 | ~30s | ~500MB |
| Search (Annoy) | 10,000 | <10ms | Minimal |
| RAG response | 10,000 | ~2s | Minimal |
| Clustering | 1,000 | ~10s | ~200MB |

### Optimization Tips

1. **Use Annoy for fast search** (O(log n) vs O(n) brute force)
2. **Batch embeddings** (90 texts at a time for Cohere)
3. **Cache indexes** (save/load Annoy index files)
4. **Limit reranking** (rerank top 10-20, not all results)
5. **Use mock mode** for development

## 🔗 Integration Examples

### With Content Generator

```python
from services.semantic_search_rag import RAGService
from services.content_generator import ContentFactory

# Use RAG to inform content generation
rag = RAGService()
rag.index_documents(existing_content)

# Get context for new content
context = rag.generate_response("Best practices for social media")

# Generate content with context
factory = ContentFactory()
pack = factory.generate_social_pack(
    business_type="cafe",
    additional_context=context['response']
)
```

### With WhatsApp Bot

```python
from services.semantic_search_rag import RAGService
from services.whatsapp_bot import WhatsAppBot

# Auto-respond to client queries
rag = RAGService()
rag.index_documents(faq_documents)

bot = WhatsAppBot(db)

def handle_client_message(phone, message):
    response = rag.generate_response(message)
    bot.send_message(phone, response['response'])
```

### With Revenue Tracking

```python
from services.semantic_search_rag import ContentClusteringService
from services.revenue_tracker import RevenueTracker

# Analyze which content clusters generate most revenue
clustering = ContentClusteringService()
result = clustering.cluster_documents(all_client_content)

tracker = RevenueTracker(db)

for cluster_id in result['cluster_keywords'].keys():
    cluster_docs = [d for d in result['documents'] if d['cluster'] == cluster_id]
    revenue = calculate_cluster_revenue(cluster_docs, tracker)
    print(f"Cluster {cluster_id}: R{revenue}")
```

## 🐛 Troubleshooting

### "COHERE_API_KEY must be set"

**Solution**: Services work in mock mode without keys for testing:
```python
# Works without API key
service = SemanticSearchService()
service.available  # False (mock mode)
```

### Slow Search Performance

**Solutions**:
1. Use Annoy backend: `backend="annoy"`
2. Reduce embedding dimensions (not recommended)
3. Limit search results: `top_k=10` instead of 100
4. Cache the index: `search_index.save("index.ann")`

### Out of Memory

**Solutions**:
1. Process documents in batches
2. Use smaller embedding batches (default: 90)
3. Clear embeddings after indexing if not needed
4. Use Elasticsearch for very large datasets

### Annoy Installation Issues

**Solution**: Annoy is optional:
```bash
# If Annoy fails to install
# System will automatically fall back to brute force search
# Or install from conda:
conda install -c conda-forge annoy
```

## 📖 API Reference

### SemanticSearchService

```python
class SemanticSearchService:
    def __init__(
        cohere_key: Optional[str] = None,
        backend: str = "annoy",
        embedding_model: str = "embed-v4.0"
    )

    def embed_texts(texts: List[str], input_type: str) -> np.ndarray
    def build_index(documents: List[Dict], text_field: str = "text")
    def search(query: str, top_k: int = 10) -> List[Dict]
    def find_similar(document_id: int, top_k: int = 10) -> List[Dict]
```

### RAGService

```python
class RAGService:
    def __init__(
        cohere_key: Optional[str] = None,
        chat_model: str = "command-a-03-2025",
        rerank_model: str = "rerank-english-v3.0"
    )

    def index_documents(documents: List[Dict], text_field: str = "text")
    def rerank_documents(query: str, documents: List[Dict], top_n: int = 10) -> List[Dict]
    def generate_response(query: str, top_k: int = 10, use_rerank: bool = True) -> Dict
    def hybrid_search_rag(query: str, top_k: int = 50) -> Dict
```

### ContentClusteringService

```python
class ContentClusteringService:
    def __init__(cohere_key: Optional[str] = None)

    def cluster_documents(
        documents: List[Dict],
        n_clusters: int = 8,
        text_field: str = "text"
    ) -> Dict

    def visualize_clusters(documents: List[Dict], text_field: str = "text") -> Dict
```

## 🎓 Best Practices

### 1. Index Management

```python
# Save indexes for reuse
search.build_index(documents)
if search.search_index:
    search.search_index.save("my_index.ann")

# Load later
from annoy import AnnoyIndex
index = AnnoyIndex(1024, 'angular')
index.load("my_index.ann")
```

### 2. Batch Processing

```python
# Process large document sets in batches
batch_size = 1000
for i in range(0, len(all_docs), batch_size):
    batch = all_docs[i:i+batch_size]
    embeddings = search.embed_texts([d['text'] for d in batch])
    # Store embeddings
```

### 3. Query Optimization

```python
# Cache frequently accessed results
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str):
    return search.search(query, top_k=10)
```

### 4. Error Handling

```python
try:
    response = rag.generate_response(query)
    if 'error' in response:
        # Handle error
        fallback_response(query)
except Exception as e:
    logger.error(f"RAG error: {e}")
    # Provide fallback
```

## 🚀 Advanced Features

### Custom Reranking

```python
# Combine multiple ranking signals
results = search.search(query, top_k=50)
reranked = rag.rerank_documents(query, results, top_n=10)

# Apply custom scoring
for doc in reranked:
    doc['final_score'] = (
        doc['similarity_score'] * 0.5 +
        doc['rerank_score'] * 0.5
    )
```

### Multi-field Search

```python
# Search across multiple fields
documents = [
    {"title": "Python Tutorial", "content": "Learn Python...", "tags": "programming"}
]

# Combine fields
for doc in documents:
    doc['searchable'] = f"{doc['title']} {doc['content']} {doc['tags']}"

search.build_index(documents, text_field="searchable")
```

### Filtered Search

```python
# Filter results by metadata
results = search.search(query, top_k=50)
filtered = [r for r in results if r.get('category') == 'tutorial']
```

---

**Built with ❤️ by Vaal AI Empire**

*Intelligent search for intelligent content* 🚀
