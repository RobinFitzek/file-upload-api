# Geodata File Upload API

REST-API zum Hochladen, Validieren und Speichern von Geodaten aus CSV- und NAS-Dateien.

## Features

- Datei-Upload für `.csv` und `.nas` Dateien
- Validierung ohne Speicherung (Test-Modus)
- Validierung mit Speicherung in PostgreSQL
- Automatische Datenbereinigung
- Detaillierter Datenqualitäts-Report
- Docker-basierte Entwicklungsumgebung
- Automatische OpenAPI/Swagger Dokumentation

---

## Schnellstart

### Voraussetzungen

- Docker und Docker Compose
- Python 3.11+ (für lokale Entwicklung) (mit Python 3.12 getestet)

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

| URL | Beschreibung |
|-----|--------------|
| http://localhost:8000 | Web-GUI |
| http://localhost:8000/docs | Swagger API Docs |
| http://localhost:8000/health | Health Check |

---

## API Endpunkte

### POST `/api/test`

Testet eine Datei ohne sie zu speichern. Gibt einen Datenqualitäts-Report zurück.

**Request:**
```bash
curl -X POST http://localhost:8000/api/test \
  -F "file=@examples/geodata_example_1.csv"
```

**Response (200 OK):**
```json
{
  "status": "OK",
  "filename": "geodata_example_1.csv",
  "file_type": "csv",
  "total_rows": 3,
  "valid_rows": 3,
  "error_rows": 0,
  "error_summary": {},
  "errors": [],
  "cleanings_applied": [
    "Whitespace entfernt (trim)",
    "Leere Werte zu NULL konvertiert",
    "Typkonvertierung (String → int/float)",
    "Spaltennamen normalisiert (deutsch → snake_case)",
    "Wertebereiche validiert (lat/lon/größe)"
  ],
  "preview": [...],
  "columns_found": ["ID", "Flurstücknummer", "longitude", "latidude", "Gemeinde", "Bundesland", "Größe in ha"],
  "columns_mapped": ["ID", "Flurstücknummer", "longitude", "latidude", "Gemeinde", "Bundesland", "Größe in ha"]
}
```

### POST `/api/upload`

Validiert und speichert Daten in der Datenbank. Bei bestehender ID wird aktualisiert (Upsert).

