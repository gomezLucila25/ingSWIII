import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock, mock_open
from fastapi import UploadFile, HTTPException
from datetime import datetime, date, timedelta
import tempfile
import os
import json
from io import BytesIO

from database import Base
from models import User, CompanyRecruiter, UserRoleEnum, GenderEnum
from services import UserService, TemporaryStorage
from schemas import CandidatoCreate, EmpresaCreate, UserUpdate


@pytest.fixture
def test_db():
    db_fd, db_path = tempfile.mkstemp()
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    
    yield TestingSessionLocal
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def user_service(test_db):
    db = test_db()
    service = UserService(db)
    yield service
    db.close()


@pytest.fixture
def mock_cv_file():
    content = b"%PDF-1.4\nFake PDF content for testing"
    file = MagicMock(spec=UploadFile)
    file.filename = "test_cv.pdf"
    file.content_type = "application/pdf"
    file.file = BytesIO(content)
    file.file.read.return_value = content
    file.file.seek = MagicMock()
    return file


@pytest.fixture
def mock_image_file():
    content = b"fake_image_content"
    file = MagicMock(spec=UploadFile)
    file.filename = "test_image.jpg"
    file.content_type = "image/jpeg"
    file.file = BytesIO(content)
    file.file.read.return_value = content
    file.file.seek = MagicMock()
    return file


class TestTemporaryStorage:
    
    def test_save_pending_registration(self):
        storage = TemporaryStorage()
        
        email = "test@example.com"
        registration_data = {"nome": "Test User", "role": "candidato"}
        verification_code = "123456"
        
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("json.dump") as mock_json_dump:
                file_path = storage.save_pending_registration(email, registration_data, verification_code)
                
                mock_file.assert_called_once()
                mock_json_dump.assert_called_once()
                assert "test_at_example_dot_com" in file_path
    
    def test_get_pending_registration_success(self):
        storage = TemporaryStorage()
        
        email = "test@example.com"
        temp_data = {
            "registration_data": {"nome": "Test"},
            "verification_code": "123456",
            "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        }
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(temp_data))):
                with patch("json.load", return_value=temp_data):
                    result = storage.get_pending_registration(email)
                    
                    assert result is not None
                    assert result["verification_code"] == "123456"
    
    def test_get_pending_registration_expired(self):
        storage = TemporaryStorage()
        
        email = "test@example.com"
        temp_data = {
            "registration_data": {"nome": "Test"},
            "verification_code": "123456",
            "expires_at": (datetime.utcnow() - timedelta(minutes=1)).isoformat()  # Expired
        }
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(temp_data))):
                with patch("json.load", return_value=temp_data):
                    with patch.object(storage, "remove_pending_registration"):
                        result = storage.get_pending_registration(email)
                        
                        assert result is None
    
    def test_remove_pending_registration(self):
        storage = TemporaryStorage()
        
        email = "test@example.com"
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.unlink") as mock_unlink:
                result = storage.remove_pending_registration(email)
                
                assert result is True
                mock_unlink.assert_called_once()


