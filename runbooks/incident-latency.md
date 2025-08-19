# Runbook: High Latency Incident

**Service:** payment-service / search-service  
**Category:** Performance  
**Last Updated:** 2025-08-19  

---

## 1. Alert

- **Trigger:** Grafana alert `Latency > 200mss for 5m`  
- **Source:** Prometheus metrics (`tenant_requests_total` / `duration`)  
- **Severity:** Critical  

---

## 2. Initial Triage (First 5 Minutes)

1. **Acknowledge the alert** in Grafana/Alertmanager.  
2. **Check dashboards:**
   - Grafana → `Latency Dashboard`
   - Look at:
     - **99th percentile latency**
     - **Error rate (4xx/5xx)**
     - **Request throughput**
3. **Check recent logs** in Grafana Explore (Loki):
   - For `payment-service`:

    ```json
    {service_name="payment-service"} | json | line_format "{{.tenant}} {{.status}} {{.path}} {{.duration}}"
    ```

   - For `search-service`:

     ```json
     {service_name="search-service"} | json | line_format "{{.tenant}} {{.status}} {{.path}} {{.duration}}"
     ```

---

## 3. Debugging Steps

- **Step A – Check resource usage**
  - Run `docker stats` (if local) or check container monitoring.
  - Look for CPU/memory throttling.

- **Step B – Check service logs**
  - Identify spikes in `status=5xx` or unusually high `duration`.
  - Confirm if it’s **one tenant** or **all tenants**.

- **Step C – Dependency check**
  - Verify if `payment-service` latency comes from DB/API calls.
  - Run synthetic request:

    ```bash
    curl -w "@curl-format.txt" -o /dev/null -s http://payment-service:8000/health
    ```

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
