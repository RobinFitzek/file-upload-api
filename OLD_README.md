# Probeaufgabe: File-Upload API + Datenbereinigung + Persistenz (Postgres)

## Ziel
Du entwickelst eine kleine Web-Anwendung, in der Benutzer **.csv**- und **.nas**-Dateien hochladen können.  
Die Anwendung soll:

1. Dateien entgegennehmen (Upload)
2. Inhalte **einlesen**
3. Eine **Datenqualitätsprüfung** und **Datenbereinigung** durchführen
4. Die bereinigten Daten in eine **Postgres-Datenbank** schreiben (Docker)
5. Dem Benutzer je nach Aktion ein verständliches Ergebnis anzeigen

> UI/UX ist nicht wichtig – Funktionalität, saubere Struktur und Nachvollziehbarkeit sind entscheidend.

---

## Rahmenbedingungen
- Architektur: frei wählbar (Monolith ist ok; Frontend/Backend müssen nicht getrennt werden)
- Technologie: frei wählbar (Python bietet sich an, ist aber kein Muss)
- Datenbank: **Postgres in Docker**
- Abgabe: **Public GitHub/GitLab Repo** + Link senden

---

## Funktionsumfang

### 1) Frontend (Minimal-UI)
Eine sehr einfache Seite, zentriert (z.B. Bootstrap), ohne Layout-Aufwand:

- **File-Upload Feld**
- Zwei Buttons:
  1. **„test“**
  2. **„upload“**

Keine Authentifizierung, keine Benutzerverwaltung.

#### Button „test“ – Erwartetes Verhalten
- Datei wird hochgeladen und serverseitig verarbeitet, aber **nicht gespeichert**
- Die Anwendung liefert dem User ein **Datenqualitäts-Report**, z.B.:
  - Ob das File **lesbar** ist
  - Ob Spalten/Datentypen **konform** zum Schema sind
  - Welche **Bereinigungen** nötig wären (oder durchgeführt würden)
  - Eine klare Einstufung, z.B.:
    -  *Konform / OK*
    -  *Konform nach Bereinigung*
    -  *Nicht konform (kann nicht verarbeitet werden)*

Ausgabe kann simpel als JSON im Browser oder als einfache HTML-Liste erfolgen.

#### Button „upload“ – Erwartetes Verhalten
- Datei wird hochgeladen
- Daten werden **eingelesen**, **bereinigt** und anschließend in Postgres **persistiert**
- User erhält eine klare **Success-Meldung** (und optional Anzahl importierter Datensätze)

---

### 2) Backend
Das Backend soll die Requests annehmen und sinnvoll verarbeiten. Erwartet wird eine saubere, nachvollziehbare Struktur, z.B.:

- Routing/Controller Layer
- Service/Business-Logik (Parsing, Validation, Cleaning)
- Persistence Layer (DB)

#### Empfohlene API-Endpunkte (Beispiel)
- `POST /api/test`  
- `POST /api/upload`

Du kannst andere Pfade wählen – aber dokumentiere sie.

---

### 3) Dateiformate: .csv und .nas
Die App muss beide Dateitypen akzeptieren.

- **CSV**: klassisches tabellarisches Format
- **NAS**: Die Endung `.nas` ist in der Praxis nicht eindeutig (kann je nach Domäne XML oder textbasiert sein).  
  Für diese Aufgabe gilt daher:
  - Implementiere einen **Parser-Mechanismus**, der klar getrennt ist (z.B. Strategy Pattern / `FileParser` Interface).
  - Lege im Repo in `./examples/` **eigene Minimal-Beispieldateien** ab (`.csv` und `.nas`), die dein System verarbeiten kann.
  - Dokumentiere in der README **welche .nas-Variante** du unterstützt und welche Annahmen du triffst.
  - Bonus: Erkenne anhand des Inhalts, ob `.nas` eher **XML** oder **textbasiert** ist, und reagiere mit einer verständlichen Fehlermeldung, falls nicht unterstützt.

> In der Bewertung achten wir besonders auf Robustheit, Fehlermeldungen und saubere Trennung der Parser-Logik.

