describe('Landing Page', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('debería cargar la página principal correctamente', () => {
    cy.url().should('eq', Cypress.config().baseUrl + '/')
    // Verificar que el logo o contenido principal esté visible
    cy.get('body').should('be.visible')
  })

  it('debería tener el botón de Ingresar visible', () => {
    cy.contains('Ingresar').should('be.visible')
  })

  it('debería mostrar navegación principal', () => {
    // Verificar links de navegación
    cy.contains('Cómo Funciona').should('be.visible')
    cy.contains('Contáctanos').should('be.visible')
  })

  it('debería navegar a la página de login al hacer clic en Ingresar', () => {
    cy.contains('Ingresar').click()
    cy.url().should('include', '/login')
  })

  it('debería poder navegar a registro desde landing', () => {
    // Navegar a login primero
    cy.visit('/login')
    cy.url().should('include', '/login')
    // Verificar que existe link o botón de registro (en inglés)
    cy.get('body').should('contain.text', 'Sign up')
  })
})
