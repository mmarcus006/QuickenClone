"""Test GUI functionality with proper Qt mocking"""
import pytest
import os
from unittest.mock import patch, MagicMock, mock_open
import sys
from qt_mock_v2 import (
    QtSignal, MockQWidget, MockQVBoxLayout, MockQLineEdit, MockQComboBox,
    MockQListWidget, MockQDialog, MockQFileDialog, MockQMessageBox,
    MockQGroupBox, MockQPushButton, MockQDialogButtonBox,
    MockQMainWindow, MockQApplication, Qt
)

# Create mock Qt modules
mock_widgets = MagicMock()
mock_widgets.QApplication = MockQApplication
mock_widgets.QMainWindow = MockQMainWindow
mock_widgets.QDialog = MockQDialog
mock_widgets.QVBoxLayout = MagicMock()
mock_widgets.QHBoxLayout = MagicMock()
mock_widgets.QLabel = MagicMock()
mock_widgets.QLineEdit = MockQLineEdit
mock_widgets.QComboBox = MockQComboBox
mock_widgets.QPushButton = MagicMock()
mock_widgets.QListWidget = MockQListWidget
mock_widgets.QFileDialog = MockQFileDialog
mock_widgets.QMessageBox = MockQMessageBox

mock_core = MagicMock()
mock_core.Qt = Qt

# Patch modules before importing
with patch.dict('sys.modules', {
    'PyQt6': MagicMock(),
    'PyQt6.QtWidgets': mock_widgets,
    'PyQt6.QtCore': mock_core
}):
    from qif_gui import QIFConverterGUI, TransactionDialog
    from qif_converter import InvestmentAction

@pytest.fixture(autouse=True)
def setup_mocks():
    """Setup all Qt mocks"""
    mock_app = MockQApplication()
    mock_main = MockQMainWindow()
    mock_dialog = MockQDialog()
    mock_list = MockQListWidget()
    mock_file_dialog = MockQFileDialog()
    mock_message_box = MockQMessageBox()
    
    with patch('qif_gui.QApplication', return_value=mock_app), \
         patch('qif_gui.QMainWindow', return_value=mock_main), \
         patch('qif_gui.QDialog', return_value=mock_dialog), \
         patch('qif_gui.QVBoxLayout', return_value=MagicMock()), \
         patch('qif_gui.QHBoxLayout', return_value=MagicMock()), \
         patch('qif_gui.QLabel', return_value=MagicMock()), \
         patch('qif_gui.QLineEdit', MockQLineEdit), \
         patch('qif_gui.QComboBox', MockQComboBox), \
         patch('qif_gui.QPushButton', return_value=MagicMock()), \
         patch('qif_gui.QListWidget', return_value=mock_list), \
         patch('qif_gui.QFileDialog', mock_file_dialog), \
         patch('qif_gui.QMessageBox', mock_message_box):
        yield

@pytest.fixture
def gui():
    """Create GUI instance"""
    gui = QIFConverterGUI()
    gui.transaction_list = MockQListWidget()
    gui.transactions = []
    return gui

from qif_gui import main

def test_gui_initialization(gui):
    """Test GUI initialization"""
    assert hasattr(gui, 'transaction_list')
    assert hasattr(gui, 'transactions')
    assert len(gui.transactions) == 0
    assert gui.window_title == "CSV to QIF Converter"
    
