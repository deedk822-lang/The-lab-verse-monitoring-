FROM node:18-alpine

# Create app directory
WORKDIR /opt/myapp

# Install Python and build tools needed for some packages
RUN apk add --no-cache python3 py3-pip make g++ gcc linux-headers libc-dev python3-dev

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Install additional tools
RUN apk add --no-cache curl bash jq

# Install Alibaba Cloud CLI
RUN curl -LO https://aliyuncli.alicdn.com/aliyun-cli-linux-latest-amd64.tgz && \
    tar xzvf aliyun-cli-linux-latest-amd64.tgz && \
    mv aliyun /usr/local/bin/ && \
    rm aliyun-cli-linux-latest-amd64.tgz

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Remove any existing GLM-4.7 references (keeping our new implementation)
RUN rm -rf node_modules/*glm* 2>/dev/null || true
RUN find . -name "*glm*" -not -path "./src/*" -delete 2>/dev/null || true

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001
USER nextjs

# Expose port
EXPOSE 3000

# Health check - this matches the URL you specified
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/api/test/health || exit 1

# Start the application
CMD ["npm", "start"]
