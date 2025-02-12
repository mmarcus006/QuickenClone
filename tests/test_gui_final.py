import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock PyQt6 modules before importing our code
sys.modules['PyQt6'] = MagicMock()
sys.modules['PyQt6.QtWidgets'] = MagicMock()
sys.modules['PyQt6.QtCore'] = MagicMock()

# Import our mock modules
from .mock_qt import QtWidgets, QtCore

# Now patch the Qt imports in qif_gui
with patch.dict('sys.modules', {
    'PyQt6': MagicMock(),
    'PyQt6.QtWidgets': QtWidgets,
    'PyQt6.QtCore': QtCore
}):
    from qif_gui import QIFConverterGUI, TransactionDialog
    from qif_converter import InvestmentAction, QIFType

@pytest.fixture(autouse=True)
def setup_mocks():
    """Reset mocks before each test"""
    for name, obj in QtWidgets.__dict__.items():
        if isinstance(obj, MagicMock):
            obj.reset_mock()
    yield

def test_gui_initialization():
    """Test GUI initialization"""
    gui = QIFConverterGUI()
    assert isinstance(gui, QIFConverterGUI)
    assert hasattr(gui, 'transaction_list')
    assert hasattr(gui, 'transactions')
    assert len(gui.transactions) == 0

def test_add_transaction():
    """Test adding a transaction"""
    gui = QIFConverterGUI()
    
    # Mock transaction dialog
    mock_dialog = MagicMock()
    mock_dialog.exec.return_value = True
    mock_dialog.get_data.return_value = {
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10
    }
    
    with patch('qif_gui.TransactionDialog', return_value=mock_dialog):
        gui.add_transaction()
    
    assert len(gui.transactions) == 1
    assert gui.transactions[0]['security'] == 'AAPL'

def test_delete_transaction():
    """Test deleting a transaction"""
    gui = QIFConverterGUI()
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10
    }]
    
    QtWidgets.QMessageBox.question.return_value = QtWidgets.QMessageBox.Yes
    QtWidgets.QListWidget.return_value.currentRow.return_value = 0
    
    gui.delete_transaction()
    assert len(gui.transactions) == 0

def test_duplicate_transaction():
    """Test transaction duplication"""
    gui = QIFConverterGUI()
    original_trans = {
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10
    }
    gui.transactions = [original_trans]
    
    # Mock date input dialog
    QtWidgets.QDialog.return_value.exec.return_value = True
    QtWidgets.QLineEdit.return_value.text.return_value = '01/16/2024'
    QtWidgets.QListWidget.return_value.currentRow.return_value = 0
    
    gui.duplicate_transaction()
    assert len(gui.transactions) == 2
    assert gui.transactions[1]['date'] == '01/16/2024'
    assert gui.transactions[1]['security'] == original_trans['security']

def test_save_transactions(tmp_path):
    """Test saving transactions to QIF"""
    gui = QIFConverterGUI()
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10
    }]
    
    output_file = str(tmp_path / "test.qif")
    QtWidgets.QFileDialog.getSaveFileName.return_value = (output_file, "QIF files (*.qif)")
    
    gui.save_transactions()
    
    with open(output_file) as f:
        content = f.read()
        assert QIFType.INVESTMENT.value in content
        assert "NBuy" in content
        assert "YAAPL" in content

def test_load_transactions(tmp_path):
    """Test loading transactions from CSV"""
    gui = QIFConverterGUI()
    
    # Create test CSV
    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w") as f:
        f.write("Date,Action,Security,Price,Quantity\n")
        f.write("2024-01-15,Buy,AAPL,185.92,10\n")
    
    QtWidgets.QFileDialog.getOpenFileName.return_value = (str(csv_file), "CSV files (*.csv)")
    gui.load_transactions()
    
    assert len(gui.transactions) == 1
    assert gui.transactions[0]['security'] == 'AAPL'

def test_transaction_dialog():
    """Test transaction dialog functionality"""
    dialog = TransactionDialog()
    
    # Test field updates
    dialog.update_fields(InvestmentAction.BUY.value)
    dialog.update_fields(InvestmentAction.DIV.value)
    dialog.update_fields(InvestmentAction.BUYX.value)
    
    # Test data retrieval
    QtWidgets.QComboBox.return_value.currentText.return_value = InvestmentAction.BUY.value
    QtWidgets.QLineEdit.return_value.text.side_effect = [
        "01/15/2024",  # date
        "AAPL",        # security
        "185.92",      # price
        "10",          # quantity
        "4.95"         # commission
    ]
    
    data = dialog.get_data()
    assert data['action'] == InvestmentAction.BUY.value
    assert data['security'] == "AAPL"
    assert data['price'] == 185.92
    assert data['quantity'] == 10
    assert data['commission'] == 4.95

def test_transaction_dialog_field_visibility():
    """Test field visibility updates"""
    dialog = TransactionDialog()
    
    # Test Buy transaction fields
    dialog.update_fields(InvestmentAction.BUY.value)
    assert QtWidgets.QLineEdit.return_value.setVisible.called
    
    # Test Dividend transaction fields
    dialog.update_fields(InvestmentAction.DIV.value)
    assert QtWidgets.QLineEdit.return_value.setVisible.called
    
    # Test Transfer transaction fields
    dialog.update_fields(InvestmentAction.BUYX.value)
    assert QtWidgets.QLineEdit.return_value.setVisible.called
