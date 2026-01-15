import re
from typing import List, Dict, Any
from app.parsers.base import FileParser


class NASParser(FileParser):

    # erstellt Liste mit Elementen aus NAS-Datei, nutzt dabei REGEX damit tag-Name XML gültig ist    
    """
    Unterstützt XML-basierte NAS-Dateien mit <Flurstueck>-Elementen.
    Text-basierte NAS-Formate werden mit einer klaren Fehlermeldung abgelehnt.
    """

    def _is_xml_format(self, text: str) -> bool:
        """
        Prüft ob der Inhalt XML-Format hat.
        
        Args:
            text: Dateiinhalt als String
            
        Returns:
            True wenn XML-Format erkannt wurde, sonst False
        """
        text_stripped = text.strip()
        
        # Positive Indikatoren für XML
        xml_indicators = [
            text_stripped.startswith('<?xml'),
            text_stripped.startswith('<NasExport'),
            text_stripped.startswith('<Flurstueck'),
            '<NasExport>' in text,
            '<Flurstueck>' in text,
            '<?xml' in text,
        ]
        
        # Negative Indikatoren (Text-basierte NAS-Formate)
        text_nas_indicators = [
            text_stripped.startswith('BEGINN'),
            text_stripped.startswith('NAS '),
            text_stripped.startswith('EINHEIT'),
            re.match(r'^\d{4}-\d{2}-\d{2}', text_stripped) is not None,
            'ENDE' in text and 'BEGINN' in text and '<' not in text,
            not any(c in text for c in ['<', '>']),  # Keine XML-Tags
        ]
        
        # Wenn Text-NAS-Indikatoren gefunden und keine XML-Tags, ist es kein XML
        if any(text_nas_indicators) and not any(xml_indicators):
            return False
        
        # Wenn XML-Indikatoren gefunden, ist es XML
        return any(xml_indicators)
    



    def parse(self, file_content: bytes) -> List[Dict[str, Any]]:

        # Bytes zu String
        text = file_content.decode("utf-8")

        # Content-Detection: Prüfe ob es sich um XML handelt
        if not self._is_xml_format(text):
            raise ValueError(
                "Nicht unterstütztes NAS-Format. "
                "Nur XML-basierte NAS-Dateien werden unterstützt. "
                "Das hochgeladene Format scheint ein Text-basiertes NAS-Format zu sein."
            )
        
        results = []
        
        # Alle <Flurstueck>...</Flurstueck> Blöcke finden
        flurstueck_pattern = r'<Flurstueck>(.*?)</Flurstueck>'
        flurstuecke = re.findall(flurstueck_pattern, text, re.DOTALL)

        if not flurstuecke:
            raise ValueError(
                "Keine <Flurstueck>-Elemente in der NAS-Datei gefunden. "
                "Stellen Sie sicher, dass die Datei das erwartete XML-Format hat."
            )
        
        for block in flurstuecke:
            row = {}
            # Alle Tags im Block finden: <TagName>Wert</TagName>
            tag_pattern = r'<([^>]+)>([^<]*)</\1>'
            matches = re.findall(tag_pattern, block)
            
            for tag_name, value in matches:
                key = tag_name.strip()
                val = value.strip() if value else None
                row[key] = val
            
            results.append(row)
        
        return results
    
    
    def get_supported_extension(self) -> str:
        return ".nas"