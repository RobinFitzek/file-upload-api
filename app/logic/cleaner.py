from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Bekannte deutsche Bundesländer
VALID_BUNDESLAENDER = {
    "baden-württemberg", "bayern", "berlin", "brandenburg", "bremen",
    "hamburg", "hessen", "mecklenburg-vorpommern", "niedersachsen",
    "nordrhein-westfalen", "rheinland-pfalz", "saarland", "sachsen",
    "sachsen-anhalt", "schleswig-holstein", "thüringen", "thueringen", "baden-wuerttemberg"
}



class DataCleaner:
    """
    Bereinigt und validiert Geodaten.
    
    Durchgeführte Operationen:
    - Whitespace entfernen (trim)
    - Leere Werte zu NULL konvertieren
    - Typkonvertierung (String → int/float)
    - Deutsche Dezimalzahlen (Komma → Punkt)
    - Spaltennamen normalisieren
    - Wertebereiche validieren
    - Semantische Validierung (Bundesland)
    """
    
    # Mapping: Quelldaten-Spalten → (Zielfeld, Typ)
    FIELD_MAPPING = {
        "ID": ("id", int),
        "Flurstücknummer": ("flurstuecknummer", str),
        "longitude": ("longitude", float),
        "latidude": ("latitude", float),  # Tippfehler in Quelldaten
        "Gemeinde": ("gemeinde", str),
        "Bundesland": ("bundesland", str),
        "Größe in ha": ("groesse_ha", float),
    }

    # Werte die als NULL behandelt werden
    NULL_VALUES = {"", "null", "NULL", "None", "N/A", "n/a", "-"}
    
    def __init__(self):
        # Zähler für durchgeführte Bereinigungen
        self.cleanings_performed = {
            "whitespace_trimmed": 0,
            "null_converted": 0,
            "comma_to_point": 0,
            "type_converted": 0,
        }
        # Detaillierte Bereinigungen pro Zeile
        self.cleaning_details = []

    
    def clean(self, raw_data: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
        """
        Bereinigt die Rohdaten.
        
        Args:
            raw_data: Liste von Dicts aus dem Parser
            
        Returns:
            Tuple von (bereinigte_daten, fehlerhafte_zeilen)
        """
        # Reset counters
        self.cleanings_performed = {
            "whitespace_trimmed": 0,
            "null_converted": 0,
            "comma_to_point": 0,
            "type_converted": 0,
        }
        self.cleaning_details = []
        
        cleaned = []
        errors = []
        
        for row_index, row in enumerate(raw_data):
            row_cleanings = []  # Bereinigungen für diese Zeile
            
            try:
                cleaned_row, row_cleanings = self._clean_row(row, row_index + 1)
                self._validate_row(cleaned_row)
                self._validate_semantics(cleaned_row)
                cleaned.append(cleaned_row)
                
                # Bereinigungen protokollieren
                if row_cleanings:
                    self.cleaning_details.append({
                        "row": row_index + 1,
                        "cleanings": row_cleanings
                    })
                    
            except Exception as e:
                errors.append({
                    "row": row_index + 1,
                    "data": row,
                    "error": str(e)
                })
                logger.warning(f"Zeile {row_index + 1} fehlerhaft: {e}")
        
        return cleaned, errors
    
    def _clean_row(self, row: Dict[str, Any], row_num: int) -> Tuple[Dict[str, Any], List[str]]:
        """
        Bereinigt eine einzelne Zeile.
        
        Returns:
            Tuple von (bereinigte_zeile, liste_der_bereinigungen)
        """
        cleaned = {}
        row_cleanings = []
        
        for source_field, (target_field, expected_type) in self.FIELD_MAPPING.items():
            value = row.get(source_field)
            original_value = value
            
            # 1. Whitespace entfernen
            if isinstance(value, str):
                stripped = value.strip()
                if stripped != value:
                    row_cleanings.append(f"'{source_field}': Whitespace entfernt")
                    self.cleanings_performed["whitespace_trimmed"] += 1
                value = stripped
            
            # 2. Leere/NULL Werte zu None
            if value in self.NULL_VALUES or value is None:
                if original_value not in [None, ""]:
                    row_cleanings.append(f"'{source_field}': '{original_value}' → NULL")
                    self.cleanings_performed["null_converted"] += 1
                cleaned[target_field] = None
                continue
            
            # 3. Typ konvertieren
            try:
                if expected_type == int:
                    cleaned[target_field] = int(float(value))
                    if isinstance(original_value, str):
                        row_cleanings.append(f"'{source_field}': String '{value}' → Integer {cleaned[target_field]}")
                        self.cleanings_performed["type_converted"] += 1
                        
                elif expected_type == float:
                    # Komma zu Punkt für deutsche Zahlen
                    if isinstance(value, str) and "," in value:
                        value_converted = value.replace(",", ".")
                        row_cleanings.append(f"'{source_field}': Komma zu Punkt '{value}' → '{value_converted}'")
                        self.cleanings_performed["comma_to_point"] += 1
                        value = value_converted
                    
                    cleaned[target_field] = float(value)
                    if isinstance(original_value, str):
                        self.cleanings_performed["type_converted"] += 1
                else:
                    cleaned[target_field] = str(value)
                    
            except (ValueError, TypeError):
                raise ValueError(f"Feld '{source_field}': '{value}' ist kein gültiger {expected_type.__name__}")
        
        return cleaned, row_cleanings
    
    def _validate_row(self, row: Dict[str, Any]) -> None:
        """Validiert Wertebereiche und Pflichtfelder."""
        errors = []
        
        # ID muss vorhanden sein
        if row.get("id") is None:
            errors.append("ID fehlt (Pflichtfeld)")
        
        # Latitude: -90 bis 90
        lat = row.get("latitude")
        if lat is not None and (lat < -90 or lat > 90):
            errors.append(f"latitude {lat} ungültig (muss zwischen -90 und 90 sein)")
        
        # Longitude: -180 bis 180
        lon = row.get("longitude")
        if lon is not None and (lon < -180 or lon > 180):
            errors.append(f"longitude {lon} ungültig (muss zwischen -180 und 180 sein)")
        
        # Größe: nicht negativ
        groesse = row.get("groesse_ha")
        if groesse is not None and groesse < 0:
            errors.append(f"groesse_ha {groesse} ungültig (darf nicht negativ sein)")
        
        if errors:
            raise ValueError("; ".join(errors))

    def _validate_semantics(self, row: Dict[str, Any]) -> None:
        """Validiert semantische Korrektheit der Daten."""
        errors = []
        
        # Bundesland prüfen
        bundesland = row.get("bundesland")
        if bundesland is not None:
            if bundesland.lower() not in VALID_BUNDESLAENDER:
                errors.append(f"'{bundesland}' ist kein gültiges deutsches Bundesland")
    
        if errors:
            raise ValueError("; ".join(errors))

    def generate_report(self, raw_data: List[Dict], cleaned_data: List[Dict], errors: List[Dict]) -> Dict:
        """
        Generiert einen detaillierten Datenqualitäts-Report.
        
        Enthält:
        - Status (OK / FIXABLE / INVALID)
        - Anzahl Zeilen (gesamt, gültig, fehlerhaft)
        - Durchgeführte Bereinigungen (aggregiert + Details)
        - Fehlerliste
        """
        # Fehler gruppieren
        error_summary = {}
        for err in errors:
            error_msg = err["error"]
            if error_msg in error_summary:
                error_summary[error_msg] += 1
            else:
                error_summary[error_msg] = 1
        
        # Status bestimmen
        if len(errors) == 0:
            status = "OK"
            status_description = "Alle Daten sind konform und können gespeichert werden."
        elif len(cleaned_data) > 0:
            status = "FIXABLE"
            status_description = f"{len(cleaned_data)} von {len(raw_data)} Zeilen sind gültig nach Bereinigung. {len(errors)} Zeilen haben Fehler."
        else:
            status = "INVALID"
            status_description = "Keine gültigen Daten. Datei kann nicht verarbeitet werden."
        
        # Bereinigungen die durchgeführt wurden (mit Anzahl)
        cleanings_applied = []
        if self.cleanings_performed["whitespace_trimmed"] > 0:
            cleanings_applied.append(f"Whitespace entfernt ({self.cleanings_performed['whitespace_trimmed']}x)")
        if self.cleanings_performed["null_converted"] > 0:
            cleanings_applied.append(f"Leere Werte zu NULL konvertiert ({self.cleanings_performed['null_converted']}x)")
        if self.cleanings_performed["comma_to_point"] > 0:
            cleanings_applied.append(f"Komma zu Punkt konvertiert ({self.cleanings_performed['comma_to_point']}x)")
        if self.cleanings_performed["type_converted"] > 0:
            cleanings_applied.append(f"Typkonvertierung String → Zahl ({self.cleanings_performed['type_converted']}x)")
        
        # Immer anzeigen (auch wenn 0x)
        cleanings_applied.append("Spaltennamen normalisiert (deutsch → snake_case)")
        cleanings_applied.append("Wertebereiche validiert (lat: -90..90, lon: -180..180, größe: ≥0)")
        cleanings_applied.append("Bundesland validiert (muss deutsches Bundesland sein)")
        
        # Zusammenfassung der Bereinigungen
        total_cleanings = sum(self.cleanings_performed.values())
        
        return {
            "status": status,
            "status_description": status_description,
            "readable": True,  # Datei war lesbar
            "schema_conform": len(errors) == 0,
            "total_rows": len(raw_data),
            "valid_rows": len(cleaned_data),
            "error_rows": len(errors),
            "cleanings_summary": {
                "total_cleanings": total_cleanings,
                "whitespace_trimmed": self.cleanings_performed["whitespace_trimmed"],
                "null_converted": self.cleanings_performed["null_converted"],
                "comma_to_point": self.cleanings_performed["comma_to_point"],
                "type_converted": self.cleanings_performed["type_converted"],
            },
            "cleanings_applied": cleanings_applied,
            "cleaning_details": self.cleaning_details[:10],  # Erste 10 Zeilen mit Details
            "error_summary": error_summary,
            "errors": errors[:10],
            "preview": cleaned_data[:5],
            "columns_found": list(raw_data[0].keys()) if raw_data else [],
            "columns_mapped": list(self.FIELD_MAPPING.keys())
        }