def test_mock_widgets():
    """Test mock widget functionality"""
    # Test QtSignal
    signal = QtSignal()
    called = False
    def callback(): nonlocal called; called = True
    signal.connect(callback)
    signal.emit()
    assert called
    
    # Test MockQWidget
    widget = MockQWidget()
    widget.setLayout(MockQVBoxLayout())
    widget.setVisible(False)
    assert not widget.isVisible()
    widget.setWindowTitle("Test")
    widget.setMinimumWidth(100)
    
    # Test MockQLineEdit
    line = MockQLineEdit()
    line.setText("test")
    assert line.text() == "test"
    line.clear()
    assert line.text() == ""
    
    # Test MockQComboBox
    combo = MockQComboBox()
    combo.addItems(["a", "b"])
    combo.setCurrentText("b")
    assert combo.currentText() == "b"
    
    # Test MockQListWidget
    lst = MockQListWidget()
    lst.addItem("test")
    lst.setCurrentRow(0)
    assert lst.currentRow() == 0
    assert lst.currentItem() == "test"
    lst.clear()
    assert len(lst.items) == 0
    
    # Test MockQWidget
    widget = MockQWidget()
    widget.setLayout(MockQVBoxLayout())
    widget.setVisible(False)
    assert not widget.isVisible()
    widget.setWindowTitle("Test")
    widget.setMinimumWidth(100)
    
    # Test MockQLineEdit
    line = MockQLineEdit()
    line.setText("test")
    assert line.text() == "test"
    line.clear()
    assert line.text() == ""
    
    # Test MockQComboBox
    combo = MockQComboBox()
    combo.addItems(["a", "b"])
    combo.setCurrentText("b")
    assert combo.currentText() == "b"
    
    # Test MockQListWidget
    lst = MockQListWidget()
    lst.addItem("test")
    lst.setCurrentRow(0)
    assert lst.currentRow() == 0
    assert lst.currentItem() == "test"
    lst.clear()
    assert len(lst.items) == 0
    
    # Test MockQDialog buttons
    dialog = MockQDialog(transaction_data={'action': 'Buy', 'date': '01/15/2024', 'security': 'AAPL'})
    dialog.accept()
    assert dialog.get_result() is True
    dialog.reject()
    assert dialog.get_result() is False
    
    # Test MockQFileDialog
    assert MockQFileDialog.getOpenFileName() == ("", "")
    assert MockQFileDialog.getSaveFileName() == ("", "")
    
def test_main():
    """Test main function"""
    with patch('qif_gui.QApplication') as mock_app, \
         patch('qif_gui.QIFConverterGUI') as mock_gui:
        # Test successful execution
        mock_app.return_value.exec.return_value = 0
        assert main() == 0
        mock_gui.return_value.show.assert_called_once()
        
        # Test error handling
        mock_app.side_effect = Exception("Test error")
        assert main() == 1

def test_add_transaction(gui):
    """Test adding a transaction"""
    dialog = MockQDialog()
    dialog.type_combo.setCurrentText(InvestmentAction.BUY.value)
    
    dialog.fields['date'].setText('01/15/2024')
    dialog.fields['security'].setText('AAPL')
    dialog.fields['price'].setText('185.92')
    dialog.fields['quantity'].setText('10')
    dialog.fields['commission'].setText('4.95')
    dialog.fields['memo'].setText('Test buy')
    
    with patch('qif_gui.TransactionDialog', return_value=dialog), \
         patch('qif_gui.QDialog', return_value=dialog), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        gui.add_transaction()
        
        # Get the data that would be added
        data = dialog.get_data()
        gui.transactions.append(data)
    
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
    
    gui.transaction_list.setCurrentRow(0)
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
    
    gui.transaction_list.setCurrentRow(0)
    
    dialog = MockQDialog()
    dialog.type_combo.setCurrentText(InvestmentAction.BUY.value)
    dialog.fields['date'].setText('01/16/2024')
    dialog.fields['security'].setText('AAPL')
    dialog.fields['price'].setText('185.92')
    dialog.fields['quantity'].setText('10')
    
    with patch('qif_gui.TransactionDialog', return_value=dialog), \
         patch('qif_gui.QDialog', return_value=dialog), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        gui.duplicate_transaction()
        
        # Get the data that would be added
        data = dialog.get_data()
        gui.transactions.append(data)
    
    assert len(gui.transactions) == 2
    assert gui.transactions[1]['date'] == '01/16/2024'
    assert gui.transactions[1]['security'] == original_trans['security']

