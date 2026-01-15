from abc import ABC, abstractmethod
from typing import List, Dict, Any

# Parser erben später von Vaterklasse
class FileParser(ABC):
    
    @abstractmethod
    def parse(self, file_content: bytes) -> List[Dict[str, Any]]:
      
        pass
    
    @abstractmethod
    def get_supported_extension(self) -> str:

        pass