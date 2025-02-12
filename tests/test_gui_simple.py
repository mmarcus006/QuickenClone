"""Test GUI components with minimal mocking"""
import pytest
from unittest.mock import MagicMock, patch
import sys

# Create minimal Qt mocks
mock_qt = MagicMock()
mock_widgets = MagicMock()
mock_core = MagicMock()

# Setup Qt Core constants
mock_core.Qt = MagicMock()
mock_core.Qt.AlignLeft = 1
mock_core.Qt.AlignRight = 2
mock_core.Qt.AlignCenter = 4

# Setup basic widget behaviors
mock_widgets.QMainWindow = MagicMock
mock_widgets.QDialog = MagicMock
mock_widgets.QWidget = MagicMock
mock_widgets.QVBoxLayout = MagicMock
mock_widgets.QHBoxLayout = MagicMock
mock_widgets.QGridLayout = MagicMock
mock_widgets.QLabel = MagicMock
mock_widgets.QComboBox = MagicMock
mock_widgets.QPushButton = MagicMock
mock_widgets.QFileDialog = MagicMock()
mock_widgets.QMessageBox = MagicMock()
mock_widgets.QLineEdit = MagicMock
mock_widgets.QListWidget = MagicMock
mock_widgets.QGroupBox = MagicMock
mock_widgets.QDialogButtonBox = MagicMock
mock_widgets.QApplication = MagicMock

# Setup special widget behaviors
mock_widgets.QMessageBox.Yes = 1
mock_widgets.QMessageBox.No = 0
mock_widgets.QMessageBox.question = MagicMock(return_value=mock_widgets.QMessageBox.Yes)

# Patch modules
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
    
    # Setup default behaviors
    mock_widgets.QMessageBox.question.return_value = mock_widgets.QMessageBox.Yes
    mock_widgets.QListWidget.return_value.currentRow.return_value = 0
    mock_widgets.QComboBox.return_value.currentText.return_value = InvestmentAction.BUY.value
    mock_widgets.QLineEdit.return_value.text.return_value = "test"
    mock_widgets.QLineEdit.return_value.isVisible.return_value = True
    
    yield

def test_gui_initialization():
    """Test GUI initialization"""
    with patch('qif_gui.QMainWindow'):
        gui = QIFConverterGUI()
        assert hasattr(gui, 'transaction_list')
        assert hasattr(gui, 'transactions')
        assert len(gui.transactions) == 0

def test_add_transaction():
    """Test adding a transaction"""
    with patch('qif_gui.QMainWindow'):
        gui = QIFConverterGUI()
        
        # Mock dialog data
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
    with patch('qif_gui.QMainWindow'):
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
    with patch('qif_gui.QMainWindow'):
        gui = QIFConverterGUI()
        original_trans = {
            'action': InvestmentAction.BUY.value,
            'date': '01/15/2024',
            'security': 'AAPL',
            'price': 185.92,
            'quantity': 10
        }
        gui.transactions = [original_trans]
        
        # Mock dialog
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.get_data.return_value = {
            'action': InvestmentAction.BUY.value,
            'date': '01/16/2024',
            'security': 'AAPL',
            'price': 185.92,
            'quantity': 10
        }
        
        with patch('qif_gui.QDialog', return_value=mock_dialog):
            gui.duplicate_transaction()
        
        assert len(gui.transactions) == 2
        assert gui.transactions[1]['date'] == '01/16/2024'
        assert gui.transactions[1]['security'] == original_trans['security']

def test_save_transactions(tmp_path):
    """Test saving transactions to QIF"""
    with patch('qif_gui.QMainWindow'):
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
        
        gui.export_qif()
        
        with open(output_file) as f:
            content = f.read()
            assert QIFType.INVESTMENT.value in content
            assert "NBuy" in content
            assert "YAAPL" in content

def test_load_transactions(tmp_path):
    """Test loading transactions from CSV"""
    with patch('qif_gui.QMainWindow'):
        gui = QIFConverterGUI()
        
        # Create test CSV
        csv_file = tmp_path / "test.csv"
        with open(csv_file, "w") as f:
            f.write("Transaction Type,Trade Date,Symbol,Price,Quantity,Commission,Notes\n")
            f.write("Buy,01/15/2024,AAPL,185.92,10,4.95,Test buy\n")
        
        mock_widgets.QFileDialog.getOpenFileName.return_value = (str(csv_file), "CSV files (*.csv)")
        gui.import_csv()
        
        assert len(gui.transactions) == 1
        assert gui.transactions[0]['security'] == 'AAPL'

def test_transaction_dialog():
    """Test transaction dialog functionality"""
    with patch('qif_gui.QDialog'):
        dialog = TransactionDialog()
        
        # Test field updates
        dialog.update_fields(InvestmentAction.BUY.value)
        dialog.update_fields(InvestmentAction.DIV.value)
        dialog.update_fields(InvestmentAction.BUYX.value)
        
        # Test data retrieval
        mock_widgets.QComboBox.return_value.currentText.return_value = InvestmentAction.BUY.value
        mock_widgets.QLineEdit.return_value.text.side_effect = [
            "01/15/2024",  # date
            "AAPL",        # security
            "185.92",      # price
            "10",          # quantity
            "4.95"         # commission
        ]
        
        data = dialog.get_data()
        assert data['action'] == InvestmentAction.BUY.value
        assert data['date'] == "01/15/2024"

def test_transaction_dialog_field_visibility():
    """Test field visibility updates"""
    with patch('qif_gui.QDialog'):
        dialog = TransactionDialog()
        
        # Test Buy transaction fields
        dialog.update_fields(InvestmentAction.BUY.value)
        
        # Test Dividend transaction fields
        dialog.update_fields(InvestmentAction.DIV.value)
        
        # Test Transfer transaction fields
        dialog.update_fields(InvestmentAction.BUYX.value)

def test_error_handling():
    """Test error handling in GUI"""
    with patch('qif_gui.QMainWindow'):
        gui = QIFConverterGUI()
        
        # Test invalid file load
        mock_widgets.QFileDialog.getOpenFileName.return_value = ("nonexistent.csv", "CSV files (*.csv)")
        gui.import_csv()  # Should not raise exception
        
        # Test invalid transaction deletion
        mock_widgets.QListWidget.return_value.currentRow.return_value = None
        gui.delete_transaction()  # Should not raise exception when no transaction selected
        
        # Test invalid transaction duplication
        mock_widgets.QListWidget.return_value.currentRow.return_value = None
        gui.duplicate_transaction()  # Should not raise exception when no transaction selected

def test_edit_transaction():
    """Test editing an existing transaction"""
    with patch('qif_gui.QMainWindow'):
        gui = QIFConverterGUI()
        original_trans = {
            'action': InvestmentAction.BUY.value,
            'date': '01/15/2024',
            'security': 'AAPL',
            'price': 185.92,
            'quantity': 10
        }
        gui.transactions = [original_trans]
        
        # Mock dialog data
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
            gui.edit_transaction(None)
        
        assert len(gui.transactions) == 1
        assert gui.transactions[0]['action'] == InvestmentAction.SELL.value
        assert gui.transactions[0]['date'] == '01/16/2024'
        assert gui.transactions[0]['price'] == 190.00
        assert gui.transactions[0]['quantity'] == 5
