import os
from fastapi import FastAPI, Request, Response, status
from pydantic import BaseModel, Field, PastDatetime, model_validator, ConfigDict
from typing import Annotated, Literal
from datetime import datetime

import random
import json
from uuid import uuid4


app = FastAPI()

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
def transfer(request: Request, response: Response, transaction: TransactionModel):
    serverUpStatus = random.choices([0, 1], weights=[1, 9])[0]
    if serverUpStatus == 0:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "error": "Server is down",
        }

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

    print(os.path.join(data_path, "transactions.json"))
    print(os.path.exists(data_path))
    with open(os.path.join(data_path, "transactions.json"), "w") as f:
        f.write(json.dumps({ "transactions": transactions }, indent=2))

    return {
        "trxId": transactionData["trxId"],
        "status": "success",
        "timestamp": datetime.now(),
    }
