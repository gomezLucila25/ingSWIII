from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from models import GenderEnum, UserRoleEnum

# =====================================================
# SCHEMAS PARA CREACIÓN DE USUARIOS
# =====================================================

class UserBase(BaseModel):
    email: str
    nombre: str
    role: UserRoleEnum

class CandidatoCreate(UserBase):
    password: str
    apellido: str
    genero: GenderEnum
    fecha_nacimiento: date
    role: UserRoleEnum = UserRoleEnum.candidato

class EmpresaCreate(UserBase):
    password: str
    descripcion: str
    role: UserRoleEnum = UserRoleEnum.empresa

# =====================================================
# SCHEMAS PARA RESPUESTAS
# =====================================================

class UserResponse(BaseModel):
    id: int
    email: str
    nombre: str
    role: UserRoleEnum
    verified: bool = Field(validation_alias='email_verified')
    profile_picture: Optional[str] = None
    # Campos opcionales según el rol
    apellido: Optional[str] = None
    genero: Optional[GenderEnum] = None
    fecha_nacimiento: Optional[date] = None
    descripcion: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# =====================================================
# SCHEMAS PARA ACTUALIZACIÓN
# =====================================================

class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    genero: Optional[GenderEnum] = None
    fecha_nacimiento: Optional[date] = None
    descripcion: Optional[str] = None

# =====================================================
# SCHEMAS PARA AUTENTICACIÓN
# =====================================================

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None
