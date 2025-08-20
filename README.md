# Monitoring Stack with Disaster Recovery

A complete monitoring solution using Prometheus and Loki with automated disaster recovery capabilities using Restic backup.

## Overview

This project provides:

- **Prometheus + Loki monitoring stack** via Docker Compose
- **Grafana alerting** with Slack integration
- **Automated disaster recovery** with backup/restore capabilities
- **RTO/RPO measurement** for compliance and optimization

## Prerequisites

- Docker and Docker Compose
- `envsubst` (usually available in `gettext` package)
- `restic` for backup operations
- `jq` for JSON processing
- `curl` for API calls

## Quick Start

1. Clone and setup environment:

   ```bash
   cp .env.example .env
   # Edit .env and set your SLACK_WEBHOOK URL
   ```

2. Create prometheus and loki data path and change the ownerships of the directories:

   ```bash
   PROMETHEUS_DIR="./prometheus-data"
   LOKI_DIR="./loki-data"
   mkdir -p "$PROMETHEUS_DIR" "$LOKI_DIR"
   sudo chown -R 10001:10001 "$LOKI_DIR"
   sudo chown -R 65534:65534 "$PROMETHEUS_DIR"
   ```

3. Start the monitoring stack:

   ```bash
   ./manager.sh up -d
   ```

   Or if you want to build and then start:

   ```bash
   ./manager.sh up --build -d
   ```

4. **Access services:**
   - Prometheus: http://localhost:9090
   - Loki: http://localhost:3100
   - Grafana: http://localhost:3000
5. To run load test:

   ```bash
   ./manager.sh restart k6
   ```

## Manager Script Usage

The `manager.sh` script handles configuration templating and Docker Compose operations:

### Starting Services

```bash
./manager.sh start            # or 'up' or 'restart'
./manager.sh up -d            # Start in detached mode
./manager.sh up -d --build    # Build images and start in detached mode
```

### Stopping Services

```bash
./manager.sh stop       # or 'down'
./manager.sh down       # Stop and remove containers
./manager.sh down -v    # Remove volumes as well
```

### Configuration Management

The script automatically manages Grafana alerting configuration:

- **On start:** Creates `contact_points.yml` from template with environment variables
- **On stop:** Resets configuration back to template format

## Environment Variables

Configure the following in your `.env` file:

| Variable        | Description                          | Required |
| --------------- | ------------------------------------ | -------- |
| `SLACK_WEBHOOK` | Slack webhook URL for Grafana alerts | Yes      |

## Prometheus Metrics

- `tenant_requests_total (Counter)`: Total number of requests received by the tenant service
- `tenant_request_latency_seconds (Histogram)`: Latency of requests to the tenant service

### SLIs

- `sli:availability`: Measures the availability of the tenant service
- `sli:availability_per_service`: Measures the availability of the tenant service per individual service
- `sli:latency_ms:p95`: Measures the 95th percentile latency of requests to the tenant service
- `sli:latency_ms:p99`: Measures the 99th percentile latency of requests to the tenant service

## Disaster Recovery

### Manual DR Drill

Run the automated disaster recovery drill:

```bash
./dr_drill.sh
```

This script will:

1. Create backups using Restic
2. Record current state for RPO measurement
3. Simulate data loss
4. Restore from backup
5. Measure RTO (Recovery Time Objective)
6. Calculate RPO (Recovery Point Objective)

### DR Components

- **Backup Tool:** Restic (snapshot-based)
- **Backup Target:** `./prometheus-data/` and `./loki-data/`
- **Backup Storage:** Local (`./restic-backup/`)
- **Metrics:** RTO and RPO measurement

### DR Report

Check the report at:

```any
DR/drill-report.md
```

## Project Structure

```dir
.
├── data/
│   └── transactions.csv            # Transaction data
├── DR/
│   └── drill-report.md             # DR drill results and analysis
├── grafana/
│   └── provisioning/
│       ├── alerting/         # Grafana alerting configs
│       ├── dashboards/       # Grafana dashboards configs
│       └── datasources/      # Grafana data sources configs
├── loads/           # Load testing scripts
├── loki-data/       # Loki data volume
├── payment/         # Payment service app
├── postmortems/     # Postmortem documents
├── prometheus-data/ # Prometheus data volume
├── restic-backup/   # Backup repository
├── runbooks/        # Runbooks and operational guides
├── search/          # Search service app
├── .env             # Your environment config (create from example)
├── .env.example     # Example environment config
├── .gitignore       # Git ignore file
├── compose.sre.yml  # Docker Compose configuration
├── dr_drill.sh      # Disaster recovery drill script
├── make_random_request.py    # Random request maker script
├── manager.sh       # Main management script
├── nginx.conf       # nginx Configuration
├── prometheus-rules.yml      # Prometheus SLIs and SLOs rules
├── prometheus.yml   # Prometheus configuration
├── promtail.yml     # Promtail configuration
└── README.md        # This file
```

## Configuration Files

### Grafana Alerting

The project uses templated configuration for Grafana alerting:

- **Template:** `contact_points-template.yml` (version controlled)
- **Active config:** `contact_points.yml` (auto-generated)
- **Variables:** Replaced via `envsubst` from `.env` file

### Docker Compose

Services are defined in `compose.sre.yml` (not shown in provided files).

## Backup Strategy

- **Tool:** Restic (deduplicating backup program)
- **Schedule:** Manual via `dr_drill.sh` (can be automated via cron)
- **Retention:** Managed by Restic snapshots
- **Storage:** Local filesystem (can be extended to cloud storage)

## Monitoring Targets

Based on the DR script, the stack monitors:

- `payment-service` container logs
- `search-service` container logs
- General system metrics via Prometheus

## Development

### Adding New Services

1. Update `compose.sre.yml` with new service definition
2. Configure Prometheus scraping if needed
3. Add logging configuration for Loki ingestion
4. Update DR script if new data volumes are introduced

### Customizing Alerts

1. Modify `grafana/provisioning/alerting/contact_points-template.yml`, or you can use grafana GUI to manage alerting contact points. Later export the contact points to `contact_points-template.yml`.
2. Add environment variables to `.env.example` if needed
3. Update the manager script if new templating is required

## Troubleshooting

### Manager Script Issues

- Ensure `.env` file exists and contains required variables
- Check that `envsubst` is installed
- Verify file permissions on shell scripts

### DR Drill Issues

- Ensure Restic is installed and accessible
- Check that services are running before starting drill
- Verify network connectivity to service endpoints

### Grafana Alerts

- Check Slack webhook URL in `.env`
- Verify contact points configuration was generated correctly
- Test webhook connectivity manually
