# Ayrshare Social Publishing Service

This directory contains a standalone Python script to generate social media content using the Hugging Face `transformers` library and publish it to multiple platforms using the Ayrshare API.

## Features

- **Robust Content Generation**: Uses the `transformers` library for stable, local text generation with a proven model (`mistralai/Mistral-7B-Instruct-v0.1`).
- **Dependency-Aware**: The script checks for required libraries (`transformers`, `torch`, `requests`) and provides installation instructions if they are missing.
- **Multi-Platform Publishing**: Posts content to Twitter, LinkedIn, and Reddit simultaneously via Ayrshare.
- **Self-Contained**: A single script that is easy to run and integrate.

## How to Use

### 1. Installation

The script requires `transformers`, `torch`, and `requests`. You can install them with pip:

```bash
pip install transformers torch requests
```
*Note: The first time you run the script, it will download the language model (approx. 15 GB), so a good internet connection is recommended.*

### 2. Set Environment Variable

The script requires an Ayrshare API key to publish content. If this key is not set, the script will generate the content and print it to the console without attempting to publish.

```bash
export AYRSHARE_API_KEY="your-ayrshare-api-key-here"
```

### 3. Run the Script

Execute the script from the command line:

```bash
python ayrshare/publish_social.py
```

The script will:
1. Generate a tweet about "SA tax incentives for SMEs" using the Mistral-7B model.
2. If the `AYRSHARE_API_KEY` is set, it will post the content to Twitter, LinkedIn, and Reddit.
3. If the key is not set, it will print the generated content to the console.
