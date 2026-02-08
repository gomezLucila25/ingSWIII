import { defineConfig } from 'cypress'

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:4200',
    viewportWidth: 1280,
    viewportHeight: 720,
    video: false,
    screenshotOnRunFailure: true,

    // Configuración para CI/CD
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },

    // Reporter para GitHub Actions
    reporter: 'junit',
    reporterOptions: {
      mochaFile: 'cypress/results/results-[hash].xml',
      toConsole: true,
    },
  },

  // Variables de entorno
  env: {
    apiUrl: 'http://localhost:8000',
  },
})
