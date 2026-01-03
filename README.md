# Lab-Verse Monitoring Dashboard

A production-ready real-time monitoring and analytics dashboard for Lab-Verse infrastructure.

## Features

✅ **Real-time Metrics** - CPU, memory, disk, network monitoring  
✅ **Performance Analytics** - Response times, throughput, success rates  
✅ **Alert Management** - Configurable thresholds and notifications  
✅ **System Logs** - Real-time log streaming with filtering  
✅ **Service Health** - Monitor all critical services  
✅ **Dark Mode** - Beautiful dark/light theme support  
✅ **Responsive Design** - Works on desktop, tablet, mobile  
✅ **API Integration** - RESTful API for custom integrations  

## Quick Start

### Prerequisites

- Node.js 18+
- npm or yarn
- Vercel account (for deployment)

### Installation

```bash
# Clone the repository
git clone https://github.com/deedk822-lang/The-lab-verse-monitoring-.git
cd The-lab-verse-monitoring-

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Edit .env.local with your configuration
```

### Development

```bash
# Start development server
npm run dev

# Open http://localhost:3000 in your browser
```

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Project Structure

```
src/
├── app/
│   ├── page.tsx              # Dashboard home
│   ├── performance/          # Performance metrics
│   ├── alerts/               # Alert management
│   ├── logs/                 # System logs
│   ├── health/               # Service health
│   ├── settings/             # Configuration
│   ├── api/                  # API routes
│   ├── layout.tsx            # Root layout
│   └── globals.css           # Global styles
├── components/
│   ├── Navbar.tsx            # Top navigation
│   ├── Sidebar.tsx           # Left sidebar
│   ├── StatCard.tsx          # Metric cards
│   ├── AlertBox.tsx          # Alert display
│   ├── charts/               # Chart components
│   ├── ThemeProvider.tsx     # Theme management
│   └── ui/                   # Reusable UI components
└── lib/
    └── utils.ts              # Utility functions
```

## API Endpoints

### Metrics
```
GET /api/metrics
Returns current system metrics and performance data
```

### Health Check
```
GET /api/health
Returns health status of all services
```

## Configuration

Edit `.env.local` to configure:

- Database connection
- API endpoints
- Integrations (Slack, Grafana)
- Feature flags
- Retention policies

## Deployment

### Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel
```

### Deploy to Docker

```bash
# Build Docker image
docker build -t lab-verse-monitoring .

# Run container
docker run -p 3000:3000 lab-verse-monitoring
```

## Key Technologies

- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization
- **Radix UI** - Accessible components
- **Next-themes** - Dark mode support

## Performance Metrics Tracked

- CPU Usage
- Memory Utilization
- Disk I/O
- Network Throughput
- API Response Times
- Request Success/Error Rates
- System Uptime
- Service Health Status

## Architecture

```
┌─────────────────┐
│  Web Browser    │
└────────┬────────┘
         │ HTTP/WebSocket
         ↓
┌─────────────────────┐
│  Next.js Frontend   │
│  (React + TypeScript)│
└────────┬────────────┘
         │ REST API
         ↓
┌─────────────────────┐
│  API Layer          │
│  (Node.js/Express)  │
└────────┬────────────┘
         │ Database/Cache
         ↓
┌─────────────────────┐
│  Monitoring Data    │
│  (PostgreSQL/Redis) │
└─────────────────────┘
```

## Contributing

1. Create a feature branch
2. Commit changes
3. Push to branch
4. Open a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.

## Roadmap

- [ ] Grafana integration
- [ ] Prometheus metrics export
- [ ] Custom dashboard creation
- [ ] Advanced alerting rules
- [ ] Team collaboration features
- [ ] Multi-tenant support

---

**Version:** 1.0.0  
**Last Updated:** January 3, 2026  
**Maintainer:** Lab-Verse Team
