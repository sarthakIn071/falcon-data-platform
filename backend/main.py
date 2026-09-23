from fastapi import FastAPI

app = FastAPI(
    title="Falcon Data Platform",
    description="nified Data Ingestion & Processing Platform",
    version="0.1.0"
)

@app.get("/health")

def health_check():
    return{
        "application":"falcon",
        "status":"UP",
        "version":"0.1.0"
    }