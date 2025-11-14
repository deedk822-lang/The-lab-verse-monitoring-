# 🔒 Security Hardening Example

This document demonstrates the **before** and **after** of automated security hardening using Moonshot AI (Kimi).

---

## Example 1: Python Script

### ❌ Before (Insecure)

```python
import os

# Hardcoded credentials (bad!)
API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "mysecretpassword"

def get_user(user_id):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)

def process_file(filename):
    # No input validation
    with open(filename) as f:
        return f.read()
```

**Security Issues:**
- ❌ Hardcoded credentials
- ❌ SQL injection vulnerability
- ❌ No input validation
- ❌ Directory traversal risk
- ❌ Poor error handling

### ✅ After (Hardened)

```python
import os
from typing import Optional, Any

# Use environment variables for sensitive data
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable must be set")

DB_PASSWORD = os.getenv("DB_PASSWORD")
if not DB_PASSWORD:
    raise ValueError("DB_PASSWORD environment variable must be set")


def get_user(user_id: int) -> Optional[dict]:
    """
    Get user by ID with input validation and SQL injection prevention.
    
    Args:
        user_id: User ID (must be positive integer)
        
    Returns:
        User data dictionary or None if not found
        
    Raises:
        ValueError: If user_id is invalid
    """
    # Input validation
    if not isinstance(user_id, int):
        raise ValueError("user_id must be an integer")
    
    if user_id < 0:
        raise ValueError("user_id must be positive")
    
    # Use parameterized query to prevent SQL injection
    query = "SELECT * FROM users WHERE id = ?"
    
    try:
        result = db.execute(query, (user_id,))
        return result.fetchone()
    except Exception as e:
        # Log error without exposing sensitive information
        print(f"Database error occurred while fetching user")
        raise


def process_file(filename: str) -> str:
    """
    Process file with input validation and error handling.
    
    Args:
        filename: Path to file to process
        
    Returns:
        File contents as string
        
    Raises:
        ValueError: If filename is invalid
        FileNotFoundError: If file doesn't exist
        PermissionError: If file cannot be read
    """
    # Input validation
    if not filename:
        raise ValueError("filename cannot be empty")
    
    if not isinstance(filename, str):
        raise ValueError("filename must be a string")
    
    # Prevent directory traversal attacks
    if ".." in filename or filename.startswith("/"):
        raise ValueError("Invalid filename: directory traversal detected")
    
    # Validate file exists and is readable
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")
    
    if not os.path.isfile(filename):
        raise ValueError(f"Path is not a file: {filename}")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {filename}")
    except Exception as e:
        # Log error without exposing sensitive information
        print(f"Error reading file")
        raise
```

**Security Improvements:**
- ✅ Credentials from environment variables
- ✅ Parameterized SQL queries
- ✅ Type hints and validation
- ✅ Directory traversal prevention
- ✅ Proper error handling
- ✅ Comprehensive documentation

---

## Example 2: Docker Compose

### ❌ Before (Insecure)

```yaml
services:
  db:
    image: postgres:latest
    environment:
      POSTGRES_PASSWORD: mysecretpassword
      POSTGRES_USER: admin
  
  app:
    image: myapp:latest
    environment:
      API_KEY: sk-1234567890
```

**Security Issues:**
- ❌ Using `latest` tag (unpredictable)
- ❌ Hardcoded passwords
- ❌ No resource limits
- ❌ Running as root
- ❌ No security options

### ✅ After (Hardened)

```yaml
services:
  db:
    image: postgres:15.3-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_USER: ${DB_USER:-postgres}
    user: postgres
    read_only: true
    tmpfs:
      - /tmp
      - /var/run/postgresql
    security_opt:
      - no-new-privileges:true
      - seccomp:unconfined
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETUID
      - SETGID
    resources:
      limits:
        memory: 512M
        cpus: '0.5'
      reservations:
        memory: 256M
        cpus: '0.25'
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
  
  app:
    image: myapp:1.2.3
    environment:
      API_KEY: ${API_KEY}
    user: "1000:1000"
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    resources:
      limits:
        memory: 256M
        cpus: '0.25'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
```

**Security Improvements:**
- ✅ Specific image versions
- ✅ Environment variable secrets
- ✅ Non-root users
- ✅ Read-only filesystems
- ✅ Security options (no-new-privileges)
- ✅ Capability dropping
- ✅ Resource limits
- ✅ Health checks
- ✅ Restart policies

---

## Example 3: Dockerfile

### ❌ Before (Insecure)

```dockerfile
FROM python:latest

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python", "app.py"]
```

**Security Issues:**
- ❌ Using `latest` tag
- ❌ Running as root
- ❌ No multi-stage build
- ❌ Copying everything (including secrets)
- ❌ No vulnerability scanning

### ✅ After (Hardened)

```dockerfile
# Multi-stage build for minimal attack surface
FROM python:3.11-slim-bullseye AS builder

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /build

# Copy only requirements first (layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim-bullseye

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code (use .dockerignore to exclude secrets)
COPY --chown=appuser:appuser . .

# Set PATH for user-installed packages
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run application
CMD ["python", "app.py"]
```

**Security Improvements:**
- ✅ Specific Python version
- ✅ Multi-stage build
- ✅ Non-root user
- ✅ Layer caching optimization
- ✅ Proper file ownership
- ✅ Health check
- ✅ No secrets in layers

---

## How to Apply These Improvements

### Manual Hardening

```bash
# Single file
make secure FILE=your-file.py

# Entire repository
make secure-bulk
```

### Automated CI/CD

The GitHub Actions workflows will automatically harden files on every PR:

1. **On PR**: Changed files are hardened automatically
2. **Weekly**: Full repository audit and hardening
3. **Manual**: Trigger hardening workflow anytime

---

## Security Principles Applied

### 🔐 Secrets Management
- Remove hardcoded credentials
- Use environment variables
- Suggest secret management tools

### ✅ Input Validation
- Validate all user inputs
- Sanitize data before use
- Implement whitelist validation

### 🛡️ Secure Defaults
- Fail securely by default
- Principle of least privilege
- Disable unnecessary features

### 🚨 Error Handling
- Don't expose sensitive info in errors
- Log errors securely
- Implement proper exception handling

### 🔒 Defense in Depth
- Multiple layers of security
- Network isolation
- Resource limits

---

## Next Steps

1. **Review** the hardened files
2. **Test** in a staging environment
3. **Update** your secrets management
4. **Deploy** with confidence

---

**Powered by:** [Moonshot AI (Kimi)](https://www.moonshot.cn/)

