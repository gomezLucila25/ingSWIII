describe('Navigation', () => {
  it('debería navegar correctamente entre páginas públicas', () => {
    cy.visit('/')

    // Verificar que la página principal carga
    cy.url().should('eq', Cypress.config().baseUrl + '/')

    // Navegar a Login
    cy.visit('/login')
    cy.url().should('include', '/login')
    cy.contains('Nice to see you again').should('be.visible')

    // Navegar a User Config (registro/configuración de usuario)
    cy.visit('/user-config')
    // Verificar que la página carga (puede redirigir a login si no está autenticado)
    cy.get('body').should('be.visible')

    // Volver al inicio
    cy.visit('/')
    cy.url().should('eq', Cypress.config().baseUrl + '/')
  })

  it('debería tener navegación consistente', () => {
    cy.visit('/')
    // Verificar que existe navegación (nav, header, o links)
    cy.get('body').should('contain.text', 'Ingresar')

    cy.visit('/login')
    cy.get('body').should('be.visible')
  })

  it('debería proteger rutas de admin (sin estar autenticado)', () => {
    cy.visit('/admin-dashboard')

    // Debería redirigir a login o inicio
    cy.url().should('satisfy', (url: string) => {
      return url.includes('/login') || url.includes('/inicio') || url === Cypress.config().baseUrl + '/'
    })
  })
})
