# PR Fix Agent

Automated PR error fixing using Ollama LLMs.

## 🏗️ Conventional Python Package Structure

The codebase now follows 100% conventional Python packaging practices:

1. ✅ **Proper package structure** with `setup.py` and `pyproject.toml`
2. ✅ **Clean imports** using `from pr_fix_agent.X import Y`
3. ✅ **Standard workflow** with `pip install -e .`
4. ✅ **No sys.path manipulation** anywhere
5. ✅ **Industry-standard approach** like NumPy, Pandas, Flask
6. ✅ **Full tool compatibility** with pytest, mypy, IDEs
7. ✅ **Professional grade** code ready for production

## 🚀 Quick Start

```bash
# Install in editable mode
pip install -e .

# Run tests
pytest tests_real/ -v
```

## 🔍 Components

- **SecurityValidator**: Validates paths and inputs to prevent traversal and injection.
- **PRErrorAnalyzer**: Parses GitHub Actions logs and analyzes errors using AI.
- **PRErrorFixer**: Generates automated fixes for common CI/CD errors.

## 📖 Documentation

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed installation and usage instructions.
