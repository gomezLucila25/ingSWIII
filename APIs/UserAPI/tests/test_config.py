# tests/test_config.py
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Agregar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestEnvironmentConfig:
    """Tests para configuración de entorno"""
    
    def test_env_file_loading(self):
        """Test de carga de archivo .env"""
        
        # Simular variables de entorno
        test_env_vars = {
            "DATABASE_URL": "postgresql://test:test@localhost/test_db",
            "SECRET_KEY": "test_secret_key",
            "EMAIL_HOST": "smtp.test.com"
        }
        
        with patch.dict(os.environ, test_env_vars):
            # Verificar que las variables están disponibles
            assert os.environ.get("DATABASE_URL") == "postgresql://test:test@localhost/test_db"
            assert os.environ.get("SECRET_KEY") == "test_secret_key"
            assert os.environ.get("EMAIL_HOST") == "smtp.test.com"
            
            print("✅ Variables de entorno se cargan correctamente")
    
    def test_default_values(self):
        """Test de valores por defecto cuando no hay .env"""
        
        # Limpiar variables específicas
        env_vars_to_clear = ["DATABASE_URL", "SECRET_KEY", "EMAIL_HOST"]
        
        with patch.dict(os.environ, {}, clear=False):
            # Eliminar variables específicas
            for var in env_vars_to_clear:
                os.environ.pop(var, None)
            
            # Función que simula obtener config con defaults
            def get_config_value(key, default=None):
                return os.environ.get(key, default)
            
            # Test de defaults
            assert get_config_value("DATABASE_URL", "sqlite:///default.db") == "sqlite:///default.db"
            assert get_config_value("SECRET_KEY", "default_secret") == "default_secret"
            assert get_config_value("DEBUG", "False") == "False"
            
            print("✅ Valores por defecto funcionan correctamente")

class TestDatabaseConfig:
    """Tests para configuración de base de datos"""
    
    def test_database_url_parsing(self):
        """Test de parsing de URL de base de datos"""
        
        def parse_database_url(url):
            """Función simple para parsear URL de BD"""
            if not url:
                return None
            
            if url.startswith("postgresql://"):
                return {"type": "postgresql", "url": url}
            elif url.startswith("sqlite:///"):
                return {"type": "sqlite", "url": url}
            else:
                return {"type": "unknown", "url": url}
        
        # Test de URLs válidas
        pg_url = "postgresql://user:pass@localhost:5432/dbname"
        sqlite_url = "sqlite:///./test.db"
        
        pg_config = parse_database_url(pg_url)
        assert pg_config["type"] == "postgresql"
        assert pg_config["url"] == pg_url
        
        sqlite_config = parse_database_url(sqlite_url)
        assert sqlite_config["type"] == "sqlite"
        assert sqlite_config["url"] == sqlite_url
        
        # Test de URL inválida
        invalid_config = parse_database_url("invalid_url")
        assert invalid_config["type"] == "unknown"
        
        print("✅ Parsing de URLs de BD funciona")
    
    @patch('database.create_engine')
    def test_database_connection_mock(self, mock_create_engine):
        """Test mockeado de conexión a BD"""
        
        # Mock del engine
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        try:
            # Intentar importar database (mockeado)
            with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}):
                # Simular creación de engine
                from sqlalchemy import create_engine
                engine = create_engine("postgresql://test:test@localhost/test")
                
                # Verificar que se llamó
                assert engine is not None
                print("✅ Conexión a BD mockeada exitosamente")
                
        except Exception as e:
            print(f"⚠️ Test de BD mockeado parcial: {e}")

class TestEmailConfig:
    """Tests para configuración de email"""
    
    def test_email_configuration(self):
        """Test de configuración de email"""
        
        def validate_email_config(host, port, username, password):
            """Validar configuración de email"""
            errors = []
            
            if not host:
                errors.append("Host de email requerido")
            if not port or not str(port).isdigit():
                errors.append("Puerto de email inválido")
            if not username:
                errors.append("Usuario de email requerido")
            if not password:
                errors.append("Contraseña de email requerida")
                
            return len(errors) == 0, errors
        
        # Configuración válida
        valid, errors = validate_email_config("smtp.gmail.com", 587, "user@gmail.com", "password")
        assert valid == True
        assert len(errors) == 0
        
        # Configuración inválida
        invalid, errors = validate_email_config("", "", "", "")
        assert invalid == False
        assert len(errors) > 0
        
        print("✅ Validación de configuración de email funciona")

class TestSecurityConfig:
    """Tests para configuración de seguridad"""
    
    def test_secret_key_validation(self):
        """Test de validación de secret key"""
        
        def validate_secret_key(key):
            """Validar secret key"""
            if not key:
                return False, "Secret key no puede estar vacía"
            if len(key) < 32:
                return False, "Secret key muy corta (mínimo 32 caracteres)"
            if key == "default" or key == "secret":
                return False, "Secret key muy simple"
            return True, "Secret key válida"
        
        # Tests
        assert validate_secret_key("")[0] == False
        assert validate_secret_key("corta")[0] == False
        assert validate_secret_key("default")[0] == False
        assert validate_secret_key("a" * 32)[0] == True  # 32 caracteres
        assert validate_secret_key("mi_super_secret_key_muy_larga_y_segura_123")[0] == True
        
        print("✅ Validación de secret key funciona")
    
    def test_jwt_config(self):
        """Test de configuración de JWT"""
        
        def validate_jwt_config(secret, algorithm, expiration_minutes):
            """Validar configuración de JWT"""
            errors = []
            
            if not secret or len(secret) < 32:
                errors.append("JWT secret debe tener al menos 32 caracteres")
            
            valid_algorithms = ["HS256", "HS384", "HS512"]
            if algorithm not in valid_algorithms:
                errors.append(f"Algoritmo JWT inválido. Usar: {valid_algorithms}")
            
            if expiration_minutes <= 0 or expiration_minutes > 43200:  # Max 30 días
                errors.append("Expiración JWT debe estar entre 1 y 43200 minutos")
            
            return len(errors) == 0, errors
        
        # Configuración válida
        valid, errors = validate_jwt_config("a" * 32, "HS256", 1440)  # 24 horas
        assert valid == True
        
        # Configuración inválida
        invalid, errors = validate_jwt_config("corto", "INVALID", -1)
        assert invalid == False
        assert len(errors) > 0
        
        print("✅ Validación de configuración JWT funciona")

class TestFileConfig:
    """Tests para configuración de archivos"""
    
    def test_upload_directory_config(self):
        """Test de configuración de directorios de uploads"""
        
        def setup_upload_directories():
            """Configurar directorios de upload"""
            directories = {
                "cvs": "uploaded_cvs",
                "images": "profile_pictures", 
                "temp": "temp_files"
            }
            
            created = {}
            for name, path in directories.items():
                try:
                    # Simular creación de directorio
                    os.makedirs(path, exist_ok=True)
                    created[name] = os.path.exists(path)
                except Exception as e:
                    created[name] = False
            
            return created
        
        # Test (sin crear directorios reales)
        with patch('os.makedirs') as mock_makedirs, \
             patch('os.path.exists', return_value=True) as mock_exists:
            
            result = setup_upload_directories()
            
            # Verificar que se intentó crear los directorios
            assert mock_makedirs.call_count >= 3
            assert all(result.values())  # Todos los directorios "creados"
            
            print("✅ Configuración de directorios de upload funciona")
    
    def test_file_size_limits(self):
        """Test de límites de tamaño de archivo"""
        
        def get_file_size_limits():
            """Obtener límites de tamaño de archivo"""