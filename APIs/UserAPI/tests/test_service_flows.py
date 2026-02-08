# tests/test_service_flows.py
"""
Tests de flujos de servicio críticos
Enfoque en lógica de negocio sin sobre-ingeniería
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock, Mock, mock_open
from datetime import date, datetime, timedelta
import json
from io import BytesIO
import tempfile
from pathlib import Path

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock completo del entorno de base de datos
@pytest.fixture(autouse=True)
def mock_database_environment():
    """Mock completo del entorno de base de datos"""
    with patch('sqlalchemy.create_engine') as mock_create_engine, \
         patch('database.engine') as mock_engine, \
         patch('database.Base') as mock_base, \
         patch('database.get_db') as mock_get_db:
        
        # Configurar mock session
        mock_session = MagicMock()
        mock_session.query.return_value = mock_session
        mock_session.filter.return_value = mock_session
        mock_session.first.return_value = None
        mock_session.all.return_value = []
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()
        
        mock_get_db.return_value = mock_session
        mock_base.metadata.create_all = MagicMock()
        
        yield {
            'session': mock_session,
            'engine': mock_engine,
            'base': mock_base
        }

@pytest.fixture
def mock_temp_dir():
    """Mock de directorio temporal"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('services.Path') as mock_path_class:
            mock_path = MagicMock()
            mock_path.mkdir = MagicMock()
            mock_path.absolute.return_value = Path(temp_dir)
            mock_path.exists.return_value = True
            mock_path.glob.return_value = []
            mock_path.__truediv__ = lambda self, other: Path(temp_dir) / other
            mock_path_class.return_value = mock_path
            yield temp_dir

class TestTemporaryStorage:
    """Tests del sistema de almacenamiento temporal"""
    
    def test_save_and_get_pending_registration(self, mock_temp_dir):
        """Test de guardar y obtener registro temporal"""
        # Import aquí para evitar problemas con mocks
        from services import TemporaryStorage
        
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump, \
             patch('json.load') as mock_json_load:
            
            # Mock del contenido del archivo
            mock_json_load.return_value = {
                "registration_data": {"user_type": "candidato", "email": "test@test.com"},
                "verification_code": "123456",
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(minutes=15)).isoformat()
            }
            
            storage = TemporaryStorage()
            
            # Test guardar
            file_path = storage.save_pending_registration(
                "test@test.com",
                {"user_type": "candidato", "email": "test@test.com"},
                "123456"
            )
            
            assert file_path is not None
            mock_json_dump.assert_called_once()
            
            # Test obtener
            result = storage.get_pending_registration("test@test.com")
            
            assert result is not None
            assert result["verification_code"] == "123456"
            mock_json_load.assert_called_once()
            
        print("✅ TemporaryStorage save/get - ÉXITO")
    
    def test_remove_pending_registration(self, mock_temp_dir):
        """Test de eliminar registro temporal"""
        from services import TemporaryStorage
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.unlink') as mock_unlink:
            
            storage = TemporaryStorage()
            result = storage.remove_pending_registration("test@test.com")
            
            assert result is True
            mock_unlink.assert_called_once()
            
        print("✅ TemporaryStorage remove - ÉXITO")

