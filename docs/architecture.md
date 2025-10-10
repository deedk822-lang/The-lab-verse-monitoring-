# LabVerse Monitoring & AI Project Manager - Architecture

```mermaid
flowchart LR
    %% Networks
    subgraph Public_Network [Public Network]
      Traefik{{Traefik Reverse Proxy}}
    end

    subgraph Monitoring_Network [Monitoring Network]
      Prometheus[(Prometheus)]
      Grafana[(Grafana)]
      Alertmanager[(Alertmanager)]
      NodeExporter[(Node Exporter)]
      Kimi[Kimi Instruct (AI PM)]
      Anomaly[Anomaly Detection Service]
      Cardinality[Cardinality Guardian]
    end

    subgraph Backend_Network [Backend Network]
      Postgres[(PostgreSQL)]
      Redis[(Redis)]
      RabbitMQ[(RabbitMQ)]
      Web[Web/API Service]
      Worker[Background Worker]
    end

    %% Traffic flow
    Traefik --- Web
    Traefik -.-> Kimi

    %% App <-> Backend
    Web <-->|DB| Postgres
    Web <-->|Cache| Redis
    Web <-->|Queue| RabbitMQ
    Worker --> RabbitMQ

    %% Monitoring
    Prometheus --> Grafana
    Prometheus --> Alertmanager
    Prometheus -->|scrape| Web
    Prometheus -->|scrape| Worker
    Prometheus -->|scrape| Kimi
    Prometheus -->|scrape| Anomaly
    Prometheus -->|scrape| Cardinality
    Prometheus -->|scrape| NodeExporter

    %% AI PM integrations
    Kimi -->|manages| Prometheus
    Kimi -->|manages| Grafana
    Kimi -->|alerts| Alertmanager
    Kimi -->|orchestrates| Web
    Kimi -->|orchestrates| Worker

    %% ML/Resilience services
    Anomaly -->|alerts| Alertmanager
    Cardinality -->|policies| Prometheus
```

## Notes
- Derived from `docker-compose.yml`, `docker-compose.kimi.yml`, and the Makefile.
- Shows networks (public, backend, monitoring), core infra (Prometheus, Grafana, Alertmanager), app stack (Web, Worker, Postgres, Redis, RabbitMQ), and AI/ML services (Kimi Instruct, Anomaly Detection, Cardinality Guardian).
