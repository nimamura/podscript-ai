"""
Test project structure and setup
"""
import sys
from pathlib import Path


def test_project_structure():
    """プロジェクト構造が正しいことを確認"""
    # Get project root directory
    project_root = Path(__file__).parent.parent
    
    # Check main directories exist
    assert (project_root / 'src').exists(), "src/ directory not found"
    assert (project_root / 'tests').exists(), "tests/ directory not found"
    assert (project_root / 'data').exists(), "data/ directory not found"
    
    # Check configuration files exist
    assert (project_root / 'requirements.txt').exists(), "requirements.txt not found"
    assert (project_root / 'pytest.ini').exists(), "pytest.ini not found"
    assert (project_root / '.env.example').exists(), ".env.example not found"


def test_python_packages():
    """Pythonパッケージとして認識されることを確認"""
    project_root = Path(__file__).parent.parent
    
    # Check __init__.py files exist
    assert (project_root / 'src' / '__init__.py').exists(), "src/__init__.py not found"
    assert (project_root / 'tests' / '__init__.py').exists(), "tests/__init__.py not found"


def test_imports():
    """srcパッケージがインポート可能であることを確認"""
    project_root = Path(__file__).parent.parent
    
    # Add src to Python path if not already there
    src_path = str(project_root / 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    # Try importing src package
    try:
        import src  # noqa: F401
        assert True
    except ImportError:
        assert False, "Failed to import src package"