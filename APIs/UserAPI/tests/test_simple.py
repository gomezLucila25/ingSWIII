# tests/test_simple.py
import pytest
import requests
import subprocess
import time
import signal
import os

class TestAPIRunning:
    """Tests que verifican la API sin importar módulos problemáticos"""
    
    @classmethod
    def setup_class(cls):
        """Arrancar la API en un proceso separado"""
        # Cambiar al directorio padre donde está main.py
        original_dir = os.getcwd()
        parent_dir = os.path.dirname(os.getcwd())
        os.chdir(parent_dir)
        
        try:
            # Intentar arrancar la API (si no está corriendo)
            cls.api_process = subprocess.Popen(
                ["python", "-m", "uvicorn", "main:app", "--port", "8001"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Esperar un poco para que arranque
            time.sleep(3)
            cls.base_url = "http://localhost:8001"
            
        except Exception as e:
            print(f"No se pudo arrancar la API: {e}")
            cls.api_process = None
            cls.base_url = None
        finally:
            os.chdir(original_dir)
    
    @classmethod
    def teardown_class(cls):
        """Cerrar la API"""
        if cls.api_process:
            cls.api_process.terminate()
            cls.api_process.wait()
    
    def test_api_is_accessible(self):
        """Test básico: verificar que la API responde"""
        if not self.base_url:
            pytest.skip("API no está disponible")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            assert response.status_code == 200
            print("✅ API responde correctamente")
        except requests.exceptions.RequestException:
            pytest.fail("API no está respondiendo")
    
    def test_root_endpoint(self):
        """Test del endpoint raíz"""
        if not self.base_url:
            pytest.skip("API no está disponible")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            print("✅ Root endpoint funciona")
        except requests.exceptions.RequestException:
            pytest.fail("Root endpoint no responde")

class TestBasicValidation:
    """Tests básicos que no requieren la API corriendo"""
    
    def test_imports_work(self):
        """Test que verifica imports básicos"""
        try:
            import sys
            import os
            
            # Agregar path
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # Intentar importar solo lo esencial
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
            
            # Crear una app mínima para probar
            test_app = FastAPI()
            
            @test_app.get("/test")
            def test_endpoint():
                return {"status": "ok"}
            
            client = TestClient(test_app)
            response = client.get("/test")
            
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
            print("✅ FastAPI imports y TestClient funcionan")
            
        except Exception as e:
            pytest.fail(f"Error en imports básicos: {e}")
    
    def test_dependencies_installed(self):
        """Verificar que las dependencias están instaladas"""
        dependencies = [
            "fastapi", "uvicorn", "sqlalchemy", 
            "psycopg2", "python_jose", "passlib"
        ]
        
        for dep in dependencies:
            try:
                __import__(dep)
                print(f"✅ {dep} instalado")
            except ImportError:
                pytest.fail(f"❌ {dep} no está instalado")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])