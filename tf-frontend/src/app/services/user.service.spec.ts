import { TestBed } from '@angular/core/testing';
import { UserService } from './user.service';
import { AuthService, User, CandidatoRequest, EmpresaRequest } from './auth.service';
import { of } from 'rxjs';

describe('UserService', () => {
  let service: UserService;
  let authServiceSpy: jasmine.SpyObj<AuthService>;

  const mockUser: User = {
    id: 1,
    email: 'test@example.com',
    nombre: 'Test User',
    role: 'candidato',
    verified: true,
    apellido: 'Apellido',
    genero: 'masculino',
    fecha_nacimiento: '1990-01-01',
    cv_filename: 'test-cv.pdf',
    cv_analizado: { skills: ['Python'] }
  };

  const mockRecruitingCompanies = {
    recruiter: 'John Doe',
    companies: [
      { id: 1, name: 'Company 1', verified: true },
      { id: 2, name: 'Company 2', verified: false }
    ],
    total: 2
  };

  const mockRecruiters = {
    company: 'Test Company',
    recruiters: [
      { id: 1, name: 'Recruiter 1', email: 'recruiter1@example.com' },
      { id: 2, name: 'Recruiter 2', email: 'recruiter2@example.com' }
    ],
    total: 2
  };

  beforeEach(() => {
    const spy = jasmine.createSpyObj('AuthService', [
      'getCurrentUser',
      'getRecruitingCompanies',
      'updateCurrentCandidato',
      'updateCurrentEmpresa',
      'getAllCandidates',
      'getAllUsers',
      'getMyRecruiters',
      'addRecruiter',
      'removeRecruiter',
      'getPendingCompanies',
      'verifyCompany'
    ]);

    TestBed.configureTestingModule({
      providers: [
        UserService,
        { provide: AuthService, useValue: spy }
      ]
    });

    service = TestBed.inject(UserService);
    authServiceSpy = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
  });

  describe('User Profile Operations', () => {
    it('should get current user', () => {
      authServiceSpy.getCurrentUser.and.returnValue(of(mockUser));

      service.getCurrentUser().subscribe(user => {
        expect(user).toEqual(mockUser);
      });

      expect(authServiceSpy.getCurrentUser).toHaveBeenCalled();
    });

    it('should update candidate profile', () => {
      const updateData: Partial<CandidatoRequest> = {
        nombre: 'Updated Name',
        apellido: 'Updated Lastname'
      };
      const mockFile = new File(['cv content'], 'updated-cv.pdf', { type: 'application/pdf' });
      const mockImage = new File(['image content'], 'profile.jpg', { type: 'image/jpeg' });
      const updatedUser = { ...mockUser, nombre: 'Updated Name' };

      authServiceSpy.updateCurrentCandidato.and.returnValue(of(updatedUser));

      service.updateCandidateProfile(updateData, mockFile, mockImage).subscribe(user => {
        expect(user.nombre).toBe('Updated Name');
      });

      expect(authServiceSpy.updateCurrentCandidato).toHaveBeenCalledWith(updateData, mockFile, mockImage);
    });

    it('should update candidate profile without files', () => {
      const updateData: Partial<CandidatoRequest> = {
        nombre: 'Updated Name'
      };
      const updatedUser = { ...mockUser, nombre: 'Updated Name' };

      authServiceSpy.updateCurrentCandidato.and.returnValue(of(updatedUser));

      service.updateCandidateProfile(updateData).subscribe(user => {
        expect(user.nombre).toBe('Updated Name');
      });

      expect(authServiceSpy.updateCurrentCandidato).toHaveBeenCalledWith(updateData, undefined, undefined);
    });

    it('should update company profile', () => {
      const updateData: Partial<EmpresaRequest> = {
        nombre: 'Updated Company Name',
        descripcion: 'Updated description'
      };
      const mockImage = new File(['image content'], 'logo.png', { type: 'image/png' });
      const companyUser = { ...mockUser, role: 'empresa' as const, nombre: 'Updated Company Name' };

      authServiceSpy.updateCurrentEmpresa.and.returnValue(of(companyUser));

      service.updateCompanyProfile(updateData, mockImage).subscribe(user => {
        expect(user.nombre).toBe('Updated Company Name');
      });

      expect(authServiceSpy.updateCurrentEmpresa).toHaveBeenCalledWith(updateData, mockImage);
    });

    it('should update company profile without image', () => {
      const updateData: Partial<EmpresaRequest> = {
        descripcion: 'New description'
      };
      const companyUser = { ...mockUser, role: 'empresa' as const };

      authServiceSpy.updateCurrentEmpresa.and.returnValue(of(companyUser));

      service.updateCompanyProfile(updateData).subscribe(user => {
        expect(user).toEqual(companyUser);
      });

      expect(authServiceSpy.updateCurrentEmpresa).toHaveBeenCalledWith(updateData, undefined);
    });
  });

  describe('Recruiting Operations', () => {
    it('should get recruiting companies', () => {
      authServiceSpy.getRecruitingCompanies.and.returnValue(of(mockRecruitingCompanies));

      service.getRecruitingCompanies().subscribe(companies => {
        expect(companies).toEqual(mockRecruitingCompanies);
        expect(companies.total).toBe(2);
        expect(companies.companies.length).toBe(2);
      });

      expect(authServiceSpy.getRecruitingCompanies).toHaveBeenCalled();
    });

    it('should get my recruiters', () => {
      authServiceSpy.getMyRecruiters.and.returnValue(of(mockRecruiters));

      service.getMyRecruiters().subscribe(recruiters => {
        expect(recruiters).toEqual(mockRecruiters);
        expect(recruiters.total).toBe(2);
        expect(recruiters.recruiters.length).toBe(2);
      });

      expect(authServiceSpy.getMyRecruiters).toHaveBeenCalled();
    });

    it('should add recruiter', () => {
      const recruiterEmail = 'newrecruiter@example.com';
      const successResponse = {
        message: 'Recruiter agregado exitosamente',
        recruiter_id: 123
      };

      authServiceSpy.addRecruiter.and.returnValue(of(successResponse));

      service.addRecruiter(recruiterEmail).subscribe(response => {
        expect(response.message).toContain('exitosamente');
        expect(response.recruiter_id).toBe(123);
      });

      expect(authServiceSpy.addRecruiter).toHaveBeenCalledWith(recruiterEmail);
    });

    it('should remove recruiter', () => {
      const recruiterEmail = 'recruiter@example.com';
      const successResponse = {
        message: 'Recruiter removido exitosamente'
      };

      authServiceSpy.removeRecruiter.and.returnValue(of(successResponse));

      service.removeRecruiter(recruiterEmail).subscribe(response => {
        expect(response.message).toContain('removido exitosamente');
      });

      expect(authServiceSpy.removeRecruiter).toHaveBeenCalledWith(recruiterEmail);
    });
  });

  describe('Admin Operations', () => {
    it('should get all candidates', () => {
      const mockCandidates = [
        { ...mockUser, id: 1 },
        { ...mockUser, id: 2, nombre: 'Candidate 2' }
      ];

      authServiceSpy.getAllCandidates.and.returnValue(of(mockCandidates));

      service.getAllCandidates(0, 50).subscribe(candidates => {
        expect(candidates).toEqual(mockCandidates);
        expect(candidates.length).toBe(2);
      });

      expect(authServiceSpy.getAllCandidates).toHaveBeenCalledWith(0, 50);
    });

    it('should get all candidates with default parameters', () => {
      const mockCandidates = [mockUser];

      authServiceSpy.getAllCandidates.and.returnValue(of(mockCandidates));

      service.getAllCandidates().subscribe(candidates => {
        expect(candidates).toEqual(mockCandidates);
      });

      expect(authServiceSpy.getAllCandidates).toHaveBeenCalledWith(0, 100);
    });

    it('should get all users', () => {
      const mockUsers = [
        { ...mockUser, id: 1, role: 'candidato' as const },
        { ...mockUser, id: 2, role: 'empresa' as const, nombre: 'Company User' },
        { ...mockUser, id: 3, role: 'admin' as const, nombre: 'Admin User' }
      ];

      authServiceSpy.getAllUsers.and.returnValue(of(mockUsers));

      service.getAllUsers(10, 25).subscribe(users => {
        expect(users).toEqual(mockUsers);
        expect(users.length).toBe(3);
      });

      expect(authServiceSpy.getAllUsers).toHaveBeenCalledWith(10, 25);
    });

    it('should get all users with default parameters', () => {
      const mockUsers = [mockUser];

      authServiceSpy.getAllUsers.and.returnValue(of(mockUsers));

      service.getAllUsers().subscribe(users => {
        expect(users).toEqual(mockUsers);
      });

      expect(authServiceSpy.getAllUsers).toHaveBeenCalledWith(0, 100);
    });

    it('should get pending companies', () => {
      const mockPendingCompanies = [
        { ...mockUser, id: 1, role: 'empresa' as const, verified: false, nombre: 'Pending Company 1' },
        { ...mockUser, id: 2, role: 'empresa' as const, verified: false, nombre: 'Pending Company 2' }
      ];

      authServiceSpy.getPendingCompanies.and.returnValue(of(mockPendingCompanies));

      service.getPendingCompanies().subscribe(companies => {
        expect(companies).toEqual(mockPendingCompanies);
        expect(companies.length).toBe(2);
        expect(companies.every(company => company.role === 'empresa')).toBeTrue();
        expect(companies.every(company => !company.verified)).toBeTrue();
      });

      expect(authServiceSpy.getPendingCompanies).toHaveBeenCalled();
    });

    it('should verify company', () => {
      const companyEmail = 'company@example.com';
      const verificationResponse = {
        message: 'Empresa verificada exitosamente',
        company: {
          id: 1,
          nombre: 'Verified Company',
          email: companyEmail,
          verified: true
        }
      };

      authServiceSpy.verifyCompany.and.returnValue(of(verificationResponse));

      service.verifyCompany(companyEmail).subscribe(response => {
        expect(response.message).toContain('verificada exitosamente');
        expect(response.company.verified).toBeTrue();
        expect(response.company.email).toBe(companyEmail);
      });

      expect(authServiceSpy.verifyCompany).toHaveBeenCalledWith(companyEmail);
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle empty recruiting companies response', () => {
      const emptyResponse = {
        recruiter: 'John Doe',
        companies: [],
        total: 0
      };

      authServiceSpy.getRecruitingCompanies.and.returnValue(of(emptyResponse));

      service.getRecruitingCompanies().subscribe(companies => {
        expect(companies.companies).toEqual([]);
        expect(companies.total).toBe(0);
      });
    });

    it('should handle empty recruiters response', () => {
      const emptyResponse = {
        company: 'Test Company',
        recruiters: [],
        total: 0
      };

      authServiceSpy.getMyRecruiters.and.returnValue(of(emptyResponse));

      service.getMyRecruiters().subscribe(recruiters => {
        expect(recruiters.recruiters).toEqual([]);
        expect(recruiters.total).toBe(0);
      });
    });

    it('should handle empty candidates list', () => {
      authServiceSpy.getAllCandidates.and.returnValue(of([]));

      service.getAllCandidates().subscribe(candidates => {
        expect(candidates).toEqual([]);
      });
    });

    it('should handle empty users list', () => {
      authServiceSpy.getAllUsers.and.returnValue(of([]));

      service.getAllUsers().subscribe(users => {
        expect(users).toEqual([]);
      });
    });

    it('should handle empty pending companies list', () => {
      authServiceSpy.getPendingCompanies.and.returnValue(of([]));

      service.getPendingCompanies().subscribe(companies => {
        expect(companies).toEqual([]);
      });
    });
  });

  describe('Service Delegation', () => {
    it('should properly delegate all methods to AuthService', () => {
      // Test that UserService is properly delegating calls to AuthService
      
      // Setup all method responses
      authServiceSpy.getCurrentUser.and.returnValue(of(mockUser));
      authServiceSpy.getRecruitingCompanies.and.returnValue(of(mockRecruitingCompanies));
      authServiceSpy.updateCurrentCandidato.and.returnValue(of(mockUser));
      authServiceSpy.updateCurrentEmpresa.and.returnValue(of(mockUser));
      authServiceSpy.getAllCandidates.and.returnValue(of([mockUser]));
      authServiceSpy.getAllUsers.and.returnValue(of([mockUser]));
      authServiceSpy.getMyRecruiters.and.returnValue(of(mockRecruiters));
      authServiceSpy.addRecruiter.and.returnValue(of({ message: 'Added' }));
      authServiceSpy.removeRecruiter.and.returnValue(of({ message: 'Removed' }));
      authServiceSpy.getPendingCompanies.and.returnValue(of([mockUser]));
      authServiceSpy.verifyCompany.and.returnValue(of({ message: 'Verified' }));

      // Call all methods
      service.getCurrentUser().subscribe();
      service.getRecruitingCompanies().subscribe();
      service.updateCandidateProfile({}).subscribe();
      service.updateCompanyProfile({}).subscribe();
      service.getAllCandidates().subscribe();
      service.getAllUsers().subscribe();
      service.getMyRecruiters().subscribe();
      service.addRecruiter('test@example.com').subscribe();
      service.removeRecruiter('test@example.com').subscribe();
      service.getPendingCompanies().subscribe();
      service.verifyCompany('company@example.com').subscribe();

      // Verify all methods were called
      expect(authServiceSpy.getCurrentUser).toHaveBeenCalled();
      expect(authServiceSpy.getRecruitingCompanies).toHaveBeenCalled();
      expect(authServiceSpy.updateCurrentCandidato).toHaveBeenCalled();
      expect(authServiceSpy.updateCurrentEmpresa).toHaveBeenCalled();
      expect(authServiceSpy.getAllCandidates).toHaveBeenCalled();
      expect(authServiceSpy.getAllUsers).toHaveBeenCalled();
      expect(authServiceSpy.getMyRecruiters).toHaveBeenCalled();
      expect(authServiceSpy.addRecruiter).toHaveBeenCalled();
      expect(authServiceSpy.removeRecruiter).toHaveBeenCalled();
      expect(authServiceSpy.getPendingCompanies).toHaveBeenCalled();
      expect(authServiceSpy.verifyCompany).toHaveBeenCalled();
    });
  });

  describe('Integration Scenarios', () => {
    it('should handle recruiter workflow', () => {
      // Simulate a complete recruiter management workflow
      
      // 1. Get current recruiters
      authServiceSpy.getMyRecruiters.and.returnValue(of(mockRecruiters));
      
      service.getMyRecruiters().subscribe(recruiters => {
        expect(recruiters.total).toBe(2);
      });

      // 2. Add a new recruiter
      const newRecruiterEmail = 'newrecruiter@example.com';
      authServiceSpy.addRecruiter.and.returnValue(of({ 
        message: 'Recruiter agregado exitosamente',
        recruiter_id: 123
      }));

      service.addRecruiter(newRecruiterEmail).subscribe(response => {
        expect(response.recruiter_id).toBe(123);
      });

      // 3. Remove an existing recruiter
      const existingRecruiterEmail = 'recruiter1@example.com';
      authServiceSpy.removeRecruiter.and.returnValue(of({
        message: 'Recruiter removido exitosamente'
      }));

      service.removeRecruiter(existingRecruiterEmail).subscribe(response => {
        expect(response.message).toContain('removido');
      });

      expect(authServiceSpy.getMyRecruiters).toHaveBeenCalled();
      expect(authServiceSpy.addRecruiter).toHaveBeenCalledWith(newRecruiterEmail);
      expect(authServiceSpy.removeRecruiter).toHaveBeenCalledWith(existingRecruiterEmail);
    });

    it('should handle admin verification workflow', () => {
      // Simulate admin company verification workflow
      
      // 1. Get pending companies
      const pendingCompanies = [
        { ...mockUser, role: 'empresa' as const, verified: false, email: 'company1@example.com' },
        { ...mockUser, role: 'empresa' as const, verified: false, email: 'company2@example.com' }
      ];
      
      authServiceSpy.getPendingCompanies.and.returnValue(of(pendingCompanies));
      
      service.getPendingCompanies().subscribe(companies => {
        expect(companies.length).toBe(2);
        expect(companies.every(c => !c.verified)).toBeTrue();
      });

      // 2. Verify a company
      authServiceSpy.verifyCompany.and.returnValue(of({
        message: 'Empresa company1@example.com verificada exitosamente',
        company: {
          id: 1,
          email: 'company1@example.com',
          verified: true
        }
      }));

      service.verifyCompany('company1@example.com').subscribe(response => {
        expect(response.company.verified).toBeTrue();
      });

      expect(authServiceSpy.getPendingCompanies).toHaveBeenCalled();
      expect(authServiceSpy.verifyCompany).toHaveBeenCalledWith('company1@example.com');
    });
  });
});