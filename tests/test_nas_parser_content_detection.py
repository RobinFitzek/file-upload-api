"""
Tests für den NAS-Parser mit Content-Detection.




















ENDE DATENEXPORTGroesse: 0.87 haBundesland: HamburgGemeinde: HamburgKoordinaten: 53.55 9.99Flurstuecknummer: 789-012-0002ID: 5002EINHEIT: FlurstueckGroesse: 1.25 haBundesland: BerlinGemeinde: BerlinKoordinaten: 52.52 13.405Flurstuecknummer: 123-456-0001ID: 5001EINHEIT: FlurstueckVERSION: 1.0Prüft ob XML-basierte und Text-basierte NAS-Dateien korrekt geparst werden.
"""

import pytest
from app.parsers.nas_parser import NASParser


class TestNASParserContentDetection:
    """Tests für die Content-Detection im NAS-Parser"""
    
    def setup_method(self):
        self.parser = NASParser()
    
    def test_is_xml_format_with_xml_declaration(self):
        """XML-Deklaration wird als XML erkannt"""
        xml_text = '<?xml version="1.0"?><NasExport></NasExport>'
        assert self.parser._is_xml_format(xml_text) is True
    
    def test_is_xml_format_with_nasexport_element(self):
        """NasExport-Element wird als XML erkannt"""
        xml_text = '<NasExport><Flurstueck></Flurstueck></NasExport>'
        assert self.parser._is_xml_format(xml_text) is True
    
    def test_is_xml_format_with_flurstueck_element(self):
        """Flurstueck-Element wird als XML erkannt"""
        xml_text = '<Flurstueck><ID>123</ID></Flurstueck>'
        assert self.parser._is_xml_format(xml_text) is True
    
    def test_is_text_format_with_beginn(self):
        """BEGINN-Start wird als Text-Format erkannt"""
        text_nas = 'BEGINN DATENEXPORT\nEINHEIT: Flurstueck\nID: 1\nENDE'
        assert self.parser._is_text_format(text_nas) is True
        assert self.parser._is_xml_format(text_nas) is False
    
    def test_is_text_format_with_einheit(self):
        """EINHEIT-Blöcke werden als Text-Format erkannt"""
        text_nas = 'EINHEIT: Flurstueck\nID: 123\nGemeinde: Hamburg'
        assert self.parser._is_text_format(text_nas) is True
    
    def test_is_not_xml_format_without_tags(self):
        """Text ohne XML-Tags wird nicht als XML erkannt"""
        text_nas = 'ID;Name;Wert\n1;Test;100\n2;Test2;200'
        assert self.parser._is_xml_format(text_nas) is False


class TestNASParserValidXML:
    """Tests für valide XML-NAS-Dateien"""
    
    def setup_method(self):
        self.parser = NASParser()
    
    def test_parse_valid_xml_nas(self):
        """Valides XML-NAS wird korrekt geparst"""
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
    
    def test_parse_multiple_flurstuecke(self):
        """Mehrere Flurstuecke werden korrekt geparst"""
        xml_content = b'''<NasExport>
            <Flurstueck><ID>1</ID><Gemeinde>A</Gemeinde></Flurstueck>
            <Flurstueck><ID>2</ID><Gemeinde>B</Gemeinde></Flurstueck>
            <Flurstueck><ID>3</ID><Gemeinde>C</Gemeinde></Flurstueck>
        </NasExport>'''
        
        result = self.parser.parse(xml_content)
        
        assert len(result) == 3
    
    def test_parse_example_file(self):
        """Beispieldatei wird korrekt geparst"""
        with open("examples/geodata_example_1.nas", "rb") as f:
            content = f.read()
        
        result = self.parser.parse(content)
        
        assert len(result) == 2
        assert result[0]['ID'] == '2001'


