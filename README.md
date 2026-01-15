# Geodata File Upload API

REST-API zum Hochladen, Validieren und Speichern von Geodaten aus CSV- und NAS-Dateien.

## Features

- Datei-Upload für `.csv` und `.nas` Dateien
- Validierung ohne Speicherung (Test-Modus)
- Validierung mit Speicherung in PostgreSQL (Upsert)
- Automatische Datenbereinigung
- Detaillierter Datenqualitäts-Report
- Strukturiertes Logging

---

## Schnellstart

```bash
# Repo klonen & Virtual Environment
git clone https://github.com/yourusername/file-upload-api.git
cd file-upload-api
python -m venv venv
source venv/bin/activate

# Dependencies & Datenbank
pip install -r requirements.txt
docker-compose up -d

# API starten
uvicorn app.main:app --reload
```

| URL | Beschreibung |
|-----|--------------|
| http://localhost:8000 | Web-GUI |
| http://localhost:8000/docs | Swagger API Docs |
| http://localhost:8000/health | Health Check |

---

## API Endpunkte

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| POST | `/api/test` | Validiert Datei ohne zu speichern |
| POST | `/api/upload` | Validiert und speichert (Upsert) |
| GET | `/health` | Health Check |

```bash
curl -X POST http://localhost:8000/api/test -F "file=@examples/geodata_example_1.csv"
curl -X POST http://localhost:8000/api/upload -F "file=@examples/geodata_example_1.csv"
```

---

## Unterstützte Formate

### CSV
```csv
ID,Flurstücknummer,longitude,latidude,Gemeinde,Bundesland,Größe in ha
1001,045-123-0001,8.6821,50.1109,Frankfurt,Hessen,0.87
```

### NAS (XML-basiert)
```xml
<Flurstueck>
  <ID>2001</ID>
  <Gemeinde>Hamburg</Gemeinde>
  <longitude>9.9937</longitude>
</Flurstueck>
```

### NAS (Text-basiert)
```
EINHEIT: Flurstueck
ID: 5001
Gemeinde: Berlin
Koordinaten: 52.52 13.405
```

---

## Datenbereinigung

| Operation | Beispiel |
|-----------|----------|
| Whitespace trimmen | `" Hamburg "` → `"Hamburg"` |
| Leere Werte → NULL | `""`, `"-"`, `"N/A"` → `NULL` |
| Deutsche Dezimalzahlen | `"1,25"` → `1.25` |
| Typkonvertierung | `"1001"` → `1001` (int) |
| Spaltennamen normalisieren | `"Größe in ha"` → `groesse_ha` |

---

## Validierungsregeln

| Feld | Regel |
|------|-------|
| `id` | Pflichtfeld, Integer |
| `latitude` | -90 bis 90 |
| `longitude` | -180 bis 180 |
| `groesse_ha` | ≥ 0 |

---

## Report-Status

| Status | Bedeutung |
|--------|-----------|
| `OK` | Alle Daten valide |
| `FIXABLE` | Teils gültig, teils fehlerhaft |
| `INVALID` | Keine gültigen Zeilen |

---

## Logging

```bash
LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

---

## Tests

```bash
pytest              # Alle Tests
pytest --cov=app    # Mit Coverage
```

---

## Projektstruktur

```
file-upload-api/
├── app/
│   ├── main.py              # FastAPI App
│   ├── database.py          # DB-Verbindung
│   ├── logging_config.py    # Logging
│   ├── GUI/GUI.html         # Web-Frontend
│   ├── models/geodata.py    # DB-Modell
│   ├── schemas/geodata.py   # Pydantic Schemas
│   ├── parsers/             # CSV & NAS Parser
│   ├── logic/cleaner.py     # Datenbereinigung
│   └── routers/upload.py    # API Endpunkte
├── tests/                   # Unit Tests
├── examples/                # Beispieldateien
├── docker-compose.yml       # PostgreSQL
└── requirements.txt
```

---

## Technologien

| Tool       | Zweck |

| FastAPI    | Web-Framework 
| SQLAlchemy | ORM 
| PostgreSQL | Datenbank 
| Docker     | DB-Container 
| pytest     | Testing 