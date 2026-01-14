"""
API-Endpunkte für File-Upload.
POST /api/test   → Datei prüfen, Report zurückgeben (nichts speichern)
POST /api/upload → Datei prüfen und in DB speichern
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.parsers import get_parser
from app.logic.cleaner import DataCleaner
from app.models.geodata import Geodata

logger = logging.getLogger(__name__)

# Router erstellen (wird in main.py eingebunden)
router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/test")
async def test_file(file: UploadFile = File(...)):
    """
    Testet eine Datei ohne sie zu speichern.
    """
    # 0. Prüfen ob Dateiname existiert
    if not file.filename:
        raise HTTPException(status_code=400, detail="Kein Dateiname angegeben")
    
    # 1. Dateiformat prüfen
    try:
        parser = get_parser(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 2. Datei lesen und parsen
    content = await file.read()
    try:
        raw_data = parser.parse(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parsing-Fehler: {str(e)}")
    
    # 3. Daten bereinigen
    cleaner = DataCleaner()
    cleaned_data, errors = cleaner.clean(raw_data)
    
    # 4. Report erstellen
    report = cleaner.generate_report(raw_data, cleaned_data, errors)
    report["filename"] = file.filename
    report["status"] = "valid" if not errors else "has_errors"
    
    return report


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Lädt eine Datei hoch und speichert sie in der Datenbank.
    """
    # 0. Prüfen ob Dateiname existiert
    if not file.filename:
        raise HTTPException(status_code=400, detail="Kein Dateiname angegeben")
    
    # 1. Dateiformat prüfen
    try:
        parser = get_parser(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 2. Datei lesen und parsen
    content = await file.read()
    try:
        raw_data = parser.parse(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parsing-Fehler: {str(e)}")
    
    # 3. Daten bereinigen
    cleaner = DataCleaner()
    cleaned_data, errors = cleaner.clean(raw_data)
    
    if not cleaned_data:
        raise HTTPException(status_code=400, detail="Keine gültigen Daten zum Speichern")
    
    # 4. In Datenbank speichern
    saved_count = 0
    for row in cleaned_data:
        # Prüfen ob ID bereits existiert (Update statt Insert)
        existing = db.query(Geodata).filter(Geodata.id == row.get("id")).first()
        
        if existing:
            # Update: vorhandenen Eintrag aktualisieren
            for key, value in row.items():
                setattr(existing, key, value)
        else:
            # Insert: neuen Eintrag erstellen
            geodata = Geodata(**row)
            db.add(geodata)
        
        saved_count += 1
    
    # Änderungen speichern
    db.commit()
    
    return {
        "status": "success",
        "filename": file.filename,
        "total_rows": len(raw_data),
        "saved_rows": saved_count,
        "error_rows": len(errors),
        "errors": errors
    }