class TestUserServiceRegistration:
    """Tests del UserService para registro de usuarios"""
    
    @pytest.fixture
    def mock_user_service(self, mock_database_environment):
        """UserService con mocks"""
        from services import UserService
        
        # Mock de la session
        mock_session = mock_database_environment['session']
        
        with patch('services.TemporaryStorage') as mock_temp_storage_class:
            mock_temp_storage = MagicMock()
            mock_temp_storage_class.return_value = mock_temp_storage
            
            service = UserService(mock_session)
            service.temp_storage = mock_temp_storage
            
            yield service, mock_temp_storage
    
    def test_generate_verification_code(self, mock_user_service):
        """Test generación de código de verificación"""
        user_service, _ = mock_user_service
        
        code = user_service.generate_verification_code()
        
        # Verificar que es un string de 6 dígitos
        assert isinstance(code, str)
        assert len(code) == 6
        assert code.isdigit()
        assert 100000 <= int(code) <= 999999
        
        print("✅ Generación código verificación - ÉXITO")
    
    @patch('services.smtplib.SMTP')
    @patch('os.getenv')
    def test_send_verification_email(self, mock_getenv, mock_smtp, mock_user_service):
        """Test envío de email de verificación"""
        user_service, _ = mock_user_service
        
        # Mock de variables de entorno
        mock_getenv.side_effect = lambda key: {
            'EMAIL_USER': 'test@gmail.com',
            'EMAIL_PASSWORD': 'test_password'
        }.get(key)
        
        # Mock del servidor SMTP
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        # Ejecutar
        user_service.send_verification_email("recipient@test.com", "123456")
        
        # Verificaciones
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()
        
        print("✅ Envío email verificación - ÉXITO")
    
    @patch('services.requests.post')
    def test_analyze_cv_with_api_success(self, mock_post, mock_user_service):
        """Test análisis de CV exitoso"""
        user_service, _ = mock_user_service
        
        # Mock de la respuesta de la API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "habilidades": ["Python", "Django"],
                "experiencia": "2 años",
                "educacion": "Ingeniería en Sistemas"
            }
        }
        mock_post.return_value = mock_response
        
        # Mock del archivo CV
        mock_cv_file = MagicMock()
        mock_cv_file.filename = "test_cv.pdf"
        mock_cv_file.content_type = "application/pdf"
        mock_cv_file.file.read.return_value = b"PDF content"
        mock_cv_file.file.seek = MagicMock()
        
        # Ejecutar
        result = user_service.analyze_cv_with_api(mock_cv_file)
        
        # Verificaciones
        assert result is not None
        assert "habilidades" in result
        assert "Python" in result["habilidades"]
        
        # Verificar que se llamó a la API
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert 'http://localhost:8001/analyze/' in call_args[0]
        
        print("✅ Análisis CV exitoso - ÉXITO")
    
    @patch('services.requests.post')
    def test_analyze_cv_with_api_failure(self, mock_post, mock_user_service):
        """Test análisis de CV fallido"""
        user_service, _ = mock_user_service
        
        # Mock de respuesta de error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        # Mock del archivo CV
        mock_cv_file = MagicMock()
        mock_cv_file.filename = "test_cv.pdf"
        mock_cv_file.content_type = "application/pdf"
        mock_cv_file.file.read.return_value = b"PDF content"
        mock_cv_file.file.seek = MagicMock()
        
        # Ejecutar
        result = user_service.analyze_cv_with_api(mock_cv_file)
        
        # Verificaciones - debe devolver None en caso de error
        assert result is None
        
        print("✅ Análisis CV fallido - ÉXITO")

