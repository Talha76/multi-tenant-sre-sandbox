from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/transfer")
def transfer(request: Request):
    tenant = request.headers.get("X-Tenant")
    return {
        "message": "Placeholder transfer endpoint",
        "status": "ok",
        "tenant": tenant
    }
