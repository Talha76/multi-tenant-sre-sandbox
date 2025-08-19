#!/usr/bin/env bash
set -e

# Config
PROMETHEUS_URL="http://localhost:9090"
LOKI_URL="http://localhost:3100"
PROMETHEUS_DATA="./prometheus-data"
LOKI_DATA="./loki-data"
RESTIC_REPO="./restic-backup"
RESTIC_PASSWORD="123"

GREEN='\033[1;32m'
RED='\033[1;31m'
BLUE='\033[1;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}Step 0: Ensuring volumes exist${NC}"
mkdir -p $PROMETHEUS_DATA $LOKI_DATA $RESTIC_REPO

# Step 1: Backup
echo -e "${BLUE}Step 1: Backup Prometheus and Loki${NC}"
export RESTIC_REPOSITORY=$RESTIC_REPO
export RESTIC_PASSWORD=$RESTIC_PASSWORD

# Initialize repository if not already
if ! restic snapshots >/dev/null 2>&1; then
  echo "Initializing new Restic repository..."
  restic init
fi

restic backup $PROMETHEUS_DATA $LOKI_DATA

echo -e "${GREEN}Backup completed.${NC}"
restic snapshots

# Step 2: Record last metric/log timestamps
echo -e "${BLUE}Step 2: Recording last metric/log timestamps for RPO${NC}"

LAST_PROM_METRIC=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=up"\
    | jq '.data.result | sort_by(.value[0]) | last(.[]).value[0]'\
    | cut -d'.' -f1)
LAST_LOKI_LOG=$(curl -s "$LOKI_URL/loki/api/v1/query_range?query=%7Bcontainer_name%3D~%22payment-service%7Csearch-service%22%7D&limit=1&direction=backward" | jq '.data.result[0].values[-1][0]' \
    | cut -c2-11)

echo "Last Prometheus metric timestamp: $LAST_PROM_METRIC"
echo "Last Loki log timestamp: $LAST_LOKI_LOG"

# Step 3: Simulate data loss
echo -e "${RED}Step 3: Simulating data loss...${NC}"
./manager.sh down
rm -rf $PROMETHEUS_DATA/* $LOKI_DATA/*

# Step 4: Restore
echo -e "${BLUE}Step 4: Restoring from backup...${NC}"
restic restore latest --target ./

# Step 5: Start containers & measure RTO
echo -e "${BLUE}Step 5: Starting containers and measuring RTO...${NC}"
start_time=$(date +%s)
./manager.sh up -d

# Wait for Prometheus
while ! curl -s $PROMETHEUS_URL/-/ready | grep -q "Prometheus"; do sleep 1; done
# Wait for Loki
while ! curl -s $LOKI_URL/ready | grep -q "ready"; do sleep 1; done

end_time=$(date +%s)
rto=$((end_time - start_time))
echo -e "${GREEN}RTO: $rto seconds${NC}"

# Step 6: Measure approximate RPO
RESTORED_LAST_PROM_METRIC=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=up" | jq '.data.result | sort_by(.value[0]) | last(.[]).value[0]' | cut -d'.' -f1)
RESTORED_LAST_LOKI_LOG=$(curl -s "$LOKI_URL/loki/api/v1/query_range?query=%7Bcontainer_name%3D~%22payment-service%7Csearch-service%22%7D&limit=1&direction=backward" | jq '.data.result[0].values[-1][0]' | cut -c2-11)

RPO_PROM=$((RESTORED_LAST_PROM_METRIC - LAST_PROM_METRIC))
RPO_LOKI=$((RESTORED_LAST_LOKI_LOG - LAST_LOKI_LOG))

echo -e "${GREEN}Approximate RPO:${NC}"
echo "Prometheus metrics gap: ${RPO_PROM}s"
echo "Loki logs gap: ${RPO_LOKI}s"

echo -e "${GREEN}Mini DR Drill completed.${NC}"
