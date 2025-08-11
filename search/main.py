from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.get("/search")
def search(request: Request):
    tenant = request.headers.get("X-Tenant")
    host = request.headers.get("Host")
    return {
        "message": "Placeholder search endpoint",
        "status": "ok",
        "tenant": tenant
    }