class TestUserServiceBasic:
    
    def test_get_user_by_email(self, user_service, test_db):
        db = test_db()
        
        user = User(
            email="test@example.com",
            hashed_password="hash",
            role=UserRoleEnum.candidato,
            nome="Test User"
        )
        
        db.add(user)
        db.commit()
        
        found_user = user_service.get_user_by_email("test@example.com")
        assert found_user is not None
        assert found_user.email == "test@example.com"
        
        not_found = user_service.get_user_by_email("nonexistent@example.com")
        assert not_found is None
        
        db.close()
    
    def test_get_user_by_id(self, user_service, test_db):
        db = test_db()
        
        user = User(
            email="test@example.com",
            hashed_password="hash",
            role=UserRoleEnum.candidato,
            nome="Test User"
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        found_user = user_service.get_user_by_id(user.id)
        assert found_user is not None
        assert found_user.id == user.id
        
        not_found = user_service.get_user_by_id(99999)
        assert not_found is None
        
        db.close()
    
    def test_get_all_users(self, user_service, test_db):
        db = test_db()
        
        users = [
            User(email=f"user{i}@example.com", hashed_password="hash", 
                 role=UserRoleEnum.candidato, nome=f"User {i}")
            for i in range(5)
        ]
        
        db.add_all(users)
        db.commit()
        
        all_users = user_service.get_all_users()
        assert len(all_users) == 5
        
        limited_users = user_service.get_all_users(skip=2, limit=2)
        assert len(limited_users) == 2
        
        db.close()


class TestCVAnalysis:
    
    @patch('services.requests.post')
    def test_analyze_cv_with_api_success(self, mock_post, user_service, mock_cv_file):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "valid": True,
            "data": {
                "experiencia": [{"puesto": "Developer"}],
                "habilidades_tecnicas": ["Python"]
            }
        }
        mock_post.return_value = mock_response
        
        result = user_service.analyze_cv_with_api(mock_cv_file)
        
        assert result is not None
        assert "experiencia" in result
        assert "habilidades_tecnicas" in result
        mock_post.assert_called_once()
    
    @patch('services.requests.post')
    def test_analyze_cv_with_api_failure(self, mock_post, user_service, mock_cv_file):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid CV"
        mock_post.return_value = mock_response
        
        result = user_service.analyze_cv_with_api(mock_cv_file)
        
        assert result is None
    
    @patch('services.requests.post')
    def test_analyze_cv_with_api_connection_error(self, mock_post, user_service, mock_cv_file):
        mock_post.side_effect = Exception("Connection error")
        
        result = user_service.analyze_cv_with_api(mock_cv_file)
        
        assert result is None


