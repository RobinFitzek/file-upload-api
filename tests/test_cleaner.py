import pytest
from app.logic.cleaner import DataCleaner


class TestDataCleanerBasic:
    """Grundlegende Cleaner Tests"""
    
    def setup_method(self):
        """Wird vor jedem Test ausgeführt"""
        self.cleaner = DataCleaner()
    
    def test_clean_valid_row(self):
        """Gültige Zeile wird korrekt bereinigt"""
        raw_data = [{
            "ID": "1001",
            "Flurstücknummer": "045-123-0001",
            "longitude": "8.6821",
            "latidude": "50.1109",
            "Gemeinde": "Frankfurt",
            "Bundesland": "Hessen",
            "Größe in ha": "0.87"
        }]
        
        cleaned, errors = self.cleaner.clean(raw_data)
        
        assert len(cleaned) == 1
        assert len(errors) == 0
        assert cleaned[0]["id"] == 1001
        assert cleaned[0]["longitude"] == 8.6821
        assert cleaned[0]["gemeinde"] == "Frankfurt"
    
    def test_whitespace_trimmed(self):
        """Whitespace wird entfernt"""
        raw_data = [{
            "ID": "  1001  ",
            "Flurstücknummer": "  045-123  ",
            "longitude": " 8.6821 ",
            "latidude": "50.1109",
            "Gemeinde": "  Hamburg  ",
            "Bundesland": "Hamburg",
            "Größe in ha": "0.87"
        }]
        
        cleaned, errors = self.cleaner.clean(raw_data)
        
        assert cleaned[0]["id"] == 1001
        assert cleaned[0]["flurstuecknummer"] == "045-123"
        assert cleaned[0]["gemeinde"] == "Hamburg"


class TestDataCleanerNullValues:
    """Tests für NULL-Wert Behandlung"""
    
    def setup_method(self):
        self.cleaner = DataCleaner()
    
    def test_empty_string_becomes_none(self):
        """Leere Strings werden zu None"""
        raw_data = [{
            "ID": "1001",
            "Flurstücknummer": "",
            "longitude": "8.6821",
            "latidude": "50.1109",
            "Gemeinde": "",
            "Bundesland": "Hessen",
            "Größe in ha": "0.87"
        }]
        
        cleaned, errors = self.cleaner.clean(raw_data)
        
        assert cleaned[0]["flurstuecknummer"] is None
        assert cleaned[0]["gemeinde"] is None
    
    def test_null_values_recognized(self):
        """NULL, N/A, - werden zu None"""
        for null_value in ["null", "NULL", "N/A", "n/a", "-"]:
            raw_data = [{
                "ID": "1001",
                "Flurstücknummer": null_value,
                "longitude": "8.6821",
                "latidude": "50.1109",
                "Gemeinde": "Frankfurt",
                "Bundesland": "Hessen",
                "Größe in ha": "0.87"
            }]
            
            cleaned, errors = self.cleaner.clean(raw_data)
            assert cleaned[0]["flurstuecknummer"] is None, f"'{null_value}' wurde nicht zu None"


