import argparse
from datetime import datetime, timedelta, timezone
import random
import requests

parser = argparse.ArgumentParser(description="Make random requests in this app.")
parser.add_argument('-c', '--count', type=int, default=1, help='Number of requests to make (default: 1)')
parser.add_argument('--post', action='store_true', help="Use this flag to make POST requests")
parser.add_argument('-p', '--path', type=str, help='Path to send the request to')
args = parser.parse_args()

def make_transfer_request() -> requests.Response:
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

    return requests.post("http://localhost:8000/transfer", json=request_data, headers={"Host": f"{tenant}.local"})

def make_search_request() -> requests.Response:
    return requests.Response()
    account = f"{random.randint(10000000, 99999999)}" if random.randint(0, 1) else None
    from_amount = random.uniform(0, 100000.0) if random.randint(0, 1) else None
    to_amount = random.uniform(from_amount if from_amount else 0, 100000.0) if random.randint(0, 1) else None
    from_date = (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 100))) if random.randint(0, 1) else None
    to_date = min(datetime.now(), ((from_date) + timedelta(days=random.randint(1, 30)))) if from_date else None
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

    return requests.post("http://localhost:8000/transfer", json=request_data, headers={"Host": f"{tenant}.local"})

if __name__ == '__main__':
    if args.path == "/transfer" and not args.post:
        print("Using POST method for /transfer path. Use --post flag to make POST requests.")

    for i in range(args.count):
        response: requests.Response = make_transfer_request() if args.path == "/transfer" else make_search_request()
        if response.ok:
            print(f"Request #{i + 1}, status code: {response.status_code}")
        else:
            print(f"Request #{i + 1} failed, status code: {response.status_code}: {response.text}")
