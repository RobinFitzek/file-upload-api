"""
Tests für CSV-Parser Edge Cases und Content-Validierung.
"""

import pytest
from app.parsers.csv_parser import CSVParser


class TestCSVParserEdgeCases:
    """Tests für Randfälle im CSV-Parser"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.parser = CSVParser()
    
    def test_parse_xml_content_as_csv(self):
        """Test: XML-Inhalt in CSV-Datei wird nicht korrekt geparst"""
        xml_content = b'''<?xml version="1.0"?>
        <NasExport>
            <Flurstueck><ID>1001</ID></Flurstueck>
        </NasExport>'''
        
        # CSV-Parser versucht zu parsen, findet aber keine sinnvollen Daten
        result = self.parser.parse(xml_content)
        
        # Entweder leere Liste oder Daten ohne sinnvolle Struktur
        # Der Parser sollte nicht crashen
        assert isinstance(result, list)
    
    def test_parse_empty_file(self):
        """Test: Leere Datei gibt leere Liste zurück"""
        result = self.parser.parse(b'')
        assert result == []
    
    def test_parse_only_header(self):
        """Test: Nur Header ohne Daten gibt leere Liste zurück"""
        result = self.parser.parse(b'ID,Name,Wert')
        assert result == []
    
    def test_parse_with_comma_delimiter(self):
        """Test: Komma als Trennzeichen funktioniert"""
        comma_csv = b'ID,Name\n1,Hamburg'
        result = self.parser.parse(comma_csv)
        assert len(result) == 1
        assert result[0]['ID'] == '1'
        assert result[0]['Name'] == 'Hamburg'
    
    def test_parse_with_quotes(self):
        """Test: Werte mit Anführungszeichen werden korrekt geparst"""
        csv_content = b'ID,Name,Beschreibung\n1,"Hamburg","Eine schoene Stadt"'
        result = self.parser.parse(csv_content)
        
        assert result[0]['Name'] == 'Hamburg'
        assert result[0]['Beschreibung'] == 'Eine schoene Stadt'
    
    def test_parse_with_newlines_in_values(self):
        """Test: Zeilenumbrüche in quoted Values"""
        csv_content = b'ID,Name,Beschreibung\n1,Hamburg,"Zeile 1\nZeile 2"'
        result = self.parser.parse(csv_content)
        
        assert len(result) == 1
        assert 'Zeile 1' in result[0]['Beschreibung']
    
    def test_parse_binary_content_fails_gracefully(self):
        """Test: Binärdaten führen nicht zum Crash"""
        binary_content = bytes([0x00, 0x01, 0x02, 0xFF, 0xFE])
        
        # Sollte entweder leere Liste zurückgeben oder Exception werfen
        try:
            result = self.parser.parse(binary_content)
            assert isinstance(result, list)
        except (UnicodeDecodeError, ValueError):
            pass  # Auch OK - Hauptsache kein unkontrollierter Crash
    
    def test_parse_inconsistent_columns(self):
        """Test: Unterschiedliche Spaltenanzahl pro Zeile"""
        csv_content = b'ID,Name,Wert\n1,Hamburg\n2,Berlin,100,Extra'
        
        result = self.parser.parse(csv_content)
        
        # Parser sollte trotzdem funktionieren
        assert len(result) >= 1


class TestCSVParserRealFiles:
    """Tests mit echten Beispieldateien"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.parser = CSVParser()
    
    def test_parse_geodata_example_1(self):
        """Test: geodata_example_1.csv wird korrekt geparst"""
        with open("examples/geodata_example_1.csv", "rb") as f:
            content = f.read()
        
        result = self.parser.parse(content)
        
        assert len(result) == 3
        assert result[0]['ID'] == '1001'
        assert result[0]['Gemeinde'] == 'Frankfurt am Main'
        assert result[0]['Bundesland'] == 'Hessen'
    
    def test_parse_geodata_example_2(self):
        """Test: geodata_example_2.csv wird korrekt geparst (auch mit fehlerhaften Daten)"""
        with open("examples/geodata_example_2.csv", "rb") as f:
            content = f.read()
        
        result = self.parser.parse(content)
        
        # Parser parst alle Zeilen, Validierung kommt später im Cleaner
        assert len(result) >= 1
    
    def test_parse_not_accepted_data(self):
        """Test: not_accepted_data_example.csv wird geparst"""
        with open("examples/not_accepted_data_example.csv", "rb") as f:
            content = f.read()
        
        result = self.parser.parse(content)
        
        # Parser parst, auch wenn Daten ungültig sind
        assert isinstance(result, list)