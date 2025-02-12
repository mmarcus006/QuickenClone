"""Mock Qt classes for testing"""
from unittest.mock import MagicMock

class QtSignal:
    """Mock Qt signal"""
    def __init__(self):
        self.callbacks = []
        self.last_value = None
    
    def connect(self, callback):
        self.callbacks.append(callback)
    
    def emit(self, *args, **kwargs):
        self.last_value = args[0] if args else None
        for callback in self.callbacks:
            callback(*args, **kwargs)

class MockQWidget:
    """Base widget class"""
    def __init__(self, parent=None):
        self.parent = parent
        self.layout = None
        self._visible = True
        self.window_title = ""
        self.minimum_width = 0
        
    def setLayout(self, layout):
        self.layout = layout
    
    def setVisible(self, visible):
        self._visible = visible
    
    def isVisible(self):
        return self._visible
    
    def setWindowTitle(self, title):
        self.window_title = title
    
    def setMinimumWidth(self, width):
        self.minimum_width = width

class MockQMainWindow(MockQWidget):
    """Mock QMainWindow"""
    def __init__(self):
        super().__init__()
        self.central_widget = None
        
    def setCentralWidget(self, widget):
        self.central_widget = widget

class MockQDialog(MockQWidget):
    """Mock QDialog"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result = True
        self.accepted = QtSignal()
        self.rejected = QtSignal()
        
    def exec(self):
        self.result = True
        self.accepted.emit()
        return self.result
    
    def accept(self):
        self.result = True
        self.accepted.emit()
        
    def reject(self):
        self.result = False
        self.rejected.emit()
        return False

class MockQLineEdit(MockQWidget):
    """Mock QLineEdit"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        self._visible = True
        self.textChanged = QtSignal()
        
    def text(self):
        return self._text
    
    def setText(self, text):
        self._text = str(text) if text is not None else ""
        self.textChanged.emit(self._text)
        return True
        
    def setVisible(self, visible):
        self._visible = visible
        
    def isVisible(self):
        return self._visible

class MockQComboBox(MockQWidget):
    """Mock QComboBox"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self._current_text = ""
        self.currentTextChanged = QtSignal()
        
    def addItems(self, items):
        self.items.extend(items)
        if not self._current_text and items:
            self.setCurrentText(items[0])
    
    def currentText(self):
        return self._current_text
    
    def setCurrentText(self, text):
        old_text = self._current_text
        self._current_text = text
        if old_text != text:
            self.currentTextChanged.emit(text)

class MockQListWidget(MockQWidget):
    """Mock QListWidget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self._current_row = -1
        self.itemDoubleClicked = QtSignal()
        
    def addItem(self, item):
        self.items.append(item)
        
    def clear(self):
        self.items = []
        self._current_row = -1
        
    def currentRow(self):
        return self._current_row
    
    def currentItem(self):
        if 0 <= self._current_row < len(self.items):
            return self.items[self._current_row]
        return self.items[0] if self.items else None
    
    def setCurrentRow(self, row):
        self._current_row = row
        if 0 <= row < len(self.items):
            return True
        return False

class MockQFileDialog:
    """Mock QFileDialog"""
    @staticmethod
    def getOpenFileName(parent=None, caption="", directory="", filter=""):
        return directory or "/tmp/test.csv", filter
    
    @staticmethod
    def getSaveFileName(parent=None, caption="", directory="", filter=""):
        if not directory:
            directory = "/tmp/test.qif"
        if not directory.lower().endswith('.qif'):
            directory += '.qif'
        return directory, filter

class MockQMessageBox:
    """Mock QMessageBox"""
    Yes = 1
    No = 0
    Ok = 2
    Cancel = 3
    
    @staticmethod
    def question(parent=None, title="", text="", buttons=None, defaultButton=None):
        return MockQMessageBox.Yes
    
    @staticmethod
    def warning(parent=None, title="", text=""):
        return MockQMessageBox.Ok
    
    @staticmethod
    def information(parent=None, title="", text=""):
        return MockQMessageBox.Ok
    
    @staticmethod
    def critical(parent=None, title="", text=""):
        return MockQMessageBox.Ok

class MockQVBoxLayout:
    """Mock QVBoxLayout"""
    def __init__(self, parent=None):
        self.widgets = []
        self.layouts = []
        
    def addWidget(self, widget):
        self.widgets.append(widget)
        
    def addLayout(self, layout):
        self.layouts.append(layout)

class MockQHBoxLayout(MockQVBoxLayout):
    """Mock QHBoxLayout"""
    pass

class MockQGroupBox(MockQWidget):
    """Mock QGroupBox"""
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.title = title

class MockQPushButton(MockQWidget):
    """Mock QPushButton"""
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.text = text
        self.clicked = QtSignal()
        
    def setToolTip(self, text):
        self.tooltip = text

class MockQDialogButtonBox(MockQWidget):
    """Mock QDialogButtonBox"""
    class StandardButton:
        Ok = 0x00000400
        Cancel = 0x00000800
        
    def __init__(self, buttons=None, parent=None):
        super().__init__(parent)
        self.accepted = QtSignal()
        self.rejected = QtSignal()
        self.buttons = buttons
        
    def addButton(self, button, role):
        pass

# Create mock Qt modules
mock_qt = MagicMock()
mock_widgets = MagicMock()
mock_core = MagicMock()

# Setup Qt Core constants
mock_core.Qt = MagicMock()
mock_core.Qt.AlignLeft = 1
mock_core.Qt.AlignRight = 2
mock_core.Qt.AlignCenter = 4

# Setup widget classes
mock_widgets.QMainWindow = MockQMainWindow
mock_widgets.QDialog = MockQDialog
mock_widgets.QWidget = MockQWidget
mock_widgets.QLineEdit = MockQLineEdit
mock_widgets.QComboBox = MockQComboBox
mock_widgets.QListWidget = MockQListWidget
mock_widgets.QFileDialog = MockQFileDialog
mock_widgets.QMessageBox = MockQMessageBox
mock_widgets.QVBoxLayout = MockQVBoxLayout
mock_widgets.QHBoxLayout = MockQHBoxLayout
mock_widgets.QGroupBox = MockQGroupBox
mock_widgets.QPushButton = MockQPushButton
mock_widgets.QDialogButtonBox = MockQDialogButtonBox
