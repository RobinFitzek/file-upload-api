"""
Parser für CSV-Dateien (Comma-Separated Values).
Liest Dateien wie geodata_example_1.csv ein.
"""

import csv
import io
from typing import List, Dict, Any
from app.parsers.base import FileParser


class CSVParser(FileParser):
    """
    Parser für CSV-Dateien.
    Erwartet Komma als Trennzeichen und Header in der ersten Zeile.
    """
    
    def parse(self, file_content: bytes) -> List[Dict[str, Any]]:
        """
        Liest CSV und gibt Liste von Dicts zurück.
        
        Beispiel Input (geodata_example_1.csv):
            ID,Flurstücknummer,longitude,...
            1001,045-123-0001,8.6821,...
            
        Beispiel Output:
            [{"ID": "1001", "Flurstücknummer": "045-123-0001", ...}, ...]
        """
        # Bytes zu String konvertieren (UTF-8)
        text = file_content.decode("utf-8")
        
        # CSV Reader erstellen
        # - io.StringIO: macht aus String ein "file-like object"
        # - delimiter=",": Komma als Trennzeichen
        # - skipinitialspace=True: Leerzeichen nach Komma ignorieren
        reader = csv.DictReader(
            io.StringIO(text),
            delimiter=",",
            skipinitialspace=True
        )
        
        results = []
        for row in reader:
            # Whitespace von Keys und Values entfernen
            cleaned_row = {}
            for key, value in row.items():
                clean_key = key.strip() if key else key
                clean_value = value.strip() if value else value
                cleaned_row[clean_key] = clean_value
            results.append(cleaned_row)
        
        return results
    
    def get_supported_extension(self) -> str:
        return ".csv"