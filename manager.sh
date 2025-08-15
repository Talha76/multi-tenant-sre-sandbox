#!/usr/bin/bash

GREEN='\033[1;32m'
RED='\033[1;31m'
BLUE='\033[1;36m'
NC='\033[0m' # No Color

if [[ "$1" == "down" || "$1" == "stop" ]]; then
    if [[ -f ./grafana/provisioning/alerting/contact_points.yml ]]; then
        sed -E 's|url: .*|url: ${SLACK_WEBHOOK}|g' ./grafana/provisioning/alerting/contact_points.yml \
        > ./grafana/provisioning/alerting/contact_points-template.yml

        echo -e "${GREEN}Done:${NC} Reset the contact points config to template"
    elif [[ -f ./grafana/provisioning/alerting/contact_points-template.yml ]]; then
        echo -e "${BLUE}Info:${NC} Config template file already exists."
    else
        echo -e "${RED}Error:${NC} There must be a ${BLUE}contact_points.yml${NC} file present in the ./grafana/provisioning/alerting/ directory."
        exit 1
    fi

    rm -f ./grafana/provisioning/alerting/contact_points.yml
elif [[ "$1" == "start" || "$1" == "restart" || "$1" == "up" ]]; then
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
fi

docker compose "$@"
