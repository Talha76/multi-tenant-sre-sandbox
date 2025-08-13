import json
import os
import random
import time
from datetime import datetime
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response, status
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import (BaseModel, ConfigDict, Field, PastDatetime,
                      model_validator)

app = FastAPI()


TENANT_REQUESTS = Counter(
    "tenant_requests_total",
    "Total number of requests per tenant",
    ["tenant", "path", "method", "status"]
)
TENANT_LATENCY = Histogram(
    "tenant_request_latency_seconds",
    "Request latency per tenant",
    ["tenant", "path", "method", "status"]
)

@app.middleware("http")
async def metricsMiddleware(request: Request, callNext):
    tenant = request.headers.get("X-Tenant", "unknown")
    path = request.url.path
    method = request.method
    start = time.perf_counter()
    response: Response = await callNext(request)
    end = time.perf_counter()
    latency = end - start
    status = str(response.status_code)

    TENANT_REQUESTS.labels(tenant, path, method, status).inc()
    TENANT_LATENCY.labels(tenant, path, method, status).observe(latency)

    return response

Instrumentator().instrument(app).expose(app)


AccountType = Annotated[str, Field(pattern=r"^[1-9][0-9]{7}")]

class TransactionModel(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True, str_strip_whitespace=True)

    fromAccount: AccountType
    toAccount: AccountType
    amount: Annotated[float, Field(gt=0)]
    trxType: Literal["mudarabah", "musharakah", "murabaha", "qard hasanah",  "ijarah", "sukuk"]
    time: PastDatetime

    @model_validator(mode='after')
    def accountsDifferent(self):
        if self.fromAccount == self.toAccount:
            raise ValueError("Accounts must be different")
        return self


@app.post("/transfer")
def transfer(request: Request, transaction: TransactionModel):
    serverUpStatus = random.choices([0, 1], weights=[1, 9])[0]
    if serverUpStatus == 0:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Server is down")

    tenant = request.headers.get("X-Tenant")
    transactionData = transaction.model_dump(mode='json')
    transactionData["tenant"] = tenant
    transactionData["trxId"] = str(uuid4())

    data_path = os.path.join(os.getcwd(), "..", "data")

    try:
        with open(os.path.join(data_path, "transactions.json")) as f:
            transactions = json.loads(f.read())["transactions"]
    except (json.JSONDecodeError, FileNotFoundError):
        transactions = []

    transactions.append(transactionData)

    if not os.path.exists(data_path):
        os.makedirs(data_path)

    with open(os.path.join(data_path, "transactions.json"), "w") as f:
        f.write(json.dumps({ "transactions": transactions }, indent=2))

    return {
        "trxId": transactionData["trxId"],
        "status": "success",
        "timestamp": datetime.now(),
    }
