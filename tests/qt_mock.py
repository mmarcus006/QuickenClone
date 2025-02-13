"""Mock PyQt6 modules for testing"""
from unittest.mock import MagicMock

# Create Qt constants
class Qt:
    AlignLeft = 1
    AlignRight = 2
    AlignCenter = 4
    AlignVCenter = 8

# Create base widget classes
class QWidget(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = None
        self.parent = lambda: None

class QMainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.central_widget = None
        self.setCentralWidget = lambda w: setattr(self, 'central_widget', w)

class QDialog(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exec = MagicMock(return_value=True)
        self.accept = MagicMock()
        self.reject = MagicMock()

class QApplication(MagicMock):
    @staticmethod
    def exec():
        return 0

# Create layout classes
class QVBoxLayout(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = []
        self.addWidget = lambda w: self.items.append(w)
        self.addLayout = lambda l: self.items.append(l)

class QHBoxLayout(QVBoxLayout): pass
class QGridLayout(QVBoxLayout): pass

# Create widget classes
class QLabel(QWidget): pass
class QLineEdit(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = MagicMock(return_value="test")
        self.setText = MagicMock()
        self.setPlaceholderText = MagicMock()

class QComboBox(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = []
        self.current_text = "test"
        self.addItems = lambda items: self.items.extend(items)
        self.currentText = lambda: self.current_text
        self.setCurrentText = lambda t: setattr(self, 'current_text', t)

class QPushButton(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clicked = MagicMock()
        self.setToolTip = MagicMock()

class QFileDialog:
    @staticmethod
    def getOpenFileName(*args, **kwargs):
        return ("test.csv", "CSV Files (*.csv)")
    
    @staticmethod
    def getSaveFileName(*args, **kwargs):
        return ("test.qif", "QIF Files (*.qif)")

class QMessageBox:
    Yes = 1
    No = 0
    Ok = 1
    Cancel = 0
    
    @staticmethod
    def question(*args, **kwargs):
        return QMessageBox.Yes
    
    @staticmethod
    def warning(*args, **kwargs):
        pass
    
    @staticmethod
    def critical(*args, **kwargs):
        pass
    
    @staticmethod
    def information(*args, **kwargs):
        pass

class QListWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = []
        self.current_row = 0
        self.addItem = lambda item: self.items.append(item)
        self.currentRow = lambda: self.current_row
        self.clear = lambda: self.items.clear()
        self.itemDoubleClicked = MagicMock()

class QGroupBox(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout = MagicMock()

class QDialogButtonBox(QWidget):
    Ok = 1
    Cancel = 2
    StandardButton = type('StandardButton', (), {'Ok': Ok, 'Cancel': Cancel})
    ButtonRole = type('ButtonRole', (), {'ActionRole': 1})
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.accepted = MagicMock()
        self.rejected = MagicMock()
        self.addButton = MagicMock()

# Create module structure
QtWidgets = type('QtWidgets', (), {
    'QMainWindow': QMainWindow,
    'QDialog': QDialog,
    'QWidget': QWidget,
    'QVBoxLayout': QVBoxLayout,
    'QHBoxLayout': QHBoxLayout,
    'QGridLayout': QGridLayout,
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
