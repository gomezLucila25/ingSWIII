# tests/test_minimal.py
import pytest

def test_python_works():
    """Test súper básico"""
    assert True
    print("✅ Python funciona")

def test_pytest_works():
    """Test que pytest funciona"""
    import pytest
    assert pytest is not None
    print("✅ Pytest funciona")

def test_basic_imports():
    """Test de imports básicos"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        print("✅ Dependencias principales importan correctamente")
        assert True
    except ImportError as e:
        pytest.fail(f"Error importando: {e}")

def test_simple_math():
    """Test de lógica básica"""
    assert 2 + 2 == 4
    assert "test" in "testing"
    print("✅ Lógica básica funciona")

def test_list_operations():
    """Test de operaciones con listas"""
    test_list = [1, 2, 3]
    assert len(test_list) == 3
    assert 2 in test_list
    print("✅ Operaciones con listas funcionan")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])