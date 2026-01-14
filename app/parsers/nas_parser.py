import re
from typing import List, Dict, Any
from app.parsers.base import FileParser


class NASParser(FileParser):

    # erstellt Liste mit Elementen aus NAS-Datei, nutzt dabei REGEX damit tag-Name XML gültig ist    
    def parse(self, file_content: bytes) -> List[Dict[str, Any]]:

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