class TestNASParserTextFormat:
    """Tests für Text-basiertes NAS-Format"""
    
    def setup_method(self):
        self.parser = NASParser()
    
    def test_parse_text_nas_basic(self):
        """Einfaches Text-NAS wird korrekt geparst"""
        text_content = b'''BEGINN DATENEXPORT
DATUM: 2024-01-15

EINHEIT: Flurstueck
ID: 9001
Flurstuecknummer: 123-456-0001
Koordinaten: 52.52 13.405
Gemeinde: Berlin
Bundesland: Berlin
Groesse: 1.25 ha

ENDE DATENEXPORT'''
        
        result = self.parser.parse(text_content)
        
        assert len(result) == 1
        assert result[0]['ID'] == '9001'
        assert result[0]['Gemeinde'] == 'Berlin'
        assert result[0]['Bundesland'] == 'Berlin'
    
    def test_parse_text_nas_multiple_einheiten(self):
        """Mehrere EINHEIT-Blöcke werden geparst"""
        text_content = b'''BEGINN DATENEXPORT

EINHEIT: Flurstueck
ID: 9001
Gemeinde: Berlin
Bundesland: Berlin

EINHEIT: Flurstueck
ID: 9002
Gemeinde: Hamburg
Bundesland: Hamburg

ENDE DATENEXPORT'''
        
        result = self.parser.parse(text_content)
        
        assert len(result) == 2
        assert result[0]['ID'] == '9001'
        assert result[1]['ID'] == '9002'
    
    def test_parse_text_nas_coordinates(self):
        """Koordinaten werden korrekt extrahiert"""
        text_content = b'''BEGINN
EINHEIT: Flurstueck
ID: 1
Koordinaten: 52.52 13.405
ENDE'''
        
        result = self.parser.parse(text_content)
        
        assert result[0]['latidude'] == '52.52'
        assert result[0]['longitude'] == '13.405'
    
    def test_parse_text_nas_groesse(self):
        """Größe wird korrekt extrahiert"""
        text_content = b'''BEGINN
EINHEIT: Flurstueck
ID: 1
Groesse: 1.25 ha
ENDE'''
        
        result = self.parser.parse(text_content)
        
        assert result[0]['Größe in ha'] == '1.25'


class TestNASParserInvalidFormats:
    """Tests für ungültige NAS-Formate"""
    
    def setup_method(self):
        self.parser = NASParser()
    
    def test_parse_csv_like_content_raises_error(self):
        """CSV-ähnlicher Inhalt wird abgelehnt"""
        csv_content = b'''ID;Name;Wert
1;Test;100
2;Test2;200'''
        
        with pytest.raises(ValueError) as exc_info:
            self.parser.parse(csv_content)
        
        assert "Nicht unterstütztes NAS-Format" in str(exc_info.value)
    
    def test_parse_empty_xml_raises_error(self):
        """XML ohne Flurstueck-Elemente wirft Fehler"""
        empty_xml = b'<?xml version="1.0"?><NasExport></NasExport>'
        
        with pytest.raises(ValueError) as exc_info:
            self.parser.parse(empty_xml)
        
        assert "Keine <Flurstueck>-Elemente" in str(exc_info.value)
    
    def test_parse_plain_text_raises_error(self):
        """Reiner Text wird abgelehnt"""
        plain_text = b'Dies ist nur Text ohne jegliche Struktur.'
        
        with pytest.raises(ValueError) as exc_info:
            self.parser.parse(plain_text)
        
        assert "Nicht unterstütztes NAS-Format" in str(exc_info.value)


class TestNASParserEdgeCases:
    """Tests für Randfälle"""
    
    def setup_method(self):
        self.parser = NASParser()
    
    def test_parse_with_special_characters_in_tags(self):
        """Tags mit Sonderzeichen werden geparst"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <NasExport>
            <Flurstueck>
                <ID>1001</ID>
                <Größe in ha>0.87</Größe in ha>
            </Flurstueck>
        </NasExport>""".encode('utf-8')
        
        result = self.parser.parse(xml_content)
        
        assert result[0]['Größe in ha'] == '0.87'
    
    def test_parse_with_empty_values(self):
        """Leere Werte werden als None/leer geparst"""
        xml_content = b'''<NasExport>
            <Flurstueck>
                <ID>1001</ID>
                <Gemeinde></Gemeinde>
            </Flurstueck>
        </NasExport>'''
        
        result = self.parser.parse(xml_content)
        
        assert result[0]['Gemeinde'] in [None, '']
    
    def test_parse_with_whitespace(self):
        """Whitespace in Werten wird getrimmt"""
        xml_content = b'''<NasExport>
            <Flurstueck>
                <ID>  1001  </ID>
                <Gemeinde>  Hamburg  </Gemeinde>
            </Flurstueck>
        </NasExport>'''
        
        result = self.parser.parse(xml_content)
        
        assert result[0]['ID'] == '1001'
        assert result[0]['Gemeinde'] == 'Hamburg'