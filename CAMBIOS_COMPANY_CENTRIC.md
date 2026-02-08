# 🎯 Resumen de Cambios: Sistema Company-Centric

## 📋 Descripción General

Se ha migrado el sistema de gestión de ofertas de **recruiter-centric** a **company-centric**, donde:
- ✅ Las empresas son propietarias principales de sus ofertas
- ✅ Los recruiters son colaboradores opcionales que pueden ser asignados/reasignados
- ✅ Si un recruiter deja la empresa, las ofertas permanecen bajo control de la empresa
- ✅ Las empresas pueden ver y gestionar todas sus ofertas desde el panel de administración
- ✅ Las empresas pueden asignar/desasignar recruiters a ofertas específicas

---

## 🔧 Cambios Implementados

### **1. BASE DE DATOS - JobsAPI/models.py**

#### **Nuevo Modelo: JobRecruiter**
```python
class JobRecruiter(Base):
    __tablename__ = "job_recruiters"
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    recruiter_id = Column(Integer, primary_key=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    is_primary = Column(Boolean, default=False)
```

#### **Modificaciones en Job Model**
- `recruiter_id` ahora es **nullable** (antes era NOT NULL)
- Marcado como DEPRECATED (para mantener compatibilidad)
- Nueva relación: `assigned_recruiters` → JobRecruiter

#### **Migración Ejecutada** ✅
- Tabla `job_recruiters` creada
- Datos existentes migrados (4 ofertas → 4 asignaciones)
- Campo `jobs.recruiter_id` convertido a nullable
- Script: `APIs/JobsAPI/migration_company_centric.py`

---

### **2. AUTENTICACIÓN Y PERMISOS - JobsAPI/auth.py**

#### **Clase CurrentUser Mejorada**
- Nuevo atributo: `is_company` (True si el usuario es empresa)

#### **Función get_current_user()**
- Ahora soporta role="empresa"
- Las empresas se gestionan a sí mismas: `company_ids = [user_id]`

#### **Nueva Función: verify_can_manage_jobs()**
Reemplaza a `verify_is_recruiter` en la mayoría de endpoints.
- Permite acceso a empresas Y recruiters
- Las empresas gestionan solo sus ofertas
- Los recruiters gestionan ofertas de empresas asignadas

#### **Nueva Función: verify_job_access()**
Verifica permisos granulares sobre una oferta específica.

---

### **3. SERVICIOS - JobsAPI/services.py**

#### **JobService - Funciones Modificadas**

**create_job():**
- Nuevo parámetro: `is_company`
- Si es empresa: `recruiter_id = None`
- Si es recruiter: crea entrada en `JobRecruiter` automáticamente

**update_job(), delete_job():**
- Nuevos parámetros: `is_company`
- Validación diferenciada empresa vs recruiter

**get_user_jobs()** (NUEVO):
- Reemplaza `get_recruiter_jobs`
- Filtra según role:
  - Empresa: `company_id == user_id`
  - Recruiter: `company_id IN user_companies`

#### **JobService - Funciones Nuevas**

1. **assign_recruiters_to_job()**
   - Asigna múltiples recruiters a una oferta
   - Solo accesible por la empresa propietaria
   - Valida que recruiters pertenezcan a la empresa

2. **get_job_recruiters()**
   - Obtiene lista de recruiters asignados a una oferta
   - Incluye fecha de asignación y si es primario

3. **remove_recruiter_from_job()**
   - Desasigna un recruiter específico
   - Solo accesible por la empresa propietaria

#### **ApplicationService - Funciones Modificadas**

- `get_job_applications()`: Soporta empresas y recruiters
- `update_application_status()`: Validación diferenciada por rol

---

### **4. ENDPOINTS - JobsAPI/routes.py**

#### **Endpoints Modificados**

Todos ahora usan `verify_can_manage_jobs()` en lugar de `verify_is_recruiter()`:

- `POST /jobs` → Empresas y recruiters pueden crear
- `GET /my-jobs` → Usa `get_user_jobs()` internamente
- `PUT /jobs/{job_id}` → Permisos diferenciados
- `DELETE /jobs/{job_id}` → Permisos diferenciados
- `GET /jobs/{job_id}/applications` → Empresas y recruiters
- `PUT /applications/{application_id}` → Empresas y recruiters
- `PUT /applications/{application_id}/status` → Empresas y recruiters
- `PUT /applications/{application_id}/notes` → Empresas y recruiters

