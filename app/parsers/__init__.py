"""
Parser-Modul: Liest verschiedene Dateiformate ein.
Strategy Pattern - je nach Dateiendung wird der richtige Parser gewählt.
"""

from app.parsers.base import FileParser
from app.parsers.csv_parser import CSVParser
from app.parsers.nas_parser import NASParser


def get_parser(filename: str) -> FileParser:
    """
    Factory-Funktion: Gibt den richtigen Parser für die Datei zurück.
    
    Args:
        filename: Name der Datei (z.B. "geodata.csv")
        
    Returns:
        Passender Parser (CSVParser oder NASParser)
        
    Raises:
        ValueError: Wenn Dateiformat nicht unterstützt wird
        
    Beispiel:
        parser = get_parser("test.csv")  # → CSVParser
        parser = get_parser("test.nas")  # → NASParser
    """
    filename_lower = filename.lower()
    
    if filename_lower.endswith(".csv"):
        return CSVParser()
    elif filename_lower.endswith(".nas"):
        return NASParser()
    else:
        raise ValueError(f"Nicht unterstütztes Dateiformat: {filename}")


# Exports für einfachen Import
__all__ = ["FileParser", "CSVParser", "NASParser", "get_parser"]