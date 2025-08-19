import csv
import json
import os
import random
import time
from datetime import datetime
from typing import Annotated, Literal
from logger import logger

from fastapi import FastAPI, HTTPException, Request, Response, status
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from typing import Callable, Awaitable
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
            message = f"timeFrom ({self.timeFrom}) must be less than or equal to timeTo ({self.timeTo})"
            raise ValueError(message)
        if self.amountFrom > self.amountTo:
            message = f"amountFrom ({self.amountFrom}) must be less than or equal to amountTo ({self.amountTo})"
            raise ValueError(message)
        return self


def getTransactions():
    data_path = os.path.join(os.getcwd(), "..", "data")
    try:
        with open(os.path.join(data_path, "transactions.csv")) as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["amount"] = float(row["amount"])
                row["time"] = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=None)
                yield row
    except FileNotFoundError:
        return


@app.get("/search")
def getSearch(request: Request):
    serverUpStatus = random.choices([0, 1], weights=[5, 995])[0]
    if serverUpStatus == 0:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Server is down")

    q = request.query_params.get('q', '')
    qType = request.query_params.get('type', 'transaction-account')
    if qType not in ["transaction-account", "transaction", "account"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid query type. Use 'transaction', 'account' or omit this field.")

    trxIds = set()
    results = []
    for trx in getTransactions():
        if "transaction" in qType:
            if q == "" or trx["trxType"] == q:
                results.append(trx) if trx["trxId"] not in trxIds else None
        if "account" in qType:
            if q == "" or trx["fromAccount"] == q or trx["toAccount"] == q:
                results.append(trx) if trx["trxId"] not in trxIds else None
        trxIds.add(trx["trxId"])

    return {
        "total": len(results),
        "results": results,
    }


@app.post("/search")
def postSearch(searchBody: SearchBodyModel, request: Request):
    # serverUpStatus = random.choices([0, 1], weights=[5, 995])[0]
    # if serverUpStatus == 0:
    #     raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Server is down")

    results = []
    for trx in getTransactions():
        if searchBody.timeFrom <= trx["time"] <= searchBody.timeTo and \
           searchBody.amountFrom <= trx["amount"] <= searchBody.amountTo and \
           (searchBody.account == "" or searchBody.account == trx["fromAccount"] or searchBody.account == trx["toAccount"]) and \
           (searchBody.trxType == "" or searchBody.trxType == trx["trxType"]):
            results.append(trx)

    tenant = request.headers.get('X-Tenant')
    return {
        "total": len(results),
        "results": results,
    }
