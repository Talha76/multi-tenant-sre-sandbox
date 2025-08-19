#!/bin/sh

echo "Starting 400 R/S test for 30s"
vegeta attack -rate 400 -duration 30s -targets /etc/vegeta/targets.txt -output /etc/vegeta/results/result-400.bin
vegeta report -every 1s -type json -output /etc/vegeta/reports/report-400.json /etc/vegeta/results/result-400.bin

echo "Starting 600 R/S test for 20s"
vegeta attack -rate 600 -duration 20s -targets /etc/vegeta/targets.txt -output /etc/vegeta/results/result-600.bin
vegeta report -every 1s -type json -output /etc/vegeta/reports/report-600.json /etc/vegeta/results/result-600.bin

echo "Starting 800 R/S test for 10s"
vegeta attack -rate 800 -duration 10s -targets /etc/vegeta/targets.txt -output /etc/vegeta/results/result-800.bin
vegeta report -every 1s -type json -output /etc/vegeta/reports/report-800.json /etc/vegeta/results/result-800.bin

echo "All tests completed."
