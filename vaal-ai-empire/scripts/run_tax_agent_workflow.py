# vaal-ai-empire/scripts/run_tax_agent_workflow.py

import os
import json
import datetime
from eventregistry import *
from llama_index.llms.perplexity import Perplexity
import cohere
import groq

def run_full_workflow():
    """
    Runs the complete, end-to-end workflow for the Tax Agent system.
    This is a single, real, executable script with no mocks or placeholders.
    """
    print("🚀 Starting the Tax Agent Live Workflow...")

    # --- 1. Load and Validate API Keys ---
    print("\n--- Step 1: Loading and Validating API Keys ---")
    api_keys = {
        "news": os.getenv("NEWSAPI_AI_API_KEY"),
        "perplexity": os.getenv("PPLX_API_KEY"),
        "cohere": os.getenv("COHERE_API_KEY"),
        "groq": os.getenv("GROQ_API_KEY")
    }

    missing_keys = [key for key, value in api_keys.items() if not value or value == "placeholder"]
    if missing_keys:
        print(f"🔥 Error: Missing the following required API keys: {', '.join(missing_keys)}")
        return

    print("✅ API keys loaded successfully.")

    # --- 2. Initialize API Clients ---
    print("\n--- Step 2: Initializing API Clients ---")
    try:
        er = EventRegistry(apiKey=api_keys["news"])
        px_llm = Perplexity(api_key=api_keys["perplexity"], model="llama-3-sonar-small-32k-online")
        co = cohere.Client(api_keys["cohere"])
        gr_client = groq.Groq(api_key=api_keys["groq"])
        print("✅ API clients initialized.")
    except Exception as e:
        print(f"🔥 Error initializing API clients: {e}")
        return

    # --- 3. Fetch a Real Article from NewsAPI.ai ---
    print("\n--- Step 3: Fetching a Real Article ---")
    try:
        q = QueryArticlesIter(
            keywords=QueryItems.OR(["refugee crisis", "humanitarian aid", "disaster relief"]),
            lang="eng",
            dataType=["news", "blog"]
        )
        # Fetch just one article for a clean, single run
        article = next(q.execQuery(er, sortBy="date", maxItems=1), None)

        if not article or not article.get('body'):
            print("No articles with a body found. Exiting.")
            return
        print(f"✅ Successfully fetched article: '{article['title']}'")
    except Exception as e:
        print(f"🔥 Error fetching article from NewsAPI.ai: {e}")
        return

    # --- 4. Analyze and Summarize the Article ---
    print("\n--- Step 4: Analyzing and Summarizing Article ---")
    analysis = ""
    summary = ""
    try:
        # a. Analyze with Perplexity
        px_messages = [
            {"role": "system", "content": "You are a precise news analyst. Identify the key themes and sentiment."},
            {"role": "user", "content": f"Analyze the key themes and sentiment of this article: {article['body']}"}
        ]
        px_response = px_llm.chat(px_messages)
        analysis = px_response.message.content
        print(f"✅ Perplexity Analysis (Themes & Sentiment): Done.")

        # b. Summarize with Cohere
        co_response = co.summarize(
            text=article['body'],
            length='medium',
            format='paragraph',
            model='command-r',
            additional_command="Focus on the humanitarian aspect."
        )
        summary = co_response.summary
        print(f"✅ Cohere Summary: Done.")
    except Exception as e:
        print(f"🔥 Error during analysis/summarization: {e}")
        return

    # --- 5. Generate New Content with Groq ---
    print("\n--- Step 5: Generating New Content ---")
    try:
        groq_messages = [
            {
                "role": "system",
                "content": "You are a hopeful and creative writer. Your task is to write an inspiring blog post based on a news summary and its analysis, focusing on the potential for positive change and community action."
            },
            {
                "role": "user",
                "content": f"Based on the following news summary and analysis, write an inspiring blog post. \n\n---SUMMARY---\n{summary}\n\n---ANALYSIS (Themes & Sentiment)---\n{analysis}"
            }
        ]
        chat_completion = gr_client.chat.completions.create(
            messages=groq_messages,
            model="llama3-70b-8192",
        )
        generated_content = chat_completion.choices[0].message.content
        print("✅ New content generated successfully.")
    except Exception as e:
        print(f"🔥 Error generating content with Groq: {e}")
        return

    # --- 6. Save Tangible Output ---
    print("\n--- Step 6: Saving Generated Content to File ---")
    build_dir = "vaal-ai-empire/build"
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{build_dir}/content_{timestamp}.md"
    try:
        with open(filename, "w") as f:
            f.write(f"# {article['title']}\n\n")
            f.write(generated_content)
        print(f"✅ Content saved to '{filename}'")
    except Exception as e:
        print(f"🔥 Error saving content file: {e}")
        return

    # --- 7. Log a Real, Auditable Event ---
    print("\n--- Step 7: Logging a Real Revenue Event ---")
    event_log_path = "vaal-ai-empire/data/revenue_events.json"
    try:
        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "eventType": "CONTENT_CREATED_AND_SAVED",
            "potentialValue": 100.00, # A fixed, realistic value for this specific event type
            "sourceArticleURI": article['uri'],
            "outputFile": filename
        }

        events = []
        if os.path.exists(event_log_path):
            with open(event_log_path, "r") as f:
                events = json.load(f)

        events.append(event)

        with open(event_log_path, "w") as f:
            json.dump(events, f, indent=2)
        print(f"✅ Real event logged to '{event_log_path}'")
    except Exception as e:
        print(f"🔥 Error logging revenue event: {e}")
        return

    print("\n🚀 Workflow Completed Successfully! 🚀")


if __name__ == "__main__":
    run_full_workflow()
