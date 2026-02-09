# HuggingFace Token Setup Guide

## 🎯 Why You Need a HuggingFace Token

The HuggingFace token (`HF_TOKEN`) is **required** for:

1. **Downloading Models** - Most models on HuggingFace Hub require authentication
2. **Gated Models** - Access to models like Llama, Mistral, and other restricted models
3. **Higher Rate Limits** - Authenticated requests have much higher rate limits
4. **Private Models** - Access to your own private/organization models
5. **Model Updates** - Download updated versions of models

### ❌ Without Token

```python
# This WILL FAIL for most models
provider = HuggingFaceProvider(LLMConfig(
    api_key=None,  # No token
    model_path="/models"
))

# Error: 401 Unauthorized
# Error: Rate limit exceeded
# Error: Repository not found (for gated models)
```

### ✅ With Token

```python
# This WORKS correctly
provider = HuggingFaceProvider(LLMConfig(
    api_key="hf_YourTokenHere",  # Valid token
    model_path="/models"
))

# Success: Model downloads with authentication
# Success: Access to gated models
# Success: Higher rate limits
```

---

## 📝 Getting Your HuggingFace Token

### Step 1: Create HuggingFace Account

1. Go to [https://huggingface.co/join](https://huggingface.co/join)
2. Sign up with email or GitHub
3. Verify your email

### Step 2: Generate Access Token

1. Go to [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Click **"New token"**
3. Enter token details:
   - **Name**: `vaal-ai-empire-production` (or any name)
   - **Type**: Select **"Read"** (for downloading models)
   - **Optional**: Select **"Write"** if you want to upload models
4. Click **"Generate token"**
5. **IMPORTANT**: Copy the token immediately! It won't be shown again.

### Step 3: Accept Model Terms (For Gated Models)

Some models require accepting terms before use:

1. Go to the model page (e.g., [meta-llama/Llama-3.2-3B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct))
2. Click **"Agree and access repository"**
3. Read and accept the license terms
4. Wait for approval (usually instant, sometimes up to 24 hours)

**Common Gated Models**:
- `meta-llama/Llama-3.2-3B-Instruct`
- `meta-llama/Llama-2-7b-chat-hf`
- `mistralai/Mistral-7B-Instruct-v0.2`
- `google/gemma-7b`

---

## ⚙️ Configuration

### Option 1: Environment Variable (Recommended)

```bash
# In .env file
HF_TOKEN=hf_YourActualTokenHere

# Or export in shell
export HF_TOKEN=hf_YourActualTokenHere
```

### Option 2: Direct in Code

```python
from agent.tools.llm_provider import HuggingFaceProvider, LLMConfig

config = LLMConfig(
    api_key="hf_YourActualTokenHere",  # Your HF token
    model_path="/models",
    device="cuda"  # or "cpu"
)

provider = HuggingFaceProvider(config)
```

### Option 3: HuggingFace CLI Login

```bash
# Install HuggingFace CLI
pip install huggingface_hub

# Login (stores token in ~/.cache/huggingface/token)
huggingface-cli login

# Enter your token when prompted
# Token: hf_YourActualTokenHere
```

---

## 🔍 Verification

### Test Your Token

```bash
# Test 1: Check token is set
echo $HF_TOKEN

# Test 2: Test with Python
python << EOF
import os
from agent.tools.llm_provider import initialize_from_env

# Should show token is configured
os.environ['LLM_PROVIDER'] = 'huggingface'
os.environ['HF_TOKEN'] = '$HF_TOKEN'

provider = initialize_from_env()
print(f"✅ Provider initialized: {provider.provider_name}")
print(f"✅ Token configured: {bool(provider.hf_token)}")
print(f"✅ Token value: {provider.hf_token[:10]}...")
EOF

# Test 3: Try downloading a small model
python << EOF
from transformers import AutoTokenizer

# This should work with valid token
tokenizer = AutoTokenizer.from_pretrained(
    "gpt2",  # Small public model for testing
    token=os.getenv('HF_TOKEN')
)
print("✅ Token works! Model downloaded successfully")
EOF
```

### Expected Output

```
✅ Provider initialized: HuggingFace
✅ Token configured: True
✅ Token value: hf_abcdefg...
✅ Token works! Model downloaded successfully
```

---

## 🚨 Troubleshooting

### Problem 1: "401 Unauthorized"

**Symptoms**:
```
OSError: 401 Unauthorized
RuntimeError: Authentication failed for model
```

**Solutions**:
1. Check token is set: `echo $HF_TOKEN`
2. Verify token is valid at [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
3. Generate new token if expired
4. Check token has "Read" permission

### Problem 2: "Repository not found" (Gated Model)

**Symptoms**:
```
OSError: Repository not found
RuntimeError: This model requires accepting terms
```

**Solutions**:
1. Go to model page on HuggingFace
2. Click "Agree and access repository"
3. Accept license terms
4. Wait for approval (check your email)
5. Retry after approval

### Problem 3: "Rate limit exceeded"

**Symptoms**:
```
OSError: Rate limit exceeded
HTTPError: 429 Too Many Requests
```

**Solutions**:
1. **Add token** - Authenticated requests have 10x higher limits
2. Wait a few minutes before retrying
3. Consider caching downloaded models locally
4. Use `model_path` to cache models:
   ```python
   config = LLMConfig(
       api_key="hf_token",
       model_path="/persistent/cache",  # Reuse downloaded models
       device="cpu"
   )
   ```

### Problem 4: Token not being used

**Symptoms**:
```
WARNING: HuggingFace token (HF_TOKEN) not provided
```

**Solutions**:
1. Check environment variable is set:
   ```bash
   echo $HF_TOKEN
   # Should output: hf_YourToken
   ```

2. Verify in Python:
   ```python
   import os
   print(f"HF_TOKEN: {os.getenv('HF_TOKEN')}")
   ```

3. Restart application after setting token

4. Check `.env` file is loaded:
   ```python
   from dotenv import load_dotenv
   load_dotenv()  # Load .env file
   ```

---

## 🔒 Security Best Practices

### ✅ DO

1. **Store in environment variables**:
   ```bash
   # .env file (not committed)
   HF_TOKEN=hf_YourToken
   ```

2. **Use secrets management** in production:
   ```bash
   # Kubernetes secret
   kubectl create secret generic hf-token --from-literal=HF_TOKEN=hf_YourToken

   # Docker secret
   echo "hf_YourToken" | docker secret create hf_token -
   ```

3. **Rotate tokens regularly**:
   - Generate new token every 90 days
   - Revoke old tokens immediately

4. **Use read-only tokens**:
   - Select "Read" permission only
   - Don't grant "Write" unless needed

### ❌ DON'T

1. **Never commit tokens to git**:
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   echo "*.token" >> .gitignore
   ```

2. **Never hardcode tokens**:
   ```python
   # ❌ WRONG
   api_key = "hf_abc123def456"

   # ✅ CORRECT
   api_key = os.getenv('HF_TOKEN')
   ```

3. **Never share tokens publicly**:
   - Don't post in issues
   - Don't share in chat
   - Don't include in screenshots

4. **Never use personal tokens in CI/CD**:
   - Create separate token for automation
   - Use organization tokens for teams

---

## 📊 Token Types Comparison

| Feature | No Token | Read Token | Write Token |
|---------|----------|------------|-------------|
| Public models | ⚠️ Limited | ✅ Full | ✅ Full |
| Gated models | ❌ No | ✅ Yes | ✅ Yes |
| Private models | ❌ No | ✅ Yes | ✅ Yes |
| Rate limit | 🔴 Low | 🟢 High | 🟢 High |
| Download speed | 🔴 Throttled | 🟢 Fast | 🟢 Fast |
| Upload models | ❌ No | ❌ No | ✅ Yes |
| Security | 🟢 Lowest risk | 🟡 Low risk | 🔴 Higher risk |

**Recommendation**: Use **Read Token** for production.

---

## 🎯 Quick Reference

### Environment Setup

```bash
# .env file
HF_TOKEN=hf_YourTokenHere
HF_MODEL_PATH=/models/huggingface
HF_DEVICE=cuda

# Start application
docker-compose up -d

# Verify
curl http://localhost:8000/ready
```

### Python Usage

```python
# Initialize from environment
from agent.tools.llm_provider import initialize_from_env

provider = initialize_from_env()

# Generate text
response = await provider.generate(
    prompt="Write a Python function",
    task=TaskType.CODE_GENERATION
)

print(response.text)
```

### Common Models

```python
# Public models (token recommended)
- "gpt2"  # Small, for testing
- "distilgpt2"  # Faster, smaller

# Gated models (token REQUIRED)
- "meta-llama/Llama-3.2-3B-Instruct"
- "meta-llama/Llama-2-7b-chat-hf"
- "mistralai/Mistral-7B-Instruct-v0.2"

# Code models
- "Qwen/Qwen2.5-Coder-7B-Instruct"
- "codellama/CodeLlama-7b-Instruct-hf"
```

---

## 📞 Getting Help

### HuggingFace Support

- **Documentation**: [https://huggingface.co/docs](https://huggingface.co/docs)
- **Forum**: [https://discuss.huggingface.co](https://discuss.huggingface.co)
- **Discord**: [https://hf.co/join/discord](https://hf.co/join/discord)

### VAAL AI Empire Support

- **Check logs**: `docker-compose logs app`
- **Run tests**: `pytest tests/test_integration.py::TestHuggingFaceTokenUsage -v`
- **Verify config**: `python -c "from agent.tools.llm_provider import initialize_from_env; initialize_from_env()"`

---

## ✅ Checklist

Before deploying to production:

- [ ] HuggingFace account created
- [ ] Access token generated (Read permission)
- [ ] Token saved in `.env` file
- [ ] `.env` file added to `.gitignore`
- [ ] Token tested with small model
- [ ] Gated model terms accepted (if using gated models)
- [ ] Application can load models successfully
- [ ] Token rotation schedule established

---

**Last Updated**: 2026-01-26
**HuggingFace Token Format**: `hf_[40 random characters]`
**Token URL**: https://huggingface.co/settings/tokens
