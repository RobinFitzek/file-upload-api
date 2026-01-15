"""
Tests für den NAS-Parser mit Content-Detection.
Prüft ob XML-basierte NAS-Dateien akzeptiert und Text-basierte abgelehnt werden.
"""

import pytest
from app.parsers.nas_parser import NASParser


class TestNASParserContentDetection:
    """Tests für die Content-Detection im NAS-Parser"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.parser = NASParser()
    
    def test_is_xml_format_with_xml_declaration(self):
        """Test: XML-Deklaration wird als XML erkannt"""
        xml_text = '<?xml version="1.0"?><NasExport></NasExport>'
        assert self.parser._is_xml_format(xml_text) is True
    
    def test_is_xml_format_with_nasexport_element(self):
        """Test: NasExport-Element wird als XML erkannt"""
        xml_text = '<NasExport><Flurstueck></Flurstueck></NasExport>'
        assert self.parser._is_xml_format(xml_text) is True
    
    def test_is_xml_format_with_flurstueck_element(self):
        """Test: Flurstueck-Element wird als XML erkannt"""
        xml_text = '<Flurstueck><ID>123</ID></Flurstueck>'
        assert self.parser._is_xml_format(xml_text) is True
    
    def test_is_not_xml_format_with_text_nas(self):
        """Test: Text-NAS wird nicht als XML erkannt"""
        text_nas = 'BEGINN\n2024-01-15\nDaten\nENDE'
        assert self.parser._is_xml_format(text_nas) is False
    
    def test_is_not_xml_format_without_tags(self):
        """Test: Text ohne XML-Tags wird nicht als XML erkannt"""
        text_nas = 'ID;Name;Wert\n1;Test;100\n2;Test2;200'
        assert self.parser._is_xml_format(text_nas) is False
    
    def test_is_not_xml_format_with_einheit_start(self):
        """Test: EINHEIT-Start wird nicht als XML erkannt"""
        text_nas = 'EINHEIT\nDaten hier\nENDE'
        assert self.parser._is_xml_format(text_nas) is False


class TestNASParserValidXML:
    """Tests für valide XML-NAS-Dateien"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.parser = NASParser()
    
    def test_parse_valid_xml_nas(self):
        """Test: Valides XML-NAS wird korrekt geparst"""
        xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
        <NasExport>
            <Flurstueck>
                <ID>1001</ID>
                <Gemeinde>Hamburg</Gemeinde>
                <longitude>9.9937</longitude>
                <latidude>53.5511</latidude>
            </Flurstueck>
        </NasExport>'''
        
        result = self.parser.parse(xml_content)
        
        assert len(result) == 1
        assert result[0]['ID'] == '1001'
        assert result[0]['Gemeinde'] == 'Hamburg'
        assert result[0]['longitude'] == '9.9937'
        assert result[0]['latidude'] == '53.5511'
    
    def test_parse_multiple_flurstuecke(self):
        """Test: Mehrere Flurstuecke werden korrekt geparst"""
        xml_content = b'''<NasExport>
            <Flurstueck><ID>1</ID><Gemeinde>A</Gemeinde></Flurstueck>
            <Flurstueck><ID>2</ID><Gemeinde>B</Gemeinde></Flurstueck>
            <Flurstueck><ID>3</ID><Gemeinde>C</Gemeinde></Flurstueck>
        </NasExport>'''
        
        result = self.parser.parse(xml_content)
        
        assert len(result) == 3
        assert result[0]['ID'] == '1'
        assert result[1]['ID'] == '2'
        assert result[2]['ID'] == '3'
    
    def test_parse_example_file(self):
        """Test: Beispieldatei wird korrekt geparst"""
        with open("examples/geodata_example_1.nas", "rb") as f:
            content = f.read()
        
        result = self.parser.parse(content)
        
        assert len(result) == 2
        assert result[0]['ID'] == '2001'
        assert result[0]['Gemeinde'] == 'Hamburg'


class TestNASParserInvalidFormats:
    """Tests für ungültige NAS-Formate"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.parser = NASParser()
    
    def test_parse_text_nas_raises_error(self):
        """Test: Text-basiertes NAS wird mit klarer Fehlermeldung abgelehnt"""
        text_nas_content = b'''BEGINN
2024-01-15 Datenexport
Flurstueck 1234
Koordinaten: 52.52 13.405
ENDE'''
        
        with pytest.raises(ValueError) as exc_info:
            self.parser.parse(text_nas_content)
        
        error_message = str(exc_info.value)
        assert "Nicht unterstütztes NAS-Format" in error_message
        assert "XML-basierte" in error_message
        assert "Text-basiert" in error_message
    
    def test_parse_csv_like_content_raises_error(self):
        """Test: CSV-ähnlicher Inhalt wird abgelehnt"""
        csv_content = b'''ID;Name;Wert
1;Test;100
2;Test2;200'''
        
        with pytest.raises(ValueError) as exc_info:
            self.parser.parse(csv_content)
        
        assert "Nicht unterstütztes NAS-Format" in str(exc_info.value)
    
    def test_parse_empty_xml_raises_error(self):
        """Test: XML ohne Flurstueck-Elemente wirft Fehler"""
        empty_xml = b'<?xml version="1.0"?><NasExport></NasExport>'
        
        with pytest.raises(ValueError) as exc_info:
            self.parser.parse(empty_xml)
        
        assert "Keine <Flurstueck>-Elemente" in str(exc_info.value)
    
    def test_parse_plain_text_raises_error(self):
        """Test: Reiner Text wird abgelehnt"""
        plain_text = b'Dies ist nur Text ohne jegliche Struktur.'
        
        with pytest.raises(ValueError) as exc_info:
            self.parser.parse(plain_text)
        
        assert "Nicht unterstütztes NAS-Format" in str(exc_info.value)


class TestNASParserEdgeCases:
    """Tests für Randfälle"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.parser = NASParser()
    
    def test_parse_with_special_characters_in_tags(self):
        """Test: Tags mit Sonderzeichen (wie 'Größe in ha') werden geparst"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <NasExport>
            <Flurstueck>
                <ID>1001</ID>
                <Größe in ha>0.87</Größe in ha>
            </Flurstueck>
        </NasExport>""".encode('utf-8')
        
        result = self.parser.parse(xml_content)
        
        assert len(result) == 1
        assert result[0]['ID'] == '1001'
        assert result[0]['Größe in ha'] == '0.87'
    
    def test_parse_with_empty_values(self):
        """Test: Leere Werte werden als None/leer geparst"""
        xml_content = b'''<NasExport>
            <Flurstueck>
                <ID>1001</ID>
                <Gemeinde></Gemeinde>
            </Flurstueck>
        </NasExport>'''
        
        result = self.parser.parse(xml_content)
        
        assert len(result) == 1
        assert result[0]['ID'] == '1001'
        # Leerer String oder None, beide sind akzeptabel
        assert result[0]['Gemeinde'] in [None, '']
    
    def test_parse_with_whitespace(self):
        """Test: Whitespace in Werten wird getrimmt"""
        xml_content = b'''<NasExport>
            <Flurstueck>
                <ID>  1001  </ID>
                <Gemeinde>  Hamburg  </Gemeinde>
            </Flurstueck>
        </NasExport>'''
        
        result = self.parser.parse(xml_content)
        
        assert result[0]['ID'] == '1001'
        assert result[0]['Gemeinde'] == 'Hamburg'