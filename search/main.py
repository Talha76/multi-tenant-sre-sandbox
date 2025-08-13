import json
import os
import random
import time
from datetime import datetime
from typing import Annotated, Literal

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


PositiveFloat = Annotated[float, Field(gt=0)]

class SearchBodyModel(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True, str_strip_whitespace=True)
    
    timeFrom: PastDatetime = datetime(1900, 1, 1)
    timeTo: PastDatetime = Field(default_factory=datetime.now)
    amountFrom: PositiveFloat = 0
    amountTo: PositiveFloat = 1000000
    account: Annotated[str, Field()] = ""
    trxType: Literal["mudarabah", "musharakah", "murabaha", "qard hasanah",  "ijarah", "sukuk", ""] = ""
    
    @model_validator(mode='after')
    def validateData(self):
        if self.timeFrom > self.timeTo:
            raise ValueError("timeFrom must be less than or equal to timeTo")
        if self.amountFrom > self.amountTo:
            raise ValueError("amountFrom must be less than or equal to amountTo")
        return self


def getTransactions():
    data_path = os.path.join(os.getcwd(), "..", "data")
    try:
        with open(os.path.join(data_path, "transactions.json")) as f:
            transactions = json.loads(f.read())["transactions"]
    except (json.JSONDecodeError, FileNotFoundError):
        transactions = []
    return transactions


@app.get("/search")
def getSearch(request: Request):
    serverUpStatus = random.choices([0, 1], weights=[35, 65])[0]
    if serverUpStatus == 0:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Server is down")

    q = request.query_params.get('q', '')
    qType = request.query_params.get('type', 'transaction-account')
    if qType not in ["transaction-account", "transaction", "account"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid query type. Use 'transaction', 'account' or omit this field.")

    transactions = getTransactions()

    trxIds = set()
    for trx in transactions:
        if "transaction" in qType:
            if trx["trxType"] == q:
                trxIds.add(trx["trxId"])
        if "account" in qType:
            if trx["fromAccount"] == q or trx["toAccount"] == q:
                trxIds.add(trx["trxId"])
    
    results = []
    for trx in transactions:
        if trx["trxId"] in trxIds:
            results.append(trx)

    delay = random.uniform(0.05, 1)
    time.sleep(delay)

    tenant = request.headers.get("X-Tenant")
    return {
        "tenant": tenant,
        "results": results,
        "total": len(results),
    }


@app.post("/search")
def postSearch(searchBody: SearchBodyModel, request: Request):
    serverUpStatus = random.choices([0, 1], weights=[1, 9])[0]
    if serverUpStatus == 0:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Server is down")

    transactions = getTransactions()
    results = []

    for trx in transactions:
        trxTime = datetime.fromisoformat(trx["time"]).replace(tzinfo=None)
        if searchBody.timeFrom <= trxTime <= searchBody.timeTo and \
           searchBody.amountFrom <= trx["amount"] <= searchBody.amountTo and \
           (searchBody.account == "" or searchBody.account == trx["fromAccount"] or searchBody.account == trx["toAccount"]) and \
           (searchBody.trxType == "" or searchBody.trxType == trx["trxType"]):
            results.append(trx)

    delay = random.uniform(0.05, 0.5)
    time.sleep(delay)

    tenant = request.headers.get('X-Tenant')
    return {
        "tenant": tenant,
        "results": results,
        "total": len(results),
    }
