describe('Login Flow', () => {
  beforeEach(() => {
    cy.visit('/login')
  })

  it('debería mostrar el formulario de login', () => {
    // Verificar que estamos en login
    cy.url().should('include', '/login')
    cy.contains('Nice to see you again').should('be.visible')

    // Verificar campos del formulario
    cy.get('input[type="email"]').should('be.visible')
    cy.get('input[type="password"]').should('be.visible')
    cy.get('button[type="submit"]').should('exist')
  })

  it('debería mostrar error con credenciales inválidas', () => {
    cy.get('input[type="email"]').type('usuario@invalido.com')
    cy.get('input[type="password"]').type('passwordincorrecto')
    cy.get('button[type="submit"]').click()

    // Esperar respuesta del servidor y verificar que sigue en login
    cy.wait(2000)
    cy.url().should('include', '/login')
  })

  it('debería deshabilitar el botón con campos vacíos', () => {
    // El botón debe estar deshabilitado cuando los campos están vacíos
    cy.get('button[type="submit"]').should('be.disabled')
  })

  it('debería habilitar el botón con campos llenos', () => {
    cy.get('input[type="email"]').type('test@test.com')
    cy.get('input[type="password"]').type('password123')

    // Esperar a que Angular procese la validación
    cy.wait(500)

    // El botón debería estar habilitado ahora
    cy.get('button[type="submit"]').should('not.be.disabled')
  })

  it('debería mostrar link o botón para registro', () => {
    // Verificar que existe opción para ir a registro (en inglés)
    cy.get('body').should('contain.text', 'Sign up')
  })
})
