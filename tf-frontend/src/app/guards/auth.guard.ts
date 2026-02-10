import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { CanActivateFn } from '@angular/router';
import { map, catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Verificar si está autenticado
  if (!authService.isAuthenticated()) {
    console.warn('🚫 No autenticado, redirigiendo a login');
    router.navigate(['/login']);
    return false;
  }

  // Verificar token válido
  return authService.validateToken().pipe(
    map(isValid => {
      if (!isValid) {
        console.warn('🚫 Token inválido, redirigiendo a login');
        router.navigate(['/login']);
        return false;
      }
      return true;
    }),
    catchError(() => {
      console.warn('🚫 Error validando token, redirigiendo a login');
      router.navigate(['/login']);
      return of(false);
    })
  );
};