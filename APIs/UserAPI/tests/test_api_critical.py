# tests/test_api_critical.py
"""
Tests críticos para endpoints de la API
Enfoque profesional - sin sobre-ingeniería
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock, Mock
from datetime import date, datetime, timedelta
import json
from io import BytesIO

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock de la base de datos ANTES de imports
@pytest.fixture(autouse=True)
def mock_database():
    """Mock automático de la base de datos para todos los tests"""
    with patch('database.engine') as mock_engine, \
         patch('database.Base') as mock_base, \
         patch('database.get_db') as mock_get_db:
        
        # Configurar mocks
        mock_base.metadata.create_all = MagicMock()
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session
        
        yield {
            'engine': mock_engine,
            'base': mock_base, 
            'session': mock_session
        }

@pytest.fixture
def client():
    """Cliente de prueba de FastAPI"""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)

@pytest.fixture
def mock_user_service():
    """Mock del UserService"""
    with patch('routes.UserService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        yield mock_service

@pytest.fixture
def sample_cv_file():
    """Archivo CV de muestra para tests"""
    cv_content = b"PDF content here - sample CV"
    cv_file = BytesIO(cv_content)
    return ("test_cv.pdf", cv_file, "application/pdf")

@pytest.fixture
def sample_image_file():
    """Archivo de imagen de muestra para tests"""
    img_content = b"JPEG content here"
    img_file = BytesIO(img_content)
    return ("test_photo.jpg", img_file, "image/jpeg")

class TestRegistroTemporalCandidatos:
    """Tests del flujo de registro temporal de candidatos"""
    
    def test_register_candidato_success(self, client, mock_user_service, sample_cv_file):
        """Test exitoso de registro temporal de candidato"""
        # Mock del resultado del servicio
        mock_user_service.create_pending_candidato.return_value = {
            "message": "Registro iniciado. Verifica tu email para completar el proceso.",
            "email": "test@example.com",
            "expires_in_minutes": 15
        }
        
        # Datos del formulario
        form_data = {
            "email": "test@example.com",
            "password": "Password123",
            "nombre": "Juan",
            "apellido": "Pérez",
            "genero": "masculino",
            "fecha_nacimiento": "1990-01-01"
        }
        
        files = {"cv_file": sample_cv_file}
        
        # Hacer la petición
        response = client.post("/api/v1/register-candidato", data=form_data, files=files)
        
        # Verificaciones
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "email" in data
        assert data["email"] == "test@example.com"
        
        # Verificar que se llamó al servicio correcto
        mock_user_service.create_pending_candidato.assert_called_once()
        print("✅ Registro temporal candidato - ÉXITO")
    
    def test_register_candidato_missing_fields(self, client):
        """Test de registro con campos faltantes"""
        form_data = {
            "email": "test@example.com"
            # Faltan campos requeridos
        }
        
        response = client.post("/api/v1/register-candidato", data=form_data)
        
        # Debe fallar por validación
        assert response.status_code == 422
        print("✅ Validación campos faltantes - ÉXITO")
    
    def test_register_candidato_invalid_email(self, client, sample_cv_file):
        """Test con email inválido"""
        form_data = {
            "email": "email-invalido",
            "password": "Password123",
            "nombre": "Juan",
            "apellido": "Pérez", 
            "genero": "masculino",
            "fecha_nacimiento": "1990-01-01"
        }
        
        files = {"cv_file": sample_cv_file}
        
        response = client.post("/api/v1/register-candidato", data=form_data, files=files)
        
        # Debe fallar por validación de email
        assert response.status_code == 422
        print("✅ Validación email inválido - ÉXITO")

class TestRegistroTemporalEmpresas:
    """Tests del flujo de registro temporal de empresas"""
    
    def test_register_empresa_success(self, client, mock_user_service):
        """Test exitoso de registro temporal de empresa"""
        # Mock del resultado del servicio
        mock_user_service.create_empresa.return_value = {
            "message": "Registro de empresa iniciado. Verifica tu email para completar el proceso.",
            "email": "empresa@example.com",
            "expires_in_minutes": 15
        }
        
        # Datos del formulario
        form_data = {
            "email": "empresa@example.com",
            "password": "Password123",
            "nombre": "Mi Empresa SA",
            "descripcion": "Somos una empresa de tecnología"
        }
        
        # Hacer la petición
        response = client.post("/api/v1/register-empresa", data=form_data)
        
        # Verificaciones
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["email"] == "empresa@example.com"
        
        # Verificar que se llamó al servicio correcto
        mock_user_service.create_empresa.assert_called_once()
        print("✅ Registro temporal empresa - ÉXITO")

class TestCompletarRegistro:
    """Tests para completar registro después de verificación email"""
    
    def test_complete_registration_candidato(self, client, mock_user_service):
        """Test de completar registro de candidato"""
        # Mock del temp storage
        mock_temp_data = {
            "registration_data": {
                "user_type": "candidato",
                "email": "test@example.com"
            }
        }
        mock_user_service.temp_storage.get_pending_registration.return_value = mock_temp_data
        
        # Mock del usuario creado
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.role = "candidato"
        mock_user_service.complete_candidato_registration.return_value = mock_user
        
        # Datos del formulario
        form_data = {
            "email": "test@example.com",
            "verification_code": "123456"
        }
        
        # Hacer la petición
        response = client.post("/api/v1/complete-registration", data=form_data)
        
        # Verificaciones
        assert response.status_code == 200
        
        # Verificar que se llamó al método correcto
        mock_user_service.complete_candidato_registration.assert_called_once_with(
            "test@example.com", "123456"
        )
        print("✅ Completar registro candidato - ÉXITO")
    
    def test_complete_registration_empresa(self, client, mock_user_service):
        """Test de completar registro de empresa"""
        # Mock del temp storage para empresa
        mock_temp_data = {
            "registration_data": {
                "user_type": "empresa",
                "email": "empresa@example.com"
            }
        }
        mock_user_service.temp_storage.get_pending_registration.return_value = mock_temp_data
        
        # Mock del usuario creado
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "empresa@example.com"
        mock_user.role = "empresa"
        mock_user_service.complete_empresa_registration.return_value = mock_user
        
        # Datos del formulario
        form_data = {
            "email": "empresa@example.com",
            "verification_code": "123456"
        }
        
        # Hacer la petición
        response = client.post("/api/v1/complete-registration", data=form_data)
        
        # Verificaciones
        assert response.status_code == 200
        
        # Verificar que se llamó al método correcto
        mock_user_service.complete_empresa_registration.assert_called_once_with(
            "empresa@example.com", "123456"
        )
        print("✅ Completar registro empresa - ÉXITO")
    
    def test_complete_registration_no_pending_data(self, client, mock_user_service):
        """Test cuando no hay datos temporales"""
        # Mock: no hay datos temporales
        mock_user_service.temp_storage.get_pending_registration.return_value = None
        
        form_data = {
            "email": "test@example.com",
            "verification_code": "123456"
        }
        
        response = client.post("/api/v1/complete-registration", data=form_data)
        
        # Debe fallar porque no hay registro temporal
        assert response.status_code == 400
        print("✅ Fallo sin datos temporales - ÉXITO")

class TestLogin:
    """Tests del sistema de login"""
    
    @patch('routes.create_access_token')
    def test_login_success(self, mock_create_token, client, mock_user_service):
        """Test de login exitoso"""
        # Mock del usuario autenticado
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.email_verified = True
        mock_user_service.authenticate_user.return_value = mock_user
        
        # Mock del token
        mock_create_token.return_value = "fake-jwt-token"
        
        # Datos de login
        login_data = {
            "email": "test@example.com",
            "password": "Password123"
        }
        
        # Hacer petición
        response = client.post("/api/v1/login", json=login_data)
        
        # Verificaciones
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
        # Verificar que se autenticó al usuario
        mock_user_service.authenticate_user.assert_called_once_with(
            "test@example.com", "Password123"
        )
        print("✅ Login exitoso - ÉXITO")
    
    def test_login_invalid_credentials(self, client, mock_user_service):
        """Test con credenciales incorrectas"""
        # Mock: usuario no autenticado
        mock_user_service.authenticate_user.return_value = None
        
        login_data = {
            "email": "test@example.com",
            "password": "wrong-password"
        }
        
        response = client.post("/api/v1/login", json=login_data)
        
        # Debe fallar
        assert response.status_code == 401
        print("✅ Login credenciales inválidas - ÉXITO")
    
    def test_login_email_not_verified(self, client, mock_user_service):
        """Test con email no verificado"""
        # Mock del usuario no verificado
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.email_verified = False  # ⭐ Email NO verificado
        mock_user_service.authenticate_user.return_value = mock_user
        
        login_data = {
            "email": "test@example.com",
            "password": "Password123"
        }
        
        response = client.post("/api/v1/login", json=login_data)
        
        # Debe fallar por email no verificado
        assert response.status_code == 403
        print("✅ Login email no verificado - ÉXITO")

class TestVerificacionEmail:
    """Tests del sistema de verificación de email"""
    
    def test_verify_email_success(self, client, mock_user_service):
        """Test de verificación exitosa de email"""
        # Mock: código válido
        mock_user_service.verify_email_code.return_value = True
        
        form_data = {
            "email": "test@example.com",
            "code": "123456"
        }
        
        response = client.post("/api/v1/verify-email", data=form_data)
        
        # Verificaciones
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        
        # Verificar que se llamó al método correcto
        mock_user_service.verify_email_code.assert_called_once_with(
            "test@example.com", "123456"
        )
        print("✅ Verificación email exitosa - ÉXITO")
    
    def test_verify_email_invalid_code(self, client, mock_user_service):
        """Test con código inválido"""
        # Mock: código inválido
        mock_user_service.verify_email_code.return_value = False
        
        form_data = {
            "email": "test@example.com",
            "code": "wrong-code"
        }
        
        response = client.post("/api/v1/verify-email", data=form_data)
        
        # Debe fallar
        assert response.status_code == 400
        print("✅ Código inválido - ÉXITO")
    
    def test_resend_verification_success(self, client, mock_user_service):
        """Test de reenvío de código"""
        # Mock: reenvío exitoso
        mock_user_service.resend_verification_code.return_value = True
        
        form_data = {
            "email": "test@example.com"
        }
        
        response = client.post("/api/v1/resend-verification", data=form_data)
        
        # Verificaciones
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verificar que se llamó al método correcto
        mock_user_service.resend_verification_code.assert_called_once_with("test@example.com")
        print("✅ Reenvío código - ÉXITO")

class TestEndpointsProtegidos:
    """Tests de endpoints que requieren autenticación"""
    
    @patch('routes.get_current_user')
    def test_get_me_success(self, mock_get_current_user, client):
        """Test del endpoint /me"""
        # Mock del usuario actual
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.role = "candidato"
        mock_get_current_user.return_value = mock_user
        
        response = client.get("/api/v1/me")
        
        assert response.status_code == 200
        print("✅ Endpoint /me - ÉXITO")
    
    def test_get_me_unauthorized(self, client):
        """Test sin autenticación"""
        response = client.get("/api/v1/me")
        
        # Debe fallar por falta de autenticación
        assert response.status_code == 401 or response.status_code == 403
        print("✅ Endpoint /me sin auth - ÉXITO")

class TestAdminEndpoints:
    """Tests de endpoints de administrador"""
    
    @patch('routes.require_admin')
    def test_get_pending_companies(self, mock_require_admin, client, mock_user_service):
        """Test para ver empresas pendientes"""
        # Mock del admin
        mock_admin = MagicMock()
        mock_admin.role = "admin"
        mock_require_admin.return_value = mock_admin
        
        # Mock de empresas pendientes
        mock_user_service.get_unverified_companies.return_value = []
        
        response = client.get("/api/v1/admin/companies/pending")
        
        assert response.status_code == 200
        print("✅ Admin - empresas pendientes - ÉXITO")
    
    @patch('routes.require_admin')
    def test_verify_company(self, mock_require_admin, client, mock_user_service):
        """Test de verificación de empresa por admin"""
        # Mock del admin
        mock_admin = MagicMock()
        mock_require_admin.return_value = mock_admin
        
        # Mock de empresa encontrada
        mock_company = MagicMock()
        mock_company.id = 1
        mock_company.role = "empresa"
        mock_company.verified = False
        mock_user_service.get_user_by_email.return_value = mock_company
        
        # Mock de empresa verificada
        mock_verified_company = MagicMock()
        mock_verified_company.verified = True
        mock_user_service.verify_company.return_value = mock_verified_company
        
        response = client.post(
            "/api/v1/admin/companies/verify",
            params={"company_email": "empresa@test.com"}
        )
        
        assert response.status_code == 200
        print("✅ Admin - verificar empresa - ÉXITO")

class TestValidacionesBasicas:
    """Tests de validaciones básicas importantes"""
    
    def test_endpoint_obsoleto_register(self, client):
        """Test que el endpoint obsoleto devuelve 410"""
        form_data = {
            "email": "test@example.com",
            "password": "Password123",
            "nombre": "Juan",
            "apellido": "Pérez",
            "genero": "masculino",
            "fecha_nacimiento": "1990-01-01"
        }
        
        files = {"cv_file": ("test.pdf", BytesIO(b"pdf content"), "application/pdf")}
        
        response = client.post("/api/v1/register", data=form_data, files=files)
        
        # Debe devolver 410 (Gone)
        assert response.status_code == 410
        print("✅ Endpoint obsoleto /register - ÉXITO")
    
    def test_get_user_by_id_public(self, client, mock_user_service):
        """Test del endpoint público para obtener usuario"""
        # Mock del usuario
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.role = "candidato"
        mock_user_service.get_user_by_id.return_value = mock_user
        
        response = client.get("/api/v1/users/1")
        
        assert response.status_code == 200
        print("✅ Get user by ID público - ÉXITO")

# Función para ejecutar tests específicos
def run_critical_tests():
    """Ejecutar solo los tests críticos"""
    pytest.main([
        __file__,
        "-v",
        "-k", "test_register_candidato_success or test_login_success or test_complete_registration_candidato",
        "--tb=short"
    ])

if __name__ == "__main__":
    # Ejecutar todos los tests del archivo
    pytest.main([__file__, "-v", "--tb=short"])