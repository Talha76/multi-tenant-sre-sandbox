# Runbook: High Latency Incident

**Service:** payment-service / search-service  
**Category:** Performance  
**Last Updated:** 2025-08-19  

---

## 1. Alert

- **Trigger:** Grafana alert `95% Latency > 300ms for 1m`  
- **Source:**
  - Prometheus metrics:

    ```json
    histogram_quantile(
      0.95, 
      sum by (le) (
        rate(
          tenant_request_latency_seconds_bucket{path!="/metrics"}[$__rate_interval]
        )
      )
    )
    ```

  - [Grafana dashboard panel](http://localhost:3000/d/fc219930-598c-44e5-bb1b-91b99bbd339f/multi-tenant-sre-sandbox-dashboard?orgId=1&from=now-5m&to=now&timezone=browser&refresh=auto&viewPanel=panel-11)
- **Severity:** Critical

---

## 2. Initial Triage (First 5 Minutes)

1. **Acknowledge the alert** in Grafana/Alertmanager.  
2. **Check dashboards:**
   - Grafana → `Dashboard` -> `Multi-Tenant SRE Sandbox Dashboard` -> `Quantiles`.
   - Look at:
     - **95th percentile latency**
     - **Error rate (4xx/5xx)**
3. **Check recent logs**:
   - For `payment-service`:
     - in Grafana Explore (Loki):

     ```json
     {service_name="payment-service",status=~"[4|5]..",path!="/metrics"} 
     | json 
     | line_format "tenant={{.tenant}}, path={{.path}}"
     ```

     - in [Grafana dashboard panel](http://localhost:3000/d/fc219930-598c-44e5-bb1b-91b99bbd339f/multi-tenant-sre-sandbox-dashboard?orgId=1&from=now-5m&to=now&timezone=browser&refresh=auto&viewPanel=panel-24)

   - For `search-service`:
     - in Grafana Explore (Loki):

     ```json
     {service_name="search-service",status=~"[4|5]..",path!="/metrics"} 
     | json 
     | line_format "tenant={{.tenant}}, path={{.path}}"
     ```

     - in [Grafana dashboard panel](http://localhost:3000/d/fc219930-598c-44e5-bb1b-91b99bbd339f/multi-tenant-sre-sandbox-dashboard?orgId=1&from=now-5m&to=now&timezone=browser&refresh=auto&viewPanel=panel-22)

---

## 3. Debugging Steps

- **Step A – Check resource usage**
  - Run `docker stats` (if local) or check container monitoring.
  - Look for CPU/memory throttling.
  - Check [cAdvisor](http://localhost:8080/containers/).

- **Step B – Check service logs**
  - Identify spikes in `status=5xx` or unusually high `duration`.
  - Confirm if it’s **one tenant** or **all tenants**.

- **Step C – Dependency check**
  - Verify if `payment-service` latency comes from DB/API calls.

- **Step D – Load test replay**
  - Reproduce using `k6` or `vegeta` with lower RPS.
  - Compare with baseline.

---

## 4. Mitigation

- **If service overloaded:**
  - Scale up container: `docker-compose up --scale payment-service=2 -d`
- **If DB/API dependency issue:**
  - Restart dependency container.
  - Apply backpressure (rate-limiting).
- **If logs show tenant-specific overload:**
  - Temporarily disable tenant traffic (if feature toggle available).

---

## 5. Escalation

- If unresolved after **30 minutes**, escalate to **Team Lead**.  
- If dependency issue → escalate to **Database/Infra team**.  

---

## 6. Post-Incident

- Export logs for the incident window:

  ```bash
  logcli query '{service_name="payment-service"}' --limit=5000 --since=1h > incident-logs.json
  ```

Here’s a concise **Baseline Recording Checklist** section you can append to your `incident-latency.md` runbook:

---

## 7. Baseline Recording Checklist

Before deploying or load testing, capture baseline metrics for healthy service performance. This will help in comparing during incidents.

### 7.1 Latency & Throughput

- Measure **response time percentiles** (p95, p99) for all critical endpoints.
- Record **requests per second (RPS)** handled per endpoint.
- Note any **timeouts** or slow endpoints.

### 7.2 Error Rates

- Record **4xx / 5xx error rates** for each endpoint.
- Confirm normal error thresholds for each service.

### 7.3 Resource Usage

- CPU and memory usage of containers (`docker stats` / cAdvisor).
- Network and disk I/O per service.
- Database connection pool usage and latency.

### 7.4 Dependencies

- Response times and error rates for **downstream dependencies** (DBs, APIs) if applicable.
- Cache hit/miss ratios if applicable.

### 7.5 Logging & Tracing

- Sample structured logs from each service for **normal operation**.
- Record distributed tracing metrics if using tracing (latency per service hop).

### 7.6 Environment Context

- Note **RPS, test duration, environment config** during baseline capture.
- Record container versions, service replicas, and configuration settings.

> **Tip:** Store all baseline measurements in a versioned file (e.g., `baselines/<service>-<date>.json`) for easy comparison during incidents.
