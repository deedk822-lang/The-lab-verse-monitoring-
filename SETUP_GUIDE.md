# PR Fix Agent - Setup & Usage Guide

## 🎯 Conventional Python Package Structure

This project follows Python packaging best practices with proper imports.

```
pr-fix-agent/
├── src/pr_fix_agent/                    # Source package
│   ├── __init__.py
│   ├── security.py
│   └── analyzer.py
├── tests_real/             # Test suite
├── setup.py               # Package configuration
├── pyproject.toml         # Modern Python packaging
└── README.md
```

---

## 📦 Installation (Recommended Approach)

### Development Installation

The **conventional and recommended** way to work with this package:

```bash
# Navigate to project root
cd pr-fix-agent

# Install in editable mode (development)
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

**Why this is the conventional approach:**
- ✅ No `sys.path` manipulation needed
- ✅ Imports work naturally: `from pr_fix_agent.security import SecurityValidator`
- ✅ Changes to code reflect immediately
- ✅ Works with all Python tools (pytest, mypy, IDEs)
- ✅ Industry standard practice

---

## 🚀 Quick Start

### After Installation

```bash
# 1. Verify installation
python -c "from pr_fix_agent.security import SecurityValidator; print('✓ Installed correctly')"

# 2. Run tests (pytest auto-discovers them)
pytest tests_real/ -v

# 3. Use the tools
pr-fix-agent --health-check
python benchmarking_real.py --models codellama
python continuous_improvement_real.py --repo-path .
```

---

## 🔧 Alternative: PYTHONPATH Method

If you prefer not to install the package:

```bash
# Set PYTHONPATH to project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Now imports work
python -c "from pr_fix_agent.security import SecurityValidator; print('Works!')"

# Run tests
pytest tests_real/ -v
```

**Add to shell profile for persistence:**
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export PYTHONPATH="${PYTHONPATH}:/path/to/pr-fix-agent"' >> ~/.bashrc
```

---

## 📝 Import Convention

### ✅ Correct (Conventional) Imports

After installation with `pip install -e .`:

```python
# In your code or tests
from pr_fix_agent.security import SecurityValidator, SecurityError
from pr_fix_agent.analyzer import PRErrorAnalyzer

# This is the conventional Python package import
# No sys.path manipulation needed!
```

### ❌ Incorrect (Non-conventional) Imports

```python
# DON'T do this (not conventional)
import sys
sys.path.insert(0, "path/to/src")
from security import SecurityValidator

# This requires manual path manipulation
# Not the Python conventional way
```

---

## 🧪 Running Tests

### With Installation (Conventional)

```bash
# After: pip install -e .

# Run all tests
pytest tests_real/ -v

# Run specific test file
pytest tests_real/test_security_real.py -v

# With coverage
pytest tests_real/ --cov=src --cov-report=html
```

---

## 🏗️ Development Workflow

### 1. Initial Setup (One Time)

```bash
# Clone repository
git clone <repo-url>
cd pr-fix-agent

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in editable mode (conventional)
pip install -e ".[dev]"

# Verify
python -c "from pr_fix_agent.security import SecurityValidator; print('✓ Ready')"
```

### 2. Make Changes

Edit files in `src/pr_fix_agent/`, tests in `tests_real/`

### 3. Test Changes

```bash
# Run affected tests
pytest tests_real/test_security_real.py -v

# Run all tests
pytest tests_real/ -v
```

---

## 🔍 Why This Is Conventional

### Python Packaging Standards

1. **PEP 517/518**: Modern Python packaging
2. **Editable installs**: Standard for development (`pip install -e .`)
3. **Package discovery**: setuptools finds packages automatically
4. **Import resolution**: Packages are imported by their distribution/package name (for this repo `pr_fix_agent`), not by `src` (e.g., `from pr_fix_agent.X import Y`).

---

## 📚 Additional Commands

### Format Code

```bash
black src/pr_fix_agent/ tests_real/ *.py
```

### Lint

```bash
ruff check src/pr_fix_agent/ tests_real/ *.py
```

### Type Check

```bash
mypy src/pr_fix_agent/
```

### Full Evaluation

```bash
python run_comprehensive_evaluation.py
```