class TestUserServiceFlows:
    """Tests de flujos completos del UserService"""
    
    @pytest.fixture
    def mock_user_service_complete(self, mock_database_environment):
        """UserService con todos los mocks necesarios"""
        from services import UserService
        
        mock_session = mock_database_environment['session']
        
        with patch('services.TemporaryStorage') as mock_temp_storage_class, \
             patch('services.get_password_hash') as mock_hash, \
             patch('services.os.makedirs'), \
             patch('services.uuid.uuid4', return_value='test-uuid'):
            
            mock_temp_storage = MagicMock()
            mock_temp_storage_class.return_value = mock_temp_storage
            mock_hash.return_value = "hashed_password"
            
            service = UserService(mock_session)
            service.temp_storage = mock_temp_storage
            
            yield service, mock_temp_storage, mock_session
    
    @patch('builtins.open', mock_open())
    @patch('services.requests.post')
    def test_create_pending_candidato_success(self, mock_post, mock_user_service_complete):
        """Test flujo completo de crear candidato temporal"""
        user_service, mock_temp_storage, mock_session = mock_user_service_complete
        
        # Mock de análisis de CV exitoso
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"habilidades": ["Python"]}}
        mock_post.return_value = mock_response
        
        # Mock: usuario no existe
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Mock: no hay registro temporal existente
        mock_temp_storage.get_pending_registration.return_value = None
        
        # Mock: guardado temporal exitoso
        mock_temp_storage.save_pending_registration.return_value = "/path/to/file"
        
        # Mock del candidato y archivos
        from schemas import CandidatoCreate
        from models import GenderEnum
        from datetime import date
        
        candidato = CandidatoCreate(
            email="test@test.com",
            password="Password123",
            nombre="Juan",
            apellido="Pérez",
            genero=GenderEnum.masculino,
            fecha_nacimiento=date(1990, 1, 1)
        )
        
        mock_cv_file = MagicMock()
        mock_cv_file.filename = "test_cv.pdf"
        mock_cv_file.content_type = "application/pdf"
        mock_cv_file.file.read.return_value = b"PDF content"
        mock_cv_file.file.seek = MagicMock()
        
        # Ejecutar
        result = user_service.create_pending_candidato(candidato, mock_cv_file)
        
        # Verificaciones
        assert result is not None
        assert "message" in result
        assert result["email"] == "test@test.com"
        assert result["expires_in_minutes"] == 15
        
        # Verificar que se guardó temporalmente
        mock_temp_storage.save_pending_registration.assert_called_once()
        
        print("✅ Crear candidato temporal exitoso - ÉXITO")
    
    def test_create_pending_candidato_user_exists(self, mock_user_service_complete):
        """Test cuando el usuario ya existe"""
        user_service, mock_temp_storage, mock_session = mock_user_service_complete
        
        # Mock: usuario ya existe
        existing_user = MagicMock()
        existing_user.email = "test@test.com"
        mock_session.query.return_value.filter.return_value.first.return_value = existing_user
        
        from schemas import CandidatoCreate
        from models import GenderEnum
        from datetime import date
        from fastapi import HTTPException
        
        candidato = CandidatoCreate(
            email="test@test.com",
            password="Password123",
            nombre="Juan",
            apellido="Pérez",
            genero=GenderEnum.masculino,
            fecha_nacimiento=date(1990, 1, 1)
        )
        
        mock_cv_file = MagicMock()
        
        # Debe lanzar excepción
        with pytest.raises(HTTPException) as exc_info:
            user_service.create_pending_candidato(candidato, mock_cv_file)
        
        assert exc_info.value.status_code == 400
        assert "ya está registrado" in str(exc_info.value.detail)
        
        print("✅ Usuario ya existe - ÉXITO")
    
    def test_verify_email_code_success(self, mock_user_service_complete):
        """Test verificación de código exitosa"""
        user_service, mock_temp_storage, _ = mock_user_service_complete
        
        # Mock de datos temporales válidos
        mock_temp_data = {
            "verification_code": "123456",
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        }
        mock_temp_storage.get_pending_registration.return_value = mock_temp_data
        
        # Ejecutar
        result = user_service.verify_email_code("test@test.com", "123456")
        
        # Verificaciones
        assert result is True
        
        print("✅ Verificar código exitoso - ÉXITO")
    
    def test_verify_email_code_invalid(self, mock_user_service_complete):
        """Test verificación con código inválido"""
        user_service, mock_temp_storage, _ = mock_user_service_complete
        
        # Mock de datos temporales con código diferente
        mock_temp_data = {
            "verification_code": "654321",  # Código diferente
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        }
        mock_temp_storage.get_pending_registration.return_value = mock_temp_data
        
        # Ejecutar
        result = user_service.verify_email_code("test@test.com", "123456")
        
        # Verificaciones
        assert result is False
        
        print("✅ Código inválido - ÉXITO")
    
    def test_verify_email_code_no_data(self, mock_user_service_complete):
        """Test verificación sin datos temporales"""
        user_service, mock_temp_storage, _ = mock_user_service_complete
        
        # Mock: no hay datos temporales
        mock_temp_storage.get_pending_registration.return_value = None
        
        # Ejecutar
        result = user_service.verify_email_code("test@test.com", "123456")
        
        # Verificaciones
        assert result is False
        
        print("✅ Sin datos temporales - ÉXITO")

