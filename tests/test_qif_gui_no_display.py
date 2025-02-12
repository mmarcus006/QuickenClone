import pytest
from unittest.mock import MagicMock, patch
from qif_gui import QIFConverterGUI, TransactionDialog
from qif_converter import InvestmentAction, QIFType
import os

# Mock PyQt6 modules before they're imported
pytestmark = pytest.mark.skipif(os.environ.get('DISPLAY') is None,
                              reason="GUI tests require display")

@pytest.fixture(autouse=True)
def mock_pyqt(monkeypatch):
    """Mock all PyQt6 widgets and functionality"""
    mocks = {}
    widgets = [
        'QMainWindow', 'QDialog', 'QVBoxLayout', 'QHBoxLayout',
        'QLabel', 'QComboBox', 'QPushButton', 'QFileDialog',
        'QMessageBox', 'QLineEdit', 'QListWidget', 'QGroupBox',
        'QDialogButtonBox', 'QWidget', 'QApplication'
    ]
    
    for widget in widgets:
        mock = MagicMock()
        mock.__str__ = lambda x: widget
        mocks[widget] = mock
        monkeypatch.setattr(f'PyQt6.QtWidgets.{widget}', mock)
    
    # Mock Qt Core functionality
    monkeypatch.setattr('PyQt6.QtCore.Qt.AlignLeft', 1)
    monkeypatch.setattr('PyQt6.QtCore.Qt.AlignRight', 2)
    
    return mocks

def test_main_window_initialization(mock_pyqt):
    """Test main window initialization"""
    gui = QIFConverterGUI()
    assert hasattr(gui, 'transaction_list')
    assert hasattr(gui, 'transactions')
    assert len(gui.transactions) == 0

def test_add_transaction(mock_pyqt):
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

def test_delete_transaction(mock_pyqt):
    """Test deleting a transaction"""
    gui = QIFConverterGUI()
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10
    }]
    
    # Mock list widget selection
    mock_pyqt['QListWidget'].return_value.currentRow.return_value = 0
    mock_pyqt['QMessageBox'].question.return_value = mock_pyqt['QMessageBox'].Yes
    
    gui.delete_transaction()
    assert len(gui.transactions) == 0

def test_duplicate_transaction(mock_pyqt):
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
    
    # Mock list widget selection and dialog
    mock_pyqt['QListWidget'].return_value.currentRow.return_value = 0
    mock_pyqt['QDialog'].return_value.exec.return_value = True
    mock_pyqt['QLineEdit'].return_value.text.return_value = '01/16/2024'
    
    gui.duplicate_transaction()
    assert len(gui.transactions) == 2
    assert gui.transactions[1]['date'] == '01/16/2024'
    assert gui.transactions[1]['security'] == original_trans['security']

def test_save_transactions(mock_pyqt, tmp_path):
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
    mock_pyqt['QFileDialog'].getSaveFileName.return_value = (output_file, "QIF files (*.qif)")
    
    gui.save_transactions()
    
    with open(output_file) as f:
        content = f.read()
        assert QIFType.INVESTMENT.value in content
        assert "NBuy" in content
        assert "YAAPL" in content

def test_transaction_dialog_initialization():
    """Test transaction dialog initialization"""
    with patch('PyQt6.QtWidgets.QDialog'), \
         patch('PyQt6.QtWidgets.QVBoxLayout'), \
         patch('PyQt6.QtWidgets.QComboBox') as mock_combo:
        dialog = TransactionDialog()
        assert hasattr(dialog, 'type_combo')
        assert hasattr(dialog, 'fields')
        
        # Verify action types are set
        actions = [action.value for action in InvestmentAction]
        mock_combo.return_value.addItems.assert_called_once()
        added_items = mock_combo.return_value.addItems.call_args[0][0]
        assert all(action in added_items for action in actions)

def test_transaction_dialog_field_updates():
    """Test field visibility updates based on transaction type"""
    with patch('PyQt6.QtWidgets.QDialog'), \
         patch('PyQt6.QtWidgets.QVBoxLayout'), \
         patch('PyQt6.QtWidgets.QLineEdit') as mock_line_edit:
        dialog = TransactionDialog()
        
        # Test Buy transaction fields
        dialog.update_fields(InvestmentAction.BUY.value)
        assert mock_line_edit.return_value.setVisible.called
        
        # Test Dividend transaction fields
        dialog.update_fields(InvestmentAction.DIV.value)
        assert mock_line_edit.return_value.setVisible.called

def test_transaction_dialog_data():
    """Test transaction data retrieval"""
    with patch('PyQt6.QtWidgets.QDialog'), \
         patch('PyQt6.QtWidgets.QVBoxLayout'), \
         patch('PyQt6.QtWidgets.QComboBox') as mock_combo, \
         patch('PyQt6.QtWidgets.QLineEdit') as mock_line_edit:
        dialog = TransactionDialog()
        
        # Mock field values
        mock_combo.return_value.currentText.return_value = InvestmentAction.BUY.value
        mock_line_edit.return_value.text.return_value = "test"
        
        data = dialog.get_data()
        assert data['action'] == InvestmentAction.BUY.value
