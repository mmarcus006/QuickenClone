"""Test core GUI functionality with minimal mocking"""
import pytest
from unittest.mock import MagicMock, patch
import sys
from datetime import datetime

# Create minimal mock modules
mock_qt = MagicMock()
mock_widgets = MagicMock()
mock_core = MagicMock()

# Patch modules before importing
sys.modules['PyQt6'] = mock_qt
sys.modules['PyQt6.QtWidgets'] = mock_widgets
sys.modules['PyQt6.QtCore'] = mock_core

# Now import our modules
from qif_gui import QIFConverterGUI, TransactionDialog
from qif_converter import InvestmentAction, QIFType

@pytest.fixture
def gui():
    """Create GUI instance with mocked widgets"""
    with patch('PyQt6.QtWidgets.QMainWindow'), \
         patch('PyQt6.QtWidgets.QWidget'), \
         patch('PyQt6.QtWidgets.QVBoxLayout'), \
         patch('PyQt6.QtWidgets.QHBoxLayout'), \
         patch('PyQt6.QtWidgets.QLabel'), \
         patch('PyQt6.QtWidgets.QComboBox'), \
         patch('PyQt6.QtWidgets.QPushButton'), \
         patch('PyQt6.QtWidgets.QFileDialog'), \
         patch('PyQt6.QtWidgets.QMessageBox'), \
         patch('PyQt6.QtWidgets.QLineEdit'), \
         patch('PyQt6.QtWidgets.QListWidget'), \
         patch('PyQt6.QtWidgets.QGroupBox'), \
         patch('PyQt6.QtWidgets.QDialogButtonBox'):
        gui = QIFConverterGUI()
        yield gui

@pytest.fixture
def dialog():
    """Create dialog instance with mocked widgets"""
    with patch('PyQt6.QtWidgets.QDialog'), \
         patch('PyQt6.QtWidgets.QVBoxLayout'), \
         patch('PyQt6.QtWidgets.QHBoxLayout'), \
         patch('PyQt6.QtWidgets.QLabel'), \
         patch('PyQt6.QtWidgets.QComboBox'), \
         patch('PyQt6.QtWidgets.QLineEdit'), \
         patch('PyQt6.QtWidgets.QGroupBox'), \
         patch('PyQt6.QtWidgets.QDialogButtonBox'):
        dialog = TransactionDialog()
        yield dialog

def test_gui_initialization(gui):
    """Test GUI initialization"""
    assert hasattr(gui, 'transaction_list')
    assert hasattr(gui, 'transactions')
    assert len(gui.transactions) == 0

def test_add_transaction(gui):
    """Test adding a transaction"""
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

def test_delete_transaction(gui):
    """Test deleting a transaction"""
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10
    }]
    
    mock_list = MagicMock()
    mock_list.currentRow.return_value = 0
    gui.transaction_list = mock_list
    
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
    
    mock_list = MagicMock()
    mock_list.currentRow.return_value = 0
    mock_list.currentItem.return_value = MagicMock()
    gui.transaction_list = mock_list
    
    mock_dialog = MagicMock()
    mock_dialog.exec.return_value = True
    mock_dialog.findChild.return_value.text.return_value = '01/16/2024'
    
    with patch('PyQt6.QtWidgets.QDialog', return_value=mock_dialog):
        gui.duplicate_transaction()
    
    assert len(gui.transactions) == 2
    assert gui.transactions[1]['date'] == '01/16/2024'
    assert gui.transactions[1]['security'] == original_trans['security']

def test_save_transactions(gui, tmp_path):
    """Test saving transactions to QIF"""
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10
    }]
    
    output_file = str(tmp_path / "test.qif")
    mock_dialog = MagicMock()
    mock_dialog.getSaveFileName.return_value = (output_file, "QIF files (*.qif)")
    
    with patch('PyQt6.QtWidgets.QFileDialog', mock_dialog):
        gui.export_qif()
    
    with open(output_file) as f:
        content = f.read()
        assert QIFType.INVESTMENT.value in content
        assert "NBuy" in content
        assert "YAAPL" in content

