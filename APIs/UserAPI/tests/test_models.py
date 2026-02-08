import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
import tempfile
import os
from database import Base
from models import User, CompanyRecruiter, GenderEnum, UserRoleEnum


@pytest.fixture
def test_db():
    db_fd, db_path = tempfile.mkstemp()
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    
    yield TestingSessionLocal
    
    os.close(db_fd)
    os.unlink(db_path)


class TestUserModel:
    
    def test_create_candidato_minimal(self, test_db):
        db = test_db()
        
        user = User(
            email="test@example.com",
            hashed_password="hashed_password_123",
            role=UserRoleEnum.candidato,
            nombre="Juan",
            apellido="Pérez"
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.role == UserRoleEnum.candidato
        assert user.nombre == "Juan"
        assert user.apellido == "Pérez"
        assert user.verified == False  # Default
        assert user.email_verified == False  # Default
        assert user.created_at is not None
        
        db.close()
    
    def test_create_candidato_complete(self, test_db):
        db = test_db()
        
        birth_date = date(1990, 1, 15)
        cv_analysis = {
            "experiencia": [{"puesto": "Developer", "empresa": "Tech Corp"}],
            "habilidades_tecnicas": ["Python", "JavaScript"]
        }
        
        user = User(
            email="candidate@example.com",
            hashed_password="hashed_password_123",
            role=UserRoleEnum.candidato,
            nombre="María",
            apellido="González",
            genero=GenderEnum.femenino,
            fecha_nacimiento=birth_date,
            cv_filename="cv_123.pdf",
            cv_analizado=cv_analysis,
            profile_picture="profile_123.jpg",
            verified=True,
            email_verified=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.genero == GenderEnum.femenino
        assert user.fecha_nacimiento == birth_date
        assert user.cv_filename == "cv_123.pdf"
        assert user.cv_analizado == cv_analysis
        assert user.profile_picture == "profile_123.jpg"
        assert user.verified == True
        assert user.email_verified == True
        
        db.close()
    
    def test_create_empresa(self, test_db):
        db = test_db()
        
        user = User(
            email="company@example.com",
            hashed_password="hashed_password_123",
            role=UserRoleEnum.empresa,
            nombre="Tech Company SA",
            descripcion="Empresa líder en tecnología",
            profile_picture="company_logo.png",
            verified=True,
            email_verified=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.role == UserRoleEnum.empresa
        assert user.nombre == "Tech Company SA"
        assert user.descripcion == "Empresa líder en tecnología"
        assert user.profile_picture == "company_logo.png"
        # Company-specific fields should be None
        assert user.apellido is None
        assert user.genero is None
        assert user.fecha_nacimiento is None
        assert user.cv_filename is None
        assert user.cv_analizado is None
        
        db.close()
    
    def test_create_admin(self, test_db):
        db = test_db()
        
        user = User(
            email="admin@example.com",
            hashed_password="hashed_password_123",
            role=UserRoleEnum.admin,
            nombre="Administrator",
            verified=True,
            email_verified=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.role == UserRoleEnum.admin
        assert user.nombre == "Administrator"
        assert user.verified == True
        # Admin should have None for role-specific fields
        assert user.apellido is None
        assert user.descripcion is None
        assert user.cv_filename is None
        
        db.close()
    
    def test_email_unique_constraint(self, test_db):
        db = test_db()
        
        user1 = User(
            email="duplicate@example.com",
            hashed_password="hash1",
            role=UserRoleEnum.candidato,
            nombre="User1"
        )
        
        user2 = User(
            email="duplicate@example.com",
            hashed_password="hash2",
            role=UserRoleEnum.empresa,
            nombre="User2"
        )
        
        db.add(user1)
        db.commit()
        
        db.add(user2)
        with pytest.raises(Exception):  # Should raise integrity error
            db.commit()
        
        db.close()
    
    def test_verification_code_fields(self, test_db):
        db = test_db()
        
        expires_at = datetime.utcnow()
        
        user = User(
            email="verification@example.com",
            hashed_password="hashed_password_123",
            role=UserRoleEnum.candidato,
            nome="Test",
            verification_code="123456",
            verification_expires=expires_at
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.verification_code == "123456"
        assert user.verification_expires == expires_at
        
        db.close()


class TestCompanyRecruiterModel:
    
    def test_create_company_recruiter_relationship(self, test_db):
        db = test_db()
        
        # Create company
        company = User(
            email="company@example.com",
            hashed_password="hash",
            role=UserRoleEnum.empresa,
            nome="Company"
        )
        
        # Create recruiter (candidato)
        recruiter = User(
            email="recruiter@example.com",
            hashed_password="hash",
            role=UserRoleEnum.candidato,
            nome="Recruiter",
            apellido="Smith"
        )
        
        db.add_all([company, recruiter])
        db.commit()
        db.refresh(company)
        db.refresh(recruiter)
        
        # Create relationship
        relationship = CompanyRecruiter(
            company_id=company.id,
            recruiter_id=recruiter.id,
            is_active=True
        )
        
        db.add(relationship)
        db.commit()
        db.refresh(relationship)
        
        assert relationship.id is not None
        assert relationship.company_id == company.id
        assert relationship.recruiter_id == recruiter.id
        assert relationship.is_active == True
        assert relationship.assigned_at is not None
        
        db.close()
    
    def test_company_recruiter_relationships(self, test_db):
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
            nome="Recruiter",
            apellido="Smith"
        )
        
        db.add_all([company, recruiter])
        db.commit()
        db.refresh(company)
        db.refresh(recruiter)
        
        relationship = CompanyRecruiter(
            company_id=company.id,
            recruiter_id=recruiter.id
        )
        
        db.add(relationship)
        db.commit()
        db.refresh(relationship)
        
        # Test relationships
        assert relationship.company.id == company.id
        assert relationship.recruiter.id == recruiter.id
        assert relationship.company.nome == "Company"
        assert relationship.recruiter.nome == "Recruiter"
        
        db.close()
    
    def test_deactivate_recruiter_relationship(self, test_db):
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
            nome="Recruiter",
            apellido="Smith"
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
        
        # Deactivate
        relationship.is_active = False
        db.commit()
        db.refresh(relationship)
        
        assert relationship.is_active == False
        
        db.close()


class TestEnumValues:
    
    def test_gender_enum_values(self):
        assert GenderEnum.masculino.value == "masculino"
        assert GenderEnum.femenino.value == "femenino"
        assert GenderEnum.otro.value == "otro"
    
    def test_user_role_enum_values(self):
        assert UserRoleEnum.candidato.value == "candidato"
        assert UserRoleEnum.empresa.value == "empresa"
        assert UserRoleEnum.admin.value == "admin"
    
    def test_enum_in_user_model(self, test_db):
        db = test_db()
        
        user = User(
            email="test@example.com",
            hashed_password="hash",
            role=UserRoleEnum.candidato,
            nome="Test",
            genero=GenderEnum.otro
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.role == UserRoleEnum.candidato
        assert user.genero == GenderEnum.otro
        
        db.close()


class TestDefaultValues:
    
    def test_user_default_values(self, test_db):
        db = test_db()
        
        user = User(
            email="defaults@example.com",
            hashed_password="hash",
            role=UserRoleEnum.candidato,
            nome="Default User"
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Test default values
        assert user.verified == False
        assert user.email_verified == False
        assert user.created_at is not None
        assert user.verification_code is None
        assert user.verification_expires is None
        
        db.close()
    
    def test_company_recruiter_defaults(self, test_db):
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
            recruiter_id=recruiter.id
        )
        
        db.add(relationship)
        db.commit()
        db.refresh(relationship)
        
        # Test defaults
        assert relationship.is_active == True
        assert relationship.assigned_at is not None
        
        db.close()


class TestJSONFields:
    
    def test_cv_analizado_json_field(self, test_db):
        db = test_db()
        
        cv_data = {
            "experiencia": [
                {
                    "puesto": "Senior Developer",
                    "empresa": "Tech Corp",
                    "funciones": "Lead development team",
                    "años_experiencia": "3"
                }
            ],
            "educacion": [
                {
                    "titulo": "Computer Science",
                    "institucion": "Universidad",
                    "certificaciones": ["AWS", "Google Cloud"]
                }
            ],
            "habilidades_tecnicas": ["Python", "JavaScript", "React", "Django"],
            "habilidades_blandas": ["Leadership", "Communication"],
            "nivel_dominio": {"Python": "Advanced", "JavaScript": "Intermediate"},
            "idiomas": [{"idioma": "English", "nivel": "Fluent"}],
            "ubicacion_actual": {"pais": "Argentina", "provincia": "Córdoba", "ciudad": "Córdoba"}
        }
        
        user = User(
            email="json_test@example.com",
            hashed_password="hash",
            role=UserRoleEnum.candidato,
            nome="JSON Tester",
            cv_analizado=cv_data
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Test that JSON is stored and retrieved correctly
        assert user.cv_analizado == cv_data
        assert user.cv_analizado["experiencia"][0]["puesto"] == "Senior Developer"
        assert "Python" in user.cv_analizado["habilidades_tecnicas"]
        assert user.cv_analizado["nivel_dominio"]["Python"] == "Advanced"
        
        db.close()
    
    def test_empty_cv_analizado(self, test_db):
        db = test_db()
        
        user = User(
            email="empty_cv@example.com",
            hashed_password="hash",
            role=UserRoleEnum.candidato,
            nome="Empty CV User",
            cv_analizado={}
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.cv_analizado == {}
        
        db.close()


class TestConstraintsAndValidation:
    
    def test_required_fields(self, test_db):
        db = test_db()
        
        # Test missing required fields
        with pytest.raises(Exception):
            user = User(
                hashed_password="hash",  # Missing email
                role=UserRoleEnum.candidato,
                nome="Test"
            )
            db.add(user)
            db.commit()
        
        with pytest.raises(Exception):
            user = User(
                email="test@example.com",
                # Missing hashed_password
                role=UserRoleEnum.candidato,
                nome="Test"
            )
            db.add(user)
            db.commit()
        
        db.close()
    
    def test_foreign_key_constraints(self, test_db):
        db = test_db()
        
        # Try to create CompanyRecruiter with non-existent user IDs
        with pytest.raises(Exception):
            relationship = CompanyRecruiter(
                company_id=999,  # Non-existent
                recruiter_id=888  # Non-existent
            )
            db.add(relationship)
            db.commit()
        
        db.close()


class TestUserRelationships:
    
    def test_user_recruiting_relationships(self, test_db):
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
            recruiter_id=recruiter.id
        )
        
        db.add(relationship)
        db.commit()
        
        # Test back references
        assert len(company.company_recruiters) == 1
        assert len(recruiter.recruiting_for) == 1
        assert company.company_recruiters[0].recruiter_id == recruiter.id
        assert recruiter.recruiting_for[0].company_id == company.id
        
        db.close()


class TestSpecialCharacters:
    
    def test_unicode_text_handling(self, test_db):
        db = test_db()
        
        user = User(
            email="unicode@example.com",
            hashed_password="hash",
            role=UserRoleEnum.candidato,
            nome="José María",
            apellido="González-Núñez",
            descripcion="Descripción con caracteres especiales: áéíóú ñ ç"
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.nome == "José María"
        assert user.apellido == "González-Núñez"
        assert "áéíóú" in user.descripcion
        
        db.close()
    
    def test_special_email_formats(self, test_db):
        db = test_db()
        
        special_emails = [
            "user+tag@example.com",
            "user.name@sub.domain.com",
            "user-name@example-domain.co.uk"
        ]
        
        for email in special_emails:
            user = User(
                email=email,
                hashed_password="hash",
                role=UserRoleEnum.candidato,
                nome="Test User"
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            assert user.email == email
            
            # Clean up for next iteration
            db.delete(user)
            db.commit()
        
        db.close()