class TestUserServiceAuthentication:
    """Tests del sistema de autenticación"""
    
    @pytest.fixture
    def mock_auth_service(self, mock_database_environment):
        """UserService para tests de autenticación"""
        from services import UserService
        
        mock_session = mock_database_environment['session']
        
        with patch('services.TemporaryStorage'):
            service = UserService(mock_session)
            yield service, mock_session
    
    @patch('services.verify_password')
    def test_authenticate_user_success(self, mock_verify_password, mock_auth_service):
        """Test autenticación exitosa"""
        user_service, mock_session = mock_auth_service
        
        # Mock del usuario en BD
        mock_user = MagicMock()
        mock_user.email = "test@test.com"
        mock_user.hashed_password = "hashed_password"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Mock verificación de contraseña exitosa
        mock_verify_password.return_value = True
        
        # Ejecutar
        result = user_service.authenticate_user("test@test.com", "password123")
        
        # Verificaciones
        assert result is not None
        assert result.email == "test@test.com"
        mock_verify_password.assert_called_once_with("password123", "hashed_password")
        
        print("✅ Autenticación exitosa - ÉXITO")
    
    @patch('services.verify_password')
    def test_authenticate_user_wrong_password(self, mock_verify_password, mock_auth_service):
        """Test autenticación con contraseña incorrecta"""
        user_service, mock_session = mock_auth_service
        
        # Mock del usuario en BD
        mock_user = MagicMock()
        mock_user.email = "test@test.com"
        mock_user.hashed_password = "hashed_password"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Mock verificación de contraseña fallida
        mock_verify_password.return_value = False
        
        # Ejecutar
        result = user_service.authenticate_user("test@test.com", "wrong_password")
        
        # Verificaciones
        assert result is None
        
        print("✅ Contraseña incorrecta - ÉXITO")
    
    def test_authenticate_user_not_found(self, mock_auth_service):
        """Test autenticación con usuario no encontrado"""
        user_service, mock_session = mock_auth_service
        
        # Mock: usuario no encontrado
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Ejecutar
        result = user_service.authenticate_user("notfound@test.com", "password123")
        
        # Verificaciones
        assert result is None
        
        print("✅ Usuario no encontrado - ÉXITO")

class TestFileHandling:
    """Tests de manejo de archivos"""
    
    @pytest.fixture
    def mock_file_service(self, mock_database_environment):
        """UserService para tests de archivos"""
        from services import UserService
        
        mock_session = mock_database_environment['session']
        
        with patch('services.TemporaryStorage'), \
             patch('services.os.makedirs'), \
             patch('services.uuid.uuid4', return_value='test-uuid'), \
             patch('builtins.open', mock_open()):
            
            service = UserService(mock_session)
            yield service
    
    def test_save_temp_cv_file(self, mock_file_service):
        """Test guardar CV temporal"""
        user_service = mock_file_service
        
        # Mock del archivo CV
        mock_cv_file = MagicMock()
        mock_cv_file.filename = "test_cv.pdf"
        mock_cv_file.file.read.return_value = b"PDF content"
        mock_cv_file.file.seek = MagicMock()
        
        # Ejecutar
        filename = user_service.save_temp_cv_file(mock_cv_file, "test@test.com")
        
        # Verificaciones
        assert filename is not None
        assert filename.startswith("temp_cv_")
        assert filename.endswith(".pdf")
        assert "test_at_test_dot_com" in filename
        
        print("✅ Guardar CV temporal - ÉXITO")
    
    def test_save_temp_profile_picture_valid(self, mock_file_service):
        """Test guardar foto de perfil válida"""
        user_service = mock_file_service
        
        # Mock del archivo de imagen
        mock_image_file = MagicMock()
        mock_image_file.filename = "photo.jpg"
        mock_image_file.file.read.return_value = b"JPEG content"
        mock_image_file.file.seek = MagicMock()
        
        # Ejecutar
        filename = user_service.save_temp_profile_picture(mock_image_file, "test@test.com")
        
        # Verificaciones
        assert filename is not None
        assert filename.startswith("temp_pic_")
        assert filename.endswith(".jpg")
        
        print("✅ Guardar foto válida - ÉXITO")
    
    def test_save_temp_profile_picture_invalid_extension(self, mock_file_service):
        """Test guardar foto con extensión inválida"""
        user_service = mock_file_service
        
        # Mock del archivo con extensión inválida
        mock_file = MagicMock()
        mock_file.filename = "document.txt"
        
        from fastapi import HTTPException
        
        # Debe lanzar excepción
        with pytest.raises(HTTPException) as exc_info:
            user_service.save_temp_profile_picture(mock_file, "test@test.com")
        
        assert exc_info.value.status_code == 400
        assert "Formato de archivo no válido" in str(exc_info.value.detail)
        
        print("✅ Foto extensión inválida - ÉXITO")

