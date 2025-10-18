FROM node:18-alpine AS deps
RUN apk add --no-cache python3 make g++
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force

FROM node:18-alpine
RUN apk add --no-cache curl
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
USER node
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node healthcheck.js
CMD ["node","src/index.js"]