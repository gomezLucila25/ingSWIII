from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Header
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import os

from database import get_db
from schemas import UserResponse, CandidatoCreate, EmpresaCreate, UserUpdate, Token, UserLogin
from services import UserService
from auth import create_access_token, get_current_user
from models import User, GenderEnum, UserRoleEnum, CompanyRecruiter

router = APIRouter()
security = HTTPBearer()

# 🔒 SEGURIDAD: API Key para comunicación interna entre servicios
INTERNAL_API_KEY = os.getenv("INTERNAL_SERVICE_API_KEY", "internal-service-key-change-in-production")

# ✅ HEALTH CHECK ENDPOINT
@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring and CI/CD pipelines"""
    return {
        "status": "healthy",
        "service": "UserAPI",
        "version": "2.0.0"
    }

def verify_internal_api_key(x_internal_api_key: Optional[str] = Header(None)):
    """Verifica que la API key interna sea válida para comunicación entre servicios"""
    if x_internal_api_key is None or x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="API key interna inválida o faltante"
        )
    return True

# =====================================================
# REGISTRO Y LOGIN
# =====================================================

@router.post("/register-candidato", response_model=UserResponse)
async def register_candidato(
    email: str = Form(...),
    password: str = Form(...),
    nombre: str = Form(...),
    apellido: str = Form(...),
    genero: GenderEnum = Form(...),
    fecha_nacimiento: date = Form(...),
    profile_picture: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Registra candidato directamente sin verificación de email"""
    try:
        password_bytes = password.encode('utf-8')[:72]
        password_truncated = password_bytes.decode('utf-8', errors='ignore')

        candidato_create = CandidatoCreate(
            email=email,
            password=password_truncated,
            nombre=nombre,
            apellido=apellido,
            genero=genero,
            fecha_nacimiento=fecha_nacimiento
        )

        user_service = UserService(db)
        user = user_service.create_candidato_simple(candidato_create, profile_picture)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar candidato: {str(e)}"
        )

