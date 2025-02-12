"""Test GUI functionality with proper Qt mocking"""
import pytest
from unittest.mock import MagicMock, patch
import sys

# Create base mock classes
class MockQWidget:
    def __init__(self, parent=None):
        self.parent = parent
        self.layout = None
        self.visible = True
        
    def setLayout(self, layout):
        self.layout = layout
    
    def setVisible(self, visible):
        self.visible = visible
    
    def isVisible(self):
        return self.visible

class MockQMainWindow(MockQWidget):
    def __init__(self):
        super().__init__()
        self.central_widget = None
        self.title = ""
        
    def setCentralWidget(self, widget):
        self.central_widget = widget
        
    def setWindowTitle(self, title):
        self.title = title
        
    def setMinimumWidth(self, width):
        pass

class MockQDialog(MockQWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result = True
        
    def exec(self):
        return self.result
    
    def accept(self):
        self.result = True
        
    def reject(self):
        self.result = False

class MockQLineEdit(MockQWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        
    def text(self):
        return self._text
    
    def setText(self, text):
        self._text = text
        
    def setPlaceholderText(self, text):
        pass

class MockQComboBox(MockQWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self._current_text = ""
        
    def addItems(self, items):
        self.items.extend(items)
        if not self._current_text and items:
            self._current_text = items[0]
    
    def currentText(self):
        return self._current_text
    
    def setCurrentText(self, text):
        self._current_text = text

class MockQListWidget(MockQWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self._current_row = -1
        
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
        return None

class MockQFileDialog:
    @staticmethod
    def getOpenFileName(parent=None, caption="", directory="", filter=""):
        return "test.csv", filter
    
    @staticmethod
    def getSaveFileName(parent=None, caption="", directory="", filter=""):
        return "test.qif", filter

# Mock Qt modules
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
mock_widgets.QVBoxLayout = MagicMock
mock_widgets.QHBoxLayout = MagicMock
mock_widgets.QLabel = MagicMock
mock_widgets.QPushButton = MagicMock
mock_widgets.QMessageBox = MagicMock
mock_widgets.QGroupBox = MagicMock
mock_widgets.QDialogButtonBox = MagicMock

# Patch modules before importing
with patch.dict('sys.modules', {
    'PyQt6': mock_qt,
    'PyQt6.QtWidgets': mock_widgets,
    'PyQt6.QtCore': mock_core
}):
    from qif_gui import QIFConverterGUI, TransactionDialog
    from qif_converter import InvestmentAction

@pytest.fixture
def gui():
    """Create GUI instance"""
    return QIFConverterGUI()

def test_gui_initialization(gui):
    """Test GUI initialization"""
    assert hasattr(gui, 'transaction_list')
    assert hasattr(gui, 'transactions')
    assert len(gui.transactions) == 0
    assert isinstance(gui, MockQMainWindow)
    assert gui.title == "CSV to QIF Converter"

def test_add_transaction(gui):
    """Test adding a transaction"""
    dialog = TransactionDialog()
    dialog.type_combo = MockQComboBox()
    dialog.type_combo.setCurrentText(InvestmentAction.BUY.value)
    
    dialog.fields = {
        'date': MockQLineEdit(),
        'security': MockQLineEdit(),
        'price': MockQLineEdit(),
        'quantity': MockQLineEdit(),
        'commission': MockQLineEdit(),
        'memo': MockQLineEdit()
    }
    
    dialog.fields['date'].setText('01/15/2024')
    dialog.fields['security'].setText('AAPL')
    dialog.fields['price'].setText('185.92')
    dialog.fields['quantity'].setText('10')
    dialog.fields['commission'].setText('4.95')
    dialog.fields['memo'].setText('Test buy')
    
    with patch('qif_gui.TransactionDialog', return_value=dialog):
        gui.add_transaction()
    
    assert len(gui.transactions) == 1
    assert gui.transactions[0]['security'] == 'AAPL'
    assert gui.transactions[0]['action'] == InvestmentAction.BUY.value

def test_delete_transaction(gui):
    """Test deleting a transaction"""
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10
    }]
    
    gui.transaction_list = MockQListWidget()
    gui.transaction_list._current_row = 0
    gui.delete_transaction()
    assert len(gui.transactions) == 0

def test_duplicate_transaction(gui):
    """Test transaction duplication"""
    original_trans = {
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10
    }
    gui.transactions = [original_trans]
    
    gui.transaction_list = MockQListWidget()
    gui.transaction_list._current_row = 0
    
    dialog = TransactionDialog()
    dialog.type_combo = MockQComboBox()
    dialog.type_combo.setCurrentText(InvestmentAction.BUY.value)
    
    dialog.fields = {
        'date': MockQLineEdit(),
        'security': MockQLineEdit(),
        'price': MockQLineEdit(),
        'quantity': MockQLineEdit(),
        'commission': MockQLineEdit(),
        'memo': MockQLineEdit()
    }
    
    dialog.fields['date'].setText('01/16/2024')
    dialog.fields['security'].setText('AAPL')
    dialog.fields['price'].setText('185.92')
    dialog.fields['quantity'].setText('10')
    
    with patch('qif_gui.TransactionDialog', return_value=dialog):
        gui.duplicate_transaction()
    
    assert len(gui.transactions) == 2
    assert gui.transactions[1]['date'] == '01/16/2024'
    assert gui.transactions[1]['security'] == original_trans['security']

def test_export_qif(gui, tmp_path):
    """Test exporting to QIF"""
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10
    }]
    
    qif_file = tmp_path / "test.qif"
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=(str(qif_file), "QIF files (*.qif)")):
        gui.export_qif()
    
    with open(qif_file) as f:
        content = f.read()
        assert "!Type:Invst" in content
        assert "NBuy" in content
        assert "YAAPL" in content

