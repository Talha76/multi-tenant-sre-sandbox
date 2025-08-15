#!/usr/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

set -a
source .env
set +a

if [[ -f ./grafana/provisioning/alerting/contact_points-template.yml ]]; then
    envsubst < ./grafana/provisioning/alerting/contact_points-template.yml > ./grafana/provisioning/alerting/contact_points.yml

    echo -e "${GREEN}Done:${NC} Created config files with the env values"
elif [[ -f ./grafana/provisioning/alerting/contact_points.yml ]]; then
    echo -e "${BLUE}Info:${NC} Config file already exists. Skipping creation."
else
    echo -e "${RED}Error:${NC} No contact points configuration found to create or template for reset."
    echo -e "- ${BLUE}Tip:${NC} Make sure that any of the ${BLUE}contact_points-template.yml${NC} or ${BLUE}contact_points.yml${NC} file is present and is properly configured."
    exit 1
fi

rm -f ./grafana/provisioning/alerting/contact_points-template.yml

docker compose restart
