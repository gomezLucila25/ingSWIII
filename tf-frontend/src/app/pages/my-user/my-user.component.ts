import { Component, ViewChild, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
import { AuthService, User, CandidatoRequest, EmpresaRequest } from '../../services/auth.service';
import { HeaderComponent } from '../../components/header/header.component'; // 🆕 AGREGADO
import { FooterComponent } from '../../components/footer/footer.component'; // 🆕 AGREGADO

@Component({
  selector: 'app-my-user',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    HttpClientModule,
    HeaderComponent, // 🆕 AGREGADO
    FooterComponent  // 🆕 AGREGADO
  ],
  templateUrl: './my-user.component.html',
  styleUrls: ['./my-user.component.css']
})
export class MyUserComponent implements OnInit {
  user: User | null = null;
  loading = true;
  errorMessage = '';

  profileImageUrl: string | null = null;
  isLookingForJob = true;
  isEditing = false;
  saving = false;

  tempUser = {
    nombre: '',
    apellido: '',
    genero: 'masculino' as 'masculino' | 'femenino' | 'otro',
    fecha_nacimiento: '',
    descripcion: ''
  };
  tempCvFile: File | null = null;
  tempProfilePicture: File | null = null;

  // Datos para recruiters
  recruiters: any[] = [];
  recruitingCompanies: any[] = [];
  showRecruiters = false;
  showRecruitingFor = false;
  loadingRecruiters = false;
  newRecruiterEmail = '';

