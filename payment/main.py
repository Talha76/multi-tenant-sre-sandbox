from fastapi import FastAPI

app = FastAPI()

@app.get("/transfer")
def transfer():
    return {
        "message": "Placeholder transfer endpoint",
        "status": "ok",
    }