@router.post("/register-empresa", response_model=UserResponse)
async def register_empresa(
    email: str = Form(...),
    password: str = Form(...),
    nombre: str = Form(...),
    descripcion: str = Form(...),
    profile_picture: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Registra empresa directamente sin verificación de email"""
    try:
        password_bytes = password.encode('utf-8')[:72]
        password_truncated = password_bytes.decode('utf-8', errors='ignore')

        empresa_create = EmpresaCreate(
            email=email,
            password=password_truncated,
            nombre=nombre,
            descripcion=descripcion
        )

        user_service = UserService(db)
        user = user_service.create_empresa_simple(empresa_create, profile_picture)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar empresa: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """Autentica usuario y retorna JWT token"""
    user_service = UserService(db)
    user = user_service.authenticate_user(user_login.email, user_login.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

# =====================================================
# PERFIL DE USUARIO
# =====================================================

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Obtiene el perfil del usuario autenticado"""
    return current_user

@router.put("/me/candidato", response_model=UserResponse)
async def update_candidato_profile(
    nombre: Optional[str] = Form(None),
    apellido: Optional[str] = Form(None),
    genero: Optional[GenderEnum] = Form(None),
    fecha_nacimiento: Optional[date] = Form(None),
    profile_picture: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza perfil de candidato"""
    if current_user.role != UserRoleEnum.candidato:
        raise HTTPException(status_code=403, detail="Solo candidatos pueden usar este endpoint")

    user_service = UserService(db)
    user_update = UserUpdate(
        nombre=nombre,
        apellido=apellido,
        genero=genero,
        fecha_nacimiento=fecha_nacimiento
    )

    return user_service.update_user(current_user.id, user_update, profile_picture=profile_picture)

@router.put("/me/empresa", response_model=UserResponse)
async def update_empresa_profile(
    nombre: Optional[str] = Form(None),
    descripcion: Optional[str] = Form(None),
    profile_picture: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza perfil de empresa"""
    if current_user.role != UserRoleEnum.empresa:
        raise HTTPException(status_code=403, detail="Solo empresas pueden usar este endpoint")

    user_service = UserService(db)
    user_update = UserUpdate(nombre=nombre, descripcion=descripcion)

    return user_service.update_user(current_user.id, user_update, profile_picture=profile_picture)

# =====================================================
# ENDPOINTS ADMIN
# =====================================================

@router.get("/admin/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene todos los usuarios (solo admin)"""
    if current_user.role != UserRoleEnum.admin:
        raise HTTPException(status_code=403, detail="Solo administradores")

    user_service = UserService(db)
    return user_service.get_all_users(skip, limit)

@router.get("/admin/candidates", response_model=List[UserResponse])
async def get_all_candidates(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene todos los candidatos (solo admin)"""
    if current_user.role != UserRoleEnum.admin:
        raise HTTPException(status_code=403, detail="Solo administradores")

    user_service = UserService(db)
    return user_service.get_all_candidates(skip, limit)

# =====================================================
# GESTIÓN DE RECRUITERS
# =====================================================

@router.post("/companies/add-recruiter")
async def add_recruiter_to_company(
    recruiter_email: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Asigna un recruiter a una empresa (solo empresas)"""
    if current_user.role != UserRoleEnum.empresa:
        raise HTTPException(status_code=403, detail="Solo empresas pueden asignar recruiters")

    # Buscar al recruiter por email
    recruiter = db.query(User).filter(User.email == recruiter_email).first()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter no encontrado")

    if recruiter.role != UserRoleEnum.candidato:
        raise HTTPException(status_code=400, detail="Solo candidatos pueden ser recruiters")

    # Verificar si ya existe la relación
    existing = db.query(CompanyRecruiter).filter(
        CompanyRecruiter.company_id == current_user.id,
        CompanyRecruiter.recruiter_id == recruiter.id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Este recruiter ya está asignado a tu empresa")

    # Crear relación
    new_relation = CompanyRecruiter(
        company_id=current_user.id,
        recruiter_id=recruiter.id
    )
    db.add(new_relation)
    db.commit()

    return {"message": f"Recruiter {recruiter_email} asignado exitosamente"}

@router.get("/companies/my-recruiters")
async def get_my_recruiters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene todos los recruiters de una empresa"""
    if current_user.role != UserRoleEnum.empresa:
        raise HTTPException(status_code=403, detail="Solo empresas")

    relations = db.query(CompanyRecruiter).filter(
        CompanyRecruiter.company_id == current_user.id,
        CompanyRecruiter.is_active == True
    ).all()

    recruiters = []
    for rel in relations:
        recruiter = db.query(User).filter(User.id == rel.recruiter_id).first()
        if recruiter:
            recruiters.append({
                "id": recruiter.id,
                "email": recruiter.email,
                "nombre": recruiter.nombre,
                "apellido": recruiter.apellido,
                "assigned_at": rel.assigned_at
            })

    return {"recruiters": recruiters}

@router.delete("/companies/remove-recruiter")
async def remove_recruiter_from_company(
    recruiter_email: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elimina un recruiter de una empresa"""
    if current_user.role != UserRoleEnum.empresa:
        raise HTTPException(status_code=403, detail="Solo empresas")

    # Buscar el recruiter por email
    recruiter = db.query(User).filter(User.email == recruiter_email).first()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter no encontrado")

    relation = db.query(CompanyRecruiter).filter(
        CompanyRecruiter.company_id == current_user.id,
        CompanyRecruiter.recruiter_id == recruiter.id
    ).first()

    if not relation:
        raise HTTPException(status_code=404, detail="Relación no encontrada")

    db.delete(relation)
    db.commit()

    return {"message": "Recruiter eliminado exitosamente"}

@router.get("/me/recruiting-for")
async def get_recruiting_for(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene las empresas para las que el usuario es recruiter"""
    relations = db.query(CompanyRecruiter).filter(
        CompanyRecruiter.recruiter_id == current_user.id,
        CompanyRecruiter.is_active == True
    ).all()

    companies = []
    for rel in relations:
        company = db.query(User).filter(User.id == rel.company_id).first()
        if company:
            companies.append({
                "id": company.id,
                "email": company.email,
                "nombre": company.nombre,
                "descripcion": company.descripcion,
                "assigned_at": rel.assigned_at
            })

    return {"companies": companies}

@router.delete("/me/resign-from-company/{company_id}")
async def resign_from_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Permite a un recruiter renunciar de una empresa"""
    # Buscar la relación
    relation = db.query(CompanyRecruiter).filter(
        CompanyRecruiter.company_id == company_id,
        CompanyRecruiter.recruiter_id == current_user.id
    ).first()

    if not relation:
        raise HTTPException(status_code=404, detail="No eres recruiter de esta empresa")

    db.delete(relation)
    db.commit()

    return {"message": "Has renunciado exitosamente como recruiter"}

# =====================================================
# ENDPOINT INTERNO (Para JobsAPI y otros servicios)
# =====================================================

@router.get("/internal/users/{user_id}", response_model=UserResponse)
async def get_user_internal(
    user_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_internal_api_key)
):
    """
    Endpoint interno para que otros servicios obtengan datos de usuario
    Requiere API key interna en header X-Internal-Api-Key
    """
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    return user
