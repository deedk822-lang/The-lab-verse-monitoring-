# Configuration Files

## price-baseline.json

This file defines the baseline costs and limits for AI providers to prevent unexpected billing increases.

### Structure:

- `providers`: Cost per 1M tokens for each AI provider
- `softLimits`: Monthly budget and daily token limits
- `alertThresholds`: Warning levels (0.8 = 80%)

### Usage:

The price-gate workflow automatically validates that:
- No provider costs exceed baseline
- Monthly budget stays within limits
- Daily token usage is monitored

This prevents accidental cost overruns from API changes or configuration errors.