#### **Endpoints Nuevos**

1. **GET /jobs/{job_id}/recruiters**
   - Obtiene recruiters asignados a una oferta
   - Enriquecido con datos de UserAPI
   - Accesible por empresa o recruiter con acceso

2. **PUT /jobs/{job_id}/recruiters**
   - Asigna/reasigna recruiters a una oferta
   - **Solo empresas** (no recruiters)
   - Valida que recruiters pertenezcan a la empresa

3. **DELETE /jobs/{job_id}/recruiters/{recruiter_id}**
   - Desasigna un recruiter de una oferta
   - **Solo empresas** (no recruiters)

---

### **5. USERAPI - Nuevo Endpoint**

**GET /api/v1/companies/{company_id}/recruiters**
- Obtiene lista de recruiters activos de una empresa
- Usado por JobsAPI para validar asignaciones
- Endpoint público (sin autenticación)

---

### **6. FRONTEND - jobs.service.ts**

#### **Nuevos Métodos**

```typescript
getJobRecruiters(jobId: number): Observable<any[]>
assignRecruiters(jobId: number, recruiterIds: number[]): Observable<any>
removeRecruiterFromJob(jobId: number, recruiterId: number): Observable<any>
getCompanyRecruiters(companyId: number): Observable<any[]>
```

---

### **7. FRONTEND - header.component.ts**

#### **Nueva Variable: canManageJobs**
- `true` si el usuario es empresa O recruiter
- Reemplaza lógica basada solo en `isRecruiter`

#### **Lógica Actualizada en loadUserData()**
```typescript
if (role === 'empresa') {
  canManageJobs = true;
} else if (role === 'candidato') {
  canManageJobs = isRecruiter;
}
```

#### **Template HTML Actualizado**
- Botón "Administrador de Ofertas" visible para empresas Y recruiters
- Condición: `*ngIf="canManageJobs && !isJobOpeningAdminPage && !isAdmin"`

---

### **8. FRONTEND - job-opening-administrator.component**

**Nota:** El componente existente YA FUNCIONA para empresas sin modificaciones adicionales porque:
- Usa `getMyJobs()` que ahora funciona para empresas
- Usa `createJob()`, `updateJob()`, `deleteJob()` que ahora soportan empresas
- El backend maneja la lógica diferenciada automáticamente

**Próximas mejoras sugeridas:**
- Añadir columna "Recruiters Asignados" en la tabla de ofertas
- Modal para asignar/desasignar recruiters (solo visible para empresas)
- Ocultar selector de empresa para usuarios empresa (solo tienen una)

---

## 🚀 Instrucciones de Prueba

### **1. Reiniciar APIs**

```bash
cd /home/franco/Desktop/TrabajoFinal/APIs
./stop_apis.sh  # Si están corriendo
./start_apis.sh
```

### **2. Verificar Migración**

```bash
cd /home/franco/Desktop/TrabajoFinal/APIs/JobsAPI
source venv/bin/activate
python migration_company_centric.py
```

Debe mostrar:
```
✅ Migration completed successfully!
```

### **3. Pruebas Manuales**

#### **A) Como Empresa:**

1. **Login como empresa**
   - Ir a `/login`
   - Ingresar credenciales de empresa

2. **Verificar acceso al header**
   - ✅ Debe aparecer "Administrador de Ofertas"

3. **Acceder a /job-opening-administrator**
   - ✅ Debe mostrar ofertas de la empresa
   - ✅ Puede crear nueva oferta (sin selector de empresa)
   - ✅ Puede editar ofertas existentes
   - ✅ Puede eliminar ofertas
   - ✅ Puede ver aplicaciones

4. **Probar crear oferta**
   - Completar formulario
   - ✅ Se crea con `company_id = empresa_id`
   - ✅ No se asigna `recruiter_id` inicial

#### **B) Como Recruiter:**

1. **Login como recruiter** (candidato asignado a empresas)
   - Ir a `/login`
   - Ingresar credenciales de recruiter

2. **Verificar acceso**
   - ✅ Debe aparecer "Administrador de Ofertas"

3. **Acceder a /job-opening-administrator**
   - ✅ Debe mostrar ofertas de TODAS las empresas asignadas
   - ✅ Puede crear oferta seleccionando empresa
   - ✅ Puede editar/eliminar ofertas de sus empresas

#### **C) Pruebas de Permisos:**

