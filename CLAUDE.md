# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a job application platform consisting of five backend FastAPI services and an Angular frontend. The system allows candidates to register with CV analysis, companies to post jobs, and recruiters to manage applications with AI-powered matching and assistance.

## Architecture

### Backend APIs (FastAPI + PostgreSQL)

Five separate microservices in the `APIs/` directory:

1. **UserAPI** (port 8000)
   - User authentication with JWT
   - Email verification with temporary 6-digit codes
   - Role-based access: candidato, empresa, admin
   - Profile management (including CV and profile picture uploads)
   - CV storage with analysis results
   - Company-recruiter relationship management
   - Internal endpoints for inter-service communication

2. **CvAnalyzerAPI** (port 8001)
   - CV analysis using Google Gemini 2.0 Flash Exp
   - PDF parsing with PyMuPDF
   - Structured data extraction (experience, education, skills, etc.)
   - CV validation (checks if uploaded file is actually a CV)
   - Returns standardized JSON data structure
   - Stateless service (no database)

3. **JobsAPI** (port 8002)
   - Job posting management
   - Application tracking
   - Multiple job statuses: active, paused, closed
   - Application workflow: applied → reviewing → shortlisted → interviewed → offer
   - Statistics and analytics
   - Multi-recruiter assignment per job
   - Communicates with UserAPI for user data enrichment

4. **MatcheoAPI** (port 8003)
   - AI-powered job-candidate matching
   - Calculates compatibility percentage between job postings and candidate CVs
   - Uses Google Gemini 2.0 Flash Exp for intelligent matching
   - Multi-criteria analysis: skills (30%), experience (35%), education (20%), general fit (15%)
   - Provides detailed match breakdown and missing skills analysis
   - Requires JWT authentication
   - Orchestrates calls to JobsAPI and UserAPI

5. **AssistantAPI** (port 8004)
   - AI-powered job posting assistant for recruiters
   - Converts free-form descriptions into structured job postings
   - Uses Google Gemini 2.0 Flash Exp for content generation
   - Generates: title, description, requirements, skills, experience levels
   - Suggests job type, work modality, and education level
   - No authentication required (internal tool)

### Frontend (Angular 19)

Located in `tf-frontend/`:
- Angular 19 with TypeScript 5.7
- Bootstrap 5.3 for styling
- Angular Material components
- Swiper for carousels
- Key pages: landing, login, register, job listings, applications, admin dashboard
- Route guards for admin-only pages

## Common Commands

### Start All Services

From the `APIs/` directory:
```bash
./start_apis.sh
```
This starts all five APIs with proper virtual environments. Services run on ports 8000-8004.

To stop:
```bash
./stop_apis.sh
```

### Individual API Commands

Each API (UserAPI, CvAnalyzerAPI, JobsAPI):
```bash
cd APIs/<APIName>

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the API
python main.py
```

### Frontend Commands

From `tf-frontend/`:
```bash
# Start development server (http://localhost:4200)
npm start
# or
ng serve

# Build for production
ng build

# Run tests
ng test

# Generate new component
ng generate component component-name

# Build and watch for changes
npm run watch
```

## Database Configuration

UserAPI and JobsAPI use PostgreSQL via SQLAlchemy. APIs with database have:
- `database.py`: Database connection and session management
- `models.py`: SQLAlchemy ORM models
- `.env`: Environment variables (DATABASE_URL, API keys)

