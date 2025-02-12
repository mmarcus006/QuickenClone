import pytest
from unittest.mock import MagicMock, patch
from qif_converter import InvestmentAction, QIFType

# Import our GUI modules after setting up mocks
with patch.dict('sys.modules', {
    'PyQt6': MagicMock(),
    'PyQt6.QtWidgets': MagicMock(),
    'PyQt6.QtCore': MagicMock()
}):
    from qif_gui import QIFConverterGUI, TransactionDialog

@pytest.fixture(autouse=True)
def mock_qt():
    """Mock Qt widgets and functionality"""
    with patch('qif_gui.QMainWindow'), \
         patch('qif_gui.QDialog'), \
         patch('qif_gui.QVBoxLayout'), \
         patch('qif_gui.QHBoxLayout'), \
         patch('qif_gui.QLabel'), \
         patch('qif_gui.QComboBox') as mock_combo, \
         patch('qif_gui.QPushButton'), \
         patch('qif_gui.QFileDialog') as mock_file_dialog, \
         patch('qif_gui.QMessageBox') as mock_msg_box, \
         patch('qif_gui.QLineEdit') as mock_line_edit, \
         patch('qif_gui.QListWidget') as mock_list_widget:
        
        # Setup mock behaviors
        mock_combo.return_value.currentText.return_value = InvestmentAction.BUY.value
        mock_line_edit.return_value.text.return_value = "test"
        mock_msg_box.Yes = 1
        mock_msg_box.No = 0
        mock_list_widget.return_value.currentRow.return_value = 0
        
        yield {
            'combo': mock_combo,
            'file_dialog': mock_file_dialog,
            'msg_box': mock_msg_box,
            'line_edit': mock_line_edit,
            'list_widget': mock_list_widget
        }

def test_gui_initialization():
    """Test GUI initialization"""
    gui = QIFConverterGUI()
    assert hasattr(gui, 'transaction_list')
    assert hasattr(gui, 'transactions')
    assert len(gui.transactions) == 0

def test_add_transaction(mock_qt):
    """Test adding a transaction"""
    gui = QIFConverterGUI()
    mock_qt['line_edit'].return_value.text.side_effect = [
        "01/15/2024",  # date
        "AAPL",        # security
        "185.92",      # price
        "10",          # quantity
        "4.95"         # commission
    ]
    
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
    
    mock_qt['msg_box'].question.return_value = mock_qt['msg_box'].Yes
    gui.delete_transaction()
    assert len(gui.transactions) == 0

def test_duplicate_transaction(mock_qt, tmp_path):
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
    
    mock_qt['line_edit'].return_value.text.return_value = '01/16/2024'
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
    mock_qt['file_dialog'].getSaveFileName.return_value = (output_file, "QIF files (*.qif)")
    
    gui.save_transactions()
    
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
        f.write("Date,Action,Security,Price,Quantity\n")
        f.write("2024-01-15,Buy,AAPL,185.92,10\n")
    
    mock_qt['file_dialog'].getOpenFileName.return_value = (str(csv_file), "CSV files (*.csv)")
    gui.load_transactions()
    
    assert len(gui.transactions) == 1
    assert gui.transactions[0]['security'] == 'AAPL'

def test_transaction_dialog():
    """Test transaction dialog functionality"""
    dialog = TransactionDialog()
    assert hasattr(dialog, 'type_combo')
    assert hasattr(dialog, 'fields')
    
    # Test field updates
    dialog.update_fields(InvestmentAction.BUY.value)
    dialog.update_fields(InvestmentAction.DIV.value)
    dialog.update_fields(InvestmentAction.BUYX.value)
    
    # Test data retrieval
    data = dialog.get_data()
    assert data['action'] == InvestmentAction.BUY.value