---

## Zielschema (Datenmodell)
Definiere ein klares Schema, nach dem du Daten validierst und speicherst.  
Du darfst das Schema selbst festlegen, aber es muss den Daten entsprechen. 
Als Beispiel und Referenz dienen die beigefügten example Dateien 


### Mindestanforderung an das Schema
Bitte implementieren:

- **Pflichtfelder** (NOT NULL)
- **Typprüfung** (z.B. Datum parsebar, Zahlen sind Zahlen)
- **Eindeutigkeit** für einen sinnvollen Schlüssel (z.B. `external_id` oder zusammengesetzter Schlüssel)
- Speicherung in mindestens **einer Tabelle** (mehr ist optional)

> Wichtig: Das Schema muss in der README dokumentiert sein.

---

## Datenbereinigung (Cleaning Rules)
Implementiere nachvollziehbare Bereinigungen. Mindestens:

1. **Whitespace entfernen** (trim) bei Strings
2. **Leere Werte normalisieren** (z.B. `""`, `"null"`, `"N/A"` → `NULL`)
3. **Typkonvertierung**:
   - Zahlenfelder in numeric/int
   - Datumsfelder in `date/datetime`
4. **Duplikate behandeln** (z.B. nach Schlüssel):
   - definieren, wie entschieden wird (erste Zeile gewinnt / letzte gewinnt / error)
5. **Spaltennamen normalisieren**:
   - z.B. case-insensitive matching (`Name`, `name`, `NAME`)
   - oder klarer Fehler, wenn Spalten fehlen

### Ergebnis der Bereinigung
- Für „test“: nur Report (nichts speichern)
- Für „upload“: tatsächlich bereinigt speichern

---

## Datenqualitäts-Report (für „test“)
Der Report soll mindestens enthalten:

- Dateityp erkannt: `csv | nas | unknown`
- Anzahl gelesener Zeilen
- Anzahl gültiger Datensätze
- Anzahl ungültiger Datensätze + Gründe (aggregiert)
- Liste/Übersicht der angewendeten oder notwendigen Bereinigungen
- Status: `OK | FIXABLE | INVALID`

---
## Datenbank (Docker Postgres)
Stelle eine lauffähige Postgres DB via Docker bereit.

### Anforderungen
- `docker-compose.yml` mit Postgres
- App kann sich verbinden (Config via ENV Variablen)
- Erstelle Tabellen automatisiert (Migrationen oder automatisch beim Start; dokumentieren)
- Bei „upload“ sollen Datensätze tatsächlich in Postgres landen

---

## Nicht-Funktionale Anforderungen
- Saubere Fehlermeldungen (Frontend und API)
- Sinnvolle HTTP Status Codes
- Logging (mindestens rudimentär)
- Klare Projektstruktur
- Clean Code
- Konsistenz
- README, damit ein Reviewer alles lokal starten kann

---

## README Mindestinhalt
Bitte dokumentieren:

1. Setup (Voraussetzungen)
2. Start via Docker (DB) + Start der App
3. Endpunkte / Bedienung der UI
4. Unterstütztes Schema + Beispiel-Dateien
5. Welche Bereinigungen durchgeführt werden
6. Typische Fehlerfälle und deren Output

---

## Bonus (optional)
- Unit Tests für Parser/Cleaner/Validator
- OpenAPI/Swagger (z.B. bei FastAPI)
- Batch Insert / Upsert Strategie
- Kleine Statistik-Ansicht nach Upload (z.B. Anzahl inserted/updated)
- Unterstützung mehrerer `.nas`-Varianten (z.B. XML vs Text) oder zumindest Content-Detection

---

## Abgabe
- Code in ein **public repo** (GitHub/GitLab)
- Link an uns senden
- Repo muss ohne manuelle „Spezialschritte“ lokal startbar sein (README)

Es geht nicht um Perfektion. Es geht darum, eure code skills einordnen zu können, eure Arbeitsweise und Herangehensweise herauszufinden.

Viel Erfolg!



