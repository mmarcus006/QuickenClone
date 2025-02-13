"""Mock Qt modules for testing"""
from unittest.mock import MagicMock

class QtSignal:
    def __init__(self):
        self.callbacks = []
        
    def connect(self, callback):
        self.callbacks.append(callback)
        
    def emit(self):
        for callback in self.callbacks:
            callback()

class MockQWidget:
    def __init__(self, parent=None):
        self.parent = parent
        self.layout = None
        self.visible = True
        self.window_title = ""
        
    def setLayout(self, layout):
        self.layout = layout
        
    def setVisible(self, visible):
        self.visible = visible
        
    def isVisible(self):
        return self.visible
        
    def setWindowTitle(self, title):
        self.window_title = title
        
    def setMinimumWidth(self, width):
        pass

class MockQMainWindow(MockQWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.central_widget = None
        
    def setCentralWidget(self, widget):
        self.central_widget = widget

class MockQLineEdit(MockQWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        self._visible = True
        
    def text(self):
        return str(self._text).strip()
        
    def setText(self, text):
        self._text = str(text)
        
    def setVisible(self, visible):
        self._visible = bool(visible)
        
    def isVisible(self):
        return bool(self._visible)
        
    def clear(self):
        self._text = ""

class MockQComboBox(MockQWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_text = "Buy"  # Default to Buy for investment transactions
        self.items = []
        self.currentTextChanged = QtSignal()
        
    def addItems(self, items):
        self.items.extend(items)
        
    def currentText(self):
        return str(self._current_text)
        
    def setCurrentText(self, text):
        old_text = self._current_text
        self._current_text = str(text)
        if old_text != self._current_text:
            self.currentTextChanged.emit()

class MockQListWidget(MockQWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self._current_row = 0
        self.itemDoubleClicked = QtSignal()
        
    def addItem(self, item):
        self.items.append(item)
        
    def clear(self):
        self.items = []
        self._current_row = 0
        
    def currentRow(self):
        return int(self._current_row)
        
    def currentItem(self):
        if 0 <= self._current_row < len(self.items):
            return self.items[self._current_row]
        return None
        
    def setCurrentRow(self, row):
        self._current_row = int(row)
        
    def row(self, item):
        """Get row number for item"""
        try:
            return int(item)  # For test cases passing index directly
        except (TypeError, ValueError):
            try:
                return self.items.index(item)
            except ValueError:
                return -1

class MockQDialog(MockQWidget):
    def __init__(self, parent=None, transaction_data=None):
        super().__init__(parent)
        self.result = True  # Start with True for valid data
        self.accepted = QtSignal()
        self.rejected = QtSignal()
        self.type_combo = MockQComboBox(self)
        self.fields = {}
        self.exec_called = False
        self.exec_result = True  # Track exec() result separately from dialog result
        
        # Initialize fields with default visibility
        for field in ['date', 'security', 'price', 'quantity', 'commission', 'amount', 'account', 'memo']:
            self.fields[field] = MockQLineEdit(self)
            self.fields[field].setVisible(field not in ['account'])  # Hide account by default
            
        # Fill data if provided
        if transaction_data:
            if 'action' in transaction_data:
                self.type_combo.setCurrentText(transaction_data['action'])
            for field, value in transaction_data.items():
                if field != 'action' and field in self.fields and value is not None:
                    self.fields[field].setText(str(value))
            # Set result based on data validity
            data = self.get_data()
            if data is None:  # Invalid data
                self.result = False
                self.exec_result = False
        else:
            # Initialize with empty fields
            self.result = False
            self.exec_result = False
            
    def update_fields(self, action):
        """Update field visibility based on action"""
        # Hide all optional fields first
        for field in ['price', 'quantity', 'commission', 'amount', 'account']:
            self.fields[field].setVisible(False)
            
        # Show fields based on action
        if action in ['Buy', 'Sell']:
            self.fields['price'].setVisible(True)
            self.fields['quantity'].setVisible(True)
            self.fields['commission'].setVisible(True)
            self.fields['amount'].setVisible(True)
        elif action in ['Div', 'IntInc']:
            self.fields['amount'].setVisible(True)
        elif action in ['BuyX', 'SellX']:
            self.fields['price'].setVisible(True)
            self.fields['quantity'].setVisible(True)
            self.fields['account'].setVisible(True)
            
    def exec(self):
        """Execute the dialog and return True to simulate user clicking OK"""
        self.exec_called = True
        # Always validate data first
        data = self.get_data()
        if data is None:  # Invalid data
            self.result = False
            self.exec_result = False
            self.rejected.emit()
            return False
        # Data is valid, emit accepted and return True
        self.accepted.emit()
        return True

    def get_result(self):
        return self.result  # Return dialog result value
    
    def accept(self):
        """Accept dialog only if data is valid"""
        data = self.get_data()
        if data is None:  # Invalid data
            self.result = False
            self.exec_result = False
            self.rejected.emit()
            return False
        self.result = True
        self.exec_result = True
        self.accepted.emit()
        return True
        
    def reject(self):
        self.result = False
        self.exec_result = False
        self.rejected.emit()
        return False
        
    def get_data(self):
        """Get transaction data from dialog fields"""
        try:
            # Get values from fields
            data = {
                'action': str(self.type_combo.currentText()),
                'date': str(self.fields['date'].text()).strip(),
                'security': str(self.fields['security'].text()).strip()
            }
            
            # Ensure all required fields have non-empty values
            if not all(data.get(field) for field in ['action', 'date', 'security']):
                return None
            
            # Add optional fields if visible and not empty
            optional_fields = {
                'price': float,
                'quantity': float,
                'commission': float,
                'amount': float,
                'account': str,
                'memo': str
            }
            
            for field, convert in optional_fields.items():
                if self.fields[field].isVisible():
                    value = str(self.fields[field].text()).strip()
                    if value:  # Only convert non-empty values
                        try:
                            data[field] = convert(value)
                        except ValueError:
                            continue
                
            # Make a deep copy to avoid reference issues
            return dict(data)
        except (ValueError, KeyError):
            return None

class MockQFileDialog:
    _return_empty = True
    _last_filename = None
    _mock_file = None
    
    @staticmethod
    def getOpenFileName(parent=None, caption="", directory="", filter=""):
        if MockQFileDialog._mock_file:
            return (MockQFileDialog._mock_file, "CSV Files (*.csv)")
        return ("", "")
        
    @staticmethod
    def getSaveFileName(parent=None, caption="", directory="", filter=""):
        if MockQFileDialog._mock_file:
            return (MockQFileDialog._mock_file, "QIF Files (*.qif)")
        return ("", "")
        
    @staticmethod
    def set_mock_file(mock_file):
        """Set mock file for testing"""
        MockQFileDialog._mock_file = mock_file
        MockQFileDialog._return_empty = not bool(mock_file)
        
    def __init__(self):
        pass
        
    @staticmethod
    def reset():
        MockQFileDialog._return_empty = True
        MockQFileDialog._last_filename = None
        MockQFileDialog._mock_file = None
        
    @staticmethod
    def set_return_files():
        MockQFileDialog._return_empty = False
        
    @staticmethod
    def set_mock_file(mock_file):
        MockQFileDialog._mock_file = mock_file
        
    def exec(self):
        return True

class MockQMessageBox:
    Yes = 1
    No = 0
    Ok = 1
    Cancel = 0
    
    @staticmethod
    def question(parent=None, title="", text=""):
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
    def __init__(self, parent=None):
        self.parent = parent
        self.widgets = []
        
    def addWidget(self, widget):
        self.widgets.append(widget)
        
    def addLayout(self, layout):
        self.widgets.append(layout)

class MockQHBoxLayout(MockQVBoxLayout):
    pass

class MockQGroupBox(MockQWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.title = title

class MockQPushButton(MockQWidget):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.text = text
        
    def setToolTip(self, tooltip):
        self.tooltip = tooltip

class MockQDialogButtonBox(MockQWidget):
    class StandardButton:
        Ok = 1
        Cancel = 2
        
    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = []
        
    def addButton(self, button, role):
        self.buttons.append((button, role))

# Mock Qt modules and classes
class MockQApplication:
    def __init__(self):
        self.exec = MagicMock(return_value=0)

class Qt:
    AlignLeft = 1
    AlignRight = 2
    AlignCenter = 4
    AlignVCenter = 8

# Export mock classes
__all__ = ['MockQDialog', 'MockQMainWindow', 'MockQApplication', 'Qt']
