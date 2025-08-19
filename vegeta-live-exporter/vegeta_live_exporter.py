#!/usr/bin/env python3
import json
import subprocess
import threading
from fastapi import FastAPI, Response
import uvicorn

EXPORTER_PORT = 9100
metrics_data = {}

app = FastAPI()


def stream_vegeta():
    global metrics_data
    # Run vegeta report in streaming mode
    proc = subprocess.Popen(
        ["vegeta", "report", "-every", "1s", "-type=json", "/etc/vegeta/results/results.bin"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            metrics_data = {
                "latency_mean_ms": data["latencies"]["mean"] / 1e6,  # ns → ms
                "latency_p95_ms": data["latencies"]["95th"] / 1e6,
                "latency_max_ms": data["latencies"]["max"] / 1e6,
                "throughput": data["throughput"],
                "success_ratio": data["success"],
                "requests_total": data["requests"],
            }

            # Status codes
            for code, count in data.get("status_codes", {}).items():
                metrics_data[f"status_{code}"] = count

        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e} line={line}")
        except Exception as e:
            print(f"Unexpected error: {e} line={line}")


@app.get("/metrics")
async def get_metrics():
    output = []
    for k, v in metrics_data.items():
        metric_name = f"vegeta_{k}"
        output.append(f"{metric_name} {v}")
    response_text = "\n".join(output) + "\n"
    return Response(content=response_text, media_type="text/plain")


def main():
    t = threading.Thread(target=stream_vegeta, daemon=True)
    t.start()

    uvicorn.run(app, host="0.0.0.0", port=EXPORTER_PORT)


if __name__ == "__main__":
    main()
