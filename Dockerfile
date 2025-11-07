
# Use a slim Node.js image
FROM node:18-slim

# Create a non-root user
RUN useradd -m -u 1000 user
USER user

# Set the working directory
ENV PATH="/home/user/.local/bin:$PATH"
WORKDIR /app

# Copy package files and install dependencies
COPY --chown=user ./package*.json ./
RUN npm install

# Copy the rest of the application code
COPY --chown=user . .

# Expose the port and start the server
EXPOSE 7860
CMD ["node", "app.js"]
