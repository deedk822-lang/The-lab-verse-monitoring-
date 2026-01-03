# Professional Full-Stack Generator (2026)

AI-powered full-stack application generator with enterprise-grade features.

## Prerequisites

- Python 3.9+
- Node.js 18+
- Docker & Docker Compose
- Moonshot AI API key

## Quick Start

```bash
# 1. Initial setup (one-time)
chmod +x setup.sh && ./setup.sh
export MOONSHOT_API_KEY="your-api-key-here"

# 2. Generate application
make generate

# 3. Start development
make dev
# Access: http://localhost:3000 (frontend), http://localhost:8000/docs (API)

# 4. Run tests
make test

# 5. Deploy (push to main branch)
git push origin main
# CI/CD handles the rest
```

## Available Commands

```bash
make generate              # Generate full-stack from contract.yml
make dev                  # Start development servers
make test                 # Run all tests (unit, e2e, performance)
make test-unit            # Unit tests only
make test-e2e             # End-to-end tests
make test-performance     # Performance/load tests
make security             # Security scans
make deploy               # Deploy application
make clean                # Clean generated files
make status               # Show project status
make help                 # Show help
```

## Features

- **Contract-First**: Define API in YAML, generate both ends
- **Type Safety**: Pydantic + TypeScript + Zod validation
- **Security**: Built-in security scanning and validation
- **Testing**: Unit, E2E, and performance tests
- **Monitoring**: Grafana/Prometheus setup included
- **CI/CD Ready**: Deployment pipeline configured
- **Cost Tracking**: AI token usage monitoring

## Architecture

```
generated_project/
├── backend/           # FastAPI application
│   ├── app/          # Main application code
│   ├── tests/        # Unit/integration tests
│   └── requirements.txt
├── frontend/          # Next.js application
│   ├── app/          # App Router pages
│   ├── components/   # React components
│   └── package.json
├── tests/            # Performance/E2E tests
├── monitoring/       # Grafana/Prometheus configs
└── generated_types/  # Shared types (Pydantic/TS)
```

## Environment Variables

Create `.env` file with:
```
MOONSHOT_API_KEY=your_key_here
NEXT_PUBLIC_API_ENDPOINT=http://localhost:8000
HUBSPOT_API_KEY=your_key_here
MAILCHIMP_API_KEY=your_key_here
OLLAMA_ENDPOINT=http://localhost:11434
```

## License

MIT
```

## Support

For issues, create a GitHub issue or contact support.
