# Cypress Tests - Polo 52

Este directorio contiene los tests de integración E2E (End-to-End) usando Cypress.

## 📂 Estructura

```
cypress/
├── e2e/              # Tests E2E
│   ├── 01-landing.cy.ts      # Tests de landing page
│   ├── 02-login.cy.ts        # Tests de login
│   └── 03-navigation.cy.ts   # Tests de navegación
├── fixtures/         # Datos de prueba estáticos
├── support/          # Comandos y configuración
│   ├── commands.ts   # Comandos personalizados
│   └── e2e.ts        # Configuración global
└── README.md         # Este archivo
```

## 🚀 Ejecutar Tests Localmente

### Modo Interactivo (con UI)
```bash
npm run cypress:open
```

### Modo Headless (sin UI)
```bash
npm run cypress:run
```

### Con el servidor local corriendo
```bash
# Terminal 1: Iniciar Angular
npm start

# Terminal 2: Ejecutar Cypress
npm run cypress:run
```

### Todo en uno (inicia servidor + tests)
```bash
npm run e2e
```

## 📝 Escribir Tests

### Ejemplo básico
```typescript
describe('Mi Feature', () => {
  beforeEach(() => {
    cy.visit('/mi-pagina')
  })

  it('debería hacer algo', () => {
    cy.get('button').click()
    cy.contains('Resultado esperado').should('be.visible')
  })
})
```

### Usar comandos personalizados
```typescript
// Login
cy.login('usuario@test.com', 'password123')

// Registro
cy.register({
  email: 'nuevo@test.com',
  password: 'password123',
  nombre: 'Test User'
})
```

## 🎯 Mejores Prácticas

1. **Selectores**: Usar data attributes en lugar de clases CSS
   ```html
   <button data-cy="submit-btn">Enviar</button>
   ```
   ```typescript
   cy.get('[data-cy="submit-btn"]').click()
   ```

2. **Esperas**: Cypress espera automáticamente, no uses `wait()`
   ```typescript
   // ❌ Evitar
   cy.wait(5000)

   // ✅ Mejor
   cy.get('.loading').should('not.exist')
   ```

3. **Assertions**: Usar assertions claras
   ```typescript
   cy.get('h1').should('contain.text', 'Bienvenido')
   cy.url().should('include', '/dashboard')
   ```

## 🔧 Configuración

La configuración de Cypress está en `/cypress.config.ts`:
- **baseUrl**: URL base para los tests (localhost:4200 por defecto)
- **viewportWidth/Height**: Tamaño de ventana para los tests
- **video**: Grabar videos de los tests
- **screenshotOnRunFailure**: Capturar pantalla en fallos

## 📊 CI/CD

Los tests se ejecutan automáticamente en GitHub Actions después de:
1. Tests unitarios (Backend + Frontend)
2. Análisis de SonarCloud
3. Build de imágenes
4. Deploy a QA

Si los tests de Cypress **pasan** ✅ → Deploy a Producción
Si los tests **fallan** ❌ → No se deploya a Producción

## 📸 Artifacts

Cuando un test falla en CI:
- **Screenshots**: `cypress/screenshots/`
- **Videos**: `cypress/videos/`

Estos se suben como artifacts en GitHub Actions.

## 🐛 Debugging

### Ver test ejecutándose
```bash
npm run cypress:open
```

### Logs de Cypress
```typescript
cy.log('Mi mensaje de debug')
```

### Pausar ejecución
```typescript
cy.pause()
```

### Inspector de Cypress
Click en los comandos en el Test Runner para ver el estado del DOM.

## 📚 Recursos

- [Documentación de Cypress](https://docs.cypress.io/)
- [Best Practices](https://docs.cypress.io/guides/references/best-practices)
- [API Reference](https://docs.cypress.io/api/table-of-contents)
