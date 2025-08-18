#!/usr/bin/env python3
import json
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

EXPORTER_PORT = 9100
metrics_data = {}


def stream_vegeta():
    global metrics_data
    # Run vegeta in report streaming mode
    proc = subprocess.Popen(
        ["vegeta", "report", "-every", "1s", "-type=json", "results.bin"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    for line in proc.stdout:
        try:
            data = json.loads(line.strip())
            metrics_data = {
                "latency_mean_ms": data["latencies"]["mean"] / 1e6,  # ns → ms
                "latency_p95_ms": data["latencies"]["95th"] / 1e6,
                "latency_max_ms": data["latencies"]["max"] / 1e6,
                "throughput": data["throughput"],
                "success_ratio": data["success"],
                "requests_total": data["requests"],
            }

            # status codes
            for code, count in data.get("status_codes", {}).items():
                metrics_data[f"status_{code}"] = count

        except Exception as e:
            print(f"Parse error: {e} line={line.strip()}")


def metrics_handler():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/metrics":
                output = []
                for k, v in metrics_data.items():
                    metric_name = f"vegeta_{k}"
                    output.append(f"{metric_name} {v}")
                response = "\n".join(output) + "\n"
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(response.encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

    return Handler


def main():
    t = threading.Thread(target=stream_vegeta, daemon=True)
    t.start()

    server = HTTPServer(("", EXPORTER_PORT), metrics_handler())
    print(f"Exporter running on :{EXPORTER_PORT}/metrics")
    server.serve_forever()


if __name__ == "__main__":
    main()
