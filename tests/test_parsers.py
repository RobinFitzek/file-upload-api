import pytest
from app.parsers import get_parser, CSVParser, NASParser


class TestGetParser:
    """Tests für die Parser-Factory"""
    
    def test_csv_parser_returned(self):
        """CSV-Datei gibt CSVParser zurück"""
        parser = get_parser("test.csv")
        assert isinstance(parser, CSVParser)
    
    def test_nas_parser_returned(self):
        """NAS-Datei gibt NASParser zurück"""
        parser = get_parser("test.nas")
        assert isinstance(parser, NASParser)
    
    def test_case_insensitive(self):
        """Dateiendung ist case-insensitive"""
        assert isinstance(get_parser("test.CSV"), CSVParser)
        assert isinstance(get_parser("test.NAS"), NASParser)
    
    def test_unknown_format_raises_error(self):
        """Unbekanntes Format wirft ValueError"""
        with pytest.raises(ValueError) as exc_info:
            get_parser("test.txt")
        assert "Nicht unterstütztes Dateiformat" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            get_parser("test.xml")
        assert "Nicht unterstütztes Dateiformat" in str(exc_info.value)


class TestCSVParser:
    """Tests für den CSV Parser"""
    
    def test_parse_simple_csv(self):
        """Einfache CSV wird korrekt geparst"""
        csv_content = b"ID,Name\n1,Hamburg\n2,Berlin"
        parser = CSVParser()
        result = parser.parse(csv_content)
        
        assert len(result) == 2
        assert result[0]["ID"] == "1"
        assert result[0]["Name"] == "Hamburg"
        assert result[1]["ID"] == "2"
        assert result[1]["Name"] == "Berlin"
    
    def test_parse_with_whitespace(self):
        """Whitespace in Values wird getrimmt"""
        csv_content = b"ID,Name\n1,  Hamburg  \n2, Berlin "
        parser = CSVParser()
        result = parser.parse(csv_content)
        
        assert result[0]["Name"] == "Hamburg"
        assert result[1]["Name"] == "Berlin"
    
    def test_parse_geodata_example(self):
        """Echte Example-Datei wird korrekt geparst"""
        with open("examples/geodata_example_1.csv", "rb") as f:
            content = f.read()
        
        parser = CSVParser()
        result = parser.parse(content)
        
        assert len(result) == 3
        assert result[0]["ID"] == "1001"
        assert result[0]["Gemeinde"] == "Frankfurt am Main"
    
    def test_empty_csv(self):
        """Leere CSV gibt leere Liste zurück"""
        csv_content = b"ID,Name"  # nur Header
        parser = CSVParser()
        result = parser.parse(csv_content)
        
        assert result == []
    
    def test_supported_extension(self):
        """Gibt .csv als Extension zurück"""
        parser = CSVParser()
        assert parser.get_supported_extension() == ".csv"


class TestNASParser:
    """Tests für den NAS Parser"""
    
    def test_parse_simple_nas(self):
        """Einfache NAS wird korrekt geparst"""
        nas_content = b"""<?xml version="1.0"?>
        <NasExport>
            <Flurstueck>
                <ID>1001</ID>
                <Gemeinde>Hamburg</Gemeinde>
            </Flurstueck>
        </NasExport>"""
        
        parser = NASParser()
        result = parser.parse(nas_content)
        
        assert len(result) == 1
        assert result[0]["ID"] == "1001"
        assert result[0]["Gemeinde"] == "Hamburg"
    
    def test_parse_multiple_flurstuecke(self):
        """Mehrere Flurstuecke werden alle geparst"""
        nas_content = b"""<NasExport>
            <Flurstueck><ID>1</ID></Flurstueck>
            <Flurstueck><ID>2</ID></Flurstueck>
            <Flurstueck><ID>3</ID></Flurstueck>
        </NasExport>"""
        
        parser = NASParser()
        result = parser.parse(nas_content)
        
        assert len(result) == 3
    
    def test_parse_with_special_tagname(self):
        """Tags mit Sonderzeichen werden korrekt geparst"""
        # Nutze .encode() statt b"..." für Umlaute
        nas_content = """<NasExport>
            <Flurstueck>
                <ID>1001</ID>
                <Groesse>0.87</Groesse>
            </Flurstueck>
        </NasExport>""".encode("utf-8")
        
        parser = NASParser()
        result = parser.parse(nas_content)
        
        assert result[0]["Groesse"] == "0.87"
    
    def test_parse_geodata_example(self):
        """Echte Example-Datei wird korrekt geparst"""
        with open("examples/geodata_example_1.nas", "rb") as f:
            content = f.read()
        
        parser = NASParser()
        result = parser.parse(content)
        
        assert len(result) == 2
        assert result[0]["ID"] == "2001"
        assert result[0]["Gemeinde"] == "Hamburg"
    
    def test_supported_extension(self):
        """Gibt .nas als Extension zurück"""
        parser = NASParser()
        assert parser.get_supported_extension() == ".nas"
    
    def test_text_nas_rejected_with_clear_error(self):
        """Text-basiertes NAS wird mit klarer Fehlermeldung abgelehnt"""
        text_nas = b"BEGINN\nDaten\nENDE"
        parser = NASParser()
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse(text_nas)
        
        error_msg = str(exc_info.value)
        assert "Nicht unterstütztes NAS-Format" in error_msg
        assert "XML-basierte" in error_msg
    
    def test_empty_nas_rejected(self):
        """NAS ohne Flurstueck-Elemente wird abgelehnt"""
        empty_nas = b"<?xml version='1.0'?><NasExport></NasExport>"
        parser = NASParser()
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse(empty_nas)
        
        assert "Keine <Flurstueck>-Elemente" in str(exc_info.value)