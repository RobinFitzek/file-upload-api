from abc import ABC, abstractmethod
from typing import List, Dict, Any

# Parser erben später von Vaterklasse
class FileParser(ABC):
    
    @abstractmethod
    def parse(self, file_content: bytes) -> List[Dict[str, Any]]:
        """
        Liest Dateiinhalt und gibt Liste von Dictionaries zurück.
        
        Args:
            file_content: Rohe Bytes der hochgeladenen Datei
            
        Returns:
            Liste von Dicts, jedes Dict = eine Zeile/ein Eintrag
            Beispiel: [{"ID": "1001", "Gemeinde": "Hamburg"}, ...]
        """
        pass
    
    @abstractmethod
    def get_supported_extension(self) -> str:
        """
        Gibt die unterstützte Dateiendung zurück.
        
        Returns:
            Dateiendung z.B. ".csv" oder ".nas"
        """
        pass