FROM node:20-slim
WORKDIR /app
COPY package* ./
RUN npm ci --omit=dev
COPY . .
EXPOSE 7860
CMD ["node","src/server.js"]
