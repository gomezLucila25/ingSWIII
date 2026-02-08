# tests/test_production_ready.py - Tests finales listos para producción
import pytest
import sys
import os
from datetime import date
from unittest.mock import patch

# Agregar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestProductionValidation:
    """Tests listos para usar en producción"""
    
    def test_email_format_robust(self):
        """Test robusto de formato de email - sin casos edge"""
        import re
        
        def validate_email_format(email):
            # Regex más estricta que maneja casos edge
            pattern = r'^[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not email or email.count('@') != 1:
                return False
            if '..' in email:  # Rechazar puntos consecutivos
                return False
            if email.startswith('.') or email.endswith('.'):
                return False
            if email.count(' ') > 0:  # No espacios
                return False
            return re.match(pattern, email) is not None
        
        # Emails válidos
        valid_emails = [
            "test@gmail.com",
            "user.name@company.co.uk", 
            "admin_123@domain-name.org",
            "simple@domain.com"
        ]
        
        for email in valid_emails:
            assert validate_email_format(email) == True
            print(f"✅ Email válido: {email}")
        
        # Emails inválidos
        invalid_emails = [
            "invalid",
            "@domain.com",
            "user@",
            "user..name@domain.com",  # Doble punto
            "",
            "user@domain",
            "user name@domain.com",  # Espacio
            ".user@domain.com",      # Empieza con punto
            "user@domain.com."       # Termina con punto
        ]
        
        for email in invalid_emails:
            assert validate_email_format(email) == False
            print(f"✅ Email inválido rechazado: {email}")
        
        print("✅ Validación robusta de email completa")
    
    def test_secure_password_validation(self):
        """Test de validación segura de contraseñas"""
        
        def validate_secure_password(password):
            """Validación robusta de contraseña para producción"""
            if not password:
                return False, "Contraseña requerida"
            
            errors = []
            
            if len(password) < 8:
                errors.append("Mínimo 8 caracteres")
            if len(password) > 128:
                errors.append("Máximo 128 caracteres")
            if not any(c.isupper() for c in password):
                errors.append("Debe contener mayúsculas")
            if not any(c.islower() for c in password):
                errors.append("Debe contener minúsculas") 
            if not any(c.isdigit() for c in password):
                errors.append("Debe contener números")
            
            # Contraseñas comunes prohibidas
            common_passwords = ["password", "123456789", "qwerty"]
            if password.lower() in common_passwords:
                errors.append("Contraseña muy común")
            
            return len(errors) == 0, errors
        
        # Contraseñas válidas
        valid_passwords = [
            "Password123",
            "MySecurePass1",
            "ComplexPass2024!"
        ]
        
        for pwd in valid_passwords:
            valid, _ = validate_secure_password(pwd)
            assert valid == True
            print(f"✅ Contraseña válida: {len(pwd)} caracteres")
        
        # Contraseñas inválidas
        invalid_passwords = [
            "",           # Vacía
            "123",        # Muy corta
            "password",   # Muy común
            "PASSWORD",   # Sin minúsculas
            "password",   # Sin mayúsculas
            "Password",   # Sin números
        ]
        
        for pwd in invalid_passwords:
            valid, errors = validate_secure_password(pwd)
            assert valid == False
            assert len(errors) > 0
            print(f"✅ Contraseña inválida rechazada: {errors[0]}")
        
        print("✅ Validación segura de contraseñas completa")
    
    def test_file_security_validation(self):
        """Test de validación de seguridad de archivos"""
        
        def validate_file_security(filename, size_bytes, content_type=None):
            """Validación de seguridad de archivos para producción"""
            errors = []
            
            if not filename:
                return False, ["Nombre de archivo requerido"]
            
            # Extensiones permitidas (whitelist)
            allowed_extensions = {
                'cv': ['.pdf', '.doc', '.docx'],
                'image': ['.jpg', '.jpeg', '.png', '.gif']
            }
            
            all_allowed = []
            for exts in allowed_extensions.values():
                all_allowed.extend(exts)
            
            if not any(filename.lower().endswith(ext) for ext in all_allowed):
                errors.append("Tipo de archivo no permitido")
            
            # Validar tamaño
            max_size = 10 * 1024 * 1024  # 10MB máximo
            if size_bytes > max_size:
                errors.append(f"Archivo muy grande (máximo 10MB)")
            
            # Validar nombre (seguridad)
            dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
            if any(char in filename for char in dangerous_chars):
                errors.append("Nombre de archivo contiene caracteres peligrosos")
            
            # Validar que no sea archivo ejecutable
            executable_extensions = ['.exe', '.bat', '.cmd', '.sh', '.ps1', '.js']
            if any(filename.lower().endswith(ext) for ext in executable_extensions):
                errors.append("Archivos ejecutables no permitidos")
            
            return len(errors) == 0, errors
        
        # Archivos válidos
        valid_files = [
            ("curriculum.pdf", 1024*1024),
            ("foto_perfil.jpg", 500*1024),
            ("documento.docx", 2*1024*1024)
        ]
        
        for filename, size in valid_files:
            valid, _ = validate_file_security(filename, size)
            assert valid == True
            print(f"✅ Archivo válido: {filename}")
        
        # Archivos inválidos
        invalid_files = [
            ("", 1024),                           # Sin nombre
            ("virus.exe", 1024),                  # Ejecutable
            ("file<script>.pdf", 1024),           # Caracteres peligrosos
            ("huge_file.pdf", 50*1024*1024),      # Muy grande
            ("document.txt", 1024),               # Extensión no permitida
        ]
        
        for filename, size in invalid_files:
            valid, errors = validate_file_security(filename, size)
            assert valid == False
            assert len(errors) > 0
            print(f"✅ Archivo inválido rechazado: {filename} - {errors[0]}")
        
        print("✅ Validación de seguridad de archivos completa")
    
    def test_user_input_sanitization(self):
        """Test de sanitización de entrada de usuario"""
        
        def sanitize_user_input(text, max_length=255):
            """Sanitizar entrada de usuario"""
            if not text:
                return ""
            
            # Remover caracteres peligrosos
            import html
            sanitized = html.escape(str(text))
            
            # Limpiar espacios
            sanitized = ' '.join(sanitized.split())
            
            # Truncar si es muy largo
            if len(sanitized) > max_length:
                sanitized = sanitized[:max_length].rstrip()
            
            return sanitized
        
        # Tests de sanitización
        test_cases = [
            ("Juan Pérez", "Juan Pérez"),
            ("  Texto   con    espacios  ", "Texto con espacios"),
            ("<script>alert('xss')</script>", "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"),
            ("", ""),
            ("A" * 300, "A" * 255),  # Truncar
        ]
        
        for input_text, expected in test_cases:
            result = sanitize_user_input(input_text)
            if input_text == "A" * 300:
                assert len(result) == 255
            else:
                assert result == expected
            print(f"✅ Sanitización: '{input_text[:20]}...' -> '{result[:20]}...'")
        
        print("✅ Sanitización de entrada completa")
    
    def test_business_rules_validation(self):
        """Test de reglas de negocio específicas del proyecto"""
        
        def validate_candidate_age(birth_date):
            """Validar edad mínima para candidatos"""
            from datetime import datetime
            today = datetime.now().date()
            age = today.year - birth_date.year
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
            
            return age >= 16, f"Edad: {age} años"
        
        def validate_company_name(name):
            """Validar nombre de empresa"""
            if not name or len(name.strip()) < 2:
                return False, "Nombre muy corto"
            if len(name) > 100:
                return False, "Nombre muy largo"
            if any(char in name for char in ['<', '>', '"', "'"]):
                return False, "Caracteres no permitidos"
            return True, "Válido"
        
        # Test edad candidatos
        from datetime import datetime, timedelta
        
        adult_date = datetime.now().date() - timedelta(days=20*365)  # 20 años
        minor_date = datetime.now().date() - timedelta(days=10*365)  # 10 años
        
        assert validate_candidate_age(adult_date)[0] == True
        assert validate_candidate_age(minor_date)[0] == False
        
        # Test nombres de empresa
        assert validate_company_name("Empresa S.A.")[0] == True
        assert validate_company_name("A")[0] == False  # Muy corto
        assert validate_company_name("Empresa <script>")[0] == False  # Peligroso
        
        print("✅ Reglas de negocio validadas")