  @ViewChild('photoInput') photoInput: any;
  @ViewChild('cvInput') cvInput: any;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadUserData();
  }

  loadUserData(): void {
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/login']);
      return;
    }

    this.loading = true;
    this.authService.getCurrentUser().subscribe({
      next: (userData) => {
        this.user = userData;
        this.loading = false;
        
        // Cargar imagen de perfil si existe
        if (userData.profile_picture) {
          this.profileImageUrl = `http://localhost:8000/profile_pictures/${userData.profile_picture}`;
        }
        
        // Cargar datos adicionales según el rol
        if (userData.role === 'empresa' && userData.verified) {
          this.loadRecruiters();
        } else if (userData.role === 'candidato') {
          this.loadRecruitingCompanies();
        }
      },
      error: (error) => {
        console.error('Error al cargar datos del usuario:', error);
        this.loading = false;
        
        if (error.status === 401) {
          this.authService.logout();
          this.router.navigate(['/login']);
        } else {
          this.errorMessage = 'Error al cargar los datos del usuario';
        }
      }
    });
  }

  getGenderDisplay(genero: string | undefined): string {
    if (!genero) return '';
    switch(genero) {
      case 'masculino': return 'Masculino';
      case 'femenino': return 'Femenino';
      case 'otro': return 'Otro';
      default: return genero;
    }
  }

  getDisplayCvName(): string {
    if (!this.user || !this.user.apellido) return 'CV.pdf';
    return `${this.user.nombre}_${this.user.apellido}_CV.pdf`;
  }

  downloadCV(): void {
    if (!this.user || !this.user.cv_filename) {
      alert('No hay CV disponible para descargar');
      return;
    }
    
    const downloadUrl = `http://localhost:8000/uploaded_cvs/${this.user.cv_filename}`;
    console.log('🔗 Intentando descargar CV desde:', downloadUrl);
    
    fetch(downloadUrl, { method: 'HEAD' })
      .then(response => {
        if (response.ok) {
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.download = this.getDisplayCvName();
          link.target = '_blank';
          
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        } else {
          alert('El archivo CV no se encuentra disponible en el servidor');
          console.error('❌ CV no encontrado:', response.status);
        }
      })
      .catch(error => {
        console.error('❌ Error al acceder al CV:', error);
        alert('Error al acceder al archivo CV');
      });
  }

  triggerFileInput() {
    if (!this.isEditing) return;
    this.photoInput.nativeElement.click();
  }

  onPhotoSelected(event: Event): void {
    if (!this.isEditing) return;
    
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file && file.type.startsWith('image/')) {
      this.tempProfilePicture = file;
      
      const reader = new FileReader();
      reader.onload = () => {
        this.profileImageUrl = reader.result as string;
      };
      reader.readAsDataURL(file);
    } else {
      alert('Por favor seleccioná una imagen válida.');
    }
  }

  triggerCvUpload() {
    this.cvInput.nativeElement.click();
  }

  onCvSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file && file.type === 'application/pdf') {
      this.tempCvFile = file;
    } else {
      alert('El archivo debe ser un PDF válido.');
    }
  }

  toggleJobStatus() {
    this.isLookingForJob = !this.isLookingForJob;
  }

  enableEdit() {
    if (!this.user) return;
    
    this.tempUser = {
      nombre: this.user.nombre,
      apellido: this.user.apellido || '',
      genero: this.user.genero || 'masculino',
      fecha_nacimiento: this.user.fecha_nacimiento || '',
      descripcion: this.user.descripcion || ''
    };
    this.tempCvFile = null;
    this.tempProfilePicture = null;
    this.isEditing = true;
  }

  saveChanges() {
    if (!this.user) return;

    this.saving = true;
    this.errorMessage = '';

    if (this.user.role === 'candidato') {
      const updateData: Partial<CandidatoRequest> = {
        nombre: this.tempUser.nombre,
        apellido: this.tempUser.apellido,
        genero: this.tempUser.genero,
        fecha_nacimiento: this.tempUser.fecha_nacimiento
      };

      this.authService.updateCurrentCandidato(
        updateData, 
        this.tempCvFile || undefined,
        this.tempProfilePicture || undefined
      ).subscribe({
        next: (updatedUser) => {
          this.user = updatedUser;
          
          if (updatedUser.profile_picture) {
            this.profileImageUrl = `http://localhost:8000/profile_pictures/${updatedUser.profile_picture}`;
          }
          
          this.isEditing = false;
          this.saving = false;
          this.tempCvFile = null;
          this.tempProfilePicture = null;
          alert('Cambios guardados correctamente.');
        },
        error: (error) => {
          this.handleUpdateError(error);
        }
      });
    } else if (this.user.role === 'empresa') {
      const updateData: Partial<EmpresaRequest> = {
        nombre: this.tempUser.nombre,
        descripcion: this.tempUser.descripcion || ''
      };

      this.authService.updateCurrentEmpresa(
        updateData,
        this.tempProfilePicture || undefined
      ).subscribe({
        next: (updatedUser) => {
          this.user = updatedUser;
          
          if (updatedUser.profile_picture) {
            this.profileImageUrl = `http://localhost:8000/profile_pictures/${updatedUser.profile_picture}`;
          }
          
          this.isEditing = false;
          this.saving = false;
          this.tempProfilePicture = null;
          alert('Cambios guardados correctamente.');
        },
        error: (error) => {
          this.handleUpdateError(error);
        }
      });
    }
  }

  private handleUpdateError(error: any): void {
    console.error('Error al guardar cambios:', error);
    this.saving = false;
    
    if (error.error && error.error.detail) {
      this.errorMessage = error.error.detail;
    } else {
      this.errorMessage = 'Error al guardar los cambios';
    }
  }

  discardChanges() {
    this.isEditing = false;
    this.tempCvFile = null;
    this.tempProfilePicture = null;
    this.errorMessage = '';
    
    if (this.user?.profile_picture) {
      this.profileImageUrl = `http://localhost:8000/profile_pictures/${this.user.profile_picture}`;
    } else {
      this.profileImageUrl = null;
    }
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  // Métodos para recruiters
  loadRecruiters(): void {
    this.loadingRecruiters = true;
    this.authService.getMyRecruiters().subscribe({
      next: (response: any) => {
        this.recruiters = response.recruiters || [];
        this.loadingRecruiters = false;
      },
      error: (error) => {
        console.error('Error al cargar recruiters:', error);
        this.loadingRecruiters = false;
      }
    });
  }

  loadRecruitingCompanies(): void {
    this.authService.getRecruitingCompanies().subscribe({
      next: (response: any) => {
        this.recruitingCompanies = response.companies || [];
      },
      error: (error) => {
        console.error('Error al cargar empresas:', error);
      }
    });
  }

  toggleRecruiters(): void {
    this.showRecruiters = !this.showRecruiters;
    if (this.showRecruiters && this.recruiters.length === 0) {
      this.loadRecruiters();
    }
  }

  toggleRecruitingFor(): void {
    this.showRecruitingFor = !this.showRecruitingFor;
  }

  addRecruiter(): void {
    if (!this.newRecruiterEmail.trim()) {
      alert('Por favor ingresa un email válido');
      return;
    }

    this.authService.addRecruiter(this.newRecruiterEmail).subscribe({
      next: (response: any) => {
        alert(response.message);
        this.newRecruiterEmail = '';
        this.loadRecruiters();
      },
      error: (error) => {
        console.error('Error al agregar recruiter:', error);
        alert(error.error?.detail || 'Error al agregar recruiter');
      }
    });
  }

  removeRecruiter(recruiterEmail: string): void {
    if (confirm(`¿Estás seguro de remover a ${recruiterEmail} como recruiter?`)) {
      this.authService.removeRecruiter(recruiterEmail).subscribe({
        next: (response: any) => {
          alert(response.message);
          this.loadRecruiters();
        },
        error: (error) => {
          console.error('Error al remover recruiter:', error);
          alert(error.error?.detail || 'Error al remover recruiter');
        }
      });
    }
  }

  resignFromCompany(companyId: number): void {
    const company = this.recruitingCompanies.find(c => c.id === companyId);
    const companyName = company?.nombre || 'esta empresa';

    if (confirm(`¿Estás seguro de que deseas renunciar como recruiter de ${companyName}? Esta acción no se puede deshacer.`)) {
      this.authService.resignFromCompany(companyId).subscribe({
        next: (response: any) => {
          alert(response.message || 'Has renunciado exitosamente');
          // Recargar la lista de empresas
          this.loadRecruitingCompanies();
          // Si ya no es recruiter de ninguna empresa, recargar el perfil completo
          if (this.recruitingCompanies.length <= 1) {
            setTimeout(() => {
              this.loadUserData();
            }, 500);
          }
        },
        error: (error) => {
          console.error('Error al renunciar:', error);
          alert(error.error?.detail || 'Error al procesar la renuncia');
        }
      });
    }
  }

  isRecruiter(): boolean {
    return this.recruitingCompanies && this.recruitingCompanies.length > 0;
  }
}