**Request:**
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@examples/geodata_example_1.csv"
```

**Response (200 OK):**
```json
{
  "status": "success",
  "filename": "geodata_example_1.csv",
  "file_type": "csv",
  "total_rows": 3,
  "saved_rows": 3,
  "inserted": 3,
  "updated": 0,
  "error_rows": 0,
  "errors": []
}
```

### GET `/health`

Health-Check für API und Datenbank.

**Response:**
```json
{
  "api": "ok",
  "database": "connected"
}
```

---

## HTTP Status Codes

| Code | Bedeutung | Wann |
|------|-----------|------|
| `200` | Erfolg | Datei erfolgreich validiert/hochgeladen |
| `400` | Client-Fehler | Ungültiges Dateiformat, Parsing-Fehler, nicht unterstütztes NAS-Format |
| `422` | Validierungsfehler | Keine Datei angegeben, Request-Body ungültig |
| `500` | Server-Fehler | Datenbankverbindung fehlgeschlagen, interner Fehler |

---

## Unterstützte Dateiformate

### CSV-Dateien (`.csv`)

Standard CSV-Format mit Komma als Trennzeichen:

```csv
ID,Flurstücknummer,longitude,latidude,Gemeinde,Bundesland,Größe in ha
1001,045-123-0001,8.6821,50.1109,Frankfurt am Main,Hessen,0.87
1002,091-456-0020,13.4050,52.5200,Berlin,Berlin,1.25
```

**Eigenschaften:**
- Trennzeichen: `,` (Komma)
- Encoding: UTF-8
- Header-Zeile erforderlich

### NAS-Dateien (`.nas`)

**Unterstützte Variante:** XML-basiertes Format mit `<Flurstueck>`-Elementen

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

**Hinweise:**
- Der Parser nutzt Regex statt XML-Parser, da Tag-Namen wie `<Größe in ha>` nicht XML-konform sind
- **Text-basierte NAS-Formate werden nicht unterstützt** und führen zu einer klaren Fehlermeldung
- Content-Detection erkennt automatisch ob eine Datei XML oder Text ist

---

## Datenbankschema

Die Geodaten werden in der Tabelle `geodata` gespeichert:

```sql
CREATE TABLE geodata (
    id INTEGER PRIMARY KEY,           -- Eindeutiger Schlüssel (Pflichtfeld)
    flurstuecknummer VARCHAR,         -- Optional
    longitude FLOAT,                  -- Optional, Bereich: -180 bis 180
    latitude FLOAT,                   -- Optional, Bereich: -90 bis 90
    gemeinde VARCHAR,                 -- Optional
    bundesland VARCHAR,               -- Optional
    groesse_ha FLOAT                  -- Optional, muss >= 0 sein
);
```

### Eindeutigkeits-Constraint

| Feld | Constraint | Beschreibung |
|------|------------|--------------|
| `id` | **PRIMARY KEY** | Eindeutiger Identifikator, Pflichtfeld |

### Duplikat-Behandlung (Upsert-Strategie)

Bei Upload werden Duplikate anhand der **ID** erkannt:

| Situation | Verhalten |
|-----------|-----------|
| ID existiert bereits | **Update** - neue Werte überschreiben alte |
| ID ist neu | **Insert** - neuer Datensatz wird angelegt |

Dies entspricht der **"Letzte gewinnt"**-Strategie.

---

## Datenbereinigung (Cleaner)

Der `DataCleaner` führt folgende Bereinigungen automatisch durch:

| Problem | Lösung | Beispiel |
|---------|--------|----------|
| Führende/nachfolgende Leerzeichen | Automatisch entfernt (trim) | `" Hamburg "` → `"Hamburg"` |
| Leere Werte | Zu `NULL` konvertiert | `""`, `"-"`, `"N/A"`, `"null"` → `NULL` |
| Deutsche Dezimalzahlen | Komma zu Punkt | `"1,25"` → `1.25` |
| String zu Integer | Automatisch konvertiert | `"1001"` → `1001` |
| String zu Float | Automatisch konvertiert | `"8.6821"` → `8.6821` |
| Spaltennamen | Normalisiert zu snake_case | `"Größe in ha"` → `groesse_ha` |

### Spaltennamen-Mapping

| Quelldaten | Datenbank-Feld |
|------------|----------------|
| `ID` | `id` |
| `Flurstücknummer` | `flurstuecknummer` |
| `longitude` | `longitude` |
| `latidude` | `latitude` (Tippfehler korrigiert!) |
| `Gemeinde` | `gemeinde` |
| `Bundesland` | `bundesland` |
| `Größe in ha` | `groesse_ha` |

---

## Validierungsregeln

| Feld | Regel | Fehlertyp |
|------|-------|-----------|
| `id` | Pflichtfeld, muss Integer sein | ERROR |
| `latitude` | Muss zwischen -90 und 90 liegen | ERROR |
| `longitude` | Muss zwischen -180 und 180 liegen | ERROR |
| `groesse_ha` | Darf nicht negativ sein | ERROR |

---

## Report-Status

| Status | Bedeutung |
|--------|-----------|
| `OK` | Alle Daten sind valide |
| `FIXABLE` | Einige Zeilen gültig, andere fehlerhaft (Teilerfolg möglich) |
| `INVALID` | Keine gültigen Zeilen, kann nicht verarbeitet werden |

---

## Typische Fehlerfälle

### 1. Ungültiges Dateiformat

```bash
curl -X POST http://localhost:8000/api/test -F "file=@test.txt"
```

**Response (400 Bad Request):**
```json
{
  "detail": "Nicht unterstütztes Dateiformat: test.txt"
}
```

### 2. Text-basiertes NAS-Format (nicht unterstützt)

```bash
curl -X POST http://localhost:8000/api/test -F "file=@text_based.nas"
```

**Response (400 Bad Request):**
```json
{
  "detail": "Parsing-Fehler: Nicht unterstütztes NAS-Format. Nur XML-basierte NAS-Dateien werden unterstützt. Das hochgeladene Format scheint ein Text-basiertes NAS-Format zu sein."
}
```

### 3. Datei mit ungültigen Daten

```bash
curl -X POST http://localhost:8000/api/test -F "file=@examples/geodata_example_2.csv"
```

**Response (200 OK mit Fehlerdetails):**
```json
{
  "status": "INVALID",
  "filename": "geodata_example_2.csv",
  "file_type": "csv",
  "total_rows": 4,
  "valid_rows": 0,
  "error_rows": 4,
  "error_summary": {
    "Feld 'longitude': '-' ist kein gültiger float": 1,
    "latitude 95.0 ungültig (muss zwischen -90 und 90 sein)": 1
  },
  "errors": [
    {"row": 1, "data": {...}, "error": "Feld 'longitude': '-' ist kein gültiger float"}
  ]
}
```

### 4. Keine Datei angegeben

```bash
curl -X POST http://localhost:8000/api/test
```

**Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "file"],
      "msg": "Field required"
    }
  ]
}
```

### 5. Datenbank nicht erreichbar

