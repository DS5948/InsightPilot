from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def health():
    return {"status": "ok"}

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}