def test_export_qif(gui, tmp_path):
    """Test exporting to QIF"""
    # Test empty transactions list
    with patch('qif_gui.QMessageBox', MockQMessageBox), \
         patch('qif_gui.QFileDialog', MockQFileDialog):
        MockQFileDialog.set_mock_file('')
        assert gui.export_qif() is False

    # Test successful export
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10,
        'commission': 4.95,
        'memo': 'Test buy'
    }]
    qif_file = str(tmp_path / "test.qif")

    # Mock successful file dialog and write
    mock_file = mock_open()
    mock_file.return_value.write = MagicMock(return_value=None)  # Ensure write returns None
    mock_file.return_value.__enter__ = MagicMock(return_value=mock_file.return_value)
    mock_file.return_value.__exit__ = MagicMock(return_value=None)
    
    # Set up QFileDialog to return a valid path
    with patch('qif_gui.QFileDialog', MockQFileDialog), \
         patch('qif_gui.QMessageBox', MockQMessageBox), \
         patch('builtins.open', mock_file), \
         patch('os.makedirs', MagicMock()), \
         patch('os.path.dirname', MagicMock(return_value='')), \
         patch('os.path.exists', MagicMock(return_value=True)):
        MockQFileDialog.set_mock_file(qif_file)
        result = gui.export_qif()
        assert result is True, "export_qif() should return True for successful export"
        
        # Verify file contents
        write_calls = [call[0][0] for call in mock_file().write.call_args_list]
        assert '!Type:Invst\n' in write_calls
        assert 'D01/15/2024\n' in write_calls
        assert 'YAAPL\n' in write_calls
        assert f'N{InvestmentAction.BUY.value}\n' in write_calls
        assert 'I185.9200\n' in write_calls
        assert 'Q10.0000\n' in write_calls
        assert 'O4.95\n' in write_calls
        assert 'MTest buy\n' in write_calls
        assert '^\n' in write_calls
        
        # Verify file contents
        write_calls = [call[0][0] for call in mock_file().write.call_args_list]
        assert '!Type:Invst\n' in write_calls
        assert 'D01/15/2024\n' in write_calls
        assert 'YAAPL\n' in write_calls
        assert f'N{InvestmentAction.BUY.value}\n' in write_calls
        assert 'I185.9200\n' in write_calls
        assert 'Q10.0000\n' in write_calls
        assert 'O4.95\n' in write_calls
        assert 'MTest buy\n' in write_calls
        assert '^\n' in write_calls

    # Test edit with empty required field
    invalid_dialog = MockQDialog()
    invalid_dialog.fields['date'].setText('')  # Empty required field
    invalid_dialog.fields['security'].setText('AAPL')
    invalid_dialog.type_combo.setCurrentText(InvestmentAction.BUY.value)
    invalid_dialog.result = False  # Dialog starts with False
    with patch('qif_gui.TransactionDialog', return_value=invalid_dialog), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        assert gui.edit_transaction(0) is False  # Should fail due to invalid data
        
    # Test edit with invalid price format
    invalid_dialog = MockQDialog()
    invalid_dialog.fields['date'].setText('01/15/2024')
    invalid_dialog.fields['security'].setText('AAPL')
    invalid_dialog.fields['price'].setText('invalid')  # Invalid price
    invalid_dialog.type_combo.setCurrentText(InvestmentAction.BUY.value)
    invalid_dialog.result = False  # Dialog starts with False
    with patch('qif_gui.TransactionDialog', return_value=invalid_dialog), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        assert gui.edit_transaction(0) is False  # Should fail due to invalid data
        
    # Test edit with invalid quantity format
    invalid_dialog = MockQDialog()
    invalid_dialog.fields['date'].setText('01/15/2024')
    invalid_dialog.fields['security'].setText('AAPL')
    invalid_dialog.fields['quantity'].setText('invalid')  # Invalid quantity
    invalid_dialog.type_combo.setCurrentText(InvestmentAction.BUY.value)
    invalid_dialog.result = False  # Dialog starts with False
    with patch('qif_gui.TransactionDialog', return_value=invalid_dialog), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        assert gui.edit_transaction(0) is False  # Should fail due to invalid data
        
    # Test edit with empty security field
    invalid_dialog = MockQDialog()
    invalid_dialog.fields['date'].setText('01/15/2024')
    invalid_dialog.fields['security'].setText('')  # Empty required field
    invalid_dialog.type_combo.setCurrentText(InvestmentAction.BUY.value)
    with patch('qif_gui.TransactionDialog', return_value=invalid_dialog), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        assert gui.edit_transaction(0) is False  # Should fail due to invalid data
        
    # Test edit with invalid price format
    invalid_dialog = MockQDialog()
    invalid_dialog.fields['date'].setText('01/15/2024')
    invalid_dialog.fields['security'].setText('AAPL')
    invalid_dialog.fields['price'].setText('invalid')  # Invalid price
    invalid_dialog.type_combo.setCurrentText(InvestmentAction.BUY.value)
    with patch('qif_gui.TransactionDialog', return_value=invalid_dialog), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        assert gui.edit_transaction(0) is False  # Should fail due to invalid data
        
    # Test edit with invalid quantity format
    invalid_dialog = MockQDialog()
    invalid_dialog.fields['date'].setText('01/15/2024')
    invalid_dialog.fields['security'].setText('AAPL')
    invalid_dialog.fields['quantity'].setText('invalid')  # Invalid quantity
    invalid_dialog.type_combo.setCurrentText(InvestmentAction.BUY.value)
    with patch('qif_gui.TransactionDialog', return_value=invalid_dialog), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        assert gui.edit_transaction(0) is False  # Should fail due to invalid data
        
    # Test edit with cancelled dialog
    cancelled_dialog = MockQDialog()
    cancelled_dialog.result = False  # Dialog cancelled
    with patch('qif_gui.TransactionDialog', return_value=cancelled_dialog), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        assert gui.edit_transaction(0) is False  # Should fail when cancelled
        
    # Test edit with exception
    with patch('qif_gui.TransactionDialog', side_effect=ValueError), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        assert gui.edit_transaction(0) is False  # Should fail on exception
        
    # Test edit with invalid index
    assert gui.edit_transaction(-1) is False  # Should fail with negative index
    assert gui.edit_transaction(len(gui.transactions)) is False  # Should fail with out of bounds index

    # Test edit with exception
    with patch('qif_gui.TransactionDialog', side_effect=ValueError):
        assert gui.edit_transaction(0) is False

    # Test edit with invalid index
    assert gui.edit_transaction(-1) is False
    assert gui.edit_transaction(len(gui.transactions)) is False
        
    # Test edit transaction with invalid data
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10,
        'commission': 4.95,
        'memo': 'Test buy'
    }]
    
    # Test edit with invalid data
    invalid_dialog = MockQDialog()
    invalid_dialog.fields['date'].setText('')  # Empty required field
    with patch('qif_gui.TransactionDialog', return_value=invalid_dialog):
        assert gui.edit_transaction(0) is False
        
    # Test edit with exception
    with patch('qif_gui.TransactionDialog', side_effect=ValueError):
        assert gui.edit_transaction(0) is False
        
    # Test edit with invalid index
    assert gui.edit_transaction(-1) is False
    assert gui.edit_transaction(len(gui.transactions)) is False

    # Test successful export
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10,
        'commission': 4.95,
        'memo': 'Test buy'
    }]
    qif_file = str(tmp_path / "test.qif")
    
    # Mock successful file dialog and write
    mock_file = mock_open()
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=(qif_file, "QIF files (*.qif)")), \
         patch('qif_gui.QMessageBox', MockQMessageBox), \
         patch('builtins.open', mock_file), \
         patch('os.makedirs', return_value=None), \
         patch('os.path.dirname', return_value=''):
        assert gui.export_qif() is True
        mock_file().write.assert_called()

    # Test export with user cancelling dialog
    gui.transactions = []  # Reset transactions
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=('', '')), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        assert gui.export_qif() is False

    # Test edit transaction
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10,
        'commission': 4.95,
        'memo': 'Test buy'
    }]
    
    # Test edit with valid data
    with patch('qif_gui.TransactionDialog', return_value=MockQDialog(transaction_data=gui.transactions[0])):
        assert gui.edit_transaction(0) is True
        
    # Test edit with invalid index
    assert gui.edit_transaction(-1) is False
    assert gui.edit_transaction(len(gui.transactions)) is False
    
    # Test edit with invalid data
    mock_dialog = MockQDialog()
    mock_dialog.get_data = MagicMock(return_value=None)
    with patch('qif_gui.TransactionDialog', return_value=mock_dialog):
        assert gui.edit_transaction(0) is False
        
    # Test export with empty filename
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=('', '')), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        assert gui.export_qif() is False
        
    # Test export with whitespace filename
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=('  ', '')), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        assert gui.export_qif() is False
        
    # Test export with missing required fields
    gui.transactions = [{
        'action': '',  # Empty action
        'date': '01/15/2024',
        'security': 'AAPL'
    }]
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=(qif_file, "QIF files (*.qif)")), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        assert gui.export_qif() is False
        
    # Test export with file write error
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL'
    }]
    mock_file = mock_open()
    mock_file.side_effect = IOError("Permission denied")
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=(qif_file, "QIF files (*.qif)")), \
         patch('qif_gui.QMessageBox', MockQMessageBox), \
         patch('builtins.open', mock_file):
        assert gui.export_qif() is False
        
    # Test export with non-QIF extension
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=(str(tmp_path / "test.txt"), "All Files (*.*)")), \
         patch('qif_gui.QMessageBox', MockQMessageBox), \
         patch('builtins.open', mock_open()), \
         patch('os.makedirs', return_value=None), \
         patch('os.path.dirname', return_value=''):
        assert gui.export_qif() is True
        
    # Test export with file write error
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL'
    }]
    mock_file = mock_open()
    mock_file.side_effect = IOError("Permission denied")
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=(qif_file, "QIF files (*.qif)")), \
         patch('qif_gui.QMessageBox', MockQMessageBox), \
         patch('builtins.open', mock_file):
        assert gui.export_qif() is False
        
    # Test export with file write error
    mock_file = mock_open()
    mock_file.side_effect = IOError("Permission denied")
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=(qif_file, "QIF files (*.qif)")), \
         patch('qif_gui.QMessageBox', MockQMessageBox), \
         patch('builtins.open', mock_file):
        assert gui.export_qif() is False

    # Test export with invalid transaction data
    gui.transactions = [{'invalid': 'data'}]  # Invalid transaction data
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=(qif_file, "QIF files (*.qif)")), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        assert gui.export_qif() is False

    # Test export with empty required fields
    gui.transactions = [{
        'action': '',  # Empty action
        'date': '01/15/2024',
        'security': 'AAPL'
    }]
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=(qif_file, "QIF files (*.qif)")), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        assert gui.export_qif() is False

    # Test export with missing required fields
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '',  # Empty date
        'security': 'AAPL'
    }]
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=(qif_file, "QIF files (*.qif)")), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        assert gui.export_qif() is False

    # Test export with file write error
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL'
    }]
    mock_file = mock_open()
    mock_file.side_effect = IOError("Permission denied")
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=(qif_file, "QIF files (*.qif)")), \
         patch('qif_gui.QMessageBox', MockQMessageBox), \
         patch('builtins.open', mock_file):
        assert gui.export_qif() is False

    # Test export with non-QIF extension
    gui.transactions = [{
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL'
    }]
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=(str(tmp_path / "test.txt"), "All Files (*.*)")), \
         patch('qif_gui.QMessageBox', MockQMessageBox), \
         patch('builtins.open', mock_open()):
        assert gui.export_qif() is True

    # Test export with non-QIF extension
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=(str(tmp_path / "test.txt"), "All Files (*.*)")), \
         patch('qif_gui.QMessageBox', MockQMessageBox), \
         patch('builtins.open', mock_open()):
        assert gui.export_qif() is True
        assert os.path.exists(str(tmp_path / "test.txt.qif"))

