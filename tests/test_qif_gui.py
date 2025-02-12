import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from qif_gui import TransactionDialog, QIFConverterGUI
import sys

@pytest.fixture
def app():
    app = QApplication(sys.argv)
    yield app
    app.quit()

@pytest.fixture
def main_window(app):
    window = QIFConverterGUI()
    yield window

@pytest.fixture
def transaction_dialog(app):
    dialog = TransactionDialog()
    yield dialog

def test_transaction_dialog_creation(transaction_dialog):
    """Test transaction dialog initialization"""
    assert transaction_dialog.windowTitle() == "Transaction Details"
    assert transaction_dialog.type_combo is not None
    assert len(transaction_dialog.fields) > 0

def test_transaction_dialog_field_visibility(transaction_dialog):
    """Test field visibility updates based on transaction type"""
    # Test Buy transaction fields
    transaction_dialog.type_combo.setCurrentText("Buy")
    visible_fields = {field for field, widget in transaction_dialog.fields.items() 
                     if widget.isVisible()}
    assert visible_fields >= {'date', 'security', 'price', 'quantity', 'commission'}

    # Test Dividend transaction fields
    transaction_dialog.type_combo.setCurrentText("Div")
    visible_fields = {field for field, widget in transaction_dialog.fields.items() 
                     if widget.isVisible()}
    assert visible_fields >= {'date', 'security', 'amount'}

def test_transaction_dialog_data(transaction_dialog):
    """Test transaction data retrieval"""
    # Set test data
    transaction_dialog.type_combo.setCurrentText("Buy")
    transaction_dialog.fields['date'].setText("01/15/2024")
    transaction_dialog.fields['security'].setText("AAPL")
    transaction_dialog.fields['price'].setText("185.92")
    transaction_dialog.fields['quantity'].setText("10")
    
    data = transaction_dialog.get_data()
    assert data['action'] == "Buy"
    assert data['date'] == "01/15/2024"
    assert data['security'] == "AAPL"
    assert data['price'] == 185.92
    assert data['quantity'] == 10.0

def test_main_window_initialization(main_window):
    """Test main window initialization"""
    assert main_window.windowTitle() == "CSV to QIF Converter"
    assert main_window.transaction_list is not None
    assert len(main_window.transactions) == 0

def test_add_transaction(main_window, monkeypatch):
    """Test adding a transaction"""
    # Mock TransactionDialog.exec to return True and provide test data
    def mock_exec(self):
        self.type_combo.setCurrentText("Buy")
        self.fields['date'].setText("01/15/2024")
        self.fields['security'].setText("AAPL")
        self.fields['price'].setText("185.92")
        self.fields['quantity'].setText("10")
        return True
    
    monkeypatch.setattr(TransactionDialog, "exec", mock_exec)
    
    # Add transaction
    main_window.add_transaction()
    
    assert len(main_window.transactions) == 1
    assert main_window.transaction_list.count() == 1
    assert "AAPL" in main_window.transaction_list.item(0).text()

def test_duplicate_transaction(main_window, monkeypatch):
    """Test transaction duplication"""
    # Add initial transaction
    main_window.transactions.append({
        'action': 'Buy',
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10
    })
    main_window.update_transaction_list()
    
    # Select the transaction
    main_window.transaction_list.setCurrentRow(0)
    
    # Mock QDialog.exec to return True and simulate date change
    def mock_exec(self):
        return True
    monkeypatch.setattr('PyQt6.QtWidgets.QDialog.exec', mock_exec)
    
    # Duplicate transaction
    main_window.duplicate_transaction()
    
    assert len(main_window.transactions) == 2
    assert main_window.transaction_list.count() == 2

def test_delete_transaction(main_window):
    """Test transaction deletion"""
    # Add test transaction
    main_window.transactions.append({
        'action': 'Buy',
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10
    })
    main_window.update_transaction_list()
    
    # Select and delete
    main_window.transaction_list.setCurrentRow(0)
    main_window.delete_transaction()
    
    assert len(main_window.transactions) == 0
    assert main_window.transaction_list.count() == 0
