FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy application
COPY . .

# Expose port and start application
EXPOSE 3001
CMD ["node", "src/server.js"]
