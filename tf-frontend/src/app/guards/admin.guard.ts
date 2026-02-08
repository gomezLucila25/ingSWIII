import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { CanActivateFn } from '@angular/router';
import { map, take } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';
import { UserService } from '../services/user.service';

export const adminGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const userService = inject(UserService);
  const router = inject(Router);

  // Verificar si está autenticado
  if (!authService.isAuthenticated()) {
    console.warn('🚫 No autenticado, redirigiendo a login');
    router.navigate(['/login']);
    return false;
  }

  // Verificar si es admin
  return userService.getCurrentUser().pipe(
    take(1),
    map(user => {
      if (user?.role === 'admin') {
        console.log('✅ Acceso permitido: Usuario es admin');
        return true;
      } else {
        console.warn('🚫 Acceso denegado: Usuario no es admin');
        alert('No tienes permisos para acceder a esta página');
        router.navigate(['/inicio']);
        return false;
      }
    })
  );
};