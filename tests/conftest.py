import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock PyQt6 modules before they're imported by any test
def pytest_configure():
    qt_mocks = {
        'PyQt6.QtWidgets': [
            'QApplication', 'QMainWindow', 'QDialog', 'QVBoxLayout',
            'QHBoxLayout', 'QLabel', 'QComboBox', 'QPushButton',
            'QFileDialog', 'QMessageBox', 'QLineEdit', 'QListWidget',
            'QGroupBox', 'QDialogButtonBox', 'QWidget'
        ],
        'PyQt6.QtCore': ['Qt']
    }
    
    for module, classes in qt_mocks.items():
        mock_module = MagicMock()
        for cls in classes:
            setattr(mock_module, cls, MagicMock())
        sys.modules[module] = mock_module
        
    # Mock Qt constants
    sys.modules['PyQt6.QtCore'].Qt.AlignLeft = 1
    sys.modules['PyQt6.QtCore'].Qt.AlignRight = 2
