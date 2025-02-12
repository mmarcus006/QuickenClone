"""Test GUI components with minimal mocking"""
import pytest
from unittest.mock import MagicMock, patch
import sys

# Create mock modules
mock_qt = MagicMock()
mock_widgets = MagicMock()
mock_core = MagicMock()

# Setup Qt Core constants
mock_core.Qt = MagicMock()
mock_core.Qt.AlignLeft = 1
mock_core.Qt.AlignRight = 2
mock_core.Qt.AlignCenter = 4

# Patch modules before importing
with patch.dict('sys.modules', {
    'PyQt6': mock_qt,
    'PyQt6.QtWidgets': mock_widgets,
    'PyQt6.QtCore': mock_core
}):
    from qif_gui import QIFConverterGUI, TransactionDialog
    from qif_converter import InvestmentAction, QIFType

@pytest.fixture(autouse=True)
def mock_qt():
    """Mock Qt modules"""
    with patch('qif_gui.QMainWindow') as mock_main, \
         patch('qif_gui.QDialog') as mock_dialog, \
         patch('qif_gui.QWidget') as mock_widget, \
         patch('qif_gui.QVBoxLayout') as mock_vbox, \
         patch('qif_gui.QHBoxLayout') as mock_hbox, \
         patch('qif_gui.QLabel') as mock_label, \
         patch('qif_gui.QComboBox') as mock_combo, \
         patch('qif_gui.QPushButton') as mock_button, \
         patch('qif_gui.QFileDialog') as mock_file, \
         patch('qif_gui.QMessageBox') as mock_msg, \
         patch('qif_gui.QLineEdit') as mock_line, \
         patch('qif_gui.QListWidget') as mock_list, \
         patch('qif_gui.QGroupBox') as mock_group, \
         patch('qif_gui.QDialogButtonBox') as mock_bbox:
        
        # Setup default behaviors
        mock_main.return_value = MagicMock(spec=['setWindowTitle', 'setCentralWidget', 'setMinimumWidth'])
        mock_dialog.return_value = MagicMock(spec=['setWindowTitle', 'setMinimumWidth', 'exec', 'accept', 'reject'])
        mock_widget.return_value = MagicMock(spec=['setLayout'])
        mock_vbox.return_value = MagicMock(spec=['addWidget', 'addLayout'])
        mock_hbox.return_value = MagicMock(spec=['addWidget', 'addLayout'])
        mock_label.return_value = MagicMock(spec=['setText', 'setVisible'])
        mock_combo.return_value = MagicMock(spec=['addItems', 'currentText', 'setCurrentText', 'currentTextChanged'])
        mock_button.return_value = MagicMock(spec=['clicked', 'setToolTip'])
        mock_file.getOpenFileName = MagicMock(return_value=("test.csv", "CSV Files (*.csv)"))
        mock_file.getSaveFileName = MagicMock(return_value=("test.qif", "QIF Files (*.qif)"))
        mock_msg.Yes = 1
        mock_msg.No = 0
        mock_msg.question = MagicMock(return_value=mock_msg.Yes)
        mock_line.return_value = MagicMock(spec=['text', 'setText', 'setPlaceholderText', 'setVisible', 'isVisible'])
        mock_list.return_value = MagicMock(spec=['addItem', 'currentRow', 'clear', 'itemDoubleClicked', 'row'])
        mock_group.return_value = MagicMock(spec=['setLayout'])
        mock_bbox.return_value = MagicMock(spec=['accepted', 'rejected', 'addButton'])
        
        yield {
            'main': mock_main,
            'dialog': mock_dialog,
            'widget': mock_widget,
            'vbox': mock_vbox,
            'hbox': mock_hbox,
            'label': mock_label,
            'combo': mock_combo,
            'button': mock_button,
            'file': mock_file,
            'msg': mock_msg,
            'line': mock_line,
            'list': mock_list,
            'group': mock_group,
            'bbox': mock_bbox
        }

