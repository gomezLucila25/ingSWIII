import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os
from main import app
from database import Base, get_db


@pytest.fixture
def test_db():
    db_fd, db_path = tempfile.mkstemp()
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal
    
    os.close(db_fd)
    os.unlink(db_path)
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    return TestClient(app)


class TestMainEndpoints:
    
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "UserAPI está funcionando correctamente" in data["message"]
        assert data["version"] == "1.0.0"
        assert "features" in data
    
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["email_verification"] == "enabled"
        assert data["temporal_storage"] == "enabled"
        assert data["cv_analyzer"] == "enabled"
    
    def test_cors_headers(self, client):
        response = client.options("/", headers={"Origin": "http://localhost:4200"})
        assert response.status_code == 200


class TestStaticFileServing:
    
    def test_uploaded_cvs_mount(self, client):
        # Test that the route exists (even if no files)
        response = client.get("/uploaded_cvs/")
        # Should return 404 for directory listing, not 500
        assert response.status_code in [404, 405]
    
    def test_profile_pictures_mount(self, client):
        response = client.get("/profile_pictures/")
        assert response.status_code in [404, 405]


class TestDirectoryCreation:
    
    def test_required_directories_created(self, client, tmp_path):
        # Test that the app creates required directories
        # This is tested indirectly through app initialization
        directories = [
            "uploaded_cvs",
            "profile_pictures", 
            "temp_files",
            "temp_registrations"
        ]
        
        for directory in directories:
            # Directory should exist after app starts
            assert os.path.exists(directory)


class TestDatabaseIntegration:
    
    def test_database_tables_creation(self, test_db):
        db = test_db()
        from models import User, CompanyRecruiter
        
        # Should not raise any errors
        db.query(User).count()
        db.query(CompanyRecruiter).count()
        db.close()
    
    def test_api_prefix_routes(self, client):
        # Test that API routes are properly prefixed
        protected_routes = [
            "/api/v1/me",
            "/api/v1/users",
            "/api/v1/register-candidato",
            "/api/v1/register-empresa"
        ]
        
        for route in protected_routes:
            response = client.get(route) if route == "/api/v1/me" else client.post(route)
            # Should not return 404 (route exists)
            assert response.status_code != 404


class TestAppConfiguration:
    
    def test_app_metadata(self):
        assert app.title == "UserAPI"
        assert app.version == "1.0.0"
        assert "autenticación JWT" in app.description
    
    def test_cors_middleware_configured(self, client):
        response = client.get("/")
        # CORS should be configured
        assert response.status_code == 200
    
    def test_static_files_configured(self):
        # Test that static files are mounted
        routes = [str(route) for route in app.routes]
        mounted_paths = [route for route in routes if "uploaded_cvs" in route or "profile_pictures" in route]
        assert len(mounted_paths) >= 2


class TestEnvironmentSetup:
    
    def test_environment_variables_handling(self, monkeypatch):
        # Test without environment variables
        monkeypatch.delenv("EMAIL_USER", raising=False)
        monkeypatch.delenv("EMAIL_PASSWORD", raising=False)
        
        # App should still start without email config
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200


class TestErrorHandling:
    
    def test_route_not_found(self, client):
        response = client.get("/nonexistent-route")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        response = client.patch("/")  # PATCH not allowed on root
        assert response.status_code == 405


class TestAPIRoutes:
    
    def test_register_candidato_structure(self, client):
        # Test that route exists and expects form data
        response = client.post("/api/v1/register-candidato")
        # Should return 422 (validation error) not 404
        assert response.status_code == 422
    
    def test_register_empresa_structure(self, client):
        response = client.post("/api/v1/register-empresa")
        assert response.status_code == 422
    
    def test_login_structure(self, client):
        response = client.post("/api/v1/login")
        assert response.status_code == 422
    
    def test_complete_registration_structure(self, client):
        response = client.post("/api/v1/complete-registration")
        assert response.status_code == 422


class TestAuthenticationFlow:
    
    def test_protected_routes_require_auth(self, client):
        # Test that protected routes require authentication
        protected_routes = [
            "/api/v1/me",
            "/api/v1/users",
            "/api/v1/me/candidato",
            "/api/v1/me/empresa"
        ]
        
        for route in protected_routes:
            response = client.get(route)
            # Should return 401/403 (unauthorized), not 404
            assert response.status_code in [401, 403, 422]
    
    def test_public_routes_accessible(self, client):
        public_routes = [
            ("/", "GET"),
            ("/health", "GET"),
            ("/api/v1/register-candidato", "POST"),
            ("/api/v1/register-empresa", "POST"),
            ("/api/v1/login", "POST")
        ]
        
        for route, method in public_routes:
            if method == "GET":
                response = client.get(route)
            else:
                response = client.post(route)
            
            # Should not return 404 (route exists)
            assert response.status_code != 404


class TestTemporaryStorageEndpoints:
    
    def test_verify_email_endpoint(self, client):
        response = client.post("/api/v1/verify-email")
        assert response.status_code == 422  # Missing form data
    
    def test_resend_verification_endpoint(self, client):
        response = client.post("/api/v1/resend-verification")
        assert response.status_code == 422


class TestAdminEndpoints:
    
    def test_admin_routes_exist(self, client):
        admin_routes = [
            "/api/v1/admin/companies/pending",
            "/api/v1/admin/companies/verify",
            "/api/v1/admin/users"
        ]
        
        for route in admin_routes:
            response = client.get(route)
            # Should require auth (401/403), not 404
            assert response.status_code in [401, 403, 422]


class TestDeprecatedEndpoints:
    
    def test_deprecated_register_endpoint(self, client):
        response = client.post("/api/v1/register")
        assert response.status_code == 410  # Gone
        data = response.json()
        assert "deshabilitado" in data["detail"]


class TestCompanyManagementEndpoints:
    
    def test_recruiter_management_routes(self, client):
        routes = [
            "/api/v1/companies/add-recruiter",
            "/api/v1/companies/my-recruiters",
            "/api/v1/me/recruiting-for"
        ]
        
        for route in routes:
            if "add-recruiter" in route:
                response = client.post(route)
            else:
                response = client.get(route)
            
            # Should require auth, not 404
            assert response.status_code in [401, 403, 422]


class TestFileHandling:
    
    def test_file_upload_endpoints_structure(self, client):
        # Test endpoints that expect file uploads
        file_routes = [
            "/api/v1/register-candidato",
            "/api/v1/me/candidato",
            "/api/v1/me/empresa"
        ]
        
        for route in file_routes:
            response = client.post(route)
            # Should expect form data with files
            assert response.status_code == 422


class TestSpecialCases:
    
    def test_users_by_id_public_access(self, client):
        # This endpoint should be public (for JobsAPI integration)
        response = client.get("/api/v1/users/1")
        # Should return 404 (user not found) not 401 (unauthorized)
        assert response.status_code == 404