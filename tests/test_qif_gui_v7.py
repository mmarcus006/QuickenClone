"""Test GUI functionality with proper Qt mocking"""
import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock Qt modules before importing
mock_app = MagicMock()
mock_app.exec = MagicMock(return_value=0)

mock_qt = MagicMock()
mock_widgets = MagicMock()
mock_core = MagicMock()

# Setup Qt Core constants
mock_core.Qt = MagicMock()
mock_core.Qt.AlignLeft = 1
mock_core.Qt.AlignRight = 2
mock_core.Qt.AlignCenter = 4

# Patch modules
with patch.dict('sys.modules', {
    'PyQt6': mock_qt,
    'PyQt6.QtWidgets': mock_widgets,
    'PyQt6.QtCore': mock_core
}):
    from qif_gui import QIFConverterGUI, TransactionDialog
    from qif_converter import InvestmentAction

@pytest.fixture(autouse=True)
def qt_application():
    """Create Qt application instance"""
    with patch('qif_gui.QApplication', return_value=mock_app):
        yield

@pytest.fixture
def gui(qt_application):
    """Create GUI instance"""
    with patch('qif_gui.QMainWindow') as mock_main:
        gui = QIFConverterGUI()
        gui.transaction_list = MagicMock()
        yield gui

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
        'quantity': 10,
        'commission': 4.95,
        'memo': 'Test buy'
    }
    
    with patch('qif_gui.TransactionDialog', return_value=mock_dialog):
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
    
    gui.transaction_list.currentRow.return_value = 0
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
    
    gui.transaction_list.currentRow.return_value = 0
    gui.transaction_list.currentItem.return_value = MagicMock()
    
    mock_dialog = MagicMock()
    mock_dialog.exec.return_value = True
    mock_dialog.get_data.return_value = {
        'action': InvestmentAction.BUY.value,
        'date': '01/16/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10
    }
    
    with patch('qif_gui.TransactionDialog', return_value=mock_dialog):
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
    mock_dialog = MagicMock()
    mock_dialog.getSaveFileName.return_value = (str(qif_file), "QIF files (*.qif)")
    
    with patch('qif_gui.QFileDialog', mock_dialog):
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
    
    mock_dialog = MagicMock()
    mock_dialog.getOpenFileName.return_value = (str(csv_file), "CSV files (*.csv)")
    
    with patch('qif_gui.QFileDialog', mock_dialog):
        gui.import_csv()
    
    assert len(gui.transactions) == 1
    assert gui.transactions[0]['security'] == 'AAPL'
    assert gui.transactions[0]['action'] == InvestmentAction.BUY.value

def test_transaction_dialog():
    """Test transaction dialog"""
    with patch('qif_gui.QDialog') as mock_dialog:
        dialog = TransactionDialog()
        dialog.type_combo = MagicMock()
        dialog.type_combo.currentText.return_value = InvestmentAction.BUY.value
        
        # Mock fields
        dialog.fields = {
            'date': MagicMock(text=lambda: '01/15/2024', isVisible=lambda: True),
            'security': MagicMock(text=lambda: 'AAPL', isVisible=lambda: True),
            'price': MagicMock(text=lambda: '185.92', isVisible=lambda: True),
            'quantity': MagicMock(text=lambda: '10', isVisible=lambda: True),
            'commission': MagicMock(text=lambda: '4.95', isVisible=lambda: True),
            'memo': MagicMock(text=lambda: 'Test buy', isVisible=lambda: True)
        }
        
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
    with patch('qif_gui.QDialog') as mock_dialog:
        dialog = TransactionDialog()
        dialog.fields = {
            'date': MagicMock(),
            'security': MagicMock(),
            'price': MagicMock(),
            'quantity': MagicMock(),
            'commission': MagicMock(),
            'amount': MagicMock(),
            'account': MagicMock(),
            'memo': MagicMock()
        }
        
        # Test Buy action
        dialog.update_fields(InvestmentAction.BUY.value)
        dialog.fields['price'].setVisible.assert_called_with(True)
        dialog.fields['quantity'].setVisible.assert_called_with(True)
        dialog.fields['commission'].setVisible.assert_called_with(True)
        dialog.fields['amount'].setVisible.assert_called_with(False)
        dialog.fields['account'].setVisible.assert_called_with(False)
        
        # Test Div action
        dialog.update_fields(InvestmentAction.DIV.value)
        dialog.fields['price'].setVisible.assert_called_with(False)
        dialog.fields['quantity'].setVisible.assert_called_with(False)
        dialog.fields['commission'].setVisible.assert_called_with(False)
        dialog.fields['amount'].setVisible.assert_called_with(True)
        dialog.fields['account'].setVisible.assert_called_with(False)
        
        # Test BuyX action
        dialog.update_fields(InvestmentAction.BUYX.value)
        dialog.fields['price'].setVisible.assert_called_with(True)
        dialog.fields['quantity'].setVisible.assert_called_with(True)
        dialog.fields['commission'].setVisible.assert_called_with(False)
        dialog.fields['amount'].setVisible.assert_called_with(False)
        dialog.fields['account'].setVisible.assert_called_with(True)

def test_all_transaction_types():
    """Test all transaction types in dialog"""
    with patch('qif_gui.QDialog') as mock_dialog:
        dialog = TransactionDialog()
        dialog.fields = {
            'date': MagicMock(),
            'security': MagicMock(),
            'price': MagicMock(),
            'quantity': MagicMock(),
            'commission': MagicMock(),
            'amount': MagicMock(),
            'account': MagicMock(),
            'memo': MagicMock()
        }
        
        for action in InvestmentAction:
            dialog.update_fields(action.value)
            # Verify all fields are properly configured
            if action in [InvestmentAction.BUY, InvestmentAction.SELL]:
                dialog.fields['price'].setVisible.assert_called_with(True)
                dialog.fields['quantity'].setVisible.assert_called_with(True)
                dialog.fields['commission'].setVisible.assert_called_with(True)
            elif action in [InvestmentAction.DIV, InvestmentAction.INTINC]:
                dialog.fields['amount'].setVisible.assert_called_with(True)
            elif action in [InvestmentAction.BUYX, InvestmentAction.SELLX]:
                dialog.fields['price'].setVisible.assert_called_with(True)
                dialog.fields['quantity'].setVisible.assert_called_with(True)
                dialog.fields['account'].setVisible.assert_called_with(True)