Connection string format in `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

**Database usage by service**:
- **UserAPI** and **JobsAPI**: Share the same PostgreSQL database
- **CvAnalyzerAPI**, **MatcheoAPI**, **AssistantAPI**: Stateless services (no database)

## Key Architectural Patterns

### Authentication Flow (UserAPI)

1. User registers with temporary storage
2. Verification code sent to email (6-digit code)
3. CV sent to CvAnalyzerAPI for validation and analysis
4. Upon verification, temp files moved to permanent storage
5. JWT tokens used for authentication
6. Role-based access control (candidato, empresa, admin)

### CV Analysis Pipeline (CvAnalyzerAPI)

1. Receive PDF via POST /analyze/
2. Extract text with PyMuPDF (utils/pdf_utils.py)
3. Validate if content is actually a CV using Gemini
4. Extract structured fields using Gemini with JSON response
5. Return standardized data: experience, education, skills, languages, location, availability

Important: CvAnalyzerAPI uses `gemini-2.0-flash` model configured in services/cv_processing.py

### Job Application Flow (JobsAPI)

1. Company (or recruiter) creates job posting
2. Candidates apply with cover letter (resume already in UserAPI)
3. Status progression: applied → reviewing → shortlisted → interview_scheduled → interviewed → offer_extended → accepted/rejected
4. Recruiters can add notes and ratings
5. Statistics tracked (view_count, application_count)

### AI Matching Flow (MatcheoAPI)

1. Recruiter requests match calculation for a job (POST /calculate-matches with JWT token)
2. MatcheoAPI fetches job details from JobsAPI
3. MatcheoAPI fetches all applications for that job from JobsAPI
4. For each application:
   - Fetch candidate data and CV analysis from UserAPI (internal endpoint)
   - Send job + CV data to Gemini 2.0 Flash Exp
   - Gemini analyzes compatibility across 4 dimensions
5. Return sorted list of candidates with match percentages and detailed breakdowns
6. Results include: skills match, experience match, education match, general compatibility

**Matching criteria**:
- **Skills (30%)**: Required vs nice-to-have, missing skills, additional skills
- **Experience (35%)**: Years, relevance, seniority level
- **Education (20%)**: Degree level, field relevance, certifications
- **General fit (15%)**: Location, availability, languages, projects

### AI Job Assistant Flow (AssistantAPI)

1. Recruiter provides free-form job description via frontend
2. POST /generate-job-posting with description text
3. AssistantAPI sends prompt to Gemini 2.0 Flash Exp
4. Gemini extracts and generates structured fields:
   - Professional job title
   - Detailed description (2-4 sentences)
   - Requirements list (plain text with bullet points)
   - Min/max experience years
   - Required and nice-to-have skills arrays
   - Suggested education level, job type, work modality
5. Returns JSON response with all generated fields
6. Frontend auto-fills job creation form with AI suggestions

## Important Implementation Details

### Virtual Environments

Each API has its own Python virtual environment (`venv/`). They are NOT committed to git. Recreate with:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### CORS Configuration

All APIs allow requests from `http://localhost:4200` (Angular dev server). Update CORS origins in production.

### File Storage

- UserAPI: `uploaded_cvs/`, `profile_pictures/`, `temp_files/`, `temp_registrations/`
- Files in temp directories are moved to permanent storage upon email verification
- Static file serving configured with FastAPI StaticFiles

### Environment Variables

Required in `.env` files:

**UserAPI**:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key (shared with JobsAPI and MatcheoAPI)
- `INTERNAL_SERVICE_API_KEY`: API key for inter-service communication
- `CV_ANALYZER_API_KEY`: API key to call CvAnalyzerAPI
- SMTP configuration: `EMAIL_USER`, `EMAIL_PASSWORD`

