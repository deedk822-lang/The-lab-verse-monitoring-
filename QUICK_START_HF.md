# Lab-Verse Agent - Quick Start with Hugging Face Token

## You Already Have HF Token? Perfect! ✅

If you have your Hugging Face API key stored in GitHub Secrets or Colab, follow these steps:

---

## Option 1: Automated Setup (Recommended)

### Step 1: Run the setup script

```bash
chmod +x scripts/setup-agent.sh
./scripts/setup-agent.sh
```

**The script will:**
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Prompt you for HF token (copy from GitHub/Colab)
- ✅ Prompt you for Bitbucket credentials
- ✅ Create `.env.production` automatically
- ✅ Download the model (~7GB)
- ✅ Test the configuration

**When prompted:**
```
Enter your Hugging Face API token: hf_your_token_here
Enter Bitbucket username: your-email@atlassian.com
Enter Bitbucket App Password: your_64_char_password
```

### Step 2: Start the agent

```bash
source venv/bin/activate
export $(cat .env.production | xargs)
python3 -m agent.main
```

**Expected output:**
```
✅ Configuration loaded
🤖 Hugging Face Model Loader initialized
🚀 FastAPI server started on http://0.0.0.0:8000
```

### Step 3: Test in another terminal

```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status": "ok"}
```

---

## Option 2: Manual Setup

If you prefer to do it manually:

### Step 1: Set up environment

```bash
# Create venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Create `.env.production`

```bash
cat > .env.production << 'EOF'
BITBUCKET_WORKSPACE=lab-verse-monitaring
BITBUCKET_USERNAME=your-email@atlassian.com
BITBUCKET_APP_PASSWORD=your-app-password

HF_TOKEN=hf_your_token_from_github_or_colab
HF_DEVICE=cuda
HF_LOAD_IN_8BIT=true
HF_CACHE_DIR=./models

ENVIRONMENT=production
LOG_LEVEL=INFO
EOF

chmod 600 .env.production
```

### Step 3: Download models

```bash
# Set HF token in environment
export HF_TOKEN=hf_your_token_here

# Download models
mkdir -p ./models
huggingface-cli download "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B" --cache-dir ./models --resume-download
```

### Step 4: Run agent

```bash
export $(cat .env.production | xargs)
python3 -m agent.main
```

---

## Getting Your HF Token

### From GitHub Secrets:
1. Go to: https://github.com/your-repo/settings/secrets/actions
2. Find the `HF_TOKEN` or `HUGGINGFACE_TOKEN` secret
3. Copy it

### From Colab:
1. Open your Colab notebook
2. Find the cell where you set `hf_token`
3. Get the token value

### Create New Token (if needed):
1. Go to: https://huggingface.co/settings/tokens
2. Create new token with **Read** access
3. Copy the `hf_...` value

---

## Troubleshooting

### "Invalid HF token"
```bash
# Verify token format (should start with hf_)
echo $HF_TOKEN

# Re-run setup or manually update .env.production
nano .env.production
```

### "Model download fails"
```bash
# Check internet connection
ping huggingface.co

# Try with explicit token
export HF_TOKEN=your_token_here
huggingface-cli download "mistralai/Mistral-7B-Instruct-v0.3" --cache-dir ./models --token $HF_TOKEN
```

### "CUDA not available"
```bash
# Update .env.production
echo "HF_DEVICE=cpu" >> .env.production

# Agent will run slower but still work
```

### "Out of Memory"
```bash
# Enable 4-bit quantization in .env.production
echo "HF_LOAD_IN_4BIT=true" >> .env.production
```

---

## What's Next?

1. ✅ Agent running locally? Great!
2. 📦 Configure Bitbucket webhook
3. 🧪 Trigger a test pipeline failure
4. 🚀 Agent should create a PR with fix

**Webhook setup:**
- Go to: `https://bitbucket.org/lab-verse-monitaring/YOUR_REPO/admin/webhooks`
- Add webhook to: `https://your-agent-url.com/webhook/bitbucket`
- Events: Repository push, Commit status updated

---

## Performance Tips

| Setting | Speed | VRAM | Latency |
|---------|-------|------|----------|
| GPU + 8-bit | Fast | 16GB+ | 30-60s |
| GPU + 4-bit | Good | 8GB+ | 60-120s |
| CPU | Slow | 32GB+ | 3-5min |

**Recommendation:** Start with `HF_LOAD_IN_8BIT=true` on GPU. If OOM, switch to 4-bit.

---

**Ready? Run: `./scripts/setup-agent.sh`** 🚀