1. **Empresa intenta editar oferta de otra empresa**
   - ❌ Debe devolver 403 Forbidden

2. **Recruiter intenta editar oferta de empresa no asignada**
   - ❌ Debe devolver 403 Forbidden

3. **Recruiter intenta asignar otro recruiter**
   - ❌ Debe devolver 403 (solo empresas)

---

## 📊 Endpoints API - Resumen

### **Jobs Management**

| Método | Endpoint | Acceso | Descripción |
|--------|----------|--------|-------------|
| POST | `/jobs` | Empresa + Recruiter | Crear oferta |
| GET | `/my-jobs` | Empresa + Recruiter | Mis ofertas |
| GET | `/jobs/{id}` | Público | Ver oferta |
| PUT | `/jobs/{id}` | Empresa + Recruiter | Editar oferta |
| DELETE | `/jobs/{id}` | Empresa + Recruiter | Eliminar oferta |

### **Recruiter Management (Nuevo)**

| Método | Endpoint | Acceso | Descripción |
|--------|----------|--------|-------------|
| GET | `/jobs/{id}/recruiters` | Empresa + Recruiter | Ver recruiters asignados |
| PUT | `/jobs/{id}/recruiters` | **Solo Empresa** | Asignar recruiters |
| DELETE | `/jobs/{id}/recruiters/{rid}` | **Solo Empresa** | Desasignar recruiter |

### **Applications**

| Método | Endpoint | Acceso | Descripción |
|--------|----------|--------|-------------|
| GET | `/jobs/{id}/applications` | Empresa + Recruiter | Ver aplicaciones |
| PUT | `/applications/{id}/status` | Empresa + Recruiter | Actualizar estado |
| PUT | `/applications/{id}/notes` | Empresa + Recruiter | Actualizar notas |

---

## 🐛 Troubleshooting

### **Problema: "No puedes editar ofertas de otras empresas"**
**Solución:** Verificar que el usuario tiene acceso a la empresa de la oferta.

### **Problema: "Administrador de Ofertas no aparece en header"**
**Solución:**
1. Verificar que el usuario es empresa O recruiter
2. Abrir consola del navegador: debe mostrar `canManageJobs: true`

### **Problema: "Recruiter {id} is not assigned to your company"**
**Solución:** Verificar que el recruiter está en la tabla `company_recruiters` con `is_active = true`

---

## 🔄 Rollback (si es necesario)

```bash
cd /home/franco/Desktop/TrabajoFinal/APIs/JobsAPI
source venv/bin/activate
python migration_company_centric.py rollback
```

⚠️ **ADVERTENCIA:** Esto eliminará la tabla `job_recruiters` y revertirá `recruiter_id` a NOT NULL.

---

## ✅ Checklist de Implementación

- [x] Modelo JobRecruiter creado
- [x] Migración de base de datos ejecutada
- [x] Auth actualizado (verify_can_manage_jobs)
- [x] Services actualizados (create, update, delete, get_user_jobs)
- [x] Nuevas funciones de asignación de recruiters
- [x] Endpoints modificados para soportar empresas
- [x] 3 endpoints nuevos para gestión de recruiters
- [x] Endpoint en UserAPI para obtener recruiters
- [x] jobs.service.ts con 4 nuevos métodos
- [x] Header actualizado para mostrar opción a empresas
- [x] job-opening-administrator compatible con empresas
- [ ] **Pendiente:** UI para asignar/desasignar recruiters (próxima iteración)

---

## 📝 Notas Adicionales

1. **Compatibilidad hacia atrás:** El campo `recruiter_id` en `jobs` se mantiene por compatibilidad, pero está marcado como DEPRECATED.

2. **Próximas mejoras sugeridas:**
   - Modal de asignación de recruiters en job-opening-administrator
   - Columna "Recruiters" en tabla de ofertas (solo para empresas)
   - Filtros por recruiter asignado
   - Notificaciones cuando se asigna/desasigna un recruiter

3. **Seguridad:**
   - Validación IDOR implementada
   - Solo empresas pueden asignar/desasignar recruiters
   - Recruiters no pueden modificar asignaciones

---

**Fecha de implementación:** 2025-10-29
**Migración ejecutada:** ✅ Exitosa (4 jobs migrados)
**APIs funcionando:** ✅ JobsAPI, UserAPI, CvAnalyzerAPI
**Frontend actualizado:** ✅ Header y services