**CvAnalyzerAPI**:
- `GENAI_API_KEY`: Google Gemini API key
- `CV_ANALYZER_API_KEY`: API key for authentication (matches UserAPI's key)

**JobsAPI**:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key (shared with UserAPI and MatcheoAPI)
- `INTERNAL_SERVICE_API_KEY`: API key for inter-service communication
- `USER_API_URL`: UserAPI base URL (default: http://localhost:8000)
- `API_PORT`: Port number (default 8002)

**MatcheoAPI**:
- `GENAI_API_KEY`: Google Gemini API key
- `SECRET_KEY`: JWT secret key (shared with UserAPI and JobsAPI)
- `INTERNAL_SERVICE_API_KEY`: API key for calling UserAPI internal endpoints
- No database required

**AssistantAPI**:
- `GENAI_API_KEY`: Google Gemini API key
- `API_PORT`: Port number (default 8004)
- No authentication or database required

### Database Models

**UserAPI models.py**:
- `User`: Main user table with role enum, verification fields, CV data
- `CompanyRecruiter`: Many-to-many relationship between companies and recruiters

**JobsAPI models.py**:
- `Job`: Job postings with status, modality, salary, skills (JSON fields)
- `JobApplication`: Applications with status tracking, ratings, interview details

Foreign keys reference users by ID (from UserAPI database).

## Angular Frontend Structure

```
src/app/
├── components/        # Reusable UI components (header, footer, modals)
├── pages/            # Route-level pages
├── services/         # HTTP services (auth, jobs, user)
├── guards/           # Route guards (admin guard)
├── interfaces/       # TypeScript interfaces
└── app.routes.ts     # Application routing
```

Key services:
- `auth.service.ts`: Authentication, JWT management
- `jobs.service.ts`: Job and application operations
- `user.service.ts`: User profile operations

## Testing

### Backend Tests

APIs don't have test files currently. To add tests:
```bash
pip install pytest pytest-asyncio httpx
pytest
```

### Frontend Tests

Angular uses Jasmine + Karma:
```bash
ng test
```

## API Ports Summary

- **UserAPI**: http://localhost:8000
- **CvAnalyzerAPI**: http://localhost:8001
- **JobsAPI**: http://localhost:8002
- **MatcheoAPI**: http://localhost:8003
- **AssistantAPI**: http://localhost:8004
- **Frontend**: http://localhost:4200

## Working with Gemini AI

Three services use Google's Gemini 2.0 Flash Exp model for different AI tasks:

### CvAnalyzerAPI
- **Model**: `gemini-2.0-flash-exp`
- **Temperature**: 0.2 (deterministic responses)
- **Max tokens**: 2048
- **Purpose**: CV parsing and structured data extraction
- **Process**: Two-stage (validation check, then field extraction)
- **Location**: `services/cv_processing.py`
- Response parsing handles markdown code blocks (```json)

### MatcheoAPI
- **Model**: `gemini-2.0-flash-exp`
- **Temperature**: 0.2 (deterministic responses)
- **Max tokens**: 2048
- **Purpose**: Calculate job-candidate compatibility percentage
- **Process**: Multi-criteria analysis with weighted scoring
- **Location**: `services/matcheo_service.py`
- Returns detailed match breakdown with scores for each criterion

### AssistantAPI
- **Model**: `gemini-2.0-flash-exp`
- **Temperature**: 0.3 (slightly more creative)
- **Max tokens**: 2048
- **Purpose**: Generate professional job posting fields from free text
- **Process**: Single-stage structured generation
- **Location**: `services/assistant_service.py`
- Generates complete job posting structure from recruiter description

**Important**: When modifying prompts, maintain JSON schema consistency with frontend expectations. All services expect valid JSON responses from Gemini.

## Deployment Notes

- All five APIs run independently (can be containerized separately)
- Frontend builds to `dist/` directory
- Angular has SSR capability (`serve:ssr:tf-frontend` script)
- Update CORS origins for production domains
- Database migrations not implemented (using SQLAlchemy create_all)
- APIs share `SECRET_KEY` for JWT validation
- Three APIs require `GENAI_API_KEY` for Gemini access

## Inter-Service Communication

The microservices communicate via HTTP requests:

### UserAPI → CvAnalyzerAPI
- **Protocol**: HTTP POST (synchronous with `requests`)
- **Endpoint**: `POST http://localhost:8001/analyze/`
- **Auth**: API Key header (`X-API-Key`)
- **Purpose**: Validate and analyze CV PDFs during candidate registration
- **Data**: PDF file upload
- **Response**: Structured JSON with CV data (experience, skills, education, etc.)

### JobsAPI → UserAPI
- **Protocol**: HTTP GET (async with `httpx`)
- **Endpoints**:
  - `GET /api/v1/me` - Get current user info (with user's JWT)
  - `GET /api/v1/me/recruiting-for` - Get recruiter's companies (with user's JWT)
  - `GET /api/v1/internal/users/{user_id}` - Get user data (with internal API key)
- **Auth**: JWT tokens (user endpoints) or Internal API Key (internal endpoints)
- **Purpose**: Enrich job application responses with candidate data
- **Data**: User profile and CV analysis data

### MatcheoAPI → JobsAPI + UserAPI
- **Protocol**: HTTP GET (synchronous with `requests`)
- **Endpoints**:
  - JobsAPI: `GET /api/v1/jobs/{job_id}` (with user's JWT)
  - JobsAPI: `GET /api/v1/jobs/{job_id}/applications` (with user's JWT)
  - UserAPI: `GET /api/v1/internal/users/{user_id}` (with internal API key)
- **Auth**: JWT for JobsAPI, Internal API Key for UserAPI
- **Purpose**: Orchestrate job-candidate matching
- **Flow**: Fetch job → fetch applications → fetch each candidate's CV → calculate matches with AI

### AssistantAPI
- **Communication**: Standalone service (no calls to other APIs)
- **Purpose**: Pure AI content generation for job postings
- **Input**: Free-form text from frontend
- **Output**: Structured job posting fields

### Shared Configuration
- `SECRET_KEY`: Shared between UserAPI, JobsAPI, and MatcheoAPI for JWT validation
- `INTERNAL_SERVICE_API_KEY`: Shared secret for internal inter-service calls
- All services use environment variables for configuration (never hardcoded)
