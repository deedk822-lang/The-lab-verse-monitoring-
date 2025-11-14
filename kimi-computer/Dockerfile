# Dockerfile for Kimi Computer App
FROM node:18-slim

# Create app directory
WORKDIR /app

# Install app dependencies
COPY package*.json ./
RUN npm install

# Copy app source
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port and start app
EXPOSE 3000
CMD [ "npm", "start" ]
