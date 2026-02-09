# Deployment Guide 🚀

Complete guide for deploying Content Creator AI to various platforms.

## Table of Contents

- [Replit Deployment](#replit-deployment)
- [Docker Deployment](#docker-deployment)
- [VPS/Cloud Deployment](#vpscloud-deployment)
- [Heroku Deployment](#heroku-deployment)
- [Vercel Deployment](#vercel-deployment)
- [Production Checklist](#production-checklist)

---

## Replit Deployment

### Method 1: Import from GitHub (Recommended)

1. Go to [Replit](https://replit.com)
2. Click "Create Repl" → "Import from GitHub"
3. Paste your repository URL
4. Replit will auto-detect Node.js

### Method 2: Manual Upload

1. Create a new Node.js Repl
2. Upload all files from `content-creator-ai/`
3. Replit will detect `package.json`

### Configuration

1. Open "Secrets" (🔒 icon in left sidebar)
2. Add your environment variables:
   ```
   GOOGLE_API_KEY=your-key
   OPENAI_API_KEY=your-key
   ZAI_API_KEY=your-key
   API_KEY=your-secure-api-key
   DEFAULT_PROVIDER=google
   ```

3. Click "Run" - Replit will:
   - Install dependencies automatically
   - Start the server
   - Expose it via a Replit URL

### Custom Domain (Replit Hacker Plan)

1. Go to your Repl
2. Click on the domain (e.g., `your-repl.replit.app`)
3. Click "Link a custom domain"
4. Follow the instructions

---

## Docker Deployment

### Using Docker Compose (Recommended)

1. **Clone the repository**:
```bash
git clone <your-repo>
cd content-creator-ai
```

2. **Create .env file**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Start with Docker Compose**:
```bash
docker-compose up -d
```

This will start:
- Content Creator AI (port 3000)
- Redis (port 6379)
- LocalAI (port 8080) - optional

4. **Check logs**:
```bash
docker-compose logs -f content-creator
```

5. **Stop**:
```bash
docker-compose down
```

### Using Docker Only

1. **Build image**:
```bash
docker build -t content-creator-ai .
```

2. **Run container**:
```bash
docker run -d \
  -p 3000:3000 \
  -e GOOGLE_API_KEY=your-key \
  -e API_KEY=your-api-key \
  -e DEFAULT_PROVIDER=google \
  --name content-creator \
  content-creator-ai
```

3. **View logs**:
```bash
docker logs -f content-creator
```

---

## VPS/Cloud Deployment

### Prerequisites

- Ubuntu 20.04+ / Debian 11+
- Node.js 18+
- nginx (optional, for reverse proxy)
- PM2 (for process management)

### Step-by-Step

1. **Install Node.js**:
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

2. **Install PM2**:
```bash
sudo npm install -g pm2
```

3. **Clone and setup**:
```bash
git clone <your-repo>
cd content-creator-ai
npm install --production
```

4. **Configure environment**:
```bash
cp .env.example .env
nano .env  # Edit with your keys
```

5. **Start with PM2**:
```bash
pm2 start server.js --name content-creator
pm2 save
pm2 startup  # Follow the instructions
```

6. **Setup nginx reverse proxy** (optional):

```nginx
# /etc/nginx/sites-available/content-creator
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # WebSocket support
    location /socket.io/ {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/content-creator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

7. **Setup SSL with Let's Encrypt**:
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

8. **Setup Redis** (optional):
```bash
sudo apt-get install redis-server
sudo systemctl enable redis-server
```

Update `.env`:
```env
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379
```

---

## Heroku Deployment

1. **Install Heroku CLI**:
```bash
npm install -g heroku
heroku login
```

2. **Create Heroku app**:
```bash
heroku create your-app-name
```

3. **Set environment variables**:
```bash
heroku config:set GOOGLE_API_KEY=your-key
heroku config:set API_KEY=your-api-key
heroku config:set DEFAULT_PROVIDER=google
heroku config:set NODE_ENV=production
```

4. **Deploy**:
```bash
git push heroku main
```

5. **Scale**:
```bash
heroku ps:scale web=1
```

6. **Add Redis** (optional):
```bash
heroku addons:create heroku-redis:hobby-dev
# Redis URL is automatically set
heroku config:set REDIS_ENABLED=true
```

7. **View logs**:
```bash
heroku logs --tail
```

---

## Vercel Deployment

**Note**: Vercel is primarily for static/serverless. For full Node.js with WebSockets, use other platforms.

If you want to try anyway:

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Create `vercel.json`:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "server.js",
      "use": "@vercel/node"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/server.js"
    }
  ]
}
```

3. Deploy:
```bash
vercel
```

4. Set environment variables in Vercel dashboard

**Limitation**: WebSocket support is limited on Vercel.

---

## Production Checklist

### Security

- [ ] Change default `API_KEY` to a secure random value
- [ ] Enable HTTPS/SSL
- [ ] Set `NODE_ENV=production`
- [ ] Use environment variables for all secrets
- [ ] Enable rate limiting
- [ ] Implement CORS policies
- [ ] Regular security updates: `npm audit fix`

### Performance

- [ ] Enable Redis caching
- [ ] Set up CDN for static files
- [ ] Enable gzip compression (built-in)
- [ ] Configure appropriate rate limits
- [ ] Monitor memory usage
- [ ] Set up auto-scaling if needed

### Monitoring

- [ ] Set up error tracking (Sentry, Rollbar)
- [ ] Configure log rotation
- [ ] Set up uptime monitoring
- [ ] Monitor API costs with `/api/stats`
- [ ] Set up alerts for errors/downtime

### Backup

- [ ] Backup Redis data if using
- [ ] Document your configuration
- [ ] Keep `.env.example` updated
- [ ] Version control (Git)

### Configuration

```env
# Production .env example
NODE_ENV=production
PORT=3000

# API Keys (required)
GOOGLE_API_KEY=your-production-key
OPENAI_API_KEY=your-production-key
ZAI_API_KEY=your-production-key

# Server
API_KEY=your-very-secure-random-string-here

# Redis (recommended for production)
REDIS_ENABLED=true
REDIS_URL=redis://your-redis-url:6379

# Rate Limiting
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100

# Logging
LOG_LEVEL=info

# Costs
TRACK_COSTS=true
```

### Health Monitoring Script

Create a simple monitoring script:

```bash
#!/bin/bash
# monitor.sh

HEALTH_URL="https://your-domain.com/api/health"

response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $response -eq 200 ]; then
  echo "✅ Service is healthy"
  exit 0
else
  echo "❌ Service is down (HTTP $response)"
  # Send alert (email, Slack, etc.)
  exit 1
fi
```

Set up cron job:
```bash
# Check every 5 minutes
*/5 * * * * /path/to/monitor.sh
```

---

## Scaling Considerations

### Horizontal Scaling

For high traffic, run multiple instances:

1. **With PM2**:
```bash
pm2 start server.js -i max  # Use all CPU cores
```

2. **With Docker**:
```bash
docker-compose up -d --scale content-creator=3
```

3. **Load Balancer**: Use nginx or cloud load balancer

### Database

Consider adding PostgreSQL/MongoDB for:
- User management
- Request history
- Analytics
- Content storage

### External Services

For production at scale:
- **S3/Cloud Storage**: Store generated images/videos
- **Queue System**: RabbitMQ/Redis Queue for async processing
- **Separate Redis**: Dedicated Redis instance
- **Monitoring**: DataDog, New Relic, Prometheus

---

## Troubleshooting

### Server won't start

1. Check logs: `pm2 logs` or `docker logs`
2. Verify environment variables
3. Check port availability
4. Ensure dependencies installed: `npm install`

### High memory usage

1. Check for memory leaks
2. Implement request timeouts
3. Clear cache regularly
4. Restart periodically: `pm2 restart all`

### Slow responses

1. Enable Redis caching
2. Optimize API calls
3. Increase server resources
4. Check network latency to AI providers

---

## Support

Need help with deployment?
- Check logs first
- Review the [README.md](./README.md)
- Test locally first
- Check cloud provider documentation

Happy deploying! 🚀
