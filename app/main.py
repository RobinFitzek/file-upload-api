from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import logging
import os

from app.database import engine, Base
from app.models.geodata import Geodata 
from app.routers import upload

# Logging fürs Terminal für Meldungen
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tabellen erstellen beim Start (falls nicht vorhanden)
Base.metadata.create_all(bind=engine)

# FastAPI App initialisieren 
app = FastAPI(
    title="Geodata File Upload API",
    description="API zum Hochladen und Verarbeiten von CSV/NAS Geodaten",
    version="1.0.0"
)

# CORS erlauben damit der Browser auf API Endpunkte zugreifen kann, wäre sonst geblockt (Monolith)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router einbinden - fügt /api/test und /api/upload hinzu
app.include_router(upload.router)

# Kommunikation mit Frontend (GUI) (Root Pfad"/")
@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the frontend"""

    # Pfad zur GUI.html
    gui_file = os.path.join(os.path.dirname(__file__), "GUI", "GUI.html")
    
    # für Debug: Prüfen ob Datei existiert
    logger.info(f"Looking for GUI at: {gui_file}")
    logger.info(f"File exists: {os.path.exists(gui_file)}")
    
    if os.path.exists(gui_file):
        with open(gui_file, "r", encoding="utf-8") as f:
            return f.read()
    else:
        # Meldung falls Datei nicht gefunden wurde
        return "<h1>GUI.html nicht gefunden!</h1><p>Pfad: " + gui_file + "</p>"


#Check ob API und DB laufen
@app.get("/health")
def health_check():
    """Prüft ob API und DB laufen"""
    try:
        from app.database import SessionLocal
        from sqlalchemy import text 
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {"api": "ok", "database": db_status}