class TestCompleteRegistration:
    """Tests de completar registro"""
    
    @pytest.fixture
    def mock_complete_service(self, mock_database_environment):
        """UserService para tests de completar registro"""
        from services import UserService
        
        mock_session = mock_database_environment['session']
        
        with patch('services.TemporaryStorage') as mock_temp_storage_class, \
             patch('services.get_password_hash', return_value="hashed_password"), \
             patch('services.os.rename'), \
             patch('services.os.path.exists', return_value=True), \
             patch('services.os.makedirs'):
            
            mock_temp_storage = MagicMock()
            mock_temp_storage_class.return_value = mock_temp_storage
            
            service = UserService(mock_session)
            service.temp_storage = mock_temp_storage
            
            yield service, mock_temp_storage, mock_session
    
    def test_complete_candidato_registration_success(self, mock_complete_service):
        """Test completar registro de candidato exitoso"""
        user_service, mock_temp_storage, mock_session = mock_complete_service
        
        # Mock verificación de código exitosa
        mock_temp_storage.get_pending_registration.return_value = {
            "registration_data": {
                "user_type": "candidato",
                "email": "test@test.com",
                "password": "Password123",
                "nombre": "Juan",
                "apellido": "Pérez",
                "genero": "masculino",
                "fecha_nacimiento": "1990-01-01",
                "cv_filename": "temp_cv.pdf",
                "cv_analysis_result": {"habilidades": ["Python"]},
                "profile_picture_filename": None
            }
        }
        
        # Mock usuario creado
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "test@test.com"
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()
        
        with patch('services.User', return_value=mock_user), \
             patch.object(user_service, 'verify_email_code', return_value=True), \
             patch.object(user_service, 'move_temp_files_to_permanent', return_value=("cv.pdf", None)):
            
            # Ejecutar
            result = user_service.complete_candidato_registration("test@test.com", "123456")
            
            # Verificaciones
            assert result is not None
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_temp_storage.remove_pending_registration.assert_called_once_with("test@test.com")
            
        print("✅ Completar registro candidato - ÉXITO")
    
    def test_complete_candidato_registration_invalid_code(self, mock_complete_service):
        """Test completar registro con código inválido"""
        user_service, mock_temp_storage, mock_session = mock_complete_service
        
        # Mock verificación de código fallida
        with patch.object(user_service, 'verify_email_code', return_value=False):
            
            from fastapi import HTTPException
            
            # Debe lanzar excepción
            with pytest.raises(HTTPException) as exc_info:
                user_service.complete_candidato_registration("test@test.com", "wrong_code")
            
            assert exc_info.value.status_code == 400
            assert "inválido o expirado" in str(exc_info.value.detail)
            
        print("✅ Código inválido completar registro - ÉXITO")

# Función de utilidad para ejecutar tests específicos
def run_service_tests():
    """Ejecutar tests de servicios críticos"""
    pytest.main([
        __file__,
        "-v",
        "-k", "test_generate_verification_code or test_analyze_cv_with_api_success or test_authenticate_user_success",
        "--tb=short"
    ])

if __name__ == "__main__":
    # Ejecutar todos los tests del archivo
    pytest.main([__file__, "-v", "--tb=short"])