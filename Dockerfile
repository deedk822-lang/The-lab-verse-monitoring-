# Use a slim Node.js image
FROM node:18-slim

# Set working directory FIRST
WORKDIR /app

# Create runtime directory explicitly
RUN mkdir -p /app/runtime

# Copy package files first (for better layer caching)
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy the rest of the application code (with trailing slash)
COPY . /app/

# Create non-root user after copying files
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Start the server
CMD ["node", "app.js"]
