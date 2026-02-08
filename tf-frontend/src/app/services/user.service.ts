// src/app/services/user.service.ts
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { AuthService, User, CandidatoRequest, EmpresaRequest } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class UserService {

  constructor(private authService: AuthService) {}

  // Reutilizar métodos del AuthService existente
  getCurrentUser(): Observable<User> {
    return this.authService.getCurrentUser();
  }

  // 🎯 MÉTODO CLAVE: Verificar si es recruiter (para qué empresas trabaja)
  getRecruitingCompanies(): Observable<any> {
    return this.authService.getRecruitingCompanies();
  }

  // Otros métodos útiles que puedas necesitar
  updateCandidateProfile(userData: Partial<CandidatoRequest>, cvFile?: File, profilePicture?: File): Observable<User> {
    return this.authService.updateCurrentCandidato(userData, cvFile, profilePicture);
  }

  updateCompanyProfile(userData: Partial<EmpresaRequest>, profilePicture?: File): Observable<User> {
    return this.authService.updateCurrentEmpresa(userData, profilePicture);
  }

  // Métodos de administradores si los necesitas
  getAllCandidates(skip: number = 0, limit: number = 100): Observable<User[]> {
    return this.authService.getAllCandidates(skip, limit);
  }

  getAllUsers(skip: number = 0, limit: number = 100): Observable<User[]> {
    return this.authService.getAllUsers(skip, limit);
  }

  // Métodos para empresas con recruiters
  getMyRecruiters(): Observable<any> {
    return this.authService.getMyRecruiters();
  }

  addRecruiter(recruiterEmail: string): Observable<any> {
    return this.authService.addRecruiter(recruiterEmail);
  }

  removeRecruiter(recruiterEmail: string): Observable<any> {
    return this.authService.removeRecruiter(recruiterEmail);
  }

  // Métodos de verificación de empresas
  getPendingCompanies(): Observable<User[]> {
    return this.authService.getPendingCompanies();
  }

  verifyCompany(companyEmail: string): Observable<any> {
    return this.authService.verifyCompany(companyEmail);
  }
}