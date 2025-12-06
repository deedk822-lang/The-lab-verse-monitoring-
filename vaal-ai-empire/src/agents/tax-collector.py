# vaal-ai-empire/src/agents/tax-collector.py

import os
import json
import cohere
from eventregistry import *
from llama_index.llms.perplexity import Perplexity

def monitor_and_process_events():
    """
    Monitors global hardship events, analyzes them, and creates a semantic index.
    """
    print("🚀 Starting Tax Agent: Monitoring for hardship events...")

    # --- API Key Validation ---
    newsapi_key = os.getenv("NEWSAPI_AI_API_KEY")
    perplexity_api_key = os.getenv("PPLX_API_KEY")
    cohere_api_key = os.getenv("COHERE_API_KEY")

    if not all([newsapi_key, perplexity_api_key, cohere_api_key]):
        print("🔥 Error: Missing one or more required API keys (NEWSAPI_AI_API_KEY, PPLX_API_KEY, COHERE_API_KEY).")
        return

    # --- Initialize Clients ---
    er = EventRegistry(apiKey=newsapi_key)
    llm = Perplexity(api_key=perplexity_api_key, model="sonar-pro")
    co = cohere.Client(cohere_api_key)

    # --- Fetch Articles ---
    q = QueryArticlesIter(
        keywords=QueryItems.OR(["refugee", "poverty", "crisis", "violence", "disaster"]),
        lang="eng",
        dataType=["news", "blog"]
    )
    articles = list(q.execQuery(er, sortBy="date", maxItems=5))
    print(f"✅ Fetched {len(articles)} articles.")

    if not articles:
        print("No articles found. Exiting.")
        return

    processed_articles = []
    texts_for_embedding = []

    # --- Analyze and Prepare Articles ---
    for art in articles:
        print(f"Processing article: {art.get('title', 'No Title')}")

        body = art.get('body')
        if not body:
            print("Skipping article with no body.")
            continue

        # 1. Analyze with Perplexity
        messages = [
            {"role": "system", "content": "You are a precise and concise news analyst."},
            {"role": "user", "content": f"Analyze the sentiment and key themes of the following article body: {body}"}
        ]
        try:
            response = llm.chat(messages)
            art['analysis'] = response.message.content
            processed_articles.append(art)
            texts_for_embedding.append(body)
        except Exception as e:
            print(f"Could not analyze article with Perplexity: {e}")

    if not processed_articles:
        print("No articles could be processed. Exiting.")
        return

    # --- Create Semantic Embeddings with Cohere ---
    print("🔬 Creating semantic embeddings for processed articles...")
    try:
        response = co.embed(
            texts=texts_for_embedding,
            model='embed-english-v3.0',
            input_type='search_document'
        )
        embeddings = response.embeddings
        print("✅ Embeddings created successfully.")

        # --- Write to Queue ---
        for i, art in enumerate(processed_articles):
            queue_item = {
                "article": art,
                "embedding": embeddings[i]
            }
            queue_path = f"vaal-ai-empire/queue/article_{art.get('uri', i)}.json"
            with open(queue_path, "w") as f:
                json.dump(queue_item, f, indent=2)
            print(f"📦 Article {art.get('uri', i)} written to queue.")

    except Exception as e:
        print(f"🔥 Error creating embeddings or writing to queue: {e}")


if __name__ == "__main__":
    # Ensure queue directory exists
    if not os.path.exists("vaal-ai-empire/queue"):
        os.makedirs("vaal-ai-empire/queue")
    monitor_and_process_events()
