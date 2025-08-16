import csv
import json
import os
import random
import time
import sys
from datetime import datetime
from typing import Annotated, Awaitable, Callable, Literal
from uuid import uuid4
from logger import logger

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
async def metricsMiddleware(request: Request, callNext: Callable[[Request], Awaitable[Response]]):
    tenant = request.headers.get("X-Tenant", "unknown")
    path = request.url.path
    method = request.method
    start = time.perf_counter()
    response: Response = await callNext(request)
    latency = round(time.perf_counter() - start, 3)
    status = response.status_code

    boundLogger = logger.bind(tenant=tenant, path=path, status=status, duration=latency)

    if 200 <= response.status_code < 400:
        boundLogger.info("Request successful")
    else:
        bodyChunks = []
        iterator = response.body_iterator # type: ignore
        async def asyncBodyIterator():
            nonlocal bodyChunks, response
            async for chunk in iterator:
                bodyChunks.append(chunk)
                yield chunk
            body = b''.join(bodyChunks).decode()
            bodyObj = json.loads(body)
            boundLogger.error(bodyObj["detail"])

        response.body_iterator = asyncBodyIterator() # type: ignore

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
    serverUpStatus = random.choices([0, 1], weights=[5, 995])[0]
    if serverUpStatus == 0:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Server is down")

    tenant = request.headers.get("X-Tenant")
    transactionData = transaction.model_dump(mode='json')
    transactionData["tenant"] = tenant
    transactionData["trxId"] = str(uuid4())
    transactionData["time"] = datetime.strftime(transaction.time, "%Y-%m-%d %H:%M:%S.%f")[:-3]

    data_path = os.path.join(os.getcwd(), "..", "data")

    if not os.path.exists(data_path):
        os.makedirs(data_path)

    with open(os.path.join(data_path, "transactions.csv"), "a") as f:
        writer = csv.DictWriter(f, fieldnames=transactionData.keys())
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(transactionData)

    return {
        "trxId": transactionData["trxId"],
        "status": "success",
        "timestamp": datetime.now(),
    }
