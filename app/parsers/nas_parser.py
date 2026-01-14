import re
from typing import List, Dict, Any
from app.parsers.base import FileParser


class NASParser(FileParser):
    """
    Parser für NAS/XML-Dateien.
    Erwartet <NasExport> als Wurzel mit <Flurstueck>-Elementen.
    """
    
    def parse(self, file_content: bytes) -> List[Dict[str, Any]]:
        """
        Liest NAS/XML und gibt Liste von Dicts zurück.
        Nutzt Regex weil die Beispieldateien ungültiges XML haben
        (z.B. <Größe in ha> mit Leerzeichen im Tag).
        """
        # Bytes zu String
        text = file_content.decode("utf-8")
        
        results = []
        
        # Alle <Flurstueck>...</Flurstueck> Blöcke finden
        flurstueck_pattern = r'<Flurstueck>(.*?)</Flurstueck>'
        flurstuecke = re.findall(flurstueck_pattern, text, re.DOTALL)
        
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