def test_gui_initialization(mock_qt):
    """Test GUI initialization"""
    gui = QIFConverterGUI()
    assert hasattr(gui, 'transaction_list')
    assert hasattr(gui, 'transactions')
    assert len(gui.transactions) == 0
    mock_qt['main'].return_value.setWindowTitle.assert_called_once_with("CSV to QIF Converter")

def test_add_transaction(mock_qt):
    """Test adding a transaction"""
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

def test_delete_transaction(mock_qt):
    """Test deleting a transaction"""
    gui = QIFConverterGUI()
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10
    }]
    
    mock_qt['list'].return_value.currentRow.return_value = 0
    gui.delete_transaction()
    assert len(gui.transactions) == 0

def test_duplicate_transaction(mock_qt):
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
    
    mock_qt['list'].return_value.currentRow.return_value = 0
    mock_qt['list'].return_value.currentItem.return_value = MagicMock()
    mock_qt['line'].return_value.text.return_value = '01/16/2024'
    mock_qt['dialog'].return_value.exec.return_value = True
    
    gui.duplicate_transaction()
    
    assert len(gui.transactions) == 2
    assert gui.transactions[1]['date'] == '01/16/2024'
    assert gui.transactions[1]['security'] == original_trans['security']

def test_save_transactions(mock_qt, tmp_path):
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
    mock_qt['file'].getSaveFileName.return_value = (output_file, "QIF files (*.qif)")
    
    gui.export_qif()
    
    with open(output_file) as f:
        content = f.read()
        assert QIFType.INVESTMENT.value in content
        assert "NBuy" in content
        assert "YAAPL" in content

def test_load_transactions(mock_qt, tmp_path):
    """Test loading transactions from CSV"""
    gui = QIFConverterGUI()
    
    # Create test CSV
    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w") as f:
        f.write("Transaction Type,Trade Date,Symbol,Price,Quantity,Commission,Notes\n")
        f.write("Buy,01/15/2024,AAPL,185.92,10,4.95,Test buy\n")
    
    mock_qt['file'].getOpenFileName.return_value = (str(csv_file), "CSV files (*.csv)")
    gui.import_csv()
    
    assert len(gui.transactions) == 1
    assert gui.transactions[0]['security'] == 'AAPL'

def test_transaction_dialog(mock_qt):
    """Test transaction dialog functionality"""
    mock_qt['combo'].return_value.currentText.return_value = InvestmentAction.BUY.value
    mock_qt['line'].return_value.text.return_value = "test"
    mock_qt['line'].return_value.isVisible.return_value = True
    
    dialog = TransactionDialog()
    
    # Test field updates
    dialog.update_fields(InvestmentAction.BUY.value)
    dialog.update_fields(InvestmentAction.DIV.value)
    dialog.update_fields(InvestmentAction.BUYX.value)
    
    data = dialog.get_data()
    assert data['action'] == InvestmentAction.BUY.value
    assert data['date'] == "test"

def test_all_transaction_types(mock_qt):
    """Test all transaction types"""
    mock_qt['combo'].return_value.currentText.return_value = InvestmentAction.BUY.value
    mock_qt['line'].return_value.text.return_value = "test"
    mock_qt['line'].return_value.isVisible.return_value = True
    
    dialog = TransactionDialog()
    
    for action in InvestmentAction:
        dialog.update_fields(action.value)
        mock_qt['combo'].return_value.currentText.return_value = action.value
        data = dialog.get_data()
        assert data['action'] == action.value

def test_error_handling(mock_qt):
    """Test error handling in GUI"""
    gui = QIFConverterGUI()
    
    # Test invalid file load
    mock_qt['file'].getOpenFileName.return_value = ("nonexistent.csv", "CSV files (*.csv)")
    gui.import_csv()  # Should not raise exception
    
    # Test invalid transaction deletion
    mock_qt['list'].return_value.currentRow.return_value = None
    gui.delete_transaction()  # Should not raise exception
    
    # Test invalid transaction duplication
    mock_qt['list'].return_value.currentItem.return_value = None
    gui.duplicate_transaction()  # Should not raise exception

def test_edit_transaction(mock_qt):
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
    
    mock_qt['list'].return_value.row.return_value = 0
    
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