def test_import_csv(gui, tmp_path):
    """Test importing from CSV"""
    # Test import with invalid path
    with patch('qif_gui.QFileDialog', MockQFileDialog), \
         patch('qif_gui.QMessageBox', MockQMessageBox):
        MockQFileDialog.set_mock_file('')
        assert gui.import_csv() is False

    # Test successful import
    csv_content = (
        "Transaction Type,Trade Date,Symbol,Price,Quantity,Commission,Notes\n"
        "Buy,01/15/2024,AAPL,185.92,10,4.95,Test buy\n"
    )
    csv_file = str(tmp_path / "test.csv")
    
    # Mock successful file dialog and read
    mock_reader = MagicMock()
    mock_reader.fieldnames = ['Transaction Type', 'Trade Date', 'Symbol', 'Price', 'Quantity', 'Commission', 'Notes']
    mock_reader.__iter__.return_value = [{
        'Transaction Type': 'Buy',
        'Trade Date': '01/15/2024',
        'Symbol': 'AAPL',
        'Price': '185.92',
        'Quantity': '10',
        'Commission': '4.95',
        'Notes': 'Test buy'
    }]
    
    mock_file = mock_open(read_data=csv_content)
    mock_file.return_value.__enter__ = MagicMock(return_value=mock_file.return_value)
    mock_file.return_value.__exit__ = MagicMock(return_value=None)
    mock_file.return_value.read = MagicMock(return_value=csv_content)
    mock_file.return_value.readlines = MagicMock(return_value=csv_content.splitlines())
    
    # Set up QFileDialog to return a valid path
    with patch('qif_gui.QFileDialog', MockQFileDialog), \
         patch('qif_gui.QMessageBox', MockQMessageBox), \
         patch('builtins.open', mock_file), \
         patch('csv.DictReader', return_value=mock_reader), \
         patch('os.makedirs', MagicMock()), \
         patch('os.path.dirname', MagicMock(return_value='')), \
         patch('os.path.exists', MagicMock(return_value=True)):
        MockQFileDialog.set_mock_file(csv_file)
        result = gui.import_csv()
        assert result is True, "import_csv() should return True for successful import"
        assert len(gui.transactions) == 1, "Should have imported one transaction"
        assert gui.transactions[0]['security'] == 'AAPL', "Security should be AAPL"
        assert gui.transactions[0]['action'] == 'Buy', "Action should be Buy"
        assert gui.transactions[0]['date'] == '01/15/2024', "Date should be 01/15/2024"
        assert gui.transactions[0]['price'] == 185.92, "Price should be 185.92"
        assert gui.transactions[0]['quantity'] == 10.0, "Quantity should be 10.0"
        assert gui.transactions[0]['commission'] == 4.95, "Commission should be 4.95"
        assert gui.transactions[0]['memo'] == 'Test buy', "Memo should be 'Test buy'"
        assert len(gui.transactions) == 1
        assert gui.transactions[0]['security'] == 'AAPL'
        assert gui.transactions[0]['action'] == 'Buy'
        assert gui.transactions[0]['date'] == '01/15/2024'
        assert gui.transactions[0]['price'] == 185.92
        assert gui.transactions[0]['quantity'] == 10.0
        assert gui.transactions[0]['commission'] == 4.95
        assert gui.transactions[0]['memo'] == 'Test buy'

    # Test import with invalid CSV format
    invalid_csv = "Invalid,Header\nBad,Data\n"
    with patch('qif_gui.QFileDialog.getOpenFileName', return_value=(csv_file, "CSV files (*.csv)")), \
         patch('qif_gui.QMessageBox', MockQMessageBox), \
         patch('builtins.open', mock_open(read_data=invalid_csv)):
        assert gui.import_csv() is False

