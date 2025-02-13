import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock Qt modules before importing our code
mock_qt = MagicMock()
mock_widgets = MagicMock()
mock_core = MagicMock()

# Setup Qt mocks
mock_core.Qt.AlignLeft = 1
mock_core.Qt.AlignRight = 2
mock_core.Qt.AlignCenter = 4

sys.modules['PyQt6'] = mock_qt
sys.modules['PyQt6.QtWidgets'] = mock_widgets
sys.modules['PyQt6.QtCore'] = mock_core

# Now we can safely import our modules
from qif_gui import QIFConverterGUI, TransactionDialog
from qif_converter import InvestmentAction, QIFType

@pytest.fixture(autouse=True)
def setup_mocks():
    """Reset mocks before each test"""
    mock_widgets.reset_mock()
    mock_core.reset_mock()
    
    # Setup common mock behaviors
    mock_widgets.QMessageBox.Yes = 1
    mock_widgets.QMessageBox.No = 0
    mock_widgets.QMessageBox.question.return_value = mock_widgets.QMessageBox.Yes
    mock_widgets.QListWidget.return_value.currentRow.return_value = 0
    mock_widgets.QComboBox.return_value.currentText.return_value = InvestmentAction.BUY.value
    mock_widgets.QLineEdit.return_value.text.return_value = "test"
    
    yield

def test_gui_initialization():
    """Test GUI initialization"""
    gui = QIFConverterGUI()
    assert mock_widgets.QMainWindow.called
    assert mock_widgets.QListWidget.called
    assert mock_widgets.QPushButton.call_count >= 3  # Add, Delete, Save buttons

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
    mock_widgets.QDialog.return_value.exec.return_value = True
    mock_widgets.QLineEdit.return_value.text.return_value = '01/16/2024'
    
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
    mock_widgets.QFileDialog.getSaveFileName.return_value = (output_file, "QIF files (*.qif)")
    
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
    
    mock_widgets.QFileDialog.getOpenFileName.return_value = (str(csv_file), "CSV files (*.csv)")
    gui.load_transactions()
    
    assert len(gui.transactions) == 1
    assert gui.transactions[0]['security'] == 'AAPL'

def test_transaction_dialog():
    """Test transaction dialog functionality"""
    dialog = TransactionDialog()
    assert mock_widgets.QDialog.called
    assert mock_widgets.QComboBox.called
    
    # Test field updates
    dialog.update_fields(InvestmentAction.BUY.value)
    dialog.update_fields(InvestmentAction.DIV.value)
    dialog.update_fields(InvestmentAction.BUYX.value)
    
    # Test data retrieval
    data = dialog.get_data()
    assert data['action'] == InvestmentAction.BUY.value

def test_transaction_dialog_field_visibility():
    """Test field visibility updates"""
    dialog = TransactionDialog()
    
    # Test Buy transaction fields
    dialog.update_fields(InvestmentAction.BUY.value)
    assert mock_widgets.QLineEdit.return_value.setVisible.called
    
    # Test Dividend transaction fields
    dialog.update_fields(InvestmentAction.DIV.value)
    assert mock_widgets.QLineEdit.return_value.setVisible.called
    
    # Test Transfer transaction fields
    dialog.update_fields(InvestmentAction.BUYX.value)
    assert mock_widgets.QLineEdit.return_value.setVisible.called
