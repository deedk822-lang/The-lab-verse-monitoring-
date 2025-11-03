<<<<<<< HEAD
# Use Node.js 18 LTS as base image
FROM public.ecr.aws/docker/library/node:20-alpine

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    ffmpeg \
    imagemagick \
    redis

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm install --omit=dev

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Create uploads directory
RUN mkdir -p uploads

# Set permissions
RUN chown -R node:node /app

# Switch to non-root user
USER node

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node healthcheck.js

# Start the application
CMD ["npm", "start"]
=======
# Multi-stage build for The-Lap-Verse-Monitoring – Production Hardened
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force
COPY . .
RUN npm run build   # emits dist/

FROM node:20-alpine AS production

# Non-root user
RUN addgroup -S lapverse && adduser -S lapverse -G lapverse
WORKDIR /app

# Copy artifacts
COPY --from=builder --chown=lapverse:lapverse /app/dist ./dist
COPY --from=builder --chown=lapverse:lapverse /app/node_modules ./node_modules
COPY --from=builder --chown=lapverse:lapverse /app/package*.json ./

# Runtime dirs
RUN mkdir -p /app/logs && chown -R lapverse:lapverse /app
USER lapverse

# Env
ENV NODE_ENV=production \
    PORT=3000 \
    REDIS_URL=redis://redis:6379 \
    JWT_SECRET=${JWT_SECRET} \
    KAGGLE_API_KEY=${KAGGLE_API_KEY} \
    GEMINI_API_KEY=${GEMINI_API_KEY:-}

# Healthcheck (hits /health endpoint)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node -e "require(\'http\').get(\'http://localhost:3000/health\',(r)=>process.exit(r.statusCode===200?0:1))"

EXPOSE 3000
CMD ["node","dist/index.js"]

>>>>>>> origin/feat/ai-connectivity-layer
