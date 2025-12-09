import os
import sys
import requests

# --- CONFIG (set these or export as env vars) ---
AYRSHARE_KEY = os.getenv("AYRSHARE_API_KEY")
PROMPT = "Write a tweet about SA tax incentives for SMEs."

# --- INSTALL CHECK ---
try:
    from transformers import pipeline
    import torch
except ImportError:
    sys.exit("❌ Run: pip install transformers torch requests")

# --- INSTRUCT MODEL (free, no key) ---
# Using the transformers pipeline for more stability
generator = pipeline('text-generation', model='mistralai/Mistral-7B-Instruct-v0.1')
sequences = generator(PROMPT, max_length=100, num_return_sequences=1)
content = sequences[0]['generated_text']

# --- PUBLISH TO SOCIAL (real Ayrshare call) ---
if not AYRSHARE_KEY:
    # We exit gracefully here for the test run
    print("✅ Content generated successfully. To publish, set the AYRSHARE_API_KEY environment variable.")
    print("\n--- Generated Content ---")
    print(content)
    print("------------------------")
    sys.exit(0)

payload = {
    "post": content,
    "platforms": ["twitter", "linkedin", "reddit"]
}

response = requests.post(
    "https://app.ayrshare.com/api/post",
    headers={"Authorization": f"Bearer {AYRSHARE_KEY}"},
    json=payload,
    timeout=30
)

print(f"✅ Posted ID: {response.json()['id']}" if response.ok else f"❌ {response.text}")
