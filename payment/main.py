from fastapi import FastAPI, Request
from pydantic import BaseModel, Field, PastDatetime, model_validator, ConfigDict
from typing import Annotated
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
    time: PastDatetime

    @model_validator(mode='after')
    def accountsDifferent(self):
        if self.fromAccount == self.toAccount:
            raise ValueError("Accounts must be different")
        return self


@app.post("/transfer")
def transfer(request: Request, transaction: TransactionModel):
    serverUpStatus = random.choices([0, 1], weights=[35, 65])[0]
    if serverUpStatus == 0:
        raise Exception("Server is down")

    tenant = request.headers.get("X-Tenant")
    transaction_data = transaction.model_dump(mode='json')
    transaction_data["tenant"] = tenant
    transaction_data["trxId"] = str(uuid4())

    try:
        with open("./transactions.json") as f:
            s = f.read()
            transactions = json.loads(s)["transactions"] if s else []
    except (json.JSONDecodeError, FileNotFoundError):
        transactions = []

    transactions.append(transaction_data)

    with open("./transactions.json", "w") as f:
        f.write(json.dumps({ "transactions": transactions }, indent=2))

    return {
        "trxId": transaction_data["trxId"],
        "status": "success",
        "timestamp": datetime.now(),
    }