class TestDataCleanerTypeConversion:
    """Tests für Typkonvertierung"""
    
    def setup_method(self):
        self.cleaner = DataCleaner()
    
    def test_string_to_int(self):
        """String wird zu Integer"""
        raw_data = [{
            "ID": "1001",
            "Flurstücknummer": "045-123",
            "longitude": "8.0",
            "latidude": "50.0",
            "Gemeinde": "Frankfurt",
            "Bundesland": "Hessen",
            "Größe in ha": "1.0"
        }]
        
        cleaned, errors = self.cleaner.clean(raw_data)
        
        assert len(errors) == 0
        assert isinstance(cleaned[0]["id"], int)
        assert cleaned[0]["id"] == 1001
    
    def test_string_to_float(self):
        """String wird zu Float"""
        raw_data = [{
            "ID": "1001",
            "Flurstücknummer": "045-123",
            "longitude": "8.6821",
            "latidude": "50.1109",
            "Gemeinde": "Frankfurt",
            "Bundesland": "Hessen",
            "Größe in ha": "0.87"
        }]
        
        cleaned, errors = self.cleaner.clean(raw_data)
        
        assert len(errors) == 0
        assert isinstance(cleaned[0]["longitude"], float)
        assert cleaned[0]["longitude"] == 8.6821
    
    def test_german_comma_to_point(self):
        """Deutsches Komma wird zu Punkt"""
        raw_data = [{
            "ID": "1001",
            "Flurstücknummer": "045-123",
            "longitude": "8,6821",
            "latidude": "50,1109",
            "Gemeinde": "Frankfurt",
            "Bundesland": "Hessen",
            "Größe in ha": "0,87"
        }]
        
        cleaned, errors = self.cleaner.clean(raw_data)
        
        assert len(errors) == 0
        assert cleaned[0]["longitude"] == 8.6821
        assert cleaned[0]["groesse_ha"] == 0.87
    
    def test_invalid_number_raises_error(self):
        """Ungültige Zahl wird als Fehler erkannt"""
        raw_data = [{
            "ID": "not_a_number",
            "Flurstücknummer": "045-123",
            "longitude": "8.0",
            "latidude": "50.0",
            "Gemeinde": "Frankfurt",
            "Bundesland": "Hessen",
            "Größe in ha": "1.0"
        }]
        
        cleaned, errors = self.cleaner.clean(raw_data)
        
        assert len(cleaned) == 0
        assert len(errors) == 1
        assert "ID" in errors[0]["error"]


class TestDataCleanerValidation:
    """Tests für Wertebereich-Validierung"""
    
    def setup_method(self):
        self.cleaner = DataCleaner()
    
    def test_valid_latitude(self):
        """Gültige Latitude wird akzeptiert"""
        for lat in ["-90", "0", "45.5", "90"]:
            raw_data = [{
                "ID": "1001",
                "Flurstücknummer": "045-123",
                "longitude": "8.0",
                "latidude": lat,
                "Gemeinde": "Frankfurt",
                "Bundesland": "Hessen",
                "Größe in ha": "1.0"
            }]
            
            cleaned, errors = self.cleaner.clean(raw_data)
            assert len(errors) == 0, f"Latitude {lat} sollte gültig sein"
    
    def test_invalid_latitude(self):
        """Ungültige Latitude wird abgelehnt"""
        for lat in ["-91", "95", "180"]:
            raw_data = [{
                "ID": "1001",
                "Flurstücknummer": "045-123",
                "longitude": "8.0",
                "latidude": lat,
                "Gemeinde": "Frankfurt",
                "Bundesland": "Hessen",
                "Größe in ha": "1.0"
            }]
            
            cleaned, errors = self.cleaner.clean(raw_data)
            assert len(errors) == 1, f"Latitude {lat} sollte ungültig sein"
    
    def test_valid_longitude(self):
        """Gültige Longitude wird akzeptiert"""
        for lon in ["-180", "0", "90", "180"]:
            raw_data = [{
                "ID": "1001",
                "Flurstücknummer": "045-123",
                "longitude": lon,
                "latidude": "50.0",
                "Gemeinde": "Frankfurt",
                "Bundesland": "Hessen",
                "Größe in ha": "1.0"
            }]
            
            cleaned, errors = self.cleaner.clean(raw_data)
            assert len(errors) == 0, f"Longitude {lon} sollte gültig sein"
    
    def test_invalid_longitude(self):
        """Ungültige Longitude wird abgelehnt"""
        for lon in ["-181", "200", "360"]:
            raw_data = [{
                "ID": "1001",
                "Flurstücknummer": "045-123",
                "longitude": lon,
                "latidude": "50.0",
                "Gemeinde": "Frankfurt",
                "Bundesland": "Hessen",
                "Größe in ha": "1.0"
            }]
            
            cleaned, errors = self.cleaner.clean(raw_data)
            assert len(errors) == 1, f"Longitude {lon} sollte ungültig sein"
    
    def test_negative_groesse_invalid(self):
        """Negative Größe wird abgelehnt"""
        raw_data = [{
            "ID": "1001",
            "Flurstücknummer": "045-123",
            "longitude": "8.0",
            "latidude": "50.0",
            "Gemeinde": "Frankfurt",
            "Bundesland": "Hessen",
            "Größe in ha": "-0.5"
        }]
        
        cleaned, errors = self.cleaner.clean(raw_data)
        
        assert len(errors) == 1
        assert "groesse_ha" in errors[0]["error"]
    
    def test_missing_id_invalid(self):
        """Fehlende ID wird abgelehnt"""
        raw_data = [{
            "ID": "",
            "Flurstücknummer": "045-123",
            "longitude": "8.0",
            "latidude": "50.0",
            "Gemeinde": "Frankfurt",
            "Bundesland": "Hessen",
            "Größe in ha": "1.0"
        }]
        
        cleaned, errors = self.cleaner.clean(raw_data)
        
        assert len(errors) == 1
        assert "ID" in errors[0]["error"]


