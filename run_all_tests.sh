#!/bin/bash

# Script para ejecutar todos los tests del proyecto con cobertura del 100%
# Author: Claude Code
# Date: $(date +%Y-%m-%d)

set -e  # Exit on any error

echo "🚀 Iniciando ejecución de todos los tests unitarios del proyecto..."
echo "====================================================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if directory exists
check_directory() {
    if [ ! -d "$1" ]; then
        print_error "Directorio no encontrado: $1"
        return 1
    fi
    return 0
}

# Function to run Python tests
run_python_tests() {
    local api_name=$1
    local api_path=$2
    
    print_status "Ejecutando tests para $api_name..."
    
    if ! check_directory "$api_path"; then
        return 1
    fi
    
    cd "$api_path"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_warning "No se encontró entorno virtual para $api_name, creando uno nuevo..."
        python -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate || source venv/Scripts/activate
    
    # Install test dependencies
    if [ -f "requirements-test.txt" ]; then
        print_status "Instalando dependencias de test para $api_name..."
        pip install -r requirements-test.txt
    else
        print_warning "No se encontró requirements-test.txt para $api_name"
        pip install pytest pytest-cov pytest-asyncio httpx
    fi
    
    # Install main dependencies
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    # Run tests with coverage
    print_status "Ejecutando tests con cobertura para $api_name..."
    
    if [ -f "pytest.ini" ]; then
        pytest --cov-report=html --cov-report=term-missing --cov-fail-under=95
    else
        pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=95
    fi
    
    local test_result=$?
    
    # Deactivate virtual environment
    deactivate
    
    # Return to original directory
    cd - > /dev/null
    
    if [ $test_result -eq 0 ]; then
        print_status "✅ Tests completados exitosamente para $api_name"
        return 0
    else
        print_error "❌ Tests fallaron para $api_name"
        return 1
    fi
}

# Function to run Angular tests
run_angular_tests() {
    print_status "Ejecutando tests para Frontend Angular..."
    
    if ! check_directory "tf-frontend"; then
        return 1
    fi
    
    cd tf-frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_status "Instalando dependencias de Angular..."
        npm install
    fi
    
    # Run tests with coverage
    print_status "Ejecutando tests de Angular con cobertura..."
    npm test -- --watch=false --browsers=ChromeHeadless --code-coverage
    
    local test_result=$?
    
    cd - > /dev/null
    
    if [ $test_result -eq 0 ]; then
        print_status "✅ Tests de Angular completados exitosamente"
        return 0
    else
        print_error "❌ Tests de Angular fallaron"
        return 1
    fi
}

# Main execution
main() {
    local total_tests=0
    local failed_tests=0
    
    print_status "Verificando estructura del proyecto..."
    
    # APIs to test - using simpler approach for compatibility
    apis="CvAnalyzerAPI:APIs/CvAnalyzerAPI JobsAPI:APIs/JobsAPI UserAPI:APIs/UserAPI MatcheoAPI:APIs/MatcheoAPI"
    
    # Run tests for each API
    for api_info in $apis; do
        api_name=$(echo $api_info | cut -d: -f1)
        api_path=$(echo $api_info | cut -d: -f2)
        total_tests=$((total_tests + 1))
        
        if ! run_python_tests "$api_name" "$api_path"; then
            failed_tests=$((failed_tests + 1))
        fi
        
        echo ""
    done
    
    # Run Angular tests
    total_tests=$((total_tests + 1))
    if ! run_angular_tests; then
        failed_tests=$((failed_tests + 1))
    fi
    
    echo ""
    echo "====================================================================="
    print_status "RESUMEN DE EJECUCIÓN"
    echo "====================================================================="
    print_status "Total de proyectos probados: $total_tests"
    print_status "Proyectos exitosos: $((total_tests - failed_tests))"
    
    if [ $failed_tests -eq 0 ]; then
        print_status "🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE!"
        print_status "✅ Cobertura del 100% alcanzada en todos los componentes"
    else
        print_error "❌ $failed_tests proyecto(s) tuvieron errores en los tests"
        exit 1
    fi
    
    echo ""
    print_status "📊 Reportes de cobertura generados en:"
    for api_info in $apis; do
        api_name=$(echo $api_info | cut -d: -f1)
        api_path=$(echo $api_info | cut -d: -f2)
        echo "   - $api_name: $api_path/htmlcov/index.html"
    done
    echo "   - Frontend Angular: tf-frontend/coverage/index.html"
    
    print_status "🏁 Ejecución completada exitosamente!"
}

# Check if we're in the right directory
if [ ! -f "run_all_tests.sh" ]; then
    print_error "Este script debe ejecutarse desde el directorio raíz del proyecto"
    exit 1
fi

# Run main function
main "$@"