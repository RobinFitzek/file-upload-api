import csv
import io
from typing import List, Dict, Any
from app.parsers.base import FileParser


class CSVParser(FileParser):

    # erstellt Liste mit Elementen aus CSV-Datei
    def parse(self, file_content: bytes) -> List[Dict[str, Any]]:
        
        # Bytes zu String konvertieren
        text = file_content.decode("utf-8")
        
        # Initialisiere CSV-Reader
        reader = csv.DictReader(
            io.StringIO(text),
            delimiter=",",
            skipinitialspace=True
        )
        
        # Jeden Block in ein Python Object (Dict) umwandeln
        results = []
        for row in reader:
            # Whitespace von Keys und Values entfernen
            cleaned_row = {}
            for key, value in row.items():
                if key is None: # Bei zu vielen Spalten wie bei der geodata:example_2.csv
                    continue
                clean_key = key.strip() if key else key
                clean_value = value.strip() if value else value
                cleaned_row[clean_key] = clean_value
            results.append(cleaned_row)
        
        return results
    
    def get_supported_extension(self) -> str:
        return ".csv"