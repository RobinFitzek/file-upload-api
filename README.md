# Geodata File Upload API

REST-API zum Hochladen, Validieren und Speichern von Geodaten aus CSV- und NAS-Dateien.

## Was kann die App?

- CSV und NAS (XML) Dateien hochladen
- Daten validieren (Typen, Wertebereiche, Pflichtfelder)
- Daten bereinigen (Whitespace, NULL-Werte, deutsche Zahlen)
- In PostgreSQL speichern
- Web-GUI zum Testen
- Swagger Docs automatisch generiert

---

## Schnellstart

### 1. Repo klonen

```bash
git clone https://github.com/yourusername/file-upload-api.git
cd file-upload-api
```

### 2. Virtual Environment erstellen

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows
```

### 3. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 4. Datenbank starten (Docker)

```bash
docker-compose up -d
```

### 5. API starten

```bash
uvicorn app.main:app --reload
```

### 6. Im Browser öffnen

- GUI: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## API Endpunkte

| Endpunkt | Methode | Was macht es? |
|----------|---------|---------------|
| `/` | GET | Web-GUI ausliefern |
| `/health` | GET | Prüft ob API und DB laufen |
| `/api/test` | POST | Datei validieren (ohne speichern) |
| `/api/upload` | POST | Datei validieren und in DB speichern |

### POST /api/test

Testet eine Datei ohne sie zu speichern.

```bash
curl -X POST http://localhost:8000/api/test \
  -F "file=@examples/geodata_example_1.csv"
```

Response:
```json
{
  "status": "OK",
  "total_rows": 3,
  "valid_rows": 3,
  "error_rows": 0,
  "error_summary": {},
  "preview": [...]
}
```

### POST /api/upload

Validiert und speichert Daten in der Datenbank. Wenn ID schon existiert wird geupdated statt neu eingefügt (Upsert).

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@examples/geodata_example_1.csv"
```

Response:
```json
{
  "status": "success",
  "filename": "geodata_example_1.csv",
  "total_rows": 3,
  "saved_rows": 3,
  "error_rows": 0
}
```

---

## Unterstützte Dateiformate

### CSV

```csv
ID,Flurstücknummer,longitude,latidude,Gemeinde,Bundesland,Größe in ha
1001,045-123-0001,8.6821,50.1109,Frankfurt am Main,Hessen,0.87
```

### NAS (XML)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NasExport>
  <Flurstueck>
    <ID>2001</ID>
    <Flurstücknummer>123-001-0007</Flurstücknummer>
    <longitude>9.9937</longitude>
    <latidude>53.5511</latidude>
    <Gemeinde>Hamburg</Gemeinde>
    <Bundesland>Hamburg</Bundesland>
    <Größe in ha>0.63</Größe in ha>
  </Flurstueck>
</NasExport>
```

NAS Parser nutzt Regex statt XML-Parser weil die Beispieldateien ungültiges XML haben (z.B. `<Größe in ha>` mit Leerzeichen im Tag-Namen).

---

## Datenbereinigung (Cleaner)

Der Cleaner macht folgendes:

| Was | Beispiel |
|-----|----------|
| Whitespace entfernen | `" Hamburg "` → `"Hamburg"` |
| NULL-Werte erkennen | `""`, `"-"`, `"N/A"` → `NULL` |
| Deutsche Zahlen | `"1,25"` → `1.25` (nur bei Semikolon-CSV oder quoted values) |
| Typkonvertierung | `"1001"` → `1001` (int) |
| Spaltennamen normalisieren | `"Größe in ha"` → `groesse_ha` |

---

## Validierung

| Feld | Regel |
|------|-------|
| `id` | Pflichtfeld, muss Integer sein |
| `latitude` | Muss zwischen -90 und 90 liegen |
| `longitude` | Muss zwischen -180 und 180 liegen |
| `groesse_ha` | Darf nicht negativ sein |

### Status Codes

| Status | Bedeutung |
|--------|-----------|
| `OK` | Alle Zeilen gültig |
| `FIXABLE` | Einige Zeilen gültig, einige fehlerhaft |
| `INVALID` | Keine gültigen Zeilen |

---

## Projektstruktur

```
file-upload-api/
├── app/
│   ├── main.py              # FastAPI App + Routing
│   ├── database.py          # DB-Verbindung (SQLAlchemy)
│   ├── GUI/
│   │   └── GUI.html         # Web-Frontend
│   ├── models/
│   │   └── geodata.py       # DB-Tabellen Definition
│   ├── schemas/
│   │   └── geodata.py       # Pydantic Schemas für Validierung
│   ├── parsers/
│   │   ├── base.py          # Parser Interface (Vaterklasse)
│   │   ├── csv_parser.py    # CSV Parser
│   │   └── nas_parser.py    # NAS/XML Parser (mit Regex)
│   ├── logic/
│   │   └── cleaner.py       # Datenbereinigung + Validierung
│   └── routers/
│       └── upload.py        # API Endpunkte (/api/test, /api/upload)
├── examples/                 # Beispieldateien zum Testen
├── docker-compose.yml        # PostgreSQL Container
├── requirements.txt          # Python Dependencies
└── README.md
```

---

## Datenbank

### Verbindung prüfen

```bash
docker exec -it geodata-postgres psql -U geodata_user -d geodata_db -c "SELECT * FROM geodata"
```

### Alle Daten löschen

```bash
docker exec -it geodata-postgres psql -U geodata_user -d geodata_db -c "DELETE FROM geodata"
```

### DB neu starten

```bash
docker-compose down
docker-compose up -d
```

---

## Wie funktioniert der Flow?

```
Datei hochladen (CSV/NAS)
        │
        ▼
    Parser
    (csv_parser.py oder nas_parser.py)
        │
        ▼
    raw_data: Liste von Dicts
    [{"ID": "1001", "Gemeinde": "Hamburg", ...}, ...]
        │
        ▼
    Cleaner
    (cleaner.py)
        │
        ├── _clean_row(): Whitespace, Typen, NULL-Werte
        └── _validate_row(): Wertebereiche prüfen
        │
        ▼
    cleaned_data + errors
        │
        ├── /api/test → Report zurückgeben
        └── /api/upload → In DB speichern (Upsert)
```

---

## Technologien

- **FastAPI** - Web-Framework
- **SQLAlchemy** - ORM für Datenbank
- **PostgreSQL** - Datenbank
- **Pydantic** - Datenvalidierung
- **Docker** - Container für DB

---

## Bekannte Einschränkungen

- `geodata_example_2.csv` wirft Parsing-Fehler weil deutsche Zahlen (Komma statt Punkt) bei Komma-getrennten CSVs nicht funktionieren. Das ist erwartetes Verhalten - der Parser kann nicht wissen ob `13,4050` eine Zahl oder zwei Spalten sind.
- NAS Parser nutzt Regex statt echten XML-Parser wegen ungültiger Tag-Namen in den Beispieldateien.