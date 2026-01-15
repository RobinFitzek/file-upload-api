

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Erstellt Test-Client für API"""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests für /health"""
    
    def test_health_returns_ok(self, client):
        """Health-Check gibt Status zurück"""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["api"] == "ok"


class TestRootEndpoint:
    """Tests für / (GUI)"""
    
    def test_root_returns_html(self, client):
        """Root gibt HTML zurück"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "html" in response.headers["content-type"]


class TestTestEndpoint:
    """Tests für POST /api/test"""
    
    def test_test_csv_file(self, client):
        """CSV-Datei wird getestet"""
        with open("examples/geodata_example_1.csv", "rb") as f:
            response = client.post(
                "/api/test",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 3
        assert data["valid_rows"] == 3
    
    def test_test_nas_file(self, client):
        """NAS-Datei wird getestet"""
        with open("examples/geodata_example_1.nas", "rb") as f:
            response = client.post(
                "/api/test",
                files={"file": ("test.nas", f, "application/xml")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 2
        assert data["valid_rows"] == 2
    
    def test_test_invalid_format(self, client):
        """Ungültiges Format wird abgelehnt"""
        response = client.post(
            "/api/test",
            files={"file": ("test.txt", b"some content", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "nicht unterstützt" in response.json()["detail"].lower()
    
    def test_test_no_file(self, client):
        """Fehlende Datei gibt Fehler"""
        response = client.post("/api/test")
        
        assert response.status_code == 422  # Validation error


class TestUploadEndpoint:
    """Tests für POST /api/upload"""
    
    def test_upload_csv_file(self, client):
        """CSV-Datei wird hochgeladen"""
        with open("examples/geodata_example_1.csv", "rb") as f:
            response = client.post(
                "/api/upload",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["saved_rows"] == 3
    
    def test_upload_invalid_format(self, client):
        """Ungültiges Format wird abgelehnt"""
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", b"some content", "text/plain")}
        )
        
        assert response.status_code == 400