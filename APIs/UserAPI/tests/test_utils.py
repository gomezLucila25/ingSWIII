# tests/test_utils.py
import pytest
import sys
import os
from datetime import datetime, date
from unittest.mock import patch, MagicMock

# Agregar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestPasswordSecurity:
    """Tests para funcionalidades de seguridad de contraseñas"""
    
    def test_password_hashing_basic(self):
        """Test básico de hashing de contraseñas"""
        try:
            from passlib.context import CryptContext
            
            # Simular el contexto que usa tu app
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            password = "test123"
            hashed = pwd_context.hash(password)
            
            # Verificar que el hash no es igual a la contraseña original
            assert hashed != password
            assert len(hashed) > 20  # Los hashes bcrypt son largos
            assert hashed.startswith("$2b$")  # bcrypt prefix
            
            # Verificar que se puede verificar la contraseña
            assert pwd_context.verify(password, hashed) == True
            assert pwd_context.verify("wrong_password", hashed) == False
            
            print("✅ Password hashing funciona correctamente")
            
        except ImportError:
            pytest.skip("passlib no disponible")

class TestEmailValidation:
    """Tests para validación de emails"""
    
    def test_valid_emails(self):
        """Test con emails válidos"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co",
            "admin@polo52.com.ar",
            "candidate123@gmail.com"
        ]
        
        try:
            from email_validator import validate_email
            
            for email in valid_emails:
                # Esto no debería lanzar excepción
                result = validate_email(email)
                assert result.email == email
                print(f"✅ Email válido: {email}")
                
        except ImportError:
            # Fallback a validación básica
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            for email in valid_emails:
                assert re.match(email_pattern, email) is not None
                print(f"✅ Email válido (regex): {email}")
    
    def test_invalid_emails(self):
        """Test con emails inválidos"""
        invalid_emails = [
            "invalid",
            "@domain.com",
            "user@",
            "user..name@domain.com",
            ""
        ]
        
        try:
            from email_validator import validate_email, EmailNotValidError
            
            for email in invalid_emails:
                with pytest.raises(EmailNotValidError):
                    validate_email(email)
                print(f"✅ Email inválido detectado: {email}")
                
        except ImportError:
            # Fallback a validación básica
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            for email in invalid_emails:
                assert re.match(email_pattern, email) is None
                print(f"✅ Email inválido detectado (regex): {email}")

class TestDataValidation:
    """Tests para validación de datos de entrada"""
    
    def test_date_validation(self):
        """Test de validación de fechas"""
        # Fechas válidas
        valid_dates = [
            "1990-01-01",
            "2000-12-31",
            "1985-06-15"
        ]
        
        for date_str in valid_dates:
            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                assert isinstance(parsed_date, date)
                assert parsed_date.year >= 1900
                print(f"✅ Fecha válida: {date_str}")
            except ValueError:
                pytest.fail(f"Fecha válida no pudo ser parseada: {date_str}")
    
    def test_age_validation(self):
        """Test de validación de edad mínima"""
        from datetime import datetime, timedelta
        
        # Persona de 25 años
        birth_date_25 = datetime.now().date() - timedelta(days=25*365)
        
        # Persona de 15 años (menor de edad)
        birth_date_15 = datetime.now().date() - timedelta(days=15*365)
        
        # Lógica de validación de edad
        def is_adult(birth_date):
            today = datetime.now().date()
            age = today.year - birth_date.year
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
            return age >= 18
        
        assert is_adult(birth_date_25) == True
        assert is_adult(birth_date_15) == False
        print("✅ Validación de edad funciona")

class TestFileValidation:
    """Tests para validación de archivos (CVs, imágenes)"""
    
    def test_file_extension_validation(self):
        """Test de validación de extensiones de archivo"""
        
        def validate_cv_file(filename):
            allowed_extensions = ['.pdf', '.doc', '.docx']
            return any(filename.lower().endswith(ext) for ext in allowed_extensions)
        
        def validate_image_file(filename):
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            return any(filename.lower().endswith(ext) for ext in allowed_extensions)
        
        # Tests de CV
        assert validate_cv_file("cv.pdf") == True
        assert validate_cv_file("resume.docx") == True
        assert validate_cv_file("curriculum.DOC") == True
        assert validate_cv_file("cv.txt") == False
        assert validate_cv_file("cv.exe") == False
        
        # Tests de imágenes
        assert validate_image_file("photo.jpg") == True
        assert validate_image_file("avatar.PNG") == True
        assert validate_image_file("pic.gif") == True
        assert validate_image_file("document.pdf") == False
        
        print("✅ Validación de archivos funciona")
    
    def test_file_size_validation(self):
        """Test de validación de tamaño de archivo"""
        
        def validate_file_size(file_size_bytes, max_mb=5):
            max_bytes = max_mb * 1024 * 1024  # Convertir MB a bytes
            return file_size_bytes <= max_bytes
        
        # 1 MB = OK
        assert validate_file_size(1024 * 1024) == True
        
        # 3 MB = OK  
        assert validate_file_size(3 * 1024 * 1024) == True
        
        # 10 MB = NO (excede límite de 5MB)
        assert validate_file_size(10 * 1024 * 1024) == False
        
        print("✅ Validación de tamaño de archivo funciona")

class TestBusinessLogic:
    """Tests para lógica de negocio específica"""
    
    def test_user_role_validation(self):
        """Test de validación de roles de usuario"""
        
        def validate_user_role(role):
            valid_roles = ["candidato", "empresa", "admin", "recruiter"]
            return role.lower() in valid_roles
        
        # Roles válidos
        assert validate_user_role("candidato") == True
        assert validate_user_role("EMPRESA") == True
        assert validate_user_role("Admin") == True
        assert validate_user_role("recruiter") == True
        
        # Roles inválidos
        assert validate_user_role("invalid") == False
        assert validate_user_role("") == False
        assert validate_user_role("usuario") == False
        
        print("✅ Validación de roles funciona")
    
    def test_gender_validation(self):
        """Test de validación de género"""
        
        def validate_gender(gender):
            valid_genders = ["masculino", "femenino", "otro", "prefiero_no_decir"]
            return gender.lower() in valid_genders
        
        assert validate_gender("masculino") == True
        assert validate_gender("FEMENINO") == True
        assert validate_gender("Otro") == True
        assert validate_gender("prefiero_no_decir") == True
        assert validate_gender("invalid") == False
        
        print("✅ Validación de género funciona")

class TestStringUtils:
    """Tests para utilidades de strings"""
    
    def test_string_cleaning(self):
        """Test de limpieza de strings"""
        
        def clean_string(text):
            if not text:
                return ""
            return text.strip().replace("  ", " ")
        
        assert clean_string("  Hola Mundo  ") == "Hola Mundo"
        assert clean_string("Juan  Pérez") == "Juan Pérez"
        assert clean_string("") == ""
        assert clean_string(None) == ""
        
        print("✅ Limpieza de strings funciona")
    
    def test_slug_generation(self):
        """Test de generación de slugs para URLs"""
        import re
        
        def generate_slug(text):
            if not text:
                return ""
            # Convertir a minúsculas, reemplazar espacios y caracteres especiales
            slug = re.sub(r'[^\w\s-]', '', text.lower())
            slug = re.sub(r'[-\s]+', '-', slug)
            return slug.strip('-')
        
        assert generate_slug("Empresa Ejemplo S.A.") == "empresa-ejemplo-sa"
        assert generate_slug("Desarrollador Full-Stack") == "desarrollador-full-stack"
        assert generate_slug("") == ""
        
        print("✅ Generación de slugs funciona")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])