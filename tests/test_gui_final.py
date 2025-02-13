"""Test GUI components with proper mocking"""
import pytest
from unittest.mock import MagicMock, patch
import sys

# Import our mock modules
from qt_mock import QtWidgets, QtCore

# Patch Qt modules before importing our code
sys.modules['PyQt6'] = MagicMock()
sys.modules['PyQt6.QtWidgets'] = QtWidgets
sys.modules['PyQt6.QtCore'] = QtCore

# Now we can safely import our modules
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
    assert hasattr(gui, 'transaction_list')
    assert hasattr(gui, 'transactions')
    assert len(gui.transactions) == 0

def test_add_transaction():
    """Test adding a transaction"""
    gui = QIFConverterGUI()
    
    # Set up mock dialog data
    QtWidgets.QDialog.return_value.exec.return_value = True
    QtWidgets.QComboBox.return_value.currentText.return_value = InvestmentAction.BUY.value
    QtWidgets.QLineEdit.return_value.text.side_effect = [
        "01/15/2024",  # date
        "AAPL",        # security
        "185.92",      # price
        "10",          # quantity
        "4.95"         # commission
    ]
    
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
    
    # Mock list widget and dialog
    QtWidgets.QListWidget.return_value.currentRow.return_value = 0
    QtWidgets.QDialog.return_value.exec.return_value = True
    QtWidgets.QLineEdit.return_value.text.return_value = '01/16/2024'
    
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
    QtWidgets.QFileDialog.getSaveFileName = lambda *args, **kwargs: (output_file, "QIF files (*.qif)")
    
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
        f.write("Transaction Type,Trade Date,Symbol,Price,Quantity,Commission,Notes\n")
        f.write("Buy,01/15/2024,AAPL,185.92,10,4.95,Test buy\n")
    
    QtWidgets.QFileDialog.getOpenFileName = lambda *args, **kwargs: (str(csv_file), "CSV files (*.csv)")
    gui.import_csv()
    
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

def test_error_handling():
    """Test error handling in GUI"""
    gui = QIFConverterGUI()
    
    # Test invalid file load
    QtWidgets.QFileDialog.getOpenFileName = lambda *args, **kwargs: ("nonexistent.csv", "CSV files (*.csv)")
    gui.import_csv()  # Should not raise exception
    
    # Test invalid transaction deletion
    QtWidgets.QListWidget.return_value.currentRow.return_value = None
    gui.delete_transaction()  # Should not raise exception when no transaction selected
    
    # Test invalid transaction duplication
    QtWidgets.QListWidget.return_value.currentRow.return_value = None
    gui.duplicate_transaction()  # Should not raise exception when no transaction selected

def test_edit_transaction():
    """Test editing an existing transaction"""
    gui = QIFConverterGUI()
    original_trans = {
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10
    }
    gui.transactions = [original_trans]
    
    # Mock list widget and dialog
    QtWidgets.QListWidget.return_value.currentRow.return_value = 0
    QtWidgets.QDialog.return_value.exec.return_value = True
    QtWidgets.QComboBox.return_value.currentText.return_value = InvestmentAction.SELL.value
    QtWidgets.QLineEdit.return_value.text.side_effect = [
        "01/16/2024",  # date
        "AAPL",        # security
        "190.00",      # price
        "5",           # quantity
        "4.95"         # commission
    ]
    
    # Simulate double-click
    item = MagicMock()
    gui.edit_transaction(item)
    
    assert len(gui.transactions) == 1
    assert gui.transactions[0]['action'] == InvestmentAction.SELL.value
    assert gui.transactions[0]['date'] == '01/16/2024'
    assert gui.transactions[0]['price'] == 190.00
    assert gui.transactions[0]['quantity'] == 5