class TestVerificationCode:
    
    def test_generate_verification_code(self, user_service):
        code = user_service.generate_verification_code()
        
        assert len(code) == 6
        assert code.isdigit()
        assert 100000 <= int(code) <= 999999
    
    def test_generate_multiple_codes_unique(self, user_service):
        codes = [user_service.generate_verification_code() for _ in range(10)]
        # While not guaranteed, highly unlikely to get duplicates
        assert len(set(codes)) >= 8  # Allow for some possible duplicates
    
    @patch('services.smtplib.SMTP')
    @patch.dict('os.environ', {'EMAIL_USER': 'test@gmail.com', 'EMAIL_PASSWORD': 'password'})
    def test_send_verification_email_success(self, mock_smtp, user_service):
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        user_service.send_verification_email("test@example.com", "123456")
        
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()
    
    @patch.dict('os.environ', {}, clear=True)
    def test_send_verification_email_no_config(self, user_service):
        # Should not raise exception even without email config
        user_service.send_verification_email("test@example.com", "123456")
        # Test passes if no exception is raised
    
    def test_verify_email_code_success(self, user_service):
        email = "test@example.com"
        code = "123456"
        
        temp_data = {
            "verification_code": code,
            "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        }
        
        with patch.object(user_service.temp_storage, 'get_pending_registration', return_value=temp_data):
            result = user_service.verify_email_code(email, code)
            assert result is True
    
    def test_verify_email_code_invalid(self, user_service):
        email = "test@example.com"
        
        temp_data = {
            "verification_code": "654321",
            "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        }
        
        with patch.object(user_service.temp_storage, 'get_pending_registration', return_value=temp_data):
            result = user_service.verify_email_code(email, "123456")
            assert result is False
    
    def test_verify_email_code_no_registration(self, user_service):
        with patch.object(user_service.temp_storage, 'get_pending_registration', return_value=None):
            result = user_service.verify_email_code("test@example.com", "123456")
            assert result is False


class TestCandidatoRegistration:
    
    @patch('services.UserService.analyze_cv_with_api')
    @patch('services.UserService.send_verification_email')
    def test_create_pending_candidato_success(self, mock_send_email, mock_analyze_cv, 
                                            user_service, mock_cv_file, mock_image_file):
        mock_analyze_cv.return_value = {"habilidades_tecnicas": ["Python"]}
        
        candidato = CandidatoCreate(
            email="candidate@example.com",
            password="password123",
            nome="Juan",
            apellido="Pérez",
            genero=GenderEnum.masculino,
            fecha_nacimiento=date(1990, 1, 1)
        )
        
        with patch('services.UserService.save_temp_cv_file', return_value="temp_cv.pdf"):
            with patch('services.UserService.save_temp_profile_picture', return_value="temp_pic.jpg"):
                result = user_service.create_pending_candidato(candidato, mock_cv_file, mock_image_file)
        
        assert "message" in result
        assert result["email"] == "candidate@example.com"
        assert result["expires_in_minutes"] == 15
        mock_analyze_cv.assert_called_once()
        mock_send_email.assert_called_once()
    
    @patch('services.UserService.analyze_cv_with_api')
    def test_create_pending_candidato_existing_user(self, mock_analyze_cv, user_service, 
                                                   mock_cv_file, test_db):
        db = test_db()
        
        # Create existing user
        existing_user = User(
            email="existing@example.com",
            hashed_password="hash",
            role=UserRoleEnum.candidato,
            nome="Existing"
        )
        db.add(existing_user)
        db.commit()
        
        candidato = CandidatoCreate(
            email="existing@example.com",
            password="password123",
            nome="Juan",
            apellido="Pérez",
            genero=GenderEnum.masculino,
            fecha_nacimiento=date(1990, 1, 1)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            user_service.create_pending_candidato(candidato, mock_cv_file)
        
        assert exc_info.value.status_code == 400
        assert "ya está registrado" in exc_info.value.detail
        
        db.close()
    
    @patch('services.UserService.analyze_cv_with_api')
    def test_create_pending_candidato_invalid_cv(self, mock_analyze_cv, user_service, 
                                                mock_cv_file):
        mock_analyze_cv.return_value = None  # Invalid CV
        
        candidato = CandidatoCreate(
            email="candidate@example.com",
            password="password123",
            nome="Juan",
            apellido="Pérez", 
            genero=GenderEnum.masculino,
            fecha_nacimiento=date(1990, 1, 1)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            user_service.create_pending_candidato(candidato, mock_cv_file)
        
        assert exc_info.value.status_code == 400
        assert "no es un CV válido" in exc_info.value.detail
    
    def test_complete_candidato_registration_success(self, user_service, test_db):
        db = test_db()
        
        email = "candidate@example.com"
        code = "123456"
        
        temp_data = {
            "registration_data": {
                "user_type": "candidato",
                "email": email,
                "password": "password123",
                "nome": "Juan",
                "apellido": "Pérez",
                "genero": "masculino",
                "fecha_nacimiento": "1990-01-01",
                "cv_filename": "temp_cv.pdf",
                "cv_analysis_result": {"habilidades_tecnicas": ["Python"]},
                "profile_picture_filename": "temp_pic.jpg"
            },
            "verification_code": code
        }
        
        with patch.object(user_service, 'verify_email_code', return_value=True):
            with patch.object(user_service.temp_storage, 'get_pending_registration', return_value=temp_data):
                with patch.object(user_service, 'move_temp_files_to_permanent', return_value=("cv.pdf", "pic.jpg")):
                    with patch.object(user_service.temp_storage, 'remove_pending_registration'):
                        user = user_service.complete_candidato_registration(email, code)
        
        assert user.email == email
        assert user.nome == "Juan"
        assert user.role == UserRoleEnum.candidato
        assert user.email_verified is True
        
        db.close()


class TestEmpresaRegistration:
    
    @patch('services.UserService.send_verification_email')
    def test_create_empresa_success(self, mock_send_email, user_service, mock_image_file):
        empresa = EmpresaCreate(
            email="company@example.com",
            password="password123",
            nome="Tech Company",
            descripcion="Leading tech company"
        )
        
        with patch('services.UserService.save_temp_profile_picture', return_value="temp_pic.jpg"):
            result = user_service.create_empresa(empresa, mock_image_file)
        
        assert "message" in result
        assert result["email"] == "company@example.com"
        mock_send_email.assert_called_once()
    
    def test_complete_empresa_registration_success(self, user_service, test_db):
        db = test_db()
        
        email = "company@example.com"
        code = "123456"
        
        temp_data = {
            "registration_data": {
                "user_type": "empresa",
                "email": email,
                "password": "password123",
                "nome": "Tech Company",
                "descripcion": "Leading tech company",
                "profile_picture_filename": "temp_pic.jpg"
            },
            "verification_code": code
        }
        
        with patch.object(user_service, 'verify_email_code', return_value=True):
            with patch.object(user_service.temp_storage, 'get_pending_registration', return_value=temp_data):
                with patch.object(user_service, 'move_temp_files_to_permanent', return_value=(None, "pic.jpg")):
                    with patch.object(user_service.temp_storage, 'remove_pending_registration'):
                        user = user_service.complete_empresa_registration(email, code)
        
        assert user.email == email
        assert user.nome == "Tech Company"
        assert user.role == UserRoleEnum.empresa
        assert user.verified is False  # Companies need admin verification
        assert user.email_verified is True
        
        db.close()


class TestFileHandling:
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    @patch('uuid.uuid4')
    def test_save_temp_cv_file(self, mock_uuid, mock_makedirs, mock_file, 
                              user_service, mock_cv_file):
        mock_uuid.return_value.hex = "fake-uuid"
        
        result = user_service.save_temp_cv_file(mock_cv_file, "test@example.com")
        
        assert "temp_cv_test_at_example_dot_com" in result
        assert result.endswith(".pdf")
        mock_makedirs.assert_called_once()
        mock_file.assert_called_once()
    
    def test_save_temp_profile_picture_invalid_extension(self, user_service):
        invalid_file = MagicMock(spec=UploadFile)
        invalid_file.filename = "test.txt"
        
        with pytest.raises(HTTPException) as exc_info:
            user_service.save_temp_profile_picture(invalid_file, "test@example.com")
        
        assert exc_info.value.status_code == 400
        assert "Formato de archivo no válido" in exc_info.value.detail
    
    @patch('os.path.exists')
    @patch('os.rename')
    @patch('os.makedirs')
    @patch('uuid.uuid4')
    def test_move_temp_files_to_permanent(self, mock_uuid, mock_makedirs, 
                                         mock_rename, mock_exists, user_service):
        mock_uuid.return_value.hex = "permanent-uuid"
        mock_exists.return_value = True
        
        cv_filename, pic_filename = user_service.move_temp_files_to_permanent(
            "temp_cv.pdf", "temp_pic.jpg"
        )
        
        assert cv_filename.endswith(".pdf")
        assert pic_filename.endswith(".jpg")
        assert mock_rename.call_count == 2


class TestUserOperations:
    
    def test_create_admin(self, user_service, test_db):
        db = test_db()
        
        admin = user_service.create_admin(
            "admin@example.com", "password123", "Administrator"
        )
        
        assert admin.email == "admin@example.com"
        assert admin.role == UserRoleEnum.admin
        assert admin.verified is True
        assert admin.email_verified is True
        
        db.close()
    
    @patch('services.requests.post')
    def test_update_user_with_cv(self, mock_post, user_service, test_db, mock_cv_file):
        db = test_db()
        
        user = User(
            email="user@example.com",
            hashed_password="hash",
            role=UserRoleEnum.candidato,
            nome="User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Mock CV analysis
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"valid": True, "data": {"skills": ["Python"]}}
        mock_post.return_value = mock_response
        
        user_update = UserUpdate(nome="Updated Name")
        
        with patch.object(user_service, 'save_cv_file', return_value="new_cv.pdf"):
            updated_user = user_service.update_user(user.id, user_update, mock_cv_file)
        
        assert updated_user.nome == "Updated Name"
        assert updated_user.cv_filename == "new_cv.pdf"
        
        db.close()
    
    def test_verify_company(self, user_service, test_db):
        db = test_db()
        
        company = User(
            email="company@example.com",
            hashed_password="hash",
            role=UserRoleEnum.empresa,
            nome="Company",
            verified=False
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        
        verified_company = user_service.verify_company(company.id, True)
        
        assert verified_company.verified is True
        
        db.close()
    
    def test_delete_user(self, user_service, test_db):
        db = test_db()
        
        user = User(
            email="delete@example.com",
            hashed_password="hash",
            role=UserRoleEnum.candidato,
            nome="Delete Me"
        )
        db.add(user)
        db.commit()
        user_id = user.id
        
        result = user_service.delete_user(user_id)
        
        assert result is True
        assert user_service.get_user_by_id(user_id) is None
        
        db.close()
    
    def test_authenticate_user(self, user_service, test_db):
        db = test_db()
        
        from auth import get_password_hash
        
        user = User(
            email="auth@example.com",
            hashed_password=get_password_hash("correct_password"),
            role=UserRoleEnum.candidato,
            nome="Auth User"
        )
        db.add(user)
        db.commit()
        
        # Correct credentials
        authenticated = user_service.authenticate_user("auth@example.com", "correct_password")
        assert authenticated is not None
        assert authenticated.email == "auth@example.com"
        
        # Wrong password
        not_authenticated = user_service.authenticate_user("auth@example.com", "wrong_password")
        assert not_authenticated is None
        
        # Wrong email
        not_found = user_service.authenticate_user("wrong@example.com", "correct_password")
        assert not_found is None
        
        db.close()


class TestRecruiterManagement:
    
    def test_add_recruiter_to_company(self, user_service, test_db):
        db = test_db()
        
        company = User(
            email="company@example.com",
            hashed_password="hash",
            role=UserRoleEnum.empresa,
            nome="Company",
            verified=True
        )
        
        recruiter = User(
            email="recruiter@example.com", 
            hashed_password="hash",
            role=UserRoleEnum.candidato,
            nome="Recruiter"
        )
        
        db.add_all([company, recruiter])
        db.commit()
        db.refresh(company)
        db.refresh(recruiter)
        
        relationship = user_service.add_recruiter_to_company(company.id, recruiter.email)
        
        assert relationship.company_id == company.id
        assert relationship.recruiter_id == recruiter.id
        assert relationship.is_active is True
        
        db.close()
    
    def test_add_recruiter_unverified_company(self, user_service, test_db):
        db = test_db()
        
        company = User(
            email="company@example.com",
            hashed_password="hash",
            role=UserRoleEnum.empresa,
            nome="Company",
            verified=False  # Not verified
        )
        
        db.add(company)
        db.commit()
        db.refresh(company)
        
        with pytest.raises(HTTPException) as exc_info:
            user_service.add_recruiter_to_company(company.id, "recruiter@example.com")
        
        assert exc_info.value.status_code == 403
        assert "verificadas" in exc_info.value.detail
        
        db.close()
    
    def test_get_company_recruiters(self, user_service, test_db):
        db = test_db()
        
        company = User(
            email="company@example.com",
            hashed_password="hash",
            role=UserRoleEnum.empresa,
            nome="Company"
        )
        
        recruiter = User(
            email="recruiter@example.com",
            hashed_password="hash", 
            role=UserRoleEnum.candidato,
            nome="Recruiter"
        )
        
        db.add_all([company, recruiter])
        db.commit()
        db.refresh(company)
        db.refresh(recruiter)
        
        relationship = CompanyRecruiter(
            company_id=company.id,
            recruiter_id=recruiter.id,
            is_active=True
        )
        db.add(relationship)
        db.commit()
        
        recruiters = user_service.get_company_recruiters(company.id)
        
        assert len(recruiters) == 1
        assert recruiters[0].recruiter_id == recruiter.id
        
        db.close()
    
    def test_remove_recruiter_from_company(self, user_service, test_db):
        db = test_db()
        
        company = User(
            email="company@example.com",
            hashed_password="hash",
            role=UserRoleEnum.empresa,
            nome="Company"
        )
        
        recruiter = User(
            email="recruiter@example.com",
            hashed_password="hash",
            role=UserRoleEnum.candidato,
            nome="Recruiter"
        )
        
        db.add_all([company, recruiter])
        db.commit()
        db.refresh(company)
        db.refresh(recruiter)
        
        relationship = CompanyRecruiter(
            company_id=company.id,
            recruiter_id=recruiter.id,
            is_active=True
        )
        db.add(relationship)
        db.commit()
        
        result = user_service.remove_recruiter_from_company(company.id, recruiter.email)
        
        assert result is True
        
        # Check that relationship is deactivated
        db.refresh(relationship)
        assert relationship.is_active is False
        
        db.close()
    
    def test_is_recruiter_for_company(self, user_service, test_db):
        db = test_db()
        
        company = User(
            email="company@example.com",
            hashed_password="hash",
            role=UserRoleEnum.empresa,
            nome="Company"
        )
        
        recruiter = User(
            email="recruiter@example.com",
            hashed_password="hash",
            role=UserRoleEnum.candidato,
            nome="Recruiter"
        )
        
        db.add_all([company, recruiter])
        db.commit()
        db.refresh(company)
        db.refresh(recruiter)
        
        # No relationship initially
        is_recruiter = user_service.is_recruiter_for_company(recruiter.id, company.id)
        assert is_recruiter is False
        
        # Add relationship
        relationship = CompanyRecruiter(
            company_id=company.id,
            recruiter_id=recruiter.id,
            is_active=True
        )
        db.add(relationship)
        db.commit()
        
        is_recruiter = user_service.is_recruiter_for_company(recruiter.id, company.id)
        assert is_recruiter is True
        
        db.close()


class TestSpecialCases:
    
    def test_get_unverified_companies(self, user_service, test_db):
        db = test_db()
        
        verified_company = User(
            email="verified@example.com",
            hashed_password="hash",
            role=UserRoleEnum.empresa,
            nome="Verified Company",
            verified=True
        )
        
        unverified_company = User(
            email="unverified@example.com",
            hashed_password="hash",
            role=UserRoleEnum.empresa,
            nome="Unverified Company",
            verified=False
        )
        
        db.add_all([verified_company, unverified_company])
        db.commit()
        
        unverified = user_service.get_unverified_companies()
        
        assert len(unverified) == 1
        assert unverified[0].email == "unverified@example.com"
        
        db.close()
    
    def test_get_all_candidates(self, user_service, test_db):
        db = test_db()
        
        candidate = User(
            email="candidate@example.com",
            hashed_password="hash",
            role=UserRoleEnum.candidato,
            nome="Candidate"
        )
        
        company = User(
            email="company@example.com",
            hashed_password="hash",
            role=UserRoleEnum.empresa,
            nome="Company"
        )
        
        db.add_all([candidate, company])
        db.commit()
        
        candidates = user_service.get_all_candidates()
        
        assert len(candidates) == 1
        assert candidates[0].role == UserRoleEnum.candidato
        
        db.close()
    
    def test_resend_verification_code(self, user_service):
        email = "test@example.com"
        
        temp_data = {
            "registration_data": {"nome": "Test"},
            "verification_code": "old_code"
        }
        
        with patch.object(user_service.temp_storage, 'get_pending_registration', return_value=temp_data):
            with patch.object(user_service, 'generate_verification_code', return_value="new_code"):
                with patch.object(user_service.temp_storage, 'save_pending_registration'):
                    with patch.object(user_service, 'send_verification_email'):
                        result = user_service.resend_verification_code(email)
        
        assert result is True
    
    def test_resend_verification_code_no_registration(self, user_service):
        with patch.object(user_service.temp_storage, 'get_pending_registration', return_value=None):
            result = user_service.resend_verification_code("nonexistent@example.com")
        
        assert result is False