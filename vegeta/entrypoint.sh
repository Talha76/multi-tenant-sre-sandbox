#!/bin/sh

echo "Starting 400 R/S test for 30s"
vegeta attack -rate 400 -duration 30s -targets /etc/vegeta/targets.txt |\
    tee /etc/results/result-400.bin |\
    vegeta report -reporter=plot > /etc/vegeta/reports/report-400.json

echo "Starting 600 R/S test for 20s"
vegeta attack -rate 600 -duration 20s -targets /etc/vegeta/targets.txt |\
    tee /etc/results/result-600.bin |\
    vegeta report -reporter=plot > /etc/vegeta/reports/report-600.json

echo "Starting 800 R/S test for 10s"
vegeta attack -rate 800 -duration 10s -targets /etc/vegeta/targets.txt |\
    tee /etc/results/result-800.bin |\
    vegeta report -reporter=plot > /etc/vegeta/reports/report-800.json

echo "All tests completed."

# Keep the container running
tail -f /dev/null
