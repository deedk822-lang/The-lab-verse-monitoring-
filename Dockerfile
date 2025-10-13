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

