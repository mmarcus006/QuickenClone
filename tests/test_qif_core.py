import pytest
from qif_converter import (
    QIFType, InvestmentAction, QIFTransaction, QIFInvestmentTransaction,
    QIFWriter, convert_date, csv_to_qif
)
from qif_gui import QIFConverterGUI
from unittest.mock import MagicMock, patch
import tempfile
import os
import csv

def test_qif_converter_core():
    """Test core QIF converter functionality"""
    # Test QIF types
    assert QIFType.INVESTMENT.value == "!Type:Invst"
    assert QIFType.BANK.value == "!Type:Bank"
    
    # Test investment actions
    assert InvestmentAction.BUY.value == "Buy"
    assert InvestmentAction.SELL.value == "Sell"
    assert InvestmentAction.DIV.value == "Div"

def test_transaction_data_handling():
    """Test transaction data handling"""
    # Test cash transaction
    cash_trans = QIFTransaction(
        date="01/15/2024",
        amount=-1234.56,
        payee="Test Payee",
        memo="Test memo"
    )
    qif_str = cash_trans.to_qif()
    assert "D01/15/2024" in qif_str
    assert "T-1234.56" in qif_str
    assert "PTest Payee" in qif_str
    
    # Test investment transaction
    inv_trans = QIFInvestmentTransaction(
        date="01/15/2024",
        action=InvestmentAction.BUY.value,
        security="AAPL",
        price=185.92,
        quantity=10,
        commission=4.95
    )
    qif_str = inv_trans.to_qif()
    assert "D01/15/2024" in qif_str
    assert "NBuy" in qif_str
    assert "YAAPL" in qif_str

def test_transaction_validation():
    """Test transaction validation"""
    # Test invalid date
    with pytest.raises(ValueError):
        convert_date("invalid-date")
    
    # Test missing required fields
    with pytest.raises(KeyError):
        csv_to_qif("test.csv", "out.qif", "investment", {})

def test_file_operations(tmp_path):
    """Test file operations"""
    # Create test CSV
    csv_path = tmp_path / "test.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Amount", "Description"])
        writer.writerow(["2024-01-15", "1234.56", "Test"])
    
    # Test CSV reading
    mapping = {
        "date": "Date",
        "amount": "Amount",
        "payee": "Description"
    }
    qif_path = tmp_path / "test.qif"
    csv_to_qif(str(csv_path), str(qif_path), "cash", mapping)
    
    # Verify QIF output
    with open(qif_path) as f:
        content = f.read()
        assert QIFType.BANK.value in content
        assert "D01/15/2024" in content
        assert "T1234.56" in content

def test_investment_actions():
    """Test all investment action types"""
    actions = [
        (InvestmentAction.BUY, {"security": "AAPL", "price": 185.92, "quantity": 10}),
        (InvestmentAction.SELL, {"security": "MSFT", "price": 390.12, "quantity": 5}),
        (InvestmentAction.DIV, {"security": "AAPL", "amount": 24.50}),
        (InvestmentAction.INTINC, {"amount": 12.34}),
        (InvestmentAction.REINVDIV, {"security": "AAPL", "amount": 24.50, "quantity": 0.126}),
        (InvestmentAction.CGLONG, {"security": "AAPL", "amount": 1000.00}),
        (InvestmentAction.CGSHORT, {"security": "MSFT", "amount": 500.00}),
        (InvestmentAction.MARGINT, {"amount": -25.50})
    ]
    
    for action, fields in actions:
        trans = QIFInvestmentTransaction(
            date="01/15/2024",
            action=action.value,
            **fields
        )
        qif = trans.to_qif()
        assert f"N{action.value}" in qif
        assert "D01/15/2024" in qif

def test_transfer_handling():
    """Test transfer transaction handling"""
    trans = QIFInvestmentTransaction(
        date="01/15/2024",
        action=InvestmentAction.BUYX.value,
        security="AAPL",
        price=185.92,
        quantity=10,
        account="Cash Account"
    )
    qif = trans.to_qif()
    assert "NBuyX" in qif
    assert "L[Cash Account]" in qif

def test_duplicate_transaction():
    """Test transaction duplication logic"""
    original = QIFInvestmentTransaction(
        date="01/15/2024",
        action=InvestmentAction.BUY.value,
        security="AAPL",
        price=185.92,
        quantity=10
    )
    duplicate = QIFInvestmentTransaction(
        date="01/16/2024",  # Only date changed
        action=original.action,
        security=original.security,
        price=original.price,
        quantity=original.quantity
    )
    assert duplicate.to_qif() != original.to_qif()
    assert "D01/16/2024" in duplicate.to_qif()