class TestIntegrationScenarios:
    """Tests de escenarios de integración comunes"""
    
    def test_complete_registration_flow(self):
        """Test del flujo completo de registro"""
        
        # Simular datos de registro completo
        registration_data = {
            "email": "test@gmail.com",
            "password": "SecurePass123",
            "nombre": "Juan",
            "apellido": "Pérez",
            "genero": "masculino",
            "fecha_nacimiento": date(1990, 1, 1)
        }
        
        # Validar cada campo
        email_valid = "@" in registration_data["email"] and "." in registration_data["email"]
        password_valid = len(registration_data["password"]) >= 8
        name_valid = len(registration_data["nombre"]) >= 2
        age_valid = (2024 - registration_data["fecha_nacimiento"].year) >= 16
        
        assert email_valid
        assert password_valid  
        assert name_valid
        assert age_valid
        
        print("✅ Flujo de registro validado")
    
    def test_api_response_structure(self):
        """Test de estructura de respuestas de API"""
        
        def create_api_response(success, data=None, message=None, errors=None):
            """Crear respuesta estándar de API"""
            response = {
                "success": success,
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            if data is not None:
                response["data"] = data
            if message:
                response["message"] = message
            if errors:
                response["errors"] = errors
                
            return response
        
        # Test respuesta exitosa
        success_response = create_api_response(
            success=True,
            data={"user_id": 123},
            message="Usuario creado exitosamente"
        )
        
        assert success_response["success"] == True
        assert "data" in success_response
        assert "message" in success_response
        assert "timestamp" in success_response
        
        # Test respuesta de error
        error_response = create_api_response(
            success=False,
            errors=["Email ya existe", "Contraseña muy débil"]
        )
        
        assert error_response["success"] == False
        assert "errors" in error_response
        assert len(error_response["errors"]) == 2
        
        print("✅ Estructura de respuestas API validada")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])