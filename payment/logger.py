import json
from loguru import logger

def json_sink(message):
    record = message.record
    log_entry = {
        "time": record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "level": record["level"].name,
        "text": record["message"],
        "tenant": record["extra"].get("tenant", "unknown"),
        "path": record["extra"].get("path", ""),
        "status": record["extra"].get("status", "-1"),
        "duration": record["extra"].get("duration", 0),
    }
    print(json.dumps(log_entry, ensure_ascii=False))

logger.remove()
logger.add(json_sink, serialize=True)
