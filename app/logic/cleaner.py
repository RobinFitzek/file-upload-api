"""
Datenbereinigung für Geodaten.
Entfernt Whitespace, konvertiert Typen, erkennt Fehler.
"""

from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Bereinigt geparste Geodaten:
    - Entfernt Whitespace
    - Konvertiert Strings zu richtigen Typen (int, float)
    - Wandelt leere Strings in None um
    - Validiert Wertebereiche (z.B. latitude -90 bis 90)
    - Erkennt fehlerhafte Zeilen
    """
    
    # Mapping: Quelldaten-Spalten → (DB-Spalte, erwarteter Typ)
    FIELD_MAPPING = {
        "ID": ("id", int),
        "Flurstücknummer": ("flurstuecknummer", str),
        "longitude": ("longitude", float),
        "latidude": ("latitude", float),  # Tippfehler in Quelldaten!
        "Gemeinde": ("gemeinde", str),
        "Bundesland": ("bundesland", str),
        "Größe in ha": ("groesse_ha", float),
    }

    # Werte die als NULL behandelt werden
    NULL_VALUES = {"", "null", "NULL", "None", "N/A", "n/a", "-"}
    
    def clean(self, raw_data: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
        """
        Bereinigt die Rohdaten.
        
        Args:
            raw_data: Liste von Dicts aus dem Parser
            
        Returns:
            Tuple von (bereinigte_daten, fehlerhafte_zeilen)
        """
        cleaned = []
        errors = []
        
        for row_index, row in enumerate(raw_data):
            try:
                cleaned_row = self._clean_row(row)
                self._validate_row(cleaned_row)  # Zusätzliche Validierung
                cleaned.append(cleaned_row)
            except Exception as e:
                errors.append({
                    "row": row_index + 1,
                    "data": row,
                    "error": str(e)
                })
                logger.warning(f"Zeile {row_index + 1} fehlerhaft: {e}")
        
        return cleaned, errors
    
    def _clean_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Bereinigt eine einzelne Zeile."""
        cleaned = {}
        
        for source_field, (target_field, expected_type) in self.FIELD_MAPPING.items():
            # Wert holen (kann None sein wenn Feld fehlt)
            value = row.get(source_field)
            
            # Whitespace entfernen
            if isinstance(value, str):
                value = value.strip()
            
            # Leere/NULL Werte → None
            if value in self.NULL_VALUES or value is None:
                cleaned[target_field] = None
                continue
            
            # Typ konvertieren
            try:
                if expected_type == int:
                    cleaned[target_field] = int(float(value))  # "3.0" → 3
                elif expected_type == float:
                    # Komma zu Punkt für deutsche Zahlen
                    if isinstance(value, str):
                        value = value.replace(",", ".")
                    cleaned[target_field] = float(value)
                else:
                    cleaned[target_field] = str(value)
            except (ValueError, TypeError):
                raise ValueError(f"Feld '{source_field}': '{value}' ist kein gültiger {expected_type.__name__}")
        
        return cleaned
    
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
    
    def generate_report(self, raw_data: List[Dict], cleaned_data: List[Dict], errors: List[Dict]) -> Dict:
        """
        Erstellt einen Datenqualitäts-Report.
        Wird für POST /api/test verwendet.
        """
        # Fehler aggregieren (gruppieren nach Fehlertyp)
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
        elif len(cleaned_data) > 0:
            status = "FIXABLE"
        else:
            status = "INVALID"
        
        # Bereinigungen die durchgeführt wurden
        cleanings_applied = [
            "Whitespace entfernt (trim)",
            "Leere Werte zu NULL konvertiert",
            "Typkonvertierung (String → int/float)",
            "Spaltennamen normalisiert (deutsch → snake_case)",
            "Wertebereiche validiert (lat/lon/größe)"
        ]
        
        return {
            "status": status,
            "total_rows": len(raw_data),
            "valid_rows": len(cleaned_data),
            "error_rows": len(errors),
            "error_summary": error_summary,  # Aggregierte Fehler
            "errors": errors[:10],  # Erste 10 Fehler im Detail
            "cleanings_applied": cleanings_applied,
            "preview": cleaned_data[:5],
            "columns_found": list(raw_data[0].keys()) if raw_data else [],
            "columns_mapped": list(self.FIELD_MAPPING.keys())
        }