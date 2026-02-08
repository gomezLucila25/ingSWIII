#!/usr/bin/env python3
import os
import sys
import subprocess

def main():
    # Verificar directorio
    if not os.path.exists("main.py"):
        print("❌ Error: Ejecuta desde el directorio UserAPI")
        sys.exit(1)
    
    # Setup de dependencias
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        print("📦 Instalando dependencias básicas...")
        
        # Instalar dependencias una por una (más seguro)
        dependencies = ["pytest", "pytest-asyncio", "httpx", "pytest-mock"]
        
        for dep in dependencies:
            print(f"Instalando {dep}...")
            result = subprocess.run(f"pip install {dep}", shell=True)
            if result.returncode != 0:
                print(f"❌ Error instalando {dep}")
                return
        
        print("✅ Todas las dependencias instaladas correctamente")
        return
    
    # Ejecutar tests
    try:
        import pytest
        print("🧪 Ejecutando tests...")
        result = subprocess.run("pytest tests/ -v", shell=True)
        if result.returncode == 0:
            print("\n🎉 Tests completados!")
        else:
            print("\n💥 Algunos tests fallaron")
    except ImportError:
        print("❌ pytest no está instalado. Ejecuta: python run_tests.py --setup")

if __name__ == "__main__":
    main()