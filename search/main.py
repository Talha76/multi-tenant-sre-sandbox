from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/search")
def serach():
    return {
        "message": "Placeholder search endpoint",
        "status": "ok"
    }
