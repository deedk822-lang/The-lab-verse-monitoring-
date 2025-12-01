# Stage 1: Build the TypeScript code
FROM node:18-alpine AS builder
WORKDIR /app

# Copy package files and install dependencies
COPY package.json ./
RUN npm install

# Copy the source code and tsconfig
COPY . .

# Build the TypeScript code
RUN npm run build

# Stage 2: Create the production image
FROM node:18-alpine
WORKDIR /app

# Copy the built code and package.json from the builder stage
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./

# Install only production dependencies
RUN npm install --omit=dev

# Expose the port the server is running on
EXPOSE 8080

# Set the command to run the application
CMD ["npm", "start"]