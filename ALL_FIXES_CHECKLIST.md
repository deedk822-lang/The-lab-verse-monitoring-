# all-fixes checklist (from provided all-fixes.md)

This checklist captures the remediation items enumerated in the provided `all-fixes.md` attachment.

## CI workflow
- [ ] `.github/workflows/kimi-enhancer.yaml`: remove `|| true` from pytest commands.
- [ ] `.github/workflows/kimi-enhancer.yaml`: add `continue-on-error: true` to the "🧪 Run tests" step so failures are visible but do not halt subsequent steps.

## Packaging / dependencies
- [ ] `setup.py`: remove `pytest>=7.0.0` from `install_requires`.
- [ ] `setup.py`: ensure pytest is only in `extras_require["dev"]` (alongside `pytest-cov`).
- [ ] `pyproject.toml`: align `ruff` dev dependency to `ruff>=0.0.250`.

## Documentation
- [ ] `SETUP_GUIDE.md`: replace `python pr_fix_agent_production.py --health-check` with `pr-fix-agent --health-check`.
- [ ] `SETUP_GUIDE.md`: correct src-layout import guidance (use `from pr_fix_agent.X import Y`, not `from src.X import Y`).

## pr_fix_agent logic
- [ ] `src/pr_fix_agent/analyzer.py`: replace substring check for requirements with normalized, line-based package matching.
- [ ] `src/pr_fix_agent/analyzer.py`: make `OllamaAgent.query` fail explicitly (raise/structured error), not by returning "Error: ..." strings.
- [ ] `src/pr_fix_agent/analyzer.py`: preserve original casing in extract helpers (search with `.lower()` but return original line).

## Security hardening
- [ ] `src/pr_fix_agent/security.py`: replace bare `except:` in JSON validation with specific exceptions.
- [ ] `src/pr_fix_agent/security.py`: make `RateLimiter` thread-safe with a lock.

## CLI robustness
- [ ] `src/pr_fix_agent/production.py`: resolve and validate `--repo-path` early; use resolved path consistently.

## Tests
- [ ] `tests_real/test_fixer_real.py`: avoid external Ollama dependency by using `MockOllamaAgent` (no localhost:11434 calls).

---

Notes:
- Production should continue to use real Ollama models.
- Tests should not require network services; prefer mocks/fakes for determinism.