```bash
curl -X POST http://localhost:8000/api/upload -F "file=@examples/geodata_example_1.csv"
```

**Response (500 Internal Server Error):**
```json
{
  "detail": "Datenbankfehler: connection refused"
}
```

### 6. Keine gültigen Daten zum Speichern

```bash
curl -X POST http://localhost:8000/api/upload -F "file=@invalid_data.csv"
```

**Response (400 Bad Request):**
```json
{
  "detail": "Keine gültigen Daten zum Speichern"
}
```

---

## Tests

```bash
# Alle Tests ausführen
pytest

# Mit Coverage
pytest --cov=app

# Nur Parser-Tests
pytest tests/test_parsers.py -v

# Nur NAS Content-Detection Tests
pytest tests/test_nas_content_detection.py -v

# Nur Cleaner-Tests
pytest tests/test_cleaner.py -v

# Nur API-Tests
pytest tests/test_api.py -v
```

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
│   │   ├── base.py          # Parser Interface (Strategy Pattern)
│   │   ├── csv_parser.py    # CSV Parser
│   │   └── nas_parser.py    # NAS/XML Parser (mit Content-Detection)
│   ├── logic/
│   │   └── cleaner.py       # Datenbereinigung + Validierung
│   └── routers/
│       └── upload.py        # API Endpunkte (/api/test, /api/upload)
├── tests/
│   ├── test_api.py          # API Integration Tests
│   ├── test_cleaner.py      # Cleaner Unit Tests
│   ├── test_parsers.py      # Parser Unit Tests
│   └── test_nas_content_detection.py  # NAS Content-Detection Tests
├── examples/                 # Beispieldateien zum Testen
│   ├── geodata_example_1.csv
│   ├── geodata_example_1.nas
│   ├── geodata_example_2.csv
│   ├── geodata_example_2.nas
│   └── not_accepted_data_example.csv
├── docker-compose.yml        # PostgreSQL Container
├── requirements.txt          # Python Dependencies
├── pytest.ini               # Pytest Konfiguration
└── README.md                # Diese Dokumentation
```

---

## Datenbank-Befehle

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
┌───────────────────────────────────────┐
│  Parser-Factory (get_parser)          │
│  - Erkennt Dateiendung                │
│  - Wählt passenden Parser             │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  Parser (CSVParser / NASParser)       │
│  - NAS: Content-Detection (XML/Text)  │
│  - Extrahiert Rohdaten                │
└───────────────────────────────────────┘
        │
        ▼
    raw_data: Liste von Dicts
    [{"ID": "1001", "Gemeinde": "Hamburg", ...}, ...]
        │
        ▼
┌───────────────────────────────────────┐
│  DataCleaner                          │
│  - _clean_row(): Whitespace, Typen    │
│  - _validate_row(): Wertebereiche     │
└───────────────────────────────────────┘
        │
        ▼
    cleaned_data + errors
        │
        ├── /api/test  → Report zurückgeben (nichts speichern)
        │
        └── /api/upload → In DB speichern (Upsert)
                │
                ▼
        ┌───────────────────────────────┐
        │  Upsert-Logik                 │
        │  - ID existiert? → Update     │
        │  - ID neu? → Insert           │
        └───────────────────────────────┘
```

---

## Technologien

| Technologie | Verwendung |
|-------------|------------|
| **FastAPI** | Web-Framework, automatische OpenAPI Docs |
| **SQLAlchemy** | ORM für Datenbankzugriff |
| **PostgreSQL** | Relationale Datenbank |
| **Pydantic** | Datenvalidierung |
| **Docker** | Container für Datenbank |
| **pytest** | Unit Tests |

---

## Bekannte Einschränkungen

- **NAS-Parser:** Unterstützt nur XML-basierte Formate mit `<Flurstueck>`-Elementen. Text-basierte NAS-Formate werden mit klarer Fehlermeldung abgelehnt.
- **CSV-Parser:** Deutsche Zahlen (Komma statt Punkt) funktionieren bei Komma-getrennten CSVs nicht zuverlässig, da der Parser nicht unterscheiden kann ob `13,4050` eine Zahl oder zwei Spalten sind.
- **Encoding:** Nur UTF-8 kodierte Dateien werden unterstützt.
- **Dateigröße:** Keine explizite Größenbeschränkung konfiguriert.

---

## Bonus-Features (implementiert)

-  Unit Tests für Parser, Cleaner, API
-  OpenAPI/Swagger Dokumentation (automatisch via FastAPI)
-  Upsert-Strategie (Insert oder Update basierend auf ID)
-  Statistik nach Upload (inserted/updated Anzahl)
-  Content-Detection für NAS-Dateien (XML vs Text)