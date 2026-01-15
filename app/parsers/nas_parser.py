import re
from typing import List, Dict, Any
from app.parsers.base import FileParser


class NASParser(FileParser):
    """
    Parser für NAS-Dateien.
    Unterstützt zwei Formate:
    - XML-basiert: <Flurstueck>-Elemente
    - Text-basiert: EINHEIT-Blöcke mit Key-Value-Paaren
    """

    def _is_xml_format(self, text: str) -> bool:
        """Prüft ob der Inhalt XML-Format hat."""
        text_stripped = text.strip()
        
        xml_indicators = [
            text_stripped.startswith('<?xml'),
            text_stripped.startswith('<NasExport'),
            text_stripped.startswith('<Flurstueck'),
            '<NasExport>' in text,
            '<Flurstueck>' in text,
            '<?xml' in text,
        ]
        
        return any(xml_indicators)

    def _is_text_format(self, text: str) -> bool:
        """Prüft ob der Inhalt Text-basiertes NAS-Format hat."""
        text_stripped = text.strip()
        
        text_indicators = [
            text_stripped.startswith('BEGINN'),
            'EINHEIT:' in text or 'EINHEIT :' in text,
            'ENDE' in text and 'BEGINN' in text,
            re.search(r'^ID:\s*\d+', text, re.MULTILINE) is not None,
        ]
        
        return any(text_indicators) and not self._is_xml_format(text)

    def _parse_xml(self, text: str) -> List[Dict[str, Any]]:
        """Parst XML-basiertes NAS-Format."""
        results = []
        
        flurstueck_pattern = r'<Flurstueck>(.*?)</Flurstueck>'
        flurstuecke = re.findall(flurstueck_pattern, text, re.DOTALL)

        if not flurstuecke:
            raise ValueError(
                "Keine <Flurstueck>-Elemente in der NAS-Datei gefunden. "
                "Stellen Sie sicher, dass die Datei das erwartete XML-Format hat."
            )
        
        for block in flurstuecke:
            row = {}
            tag_pattern = r'<([^>]+)>([^<]*)</\1>'
            matches = re.findall(tag_pattern, block)
            
            for tag_name, value in matches:
                key = tag_name.strip()
                val = value.strip() if value else None
                row[key] = val
            
            results.append(row)
        
        return results

    def _parse_text(self, text: str) -> List[Dict[str, Any]]:
        """Parst Text-basiertes NAS-Format (EINHEIT-Blöcke)."""
        results = []
        
        # Finde alle EINHEIT-Blöcke
        einheit_pattern = r'EINHEIT:\s*Flurstueck(.*?)(?=EINHEIT:|ENDE|$)'
        einheiten = re.findall(einheit_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if not einheiten:
            raise ValueError(
                "Keine EINHEIT-Blöcke in der NAS-Datei gefunden. "
                "Stellen Sie sicher, dass die Datei das erwartete Text-Format hat."
            )
        
        for block in einheiten:
            row = {}
            
            # ID
            id_match = re.search(r'ID:\s*(\d+)', block)
            if id_match:
                row["ID"] = id_match.group(1)
            
            # Flurstücknummer
            flst_match = re.search(r'Flurstuecknummer:\s*([^\n]+)', block)
            if flst_match:
                row["Flurstücknummer"] = flst_match.group(1).strip()
            
            # Koordinaten (Format: "lat lon")
            coord_match = re.search(r'Koordinaten:\s*([\d.]+)\s+([\d.]+)', block)
            if coord_match:
                lat = coord_match.group(1)
                lon = coord_match.group(2)
                # Heuristik: Wert > 90 ist Longitude
                if float(lat) > 90:
                    lat, lon = lon, lat
                row["latidude"] = lat
                row["longitude"] = lon
            
            # Gemeinde
            gemeinde_match = re.search(r'Gemeinde:\s*([^\n]+)', block)
            if gemeinde_match:
                row["Gemeinde"] = gemeinde_match.group(1).strip()
            
            # Bundesland
            bundesland_match = re.search(r'Bundesland:\s*([^\n]+)', block)
            if bundesland_match:
                row["Bundesland"] = bundesland_match.group(1).strip()
            
            # Größe (mit oder ohne "ha")
            groesse_match = re.search(r'Groesse:\s*([\d.,]+)\s*(?:ha)?', block)
            if groesse_match:
                row["Größe in ha"] = groesse_match.group(1).strip()
            
            if row:
                results.append(row)
        
        return results

    def parse(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Parst NAS-Datei. Erkennt automatisch ob XML oder Text-Format."""
        text = file_content.decode("utf-8")
        
        if self._is_xml_format(text):
            return self._parse_xml(text)
        elif self._is_text_format(text):
            return self._parse_text(text)
        else:
            raise ValueError(
                "Nicht unterstütztes NAS-Format. "
                "Unterstützte Formate: XML-basiert (<Flurstueck>-Elemente) "
                "oder Text-basiert (EINHEIT-Blöcke)."
            )

    def get_supported_extension(self) -> str:
        return ".nas"