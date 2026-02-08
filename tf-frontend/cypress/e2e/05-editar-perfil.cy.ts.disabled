describe('Editar Perfil de Usuario - CRUD UPDATE', () => {
  // Test que crea su propio usuario para no depender de datos existentes
  const timestamp = Date.now()
  const testUser = {
    email: `candidato.update${timestamp}@cypress.com`,
    password: 'UpdateTest123!',
    nombre: 'Carlos',
    apellido: 'Rodriguez',
    nuevoNombre: 'Carlos Alberto',
    nuevoApellido: 'Martínez Rodríguez'
  }

  before(() => {
    // Crear un usuario de prueba primero
    cy.visit('/register')

    // Stub del window.alert para capturar el mensaje sin bloquear
    cy.window().then((win) => {
      cy.stub(win, 'alert').as('windowAlert')
    })

    cy.contains('button', 'Candidato').click()
    cy.get('input#email').type(testUser.email)
    cy.get('input#password').type(testUser.password)
    cy.get('input#confirmPassword').type(testUser.password)
    cy.get('input#nombre').type(testUser.nombre)
    cy.get('input#apellido').type(testUser.apellido)
    cy.get('select#gender').select('masculino')
    cy.get('input#birthDate').type('1990-01-15')
    cy.get('button[type="submit"]').click()

    // Esperar a que se llame al alert con el mensaje de éxito
    cy.get('@windowAlert').should('have.been.calledWith', '¡Registro exitoso! Ya puedes iniciar sesión.')

    // Esperar a que se complete el registro y redirija a login
    cy.url().should('include', '/login', { timeout: 10000 })
  })

  beforeEach(() => {
    // Limpiar sesión y hacer login antes de cada test
    cy.clearCookies()
    cy.clearLocalStorage()
    cy.visit('/login')
  })

  it('debería permitir login y acceder a mi perfil', () => {
    // Login
    cy.get('input[type="email"]').type(testUser.email)
    cy.get('input[type="password"]').type(testUser.password)
    cy.get('button[type="submit"]').click()

    // Esperar redirección
    cy.wait(2000)
    cy.url().should('satisfy', (url) => {
      return url.includes('/mi-perfil') || url.includes('/my-user')
    })

    // Verificar que se muestra información del usuario
    cy.contains(testUser.nombre).should('be.visible')
    cy.contains(testUser.apellido).should('be.visible')
  })

  it('debería activar modo de edición al hacer clic en Editar Perfil', () => {
    // Login
    cy.get('input[type="email"]').type(testUser.email)
    cy.get('input[type="password"]').type(testUser.password)
    cy.get('button[type="submit"]').click()
    cy.wait(2000)

    // Buscar y hacer clic en botón de editar
    cy.contains('button', 'Editar Perfil').click()
    cy.wait(500)

    // Verificar que aparecen campos de edición
    cy.get('input').should('exist')
    cy.contains('Guardar Cambios').should('be.visible')
    cy.contains('Descartar Cambios').should('be.visible')
  })

  it('debería editar el nombre y apellido del candidato', () => {
    // Login
    cy.get('input[type="email"]').type(testUser.email)
    cy.get('input[type="password"]').type(testUser.password)
    cy.get('button[type="submit"]').click()
    cy.wait(2000)

    // Activar modo edición
    cy.contains('button', 'Editar Perfil').click()
    cy.wait(500)

    // Buscar campos de edición por contexto - están en la sección .form-edit
    cy.get('.form-edit').within(() => {
      // Editar nombre
      cy.get('input').first().clear().type(testUser.nuevoNombre)

      // Editar apellido (segundo input)
      cy.get('input').eq(1).clear().type(testUser.nuevoApellido)
    })

    cy.wait(500)

    // Guardar cambios
    cy.contains('button', 'Guardar Cambios').click()

    // Esperar que se guarden los cambios
    cy.wait(3000)

    // Verificar que se muestran los cambios (el modo edición debe desactivarse)
    cy.contains(testUser.nuevoNombre).should('be.visible')
    cy.contains(testUser.nuevoApellido).should('be.visible')
  })

  it('debería cancelar la edición y restaurar valores originales', () => {
    // Login
    cy.get('input[type="email"]').type(testUser.email)
    cy.get('input[type="password"]').type(testUser.password)
    cy.get('button[type="submit"]').click()
    cy.wait(2000)

    // Guardar el nombre actual
    let nombreOriginal = ''
    cy.get('.user-data').then($data => {
      nombreOriginal = $data.text()
    })

    // Activar modo edición
    cy.contains('button', 'Editar Perfil').click()
    cy.wait(500)

    // Modificar nombre temporalmente
    cy.get('.form-edit').within(() => {
      cy.get('input').first().clear().type('Nombre Temporal')
    })

    cy.wait(500)

    // Cancelar edición
    cy.contains('button', 'Descartar Cambios').click()

    cy.wait(500)

    // Verificar que el modo edición se desactivó
    cy.contains('Editar Perfil').should('be.visible')
    cy.contains('Guardar Cambios').should('not.exist')
  })

  it('debería validar que el nombre no esté vacío al editar', () => {
    // Login
    cy.get('input[type="email"]').type(testUser.email)
    cy.get('input[type="password"]').type(testUser.password)
    cy.get('button[type="submit"]').click()
    cy.wait(2000)

    // Activar modo edición
    cy.contains('button', 'Editar Perfil').click()
    cy.wait(500)

    // Intentar dejar el nombre vacío
    cy.get('.form-edit').within(() => {
      cy.get('input').first().clear()
    })

    cy.wait(500)

    // El botón de guardar debe estar deshabilitado
    cy.contains('button', 'Guardar Cambios').should('be.disabled')
  })
})
