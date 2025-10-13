# Build stage
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /quantumguard .

# Final stage
FROM alpine:latest
WORKDIR /
COPY --from=builder /quantumguard /quantumguard
EXPOSE 3001
CMD ["/quantumguard"]