def test_import_csv(gui, tmp_path):
    """Test importing from CSV"""
    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w") as f:
        f.write("""Transaction Type,Trade Date,Symbol,Price,Quantity,Commission,Notes
Buy,01/15/2024,AAPL,185.92,10,4.95,Test buy""")
    
    with patch('qif_gui.QFileDialog.getOpenFileName', return_value=(str(csv_file), "CSV files (*.csv)")):
        gui.import_csv()
    
    assert len(gui.transactions) == 1
    assert gui.transactions[0]['security'] == 'AAPL'
    assert gui.transactions[0]['action'] == InvestmentAction.BUY.value

def test_transaction_dialog():
    """Test transaction dialog"""
    dialog = TransactionDialog()
    dialog.type_combo = MockQComboBox()
    dialog.type_combo.setCurrentText(InvestmentAction.BUY.value)
    
    dialog.fields = {
        'date': MockQLineEdit(),
        'security': MockQLineEdit(),
        'price': MockQLineEdit(),
        'quantity': MockQLineEdit(),
        'commission': MockQLineEdit(),
        'memo': MockQLineEdit()
    }
    
    dialog.fields['date'].setText('01/15/2024')
    dialog.fields['security'].setText('AAPL')
    dialog.fields['price'].setText('185.92')
    dialog.fields['quantity'].setText('10')
    dialog.fields['commission'].setText('4.95')
    dialog.fields['memo'].setText('Test buy')
    
    data = dialog.get_data()
    assert data['action'] == InvestmentAction.BUY.value
    assert data['date'] == '01/15/2024'
    assert data['security'] == 'AAPL'
    assert float(data['price']) == 185.92
    assert float(data['quantity']) == 10
    assert float(data['commission']) == 4.95
    assert data['memo'] == 'Test buy'

def test_transaction_dialog_field_visibility():
    """Test transaction dialog field visibility"""
    dialog = TransactionDialog()
    dialog.fields = {
        'date': MockQLineEdit(),
        'security': MockQLineEdit(),
        'price': MockQLineEdit(),
        'quantity': MockQLineEdit(),
        'commission': MockQLineEdit(),
        'amount': MockQLineEdit(),
        'account': MockQLineEdit(),
        'memo': MockQLineEdit()
    }
    
    # Test Buy action
    dialog.update_fields(InvestmentAction.BUY.value)
    assert dialog.fields['price'].isVisible()
    assert dialog.fields['quantity'].isVisible()
    assert dialog.fields['commission'].isVisible()
    assert not dialog.fields['amount'].isVisible()
    assert not dialog.fields['account'].isVisible()
    
    # Test Div action
    dialog.update_fields(InvestmentAction.DIV.value)
    assert not dialog.fields['price'].isVisible()
    assert not dialog.fields['quantity'].isVisible()
    assert not dialog.fields['commission'].isVisible()
    assert dialog.fields['amount'].isVisible()
    assert not dialog.fields['account'].isVisible()
    
    # Test BuyX action
    dialog.update_fields(InvestmentAction.BUYX.value)
    assert dialog.fields['price'].isVisible()
    assert dialog.fields['quantity'].isVisible()
    assert not dialog.fields['commission'].isVisible()
    assert not dialog.fields['amount'].isVisible()
    assert dialog.fields['account'].isVisible()

def test_all_transaction_types():
    """Test all transaction types in dialog"""
    dialog = TransactionDialog()
    dialog.fields = {
        'date': MockQLineEdit(),
        'security': MockQLineEdit(),
        'price': MockQLineEdit(),
        'quantity': MockQLineEdit(),
        'commission': MockQLineEdit(),
        'amount': MockQLineEdit(),
        'account': MockQLineEdit(),
        'memo': MockQLineEdit()
    }
    
    for action in InvestmentAction:
        dialog.update_fields(action.value)
        if action in [InvestmentAction.BUY, InvestmentAction.SELL]:
            assert dialog.fields['price'].isVisible()
            assert dialog.fields['quantity'].isVisible()
            assert dialog.fields['commission'].isVisible()
        elif action in [InvestmentAction.DIV, InvestmentAction.INTINC]:
            assert dialog.fields['amount'].isVisible()
        elif action in [InvestmentAction.BUYX, InvestmentAction.SELLX]:
            assert dialog.fields['price'].isVisible()
            assert dialog.fields['quantity'].isVisible()
            assert dialog.fields['account'].isVisible()
