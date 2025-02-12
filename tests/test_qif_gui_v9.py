"""Test GUI functionality with proper Qt mocking"""
import pytest
import os
from unittest.mock import patch
import sys
from qt_mock_v2 import mock_qt, mock_widgets, mock_core

# Patch modules before importing
with patch.dict('sys.modules', {
    'PyQt6': mock_qt,
    'PyQt6.QtWidgets': mock_widgets,
    'PyQt6.QtCore': mock_core
}):
    from qif_gui import QIFConverterGUI, TransactionDialog
    from qif_converter import InvestmentAction

@pytest.fixture
def gui():
    """Create GUI instance"""
    return QIFConverterGUI()

def test_gui_initialization(gui):
    """Test GUI initialization"""
    assert hasattr(gui, 'transaction_list')
    assert hasattr(gui, 'transactions')
    assert len(gui.transactions) == 0
    assert gui.window_title == "CSV to QIF Converter"

def test_add_transaction(gui):
    """Test adding a transaction"""
    dialog = TransactionDialog()
    dialog.type_combo.setCurrentText(InvestmentAction.BUY.value)
    
    dialog.fields['date'].setText('01/15/2024')
    dialog.fields['security'].setText('AAPL')
    dialog.fields['price'].setText('185.92')
    dialog.fields['quantity'].setText('10')
    dialog.fields['commission'].setText('4.95')
    dialog.fields['memo'].setText('Test buy')
    
    with patch('qif_gui.TransactionDialog', return_value=dialog):
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
    
    dialog = TransactionDialog()
    dialog.type_combo.setCurrentText(InvestmentAction.BUY.value)
    dialog.fields['date'].setText('01/16/2024')
    dialog.fields['security'].setText('AAPL')
    dialog.fields['price'].setText('185.92')
    dialog.fields['quantity'].setText('10')
    
    with patch('qif_gui.TransactionDialog', return_value=dialog):
        gui.duplicate_transaction()
    
    assert len(gui.transactions) == 2
    assert gui.transactions[1]['date'] == '01/16/2024'
    assert gui.transactions[1]['security'] == original_trans['security']

def test_export_qif(gui, tmp_path):
    """Test exporting to QIF"""
    os.makedirs(tmp_path, exist_ok=True)
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
    with patch('qif_gui.QFileDialog.getSaveFileName', return_value=(qif_file, "QIF files (*.qif)")):
        gui.export_qif()
    
    assert os.path.exists(qif_file)
    with open(qif_file) as f:
        content = f.read()
        assert "!Type:Invst" in content
        assert "NBuy" in content
        assert "YAAPL" in content
        assert "I185.9200" in content
        assert "Q10.0000" in content
        assert "O4.95" in content

def test_import_csv(gui, tmp_path):
    """Test importing from CSV"""
    os.makedirs(tmp_path, exist_ok=True)
    csv_file = str(tmp_path / "test.csv")
    with open(csv_file, "w") as f:
        f.write("Transaction Type,Trade Date,Symbol,Price,Quantity,Commission,Notes\n")
        f.write("Buy,01/15/2024,AAPL,185.92,10,4.95,Test buy\n")
    
    with patch('qif_gui.QFileDialog.getOpenFileName', return_value=(csv_file, "CSV files (*.csv)")):
        gui.import_csv()
    
    assert len(gui.transactions) == 1
    assert gui.transactions[0]['security'] == 'AAPL'
    assert gui.transactions[0]['action'] == 'Buy'

def test_transaction_dialog():
    """Test transaction dialog"""
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
