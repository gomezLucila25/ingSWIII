import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';
import { LandingComponent } from './components/landing/landing.component';
import { RegisterComponent } from './components/register/register.component';
import { UserConfigComponent } from './pages/user-config/user-config.component';
import { MyUserComponent } from './pages/my-user/my-user.component';
import { AdminDashboardComponent } from './pages/admin-dashboard/admin-dashboard.component';
import { adminGuard } from './guards/admin.guard';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  // Landing page
  { path: '', component: LandingComponent },

  // Autenticación
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent }, // Nuevo componente de registro
  { path: 'user-config', component: UserConfigComponent }, // Registro completo alternativo

  // Mi perfil (protegido)
  { 
    path: 'mi-perfil', 
    component: MyUserComponent,
    canActivate: [authGuard]
  },
  { path: 'my-user', redirectTo: 'mi-perfil' }, // Redirect antigua ruta

  // Panel de administración (solo admin)
  {
    path: 'admin-dashboard',
    component: AdminDashboardComponent,
    canActivate: [adminGuard]
  },

  // Wildcard - redirigir a landing
  { path: '**', redirectTo: '' }
];
