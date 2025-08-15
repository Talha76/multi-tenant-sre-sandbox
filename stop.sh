#!/usr/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

if [[ -f ./grafana/provisioning/alerting/contact_points.yml ]]; then
    sed -E 's|url: .*|url: ${SLACK_WEBHOOK}|g' ./grafana/provisioning/alerting/contact_points.yml \
    > ./grafana/provisioning/alerting/contact_points-template.yml

    echo -e "${GREEN}Done:${NC} Reset the contact points config to template"
else
    echo -e "${RED}Error:${NC} There must be a ${BLUE}contact_points.yml${NC} file present in the ./grafana/provisioning/alerting/ directory."
    exit 1
fi

rm -f ./grafana/provisioning/alerting/contact_points.yml


docker compose stop

echo -e "${GREEN}Done:${NC} Stopped the services and reset the contact points configuration."
