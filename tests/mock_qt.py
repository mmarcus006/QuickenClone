"""Mock PyQt6 modules for testing"""
from unittest.mock import MagicMock

# Create Qt constants
class Qt:
    AlignLeft = 1
    AlignRight = 2
    AlignCenter = 4
    AlignVCenter = 8

# Create widget mocks
class QMainWindow(MagicMock): pass
class QDialog(MagicMock): pass
class QWidget(MagicMock): pass
class QVBoxLayout(MagicMock): pass
class QHBoxLayout(MagicMock): pass
class QLabel(MagicMock): pass
class QComboBox(MagicMock): pass
class QPushButton(MagicMock): pass
class QFileDialog(MagicMock): pass
class QMessageBox(MagicMock):
    Yes = 1
    No = 0
    question = MagicMock(return_value=Yes)
class QLineEdit(MagicMock): pass
class QListWidget(MagicMock): pass
class QGroupBox(MagicMock): pass
class QDialogButtonBox(MagicMock): pass
class QApplication(MagicMock): pass

# Create module structure
QtWidgets = type('QtWidgets', (), {
    'QMainWindow': QMainWindow,
    'QDialog': QDialog,
    'QWidget': QWidget,
    'QVBoxLayout': QVBoxLayout,
    'QHBoxLayout': QHBoxLayout,
    'QLabel': QLabel,
    'QComboBox': QComboBox,
    'QPushButton': QPushButton,
    'QFileDialog': QFileDialog,
    'QMessageBox': QMessageBox,
    'QLineEdit': QLineEdit,
    'QListWidget': QListWidget,
    'QGroupBox': QGroupBox,
    'QDialogButtonBox': QDialogButtonBox,
    'QApplication': QApplication
})()

QtCore = type('QtCore', (), {'Qt': Qt})()

# Export modules
__all__ = ['QtWidgets', 'QtCore']
