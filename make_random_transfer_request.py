import argparse
from datetime import datetime, timezone
import random
import requests

parser = argparse.ArgumentParser(description="Make random transfer requests.")
parser.add_argument('-c', '--count', type=int, default=1, help='Number of requests to make')
args = parser.parse_args()

for i in range(args.count):
    from_account = f"{random.randint(10000000, 99999999)}"
    to_account = f"{random.randint(10000000, 99999999)}"
    amount = random.uniform(1.0, 100000.0)
    trx_type = random.choice(["mudarabah", "musharakah", "murabaha", "qard hasanah", "ijarah", "sukuk"])
    time = datetime.now(timezone.utc).isoformat()

    request_data = {
        "fromAccount": from_account,
        "toAccount": to_account,
        "amount": amount,
        "trxType": trx_type,
        "time": time
    }
    
    tenant_id = random.randint(0, 2)
    if tenant_id == 0:
        tenant = "alpha"
    elif tenant_id == 1:
        tenant = "beta"
    else:
        tenant = "gamma"

    res = requests.post("http://localhost:8000/transfer", json=request_data, headers={"Host": f"{tenant}.local"})
    if res.ok:
        print(f"Request {i+1} successful, by tenant {tenant}")
    else:
        print(f"Request {i+1} failed by tenant {tenant}: {res.text}")