class TestDataCleanerReport:
    """Tests für Report-Generierung"""
    
    def setup_method(self):
        self.cleaner = DataCleaner()
    
    def test_report_status_ok(self):
        """Status OK wenn keine Fehler"""
        raw_data = [{"ID": "1", "Flurstücknummer": "123", "longitude": "8", "latidude": "50", "Gemeinde": "Frankfurt", "Bundesland": "Hessen", "Größe in ha": "1"}]
        cleaned, errors = self.cleaner.clean(raw_data)
        report = self.cleaner.generate_report(raw_data, cleaned, errors)
        
        assert report["status"] == "OK"
    
    def test_report_status_fixable(self):
        """Status FIXABLE wenn einige Fehler"""
        raw_data = [
            {"ID": "1", "Flurstücknummer": "123", "longitude": "8", "latidude": "50", "Gemeinde": "Frankfurt", "Bundesland": "Hessen", "Größe in ha": "1"},
            {"ID": "invalid", "Flurstücknummer": "123", "longitude": "8", "latidude": "50", "Gemeinde": "Frankfurt", "Bundesland": "Hessen", "Größe in ha": "1"}
        ]
        cleaned, errors = self.cleaner.clean(raw_data)
        report = self.cleaner.generate_report(raw_data, cleaned, errors)
        
        assert report["status"] == "FIXABLE"
    
    def test_report_status_invalid(self):
        """Status INVALID wenn alle fehlerhaft"""
        raw_data = [
            {"ID": "invalid", "Flurstücknummer": "123", "longitude": "8", "latidude": "50", "Gemeinde": "Frankfurt", "Bundesland": "Hessen", "Größe in ha": "1"}
        ]
        cleaned, errors = self.cleaner.clean(raw_data)
        report = self.cleaner.generate_report(raw_data, cleaned, errors)
        
        assert report["status"] == "INVALID"
    
    def test_report_contains_counts(self):
        """Report enthält Zählungen"""
        raw_data = [
            {"ID": "1", "Flurstücknummer": "123", "longitude": "8", "latidude": "50", "Gemeinde": "Frankfurt", "Bundesland": "Hessen", "Größe in ha": "1"},
            {"ID": "2", "Flurstücknummer": "123", "longitude": "8", "latidude": "50", "Gemeinde": "München", "Bundesland": "Bayern", "Größe in ha": "1"},
            {"ID": "invalid", "Flurstücknummer": "123", "longitude": "8", "latidude": "50", "Gemeinde": "Berlin", "Bundesland": "Berlin", "Größe in ha": "1"}
        ]
        cleaned, errors = self.cleaner.clean(raw_data)
        report = self.cleaner.generate_report(raw_data, cleaned, errors)
        
        assert report["total_rows"] == 3
        assert report["valid_rows"] == 2
        assert report["error_rows"] == 1