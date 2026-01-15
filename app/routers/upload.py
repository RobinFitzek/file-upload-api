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

def get_file_type(filename: str) -> str:
    """Erkennt Dateityp anhand der Endung"""
    if filename.lower().endswith(".csv"):
        return "csv"
    elif filename.lower().endswith(".nas"):
        return "nas"
    return "unknown"

@router.post("/test")
async def test_file(file: UploadFile = File(...)):
    """
    Testet eine Datei ohne sie zu speichern.
    """
    # 0. Prüfen ob Dateiname existiert
    if not file.filename:
        raise HTTPException(status_code=400, detail="Kein Dateiname angegeben")
    
    file_type = get_file_type(file.filename) 

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
    report["file_type"] = file_type 
    
    return report


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Lädt eine Datei hoch und speichert sie in der Datenbank.
    """
    # 0. Prüfen ob Dateiname existiert
    if not file.filename:
        raise HTTPException(status_code=400, detail="Kein Dateiname angegeben")
    
    file_type = get_file_type(file.filename)
    
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
    inserted_count = 0
    updated_count = 0

    for row in cleaned_data:
        # Prüfen ob ID bereits existiert (Update statt Insert)
        existing = db.query(Geodata).filter(Geodata.id == row.get("id")).first()
        
        if existing:
            # Update: vorhandenen Eintrag aktualisieren
            for key, value in row.items():
                setattr(existing, key, value)
            updated_count += 1
        else:
            # Insert: neuen Eintrag erstellen
            geodata = Geodata(**row)
            db.add(geodata)
            inserted_count += 1
        
        saved_count += 1
    
    # Änderungen speichern
    db.commit()

    
    return {
        "status": "success",
        "filename": file.filename,
        "file_type": file_type, 
        "total_rows": len(raw_data),
        "saved_rows": inserted_count + updated_count,
        "inserted": inserted_count,  
        "updated": updated_count,    
        "error_rows": len(errors),
        "errors": errors[:10]
    }


@router.get("/data")
async def get_all_data(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """
    Alle Geodaten abrufen (mit Pagination).
    """
    data = db.query(Geodata).offset(skip).limit(limit).all()
    total = db.query(Geodata).count()
    
    # Konvertiere SQLAlchemy-Objekte zu Dicts (ohne _sa_instance_state)
    result = []
    for row in data:
        row_dict = {c.name: getattr(row, c.name) for c in row.__table__.columns}
        result.append(row_dict)
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": result
    }


@router.delete("/data")
async def delete_all_data(db: Session = Depends(get_db)):
    """
    ALLE Geodaten löschen (Vorsicht!).
    """
    count = db.query(Geodata).count()
    db.query(Geodata).delete()
    db.commit()
    
    return {"status": "deleted", "deleted_count": count}


@router.get("/data/{id}")
async def get_data_by_id(id: int, db: Session = Depends(get_db)):
    """
    Einzelnen Datensatz nach ID abrufen.
    """
    data = db.query(Geodata).filter(Geodata.id == id).first()
    if not data:
        raise HTTPException(status_code=404, detail=f"Datensatz mit ID {id} nicht gefunden")
    return data


@router.delete("/data/{id}")
async def delete_data_by_id(id: int, db: Session = Depends(get_db)):
    """
    Einzelnen Datensatz löschen.
    """
    data = db.query(Geodata).filter(Geodata.id == id).first()
    if not data:
        raise HTTPException(status_code=404, detail=f"Datensatz mit ID {id} nicht gefunden")
    
    db.delete(data)
    db.commit()
    
    return {"status": "deleted", "id": id}