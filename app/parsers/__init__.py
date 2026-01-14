from app.parsers.base import FileParser
from app.parsers.csv_parser import CSVParser
from app.parsers.nas_parser import NASParser


def get_parser(filename: str) -> FileParser:
    
    # Überprüfe Dateiendung und gebe passenden Parser zurück
    filename_lower = filename.lower()
    
    if filename_lower.endswith(".csv"):
        return CSVParser()
    elif filename_lower.endswith(".nas"):
        return NASParser()
    else:
        raise ValueError(f"Nicht unterstütztes Dateiformat: {filename}")


# Exports für einfachen Import
__all__ = ["FileParser", "CSVParser", "NASParser", "get_parser"]