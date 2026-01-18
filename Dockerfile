 feat/ci-cd-alibaba-cloud-integration-10364585358297276748
# Dockerfile

 main
FROM node:18-alpine

# Create app directory
WORKDIR /opt/myapp

 feat/ci-cd-alibaba-cloud-integration-10364585358297276748
# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Remove any existing GLM-4.7 references to prevent conflicts with the Zhipu AI SDK.
RUN rm -rf node_modules/*glm* || true
RUN find . -name "*glm*" -delete || true

# Install Python dependencies for security scanner
RUN apk add --no-cache python3 py3-pip curl bash jq

# Install Python and build tools needed for some packages
RUN apk add --no-cache python3 py3-pip make g++ gcc linux-headers libc-dev python3-dev

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Install additional tools
RUN apk add --no-cache curl bash jq
 main

# Install Alibaba Cloud CLI
RUN curl -LO https://aliyuncli.alicdn.com/aliyun-cli-linux-latest-amd64.tgz && \
    tar xzvf aliyun-cli-linux-latest-amd64.tgz && \
    mv aliyun /usr/local/bin/ && \
    rm aliyun-cli-linux-latest-amd64.tgz

 feat/ci-cd-alibaba-cloud-integration-10364585358297276748

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Remove any existing GLM-4.7 references (keeping our new implementation)
RUN rm -rf node_modules/*glm* 2>/dev/null || true
RUN find . -name "*glm*" -not -path "./src/*" -delete 2>/dev/null || true

 main
# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001
USER nextjs

# Expose port
EXPOSE 3000

 feat/ci-cd-alibaba-cloud-integration-10364585358297276748
# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Health check - this matches the URL you specified
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/api/test/health || exit 1
 main

# Start the application
CMD ["npm", "start"]