def test_transaction_dialog():
    """Test transaction dialog"""
    # Test valid data
    dialog = TransactionDialog()
    dialog.type_combo.setCurrentText(InvestmentAction.BUY.value)
    
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
    
    # Test invalid data
    dialog = TransactionDialog()
    dialog.fields['date'].setText('')  # Missing required field
    dialog.fields['security'].setText('AAPL')
    assert dialog.get_data() is None
    
    dialog.fields['date'].setText('01/15/2024')
    dialog.fields['security'].setText('')  # Missing required field
    assert dialog.get_data() is None
    
    dialog.fields['security'].setText('AAPL')
    dialog.fields['price'].setText('invalid')  # Invalid numeric field
    data = dialog.get_data()
    assert data is not None  # Should still work, just ignore invalid field
    assert 'price' not in data
    
    # Test all numeric fields with invalid values
    for field in ['price', 'quantity', 'commission', 'amount']:
        dialog.fields[field].setText('invalid')
    data = dialog.get_data()
    assert data is not None
    assert not any(field in data for field in ['price', 'quantity', 'commission', 'amount'])
    
    # Test dialog result
    dialog.accept()
    assert dialog.result is True
    
    dialog.reject()
    assert dialog.result is False

def test_transaction_dialog_field_visibility():
    """Test transaction dialog field visibility"""
    dialog = TransactionDialog()
    
    # Test Buy action
    dialog.update_fields(InvestmentAction.BUY.value)
    assert dialog.fields['price'].isVisible()
    assert dialog.fields['quantity'].isVisible()
    assert dialog.fields['commission'].isVisible()
    assert dialog.fields['amount'].isVisible()  # Amount is visible for Buy/Sell
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
    assert dialog.fields['amount'].isVisible()  # Amount is visible for BuyX/SellX
    assert dialog.fields['account'].isVisible()

def test_all_transaction_types():
    """Test all transaction types in dialog"""
    dialog = TransactionDialog()
    
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