def test_load_transactions(gui, tmp_path):
    """Test loading transactions from CSV"""
    # Create test CSV
    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w") as f:
        f.write("Transaction Type,Trade Date,Symbol,Price,Quantity,Commission,Notes\n")
        f.write("Buy,01/15/2024,AAPL,185.92,10,4.95,Test buy\n")
    
    mock_dialog = MagicMock()
    mock_dialog.getOpenFileName.return_value = (str(csv_file), "CSV files (*.csv)")
    
    with patch('PyQt6.QtWidgets.QFileDialog', mock_dialog):
        gui.import_csv()
    
    assert len(gui.transactions) == 1
    assert gui.transactions[0]['security'] == 'AAPL'

def test_transaction_dialog(dialog):
    """Test transaction dialog functionality"""
    # Test field updates
    dialog.update_fields(InvestmentAction.BUY.value)
    dialog.update_fields(InvestmentAction.DIV.value)
    dialog.update_fields(InvestmentAction.BUYX.value)
    
    # Test data retrieval
    mock_combo = MagicMock()
    mock_combo.currentText.return_value = InvestmentAction.BUY.value
    dialog.type_combo = mock_combo
    
    mock_fields = {}
    for field in ['date', 'security', 'price', 'quantity', 'commission']:
        mock_field = MagicMock()
        mock_field.text.return_value = "test"
        mock_field.isVisible.return_value = True
        mock_fields[field] = mock_field
    dialog.fields = mock_fields
    
    data = dialog.get_data()
    assert data['action'] == InvestmentAction.BUY.value
    assert data['date'] == "test"

def test_all_transaction_types(dialog):
    """Test all transaction types"""
    mock_combo = MagicMock()
    dialog.type_combo = mock_combo
    
    mock_fields = {}
    for field in ['date', 'security', 'price', 'quantity', 'commission', 'amount', 'account', 'memo']:
        mock_field = MagicMock()
        mock_field.text.return_value = "test"
        mock_field.isVisible.return_value = True
        mock_fields[field] = mock_field
    dialog.fields = mock_fields
    
    for action in InvestmentAction:
        dialog.update_fields(action.value)
        mock_combo.currentText.return_value = action.value
        data = dialog.get_data()
        assert data['action'] == action.value

def test_error_handling(gui):
    """Test error handling in GUI"""
    # Test invalid file load
    mock_dialog = MagicMock()
    mock_dialog.getOpenFileName.return_value = ("nonexistent.csv", "CSV files (*.csv)")
    
    with patch('PyQt6.QtWidgets.QFileDialog', mock_dialog):
        gui.import_csv()  # Should not raise exception
    
    # Test invalid transaction deletion
    mock_list = MagicMock()
    mock_list.currentRow.return_value = None
    gui.transaction_list = mock_list
    
    gui.delete_transaction()  # Should not raise exception
    
    # Test invalid transaction duplication
    mock_list.currentItem.return_value = None
    gui.duplicate_transaction()  # Should not raise exception

def test_edit_transaction(gui):
    """Test editing an existing transaction"""
    original_trans = {
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10
    }
    gui.transactions = [original_trans]
    
    mock_list = MagicMock()
    mock_list.row.return_value = 0
    gui.transaction_list = mock_list
    
    mock_dialog = MagicMock()
    mock_dialog.exec.return_value = True
    mock_dialog.get_data.return_value = {
        'action': InvestmentAction.SELL.value,
        'date': '01/16/2024',
        'security': 'AAPL',
        'price': 190.00,
        'quantity': 5
    }
    
    with patch('qif_gui.TransactionDialog', return_value=mock_dialog):
        gui.edit_transaction(MagicMock())
    
    assert len(gui.transactions) == 1
    assert gui.transactions[0]['action'] == InvestmentAction.SELL.value
    assert gui.transactions[0]['date'] == '01/16/2024'
    assert gui.transactions[0]['price'] == 190.00
    assert gui.transactions[0]['quantity'] == 5
