# Disaster Recovery Drill Report

**Date:** `2025-08-20`
**System under test:** Prometheus + Loki monitoring stack

---

## 1. Objective

The goal of this DR drill was to validate backup, restore, and recovery time for the monitoring stack (Prometheus + Loki), ensuring business continuity in case of data loss.

---

## 2. Drill Steps

### Step 0: Environment Setup

* Verify required directories: `prometheus-data/`, `loki-data/`, `restic-backup/`.
* Confirm containers are running before drill.

### Step 1: Backup

* Use **Restic** for snapshot-based backup.
* Target data volumes:
  * Prometheus: `./prometheus-data/`
  * Loki: `./loki-data/`
* Confirm snapshot creation via `restic snapshots`.

### Step 2: Capture Last Known State (for RPO)

* Record latest Prometheus metric timestamp (`up` series).
* Record latest Loki log timestamp for `payment-service` and `search-service`.

### Step 3: Simulate Data Loss

* Stop monitoring stack (`./manager.sh down`).
* Purge Prometheus & Loki local data directories.

### Step 4: Restore

* Run `restic restore latest --target ./`.
* Verify data restoration into original directories.

### Step 5: Restart & Measure RTO

* Restart containers (`./manager.sh up -d`).
* Measure **RTO** (Recovery Time Objective) as the time from restart initiation until both Prometheus and Loki reported ready status.

### Step 6: Measure RPO

* Compare restored metric/log timestamps with those recorded in Step 2.
* Calculate **RPO** (Recovery Point Objective) as the data gap in seconds.

All of these steps can be automated by a script in this project called `dr_drill.sh`.

---

## 3. Results

* **RTO (Recovery Time Objective):** `1` second
* **RPO (Prometheus metrics):** `7` seconds
* **RPO (Loki logs):** `0` second

---

## 4. Observations

* Backups were consistent and Restic restore completed successfully.
* Prometheus and Loki became operational quickly after restore.
* No corruption observed in restored data.
* Minimal data loss observed (as measured in RPO).

---

## 5. Corrective Actions / Improvements

* Automate drill execution via CI/CD pipeline for repeatability.
* Schedule recurring backups with retention policies.
* Enhance monitoring to alert on backup failures.
* Explore remote backup storage (e.g., S3, GCS) for site-level resilience.
