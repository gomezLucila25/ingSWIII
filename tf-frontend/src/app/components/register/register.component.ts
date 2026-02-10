import { Component } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators, AbstractControl } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css']
})
export class RegisterComponent {
  registerForm!: FormGroup;
  userType: 'candidato' | 'empresa' = 'candidato';
  isLoading = false;
  errorMessage = '';

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private authService: AuthService
  ) {
    this.initializeForm();
  }

  initializeForm() {
    this.registerForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', Validators.required],
      nombre: ['', Validators.required],
      // Campos específicos de candidato
      apellido: [''],
      gender: [''],
      birthDate: [''],
      // Campos específicos de empresa
      descripcion: [''],
      terms: [false, Validators.requiredTrue]
    }, { validators: this.passwordMatchValidator });

    this.updateValidators();
  }

  passwordMatchValidator(control: AbstractControl): {[key: string]: any} | null {
    const password = control.get('password');
    const confirmPassword = control.get('confirmPassword');
    
    if (!password || !confirmPassword) {
      return null;
    }

    if (password.value !== confirmPassword.value) {
      return { passwordMismatch: true };
    }
    
    return null;
  }

  selectUserType(type: 'candidato' | 'empresa') {
    this.userType = type;
    this.updateValidators();
    this.resetSpecificFields();
  }

  updateValidators() {
    if (this.userType === 'candidato') {
      this.registerForm.get('apellido')?.setValidators([Validators.required, this.onlyLettersValidator]);
      this.registerForm.get('gender')?.setValidators([Validators.required]);
      this.registerForm.get('birthDate')?.setValidators([Validators.required, this.ageValidator]);
      this.registerForm.get('descripcion')?.clearValidators();
    } else {
      this.registerForm.get('apellido')?.clearValidators();
      this.registerForm.get('gender')?.clearValidators();
      this.registerForm.get('birthDate')?.clearValidators();
      this.registerForm.get('descripcion')?.setValidators([Validators.required]);
    }
    
    this.registerForm.get('apellido')?.updateValueAndValidity();
    this.registerForm.get('gender')?.updateValueAndValidity();
    this.registerForm.get('birthDate')?.updateValueAndValidity();
    this.registerForm.get('descripcion')?.updateValueAndValidity();
  }

  resetSpecificFields() {
    if (this.userType === 'candidato') {
      this.registerForm.patchValue({
        descripcion: ''
      });
    } else {
      this.registerForm.patchValue({
        apellido: '',
        gender: '',
        birthDate: ''
      });
    }
  }

  onlyLettersValidator(control: AbstractControl): {[key: string]: any} | null {
    const value = control.value;
    if (!value) return null;
    
    const letterPattern = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/;
    if (!letterPattern.test(value)) {
      return { onlyLetters: true };
    }
    
    return null;
  }

  ageValidator(control: AbstractControl): {[key: string]: any} | null {
    const birthDate = control.value;
    if (!birthDate) return null;

    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }

    if (age < 18) {
      return { underage: true };
    }
    
    return null;
  }

  async onSubmit() {
    if (!this.registerForm.valid) {
      this.markFormGroupTouched();
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    try {
      const formData = this.registerForm.value;
      
      if (this.userType === 'candidato') {
        const candidatoData = {
          email: formData.email,
          password: formData.password,
          nombre: formData.nombre,
          apellido: formData.apellido,
          genero: formData.gender as 'masculino' | 'femenino' | 'otro',
          fecha_nacimiento: formData.birthDate
        };

        await this.authService.registerCandidato(candidatoData).toPromise();
      } else {
        const empresaData = {
          email: formData.email,
          password: formData.password,
          nombre: formData.nombre,
          descripcion: formData.descripcion
        };

        await this.authService.registerEmpresa(empresaData).toPromise();
      }
      
      alert('¡Registro exitoso! Ya puedes iniciar sesión.');
      this.router.navigate(['/login']);
    } catch (error: any) {
      console.error('Error en registro:', error);
      this.errorMessage = error.error?.detail || 'Error en el registro. Por favor, intenta de nuevo.';
    } finally {
      this.isLoading = false;
    }
  }

  markFormGroupTouched() {
    Object.keys(this.registerForm.controls).forEach(key => {
      const control = this.registerForm.get(key);
      control?.markAsTouched();
    });
  }

  getErrorMessage(fieldName: string): string {
    const control = this.registerForm.get(fieldName);
    if (!control || !control.errors || !control.touched) {
      return '';
    }

    if (control.errors['required']) {
      return `${fieldName} es requerido`;
    }
    if (control.errors['email']) {
      return 'Formato de email inválido';
    }
    if (control.errors['minlength']) {
      return 'Contraseña debe tener al menos 8 caracteres';
    }
    if (control.errors['onlyLetters']) {
      return 'Solo se permiten letras';
    }
    if (control.errors['underage']) {
      return 'Debes ser mayor de 18 años';
    }
    
    return '';
  }

  registerWithGoogle() {
    console.log('Google register - not implemented yet');
  }
}
