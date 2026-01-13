from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Geodata File Upload API",
    description="API zum Hochladen und Verarbeiten von CSV/NAS Geodaten",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "running", "message": "Geodata API is ready"}

@app.get("/health")
def health_check():
    return {"api": "ok", "database": "not connected yet"}