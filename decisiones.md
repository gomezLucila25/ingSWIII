# Decisiones Técnicas - TP5/TP6 Final Ingeniería de Software 3

## Índice
1. [Arquitectura General](#arquitectura-general)
2. [Simplificaciones para Entorno Académico](#simplificaciones-para-entorno-académico)
3. [Plataforma Cloud](#plataforma-cloud)
4. [Pipeline CI/CD](#pipeline-cicd)
5. [Testing y Code Coverage (TP6)](#testing-y-code-coverage-tp6)
6. [Ambientes](#ambientes)
7. [Base de Datos](#base-de-datos)
8. [Seguridad](#seguridad)
9. [Monitoreo](#monitoreo)

---

## Arquitectura General

### Decisión: Arquitectura de Microservicios Simplificada
**Contexto**: El proyecto original contiene 5 microservicios (UserAPI, CvAnalyzerAPI, JobsAPI, MatcheoAPI, AssistantAPI) y un frontend Angular.

**Decisión**: Para el TP5, se decidió desplegar únicamente **UserAPI + Frontend** por las siguientes razones:
- Fines académicos: Demostrar el pipeline CI/CD completo sin complejidad innecesaria
- Reducción de costos en Google Cloud
- UserAPI es el servicio core que contiene toda la lógica de autenticación y gestión de usuarios
- Permite demostrar los conceptos de DevOps sin sobrecarga operativa

**Consecuencias**:
- ✅ Despliegue más rápido y económico
- ✅ Pipeline CI/CD más simple de mantener
- ✅ Enfoque en calidad sobre cantidad
- ⚠️ Funcionalidad reducida (sin análisis de CV, matching, ni asistente de IA)

---

## Simplificaciones para Entorno Académico

### Decisión: Eliminar Verificación de Email
**Contexto**: El sistema original requería verificación de email con código de 6 dígitos enviado por SMTP.

**Decisión**: Eliminar el paso de verificación de email para simplificar el flujo de registro.

**Implementación**:
- Creados métodos `create_candidato_simple()` y `create_empresa_simple()` en `services.py`
- Usuarios creados directamente con `verified=True` y `email_verified=True`
- Eliminadas referencias a `verification_code` y `verification_expires`
- Frontend redirige directamente a login después de registro exitoso

**Justificación**:
- Evita necesidad de configurar servidor SMTP en producción
- Simplifica testing y demostración del TP
- Enfoque en CI/CD, no en funcionalidades de negocio

### Decisión: Eliminar Upload y Análisis de CV
**Contexto**: El sistema original permitía upload de CV en PDF con análisis automático usando Google Gemini 2.0.

**Decisión**: Eliminar completamente el upload y análisis de CV para candidatos.

**Implementación**:
- Removidos campos `cv_file` de formularios y endpoints
- Eliminadas llamadas a `CvAnalyzerAPI`
- Campo `cv_filename` en base de datos se mantiene como `NULL`
- Removida lógica de validación de CV con IA

**Justificación**:
- Reduce dependencias (no se necesita `CvAnalyzerAPI` ni Google Gemini API)
- Simplifica el registro de candidatos
- Reduce costos de almacenamiento y procesamiento
- Permite enfocarse en el pipeline de deployment

---

## Plataforma Cloud

### Decisión: Google Cloud Platform
**Alternativas consideradas**:
- AWS (Amazon Web Services)
- Azure
- Google Cloud Platform ✅

**Razones para elegir GCP**:
1. **Créditos gratuitos**: $300 USD para nuevas cuentas
2. **Cloud Run**: Servicio serverless que escala automáticamente (pay-per-use)
3. **Integración nativa**: Cloud SQL, Secret Manager, Container Registry en un mismo ecosistema
4. **Simplicidad**: Menos configuración que AWS o Azure para casos de uso básicos
5. **Pricing amigable**: Cloud Run solo cobra cuando hay requests activos

**Servicios GCP utilizados**:
- **Cloud Run**: Hosting de contenedores Docker (UserAPI y Frontend)
- **Cloud SQL**: PostgreSQL managed database
- **Secret Manager**: Gestión segura de credenciales y API keys
- **Container Registry (GCR)**: Almacenamiento de imágenes Docker
- **IAM**: Service accounts y permisos

### Decisión: Cloud Run en lugar de Compute Engine o GKE
**Contexto**: GCP ofrece múltiples opciones para hosting:
- Compute Engine (VMs tradicionales)
- Google Kubernetes Engine (GKE)
- Cloud Run ✅

**Razones**:
- **Serverless**: No hay que gestionar servidores ni infraestructura
- **Autoscaling**: Escala automáticamente de 0 a N instancias según demanda
- **Costo**: Solo se paga cuando hay requests (ideal para proyecto académico)
- **Simplicidad**: Deploy directo desde Docker images
- **HTTPS automático**: Certificados SSL/TLS gestionados automáticamente

**Trade-offs**:
- ✅ Menor costo operativo
- ✅ Deploy más rápido
- ⚠️ Menos control sobre infraestructura (no se necesita para este proyecto)
- ⚠️ Cold starts (aceptable para demo académica)

---

## Pipeline CI/CD

### Decisión: GitHub Actions
**Alternativas consideradas**:
- Azure DevOps Pipelines
- GitLab CI/CD
- Jenkins
- GitHub Actions ✅

**Razones**:
1. **Integración nativa**: El código ya está en GitHub
2. **Free tier generoso**: 2000 minutos/mes para cuentas públicas
3. **YAML declarativo**: Fácil de versionar y mantener
4. **Marketplace**: Abundancia de actions pre-construidas
5. **GitHub Environments**: Soporte nativo para ambientes y aprobaciones manuales

### Decisión: Estrategia de Build
**Decisión**: Build separado para QA y Production con imágenes Docker específicas.

**Implementación**:
```yaml
build-frontend-qa:    # Imagen con environment.qa.ts
build-frontend-prod:  # Imagen con environment.prod.ts
```

**Razones**:
- Diferentes URLs de API backend según ambiente
- Inmutabilidad: La imagen QA no es la misma que PROD
- Trazabilidad: Cada imagen tiene configuración explícita

**Alternativas descartadas**:
- ❌ Variables de entorno en runtime: Angular necesita URLs en build time
- ❌ Única imagen para ambos ambientes: No permite diferentes configuraciones

### Decisión: Estrategia de Tags
**Tags aplicados a cada imagen**:
- `{github.sha}`: Commit hash específico (inmutable)
- `latest`: Última versión buildada

**Razones**:
- `{github.sha}` permite rollback exacto a cualquier versión
- `latest` facilita testing manual rápido
- Cada deploy de Cloud Run referencia el SHA específico

### Decisión: Orden de Deployment
**Flujo**:
```
Build UserAPI → Build Frontend QA → Build Frontend PROD
     ↓                ↓                    ↓
Deploy QA UserAPI → Deploy QA Frontend
     ↓ (Aprobación Manual)
Deploy PROD UserAPI → Deploy PROD Frontend
```

**Razones**:
- Backend antes que frontend (evita errores 503)
- QA siempre antes que PROD
- Aprobación manual entre ambientes (requisito TP5)

---

## Testing y Code Coverage (TP6)

### Decisión: Pytest para Backend Testing
**Framework seleccionado**: pytest + pytest-cov

**Razones**:
1. **Estándar de industria** para testing en Python
2. **Fixtures poderosas**: Permite setup/teardown de DB y cliente de testing
3. **Coverage integrado**: pytest-cov proporciona métricas detalladas
4. **AAA Pattern**: Arrange-Act-Assert para tests legibles

**Implementación**:
```python
# tests/test_simplified_api.py
@pytest.fixture(scope="function")
def test_db():
    """Crea una base de datos SQLite en memoria para tests"""
    # Crea DB temporal, sobrescribe dependency, cleanup
```

**Tests creados**:
- Health check (2 tests)
- Registro de candidatos (4 tests)
- Registro de empresas (2 tests)
- Login con JWT (3 tests)
- Endpoints protegidos (2 tests)
- Endpoints obsoletos (1 test)
- Validaciones y edge cases (3 tests)

**Total: 17 tests, 100% passing**

### Decisión: Jasmine/Karma para Frontend Testing
**Framework**: Jasmine + Karma + ChromeHeadless

**Razones**:
1. **Default de Angular**: Configuración out-of-the-box
2. **Browser real**: Tests corren en Chrome para validar comportamiento real
3. **Mocking integrado**: Jasmine spy objects para dependencies
4. **Coverage HTML reports**: Karma genera reportes detallados

**Fixes aplicados**:
- Eliminados tests de métodos inexistentes (`analyzeCv`, `validateCvOnly`)
- Corregidos constructors para usar `TestBed.inject(HttpClient)`
- Tests ahora compilan sin errores TypeScript

### Decisión: Code Coverage como Métrica de Calidad
**Target establecido**:
- **TP6**: 60%+ coverage mínimo
- **TP7**: 70%+ coverage requerido

**Coverage actual del backend**:
```
models.py:    100% ✅
schemas.py:   100% ✅
auth.py:       75%
database.py:   73%
main.py:       67%
services.py:   53% (mejorado desde 16% tras cleanup)
routes.py:     33%
----------------------------
TOTAL:         63% ✅
```

**Estrategia de mejora**:
1. ✅ **Limpieza de código**: Eliminado código no utilizado en `services.py`
   - Reducido de 701 líneas a 363 líneas
   - Removed complex features (email verification, CV upload, recruiter management)
   - Solo funciones utilizadas en la API simplificada
2. **Enfoque en código crítico**: 100% coverage en models y schemas
3. **Tests de integración**: Endpoint tests cubren múltiples capas (routes + services + models)

### Decisión: Integración de Tests en CI/CD
**Implementación en GitHub Actions**:

```yaml
jobs:
  test-backend:
    name: Test Backend (Pytest)
    runs-on: ubuntu-latest
    steps:
      - Set up Python 3.12
      - Install dependencies
      - Run pytest with coverage
      - Upload coverage to Codecov

  test-frontend:
    name: Test Frontend (Angular)
    runs-on: ubuntu-latest
    steps:
      - Set up Node.js 20
      - Install dependencies
      - Run Karma tests with ChromeHeadless
      - Upload coverage to Codecov

  build-userapi:
    needs: test-backend  # ⬅️ Build solo si tests pasan

  build-frontend-qa:
    needs: test-frontend  # ⬅️ Build solo si tests pasan
```

**Razones**:
- ✅ **Tests antes de build**: Evita builddear código roto
- ✅ **Fast fail**: Pipeline falla rápido si tests fallan
- ✅ **Coverage tracking**: Codecov muestra tendencias de cobertura
- ✅ **Quality gates**: No se puede deployar sin tests verdes

### Decisión: Test Database Pattern
**Patrón implementado**: In-memory SQLite para tests

```python
db_fd, db_path = tempfile.mkstemp()
engine = create_engine(f"sqlite:///{db_path}", ...)
TestingSessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)
```

**Razones**:
- ✅ **Aislamiento total**: Cada test tiene DB limpia
- ✅ **Velocidad**: In-memory DB es ~100x más rápido que PostgreSQL
- ✅ **Sin side effects**: Tests no modifican DB de desarrollo
- ✅ **Cleanup automático**: `tempfile.mkstemp()` se limpia solo

**Alternativa descartada**:
- ❌ PostgreSQL de testing: Más lento, requiere setup adicional

### Decisión: AAA Pattern para Legibilidad
**Patrón adoptado**: Arrange-Act-Assert

```python
def test_login_success(self, client):
    """
    GIVEN un usuario registrado
    WHEN hace login con credenciales correctas
    THEN recibe access token válido
    """
    # Arrange: Registrar usuario
    register_data = {...}
    client.post("/api/v1/register-candidato", data=register_data)

    # Act: Login
    login_data = {...}
    response = client.post("/api/v1/login", json=login_data)

    # Assert
    assert response.status_code == 200
    assert "access_token" in response.json()
```

**Razones**:
- ✅ **Legibilidad**: Estructura clara de cada test
- ✅ **Mantenibilidad**: Fácil identificar qué hace cada parte
- ✅ **Documentación**: Docstrings con Given-When-Then
- ✅ **Best practice**: Estándar de industria

### Decisión: Limpieza de Código No Utilizado
**Acción**: Simplificación masiva de `services.py`

**Funciones eliminadas** (no utilizadas en versión simplificada):
- Email verification (`verify_email`, `resend_code`, `complete_registration`)
- CV upload complex (`register_with_cv`, `verify_cv_with_ai`)
- Recruiter management (`add_recruiter`, `remove_recruiter`, `get_recruiters`)
- Complex update flows (`update_with_verification`)
- Temporal storage (`save_temp_registration`, `cleanup_expired_temps`)

**Funciones conservadas** (utilizadas):
- `get_user_by_email`, `get_user_by_id` (queries básicas)
- `get_all_users`, `get_all_candidates`, `get_unverified_companies` (admin)
- `authenticate_user` (login)
- `create_candidato_simple`, `create_empresa_simple` (registro)
- `update_user` (actualización de perfil)
- `verify_company` (admin)
- `_save_profile_picture`, `_save_cv_file` (helpers)

**Impacto**:
- 📉 **De 701 líneas a 363 líneas** (~50% reducción)
- 📈 **Coverage de services.py: 16% → 53%** (mejora de 237%)
- 📈 **Coverage total: 31% → 63%** (mejora de 103%)

**Justificación**:
- Código muerto reduce coverage artificialmente
- Simplificación alinea código con funcionalidad real
- Mantenimiento más fácil (menos código = menos bugs)

### Decisión: ChromeHeadless con --no-sandbox para CI
**Configuración de Karma**:
```javascript
customLaunchers: {
  ChromeHeadlessCI: {
    base: 'ChromeHeadless',
    flags: ['--no-sandbox', '--disable-web-security']
  }
}
```

**Razones**:
- ✅ **CI compatibility**: GitHub Actions no tiene display gráfico
- ✅ **--no-sandbox**: Requerido para contenedores sin privilegios
- ✅ **Headless**: Más rápido que Chrome completo
- ✅ **Real browser**: Catch bugs que tests unitarios pierden

### Resumen de Métricas TP6

| Métrica | Backend (Python) | Frontend (Angular) |
|---------|------------------|---------------------|
| **Framework** | pytest 7.4.3 | Jasmine + Karma |
| **Tests totales** | 17 | ~40+ (auth service) |
| **Tests passing** | 17/17 (100%) | Compilación OK ✅ |
| **Coverage** | 63% | TBD (requiere Chrome) |
| **Archivos con 100%** | models.py, schemas.py | - |
| **Archivo crítico mejorado** | services.py (53%) | auth.service.ts |

**Objetivos cumplidos**:
- ✅ Tests unitarios implementados
- ✅ Coverage >60% en backend
- ✅ Integración en CI/CD pipeline
- ✅ Tests automáticos antes de build
- ✅ Código simplificado y limpio

**Próximos pasos para TP7** (70% coverage):
- Agregar tests para routes.py (actualmente 33%)
- Agregar tests con mocks para services.py
- Completar coverage de auth.py (75% → 90%)

---

## Ambientes

### Decisión: Dos Ambientes (QA + Production)
**Ambientes configurados**:

| Ambiente | UserAPI | Frontend | Base de Datos | Propósito |
|----------|---------|----------|---------------|-----------|
| **QA** | `userapi-qa` | `frontend-qa` | Shared DB | Testing pre-producción |
| **Production** | `userapi` | `frontend` | Shared DB | Usuarios finales |

**Decisión importante**: **Base de datos compartida entre QA y PROD**

**Razones**:
- Simplificación para entorno académico
- Reducción de costos (Cloud SQL cobra por instancia)
- Datos de testing no interfieren con producción (volumen bajo)

**Alternativa ideal para producción real**:
- ✅ Bases de datos separadas por ambiente
- ✅ Datos de QA aislados de producción
- ⚠️ Mayor costo y complejidad operativa

### Decisión: GitHub Environments con Manual Approval
**Configuración**:
```yaml
environment:
  name: qa              # Sin aprobaciones

environment:
  name: production     # Requiere aprobación manual
```

**Razones**:
- Cumple con requisito TP5 de aprobaciones manuales
- Previene deployments accidentales a producción
- Permite validar QA antes de liberar a PROD

**Implementación**:
En GitHub: Settings → Environments → production → Required reviewers

---

## Base de Datos

### Decisión: Cloud SQL PostgreSQL
**Alternativas consideradas**:
- Cloud SQL MySQL
- Cloud Firestore (NoSQL)
- Cloud Spanner
- PostgreSQL en Cloud SQL ✅

**Razones**:
1. **Compatibilidad**: El proyecto usa PostgreSQL con SQLAlchemy
2. **Managed service**: Backups automáticos, updates, alta disponibilidad
3. **Cloud SQL Proxy**: Conexión segura sin necesidad de IP públicas
4. **Costo**: Más económico que Spanner para este volumen de datos

### Decisión: Unix Socket Connection (Cloud SQL Proxy)
**Implementación**:
```python
DATABASE_URL=postgresql://postgres:PASSWORD@/userapi?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
```

**Razones**:
- ✅ Más seguro que conexión por IP pública
- ✅ No requiere configurar VPC o whitelisting de IPs
- ✅ Cloud Run tiene soporte nativo para Cloud SQL Proxy
- ✅ Encriptación automática de conexiones

**Alternativa descartada**:
- ❌ IP pública: Requiere whitelist de IPs, menos seguro, más complejo

### Decisión: Configuración de Instancia
**Specs seleccionadas**:
- **Tier**: `db-f1-micro` (1 vCPU compartido, 614 MB RAM)
- **Storage**: 10 GB SSD
- **Región**: `us-central1` (misma que Cloud Run)

**Razones**:
- Suficiente para proyecto académico y demos
- Costo mínimo (~$10/mes)
- Misma región que Cloud Run = menor latencia

---

## Seguridad

### Decisión: Secret Manager para Credenciales
**Secrets almacenados**:
- `DATABASE_URL`: Connection string de PostgreSQL
- `SECRET_KEY`: JWT secret key
- `EMAIL_USER` y `EMAIL_PASSWORD`: Credenciales SMTP (aunque no se usan actualmente)
- `INTERNAL_SERVICE_API_KEY`: Para comunicación entre servicios

**Razones**:
- ✅ Credenciales nunca en código fuente o variables de entorno visibles
- ✅ Versionado de secrets (rollback disponible)
- ✅ Auditoría de accesos
- ✅ Integración nativa con Cloud Run

**Alternativa descartada**:
- ❌ Variables de entorno en Cloud Run: Menos seguro, no versionado

### Decisión: Service Account con Mínimos Privilegios
**Permisos otorgados a `userapi-service-account`**:
- Cloud SQL Client
- Secret Manager Secret Accessor

**Razones**:
- Principio de **least privilege**
- Si el servicio se ve comprometido, daño limitado
- Auditoría clara de qué servicios acceden a qué recursos

### Decisión: CORS Configurado Explícitamente
**Orígenes permitidos**:
```python
allow_origins=[
    "http://localhost:4200",        # Desarrollo
    "https://frontend-qa-...",      # QA
    "https://frontend-..."          # Production
]
```

**Razones**:
- ✅ Solo frontends legítimos pueden hacer requests
- ✅ Previene ataques CSRF desde dominios maliciosos
- ❌ Evita wildcard `"*"` que sería inseguro

### Decisión: Bcrypt para Hashing de Passwords
**Configuración**:
```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

**Implementación crítica**:
- **Truncado a 72 bytes**: Bcrypt tiene límite de 72 bytes
- **Implementado en 3 niveles**: endpoint, service, auth module

**Razones**:
- ✅ bcrypt es estándar de industria para password hashing
- ✅ Resistente a ataques de fuerza bruta (computacionalmente costoso)
- ✅ Integración sencilla con Passlib

**Problema resuelto**:
- Error inicial: `AttributeError: module 'bcrypt' has no attribute '__about__'`
- Solución: Pinear `bcrypt==4.0.1` (compatible con `passlib==1.7.4`)

---

## Monitoreo

### Decisión: Health Checks en Pipeline
**Implementación**:
```yaml
- name: Health Check QA UserAPI
  run: |
    sleep 10
    curl -f ${{ steps.qa-url.outputs.url }}/health || exit 1
```

**Endpoints de health check**:
- `/health`: Endpoint raíz (también definido en routes.py)
- Respuesta:
```json
{
  "status": "healthy",
  "service": "UserAPI",
  "version": "1.0.0"
}
```

**Razones**:
- ✅ Pipeline falla si deployment no responde correctamente
- ✅ Detecta problemas de configuración inmediatamente
- ✅ Previene deployments rotos llegando a producción

### Decisión: Cloud Run Logging
**Por defecto habilitado**:
- Logs de requests HTTP
- Logs de aplicación (stdout/stderr)
- Métricas de latencia, requests/s, errores

**Razones**:
- ✅ Sin configuración adicional necesaria
- ✅ Integrado con Cloud Logging (Stackdriver)
- ✅ Búsqueda y filtrado avanzado
- ✅ Retention configurable

**No implementado (por ahora)**:
- ⚠️ Alertas automáticas (no crítico para TP académico)
- ⚠️ Dashboards personalizados
- ⚠️ APM (Application Performance Monitoring)

---

## Gestión de Código

### Decisión: Monorepo
**Estructura**:
```
/
├── APIs/
│   └── UserAPI/
├── tf-frontend/
└── .github/workflows/
```

**Razones**:
- ✅ Único repositorio para backend + frontend
- ✅ Cambios atómicos (un commit puede actualizar ambos)
- ✅ Pipeline único maneja todo el deployment
- ❌ Evita complejidad de múltiples repos para proyecto académico

**Alternativa descartada**:
- ❌ Repos separados: Mayor complejidad de coordinación

### Decisión: Dockerfiles Multi-stage
**Frontend**:
```dockerfile
FROM node:20-alpine AS build     # Build de Angular
FROM nginx:alpine                # Serve estático
```

**Backend**:
```dockerfile
FROM python:3.11-slim
# Single stage (no se necesita compilación)
```

**Razones**:
- ✅ Imágenes más livianas (solo runtime en imagen final)
- ✅ Build más rápido en pipeline
- ✅ Mejor para producción

---

## Costos

### Estimación Mensual (USD)
| Servicio | Configuración | Costo Estimado |
|----------|---------------|----------------|
| Cloud Run (UserAPI QA) | Pay-per-use | ~$1-3 |
| Cloud Run (UserAPI PROD) | Pay-per-use | ~$2-5 |
| Cloud Run (Frontend QA) | Pay-per-use | ~$0.50 |
| Cloud Run (Frontend PROD) | Pay-per-use | ~$0.50 |
| Cloud SQL PostgreSQL | db-f1-micro | ~$10 |
| Container Registry | Storage | ~$0.50 |
| Secret Manager | Secrets + accesos | ~$0.20 |
| **TOTAL** | | **~$15-20/mes** |

**Nota**: Con créditos de $300, el proyecto puede correr ~15-20 meses sin costo.

---

## Decisiones Pendientes / Mejoras Futuras

### Si esto fuera producción real:
1. **Bases de datos separadas** para QA y PROD
2. **CDN** (Cloud CDN) para el frontend
3. **Load balancing** con Cloud Load Balancer
4. **Autoscaling avanzado** con mínimo de instancias warm
5. **Monitoring y alerting** con Cloud Monitoring
6. **WAF** (Web Application Firewall) con Cloud Armor
7. **Disaster recovery** con backups automatizados y cross-region
8. ✅ **CI con tests automatizados** (unit, integration, e2e) - **IMPLEMENTADO TP6**
9. **Feature flags** para deployments graduales
10. **Rollback automatizado** si health checks fallan
11. **E2E tests** con Playwright o Cypress (actualmente solo unit tests)
12. **Performance tests** con K6 o Locust

---

## Resumen de Decisiones Clave

| Decisión | Elección | Justificación |
|----------|----------|---------------|
| **Cloud Provider** | Google Cloud Platform | Créditos gratuitos, simplicidad, Cloud Run |
| **Hosting** | Cloud Run | Serverless, autoscaling, pay-per-use |
| **Base de Datos** | Cloud SQL PostgreSQL | Managed, compatible con proyecto existente |
| **CI/CD** | GitHub Actions | Integración nativa, free tier, YAML |
| **Ambientes** | QA + Production | Requisito TP5, aprobaciones manuales |
| **Testing** | Pytest + Jasmine/Karma | TP6, 63% coverage backend |
| **CI/CD con Tests** | Tests antes de build | Quality gates en pipeline |
| **Seguridad** | Secret Manager + Service Accounts | Best practices de GCP |
| **Simplificaciones** | Sin CV ni email verification | Enfoque académico en DevOps |
| **Monorepo** | Backend + Frontend juntos | Simplicidad para TP |

---

**Fecha**: Diciembre 2025
**Materia**: Ingeniería de Software 3
**Trabajos Prácticos**:
- TP5 - Release Pipelines (CI/CD con GitHub Actions + Google Cloud Run)
- TP6 - Unit Tests & Code Coverage (Pytest + Jasmine/Karma integrados en pipeline)
