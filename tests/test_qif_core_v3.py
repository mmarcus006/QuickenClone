"""Test core QIF converter functionality"""
import pytest
from qif_converter import (
    QIFType, InvestmentAction, QIFTransaction, QIFInvestmentTransaction,
    QIFWriter, convert_date, csv_to_qif
)
import csv
from io import StringIO
import tempfile
import os

def test_convert_date():
    """Test date conversion"""
    assert convert_date("2024-01-15") == "01/15/2024"
    assert convert_date("01/15/2024") == "01/15/2024"
    assert convert_date("15-01-2024") == "01/15/2024"

def test_qif_transaction():
    """Test QIF transaction creation"""
    transaction = QIFTransaction(
        date="01/15/2024",
        amount=185.92,
        payee="AAPL",
        memo="Test buy",
        category="Investments",
        check_num="1001"
    )
    qif = transaction.to_qif()
    assert "D01/15/2024" in qif
    assert "T185.92" in qif
    assert "PAAPL" in qif
    assert "MTest buy" in qif
    assert "LInvestments" in qif
    assert "N1001" in qif
    assert "^" in qif

def test_investment_transaction():
    """Test investment transaction creation"""
    transaction = QIFInvestmentTransaction(
        date="01/15/2024",
        action=InvestmentAction.BUY.value,
        security="AAPL",
        price=185.92,
        quantity=10,
        commission=4.95,
        memo="Test buy",
        amount=1859.20
    )
    qif = transaction.to_qif()
    assert "D01/15/2024" in qif
    assert "NBuy" in qif
    assert "YAAPL" in qif
    assert "I185.9200" in qif
    assert "Q10.0000" in qif
    assert "O4.95" in qif
    assert "T1859.20" in qif
    assert "MTest buy" in qif
    assert "^" in qif

def test_qif_writer(tmp_path):
    """Test QIF writer"""
    qif_file = tmp_path / "test.qif"
    writer = QIFWriter(str(qif_file))
    
    # Write header
    writer.write_header(QIFType.INVESTMENT)
    
    # Write transaction
    transaction = QIFInvestmentTransaction(
        date="01/15/2024",
        action=InvestmentAction.BUY.value,
        security="AAPL",
        price=185.92,
        quantity=10,
        commission=4.95,
        memo="Test buy"
    )
    writer.write_transaction(transaction)
    
    with open(qif_file) as f:
        content = f.read()
        assert QIFType.INVESTMENT.value in content
        assert "NBuy" in content
        assert "YAAPL" in content

def test_investment_actions():
    """Test all investment action types"""
    actions = {
        InvestmentAction.BUY: {'price', 'quantity', 'commission'},
        InvestmentAction.SELL: {'price', 'quantity', 'commission'},
        InvestmentAction.DIV: {'amount'},
        InvestmentAction.INTINC: {'amount'},
        InvestmentAction.CGLONG: {'amount'},
        InvestmentAction.CGSHORT: {'amount'},
        InvestmentAction.REINVDIV: {'price', 'quantity', 'amount'},
        InvestmentAction.BUYX: {'price', 'quantity', 'account'},
        InvestmentAction.SELLX: {'price', 'quantity', 'account'},
        InvestmentAction.SHRSIN: {'quantity', 'price', 'account'},
        InvestmentAction.SHRSOUT: {'quantity', 'price', 'account'},
        InvestmentAction.STKSPLIT: {'quantity'},
        InvestmentAction.MARGINT: {'amount'},
        InvestmentAction.MISCINC: {'amount'},
        InvestmentAction.MISCEXP: {'amount'}
    }
    
    for action, required_fields in actions.items():
        transaction = QIFInvestmentTransaction(
            date="01/15/2024",
            action=action.value,
            security="AAPL",
            price=185.92 if 'price' in required_fields else None,
            quantity=10 if 'quantity' in required_fields else None,
            commission=4.95 if 'commission' in required_fields else None,
            amount=1859.20 if 'amount' in required_fields else None,
            account="Cash" if 'account' in required_fields else None,
            memo=f"Test {action.value}"
        )
        qif = transaction.to_qif()
        assert f"N{action.value}" in qif
        for field in required_fields:
            if field == 'price':
                assert 'I185.9200' in qif
            elif field == 'quantity':
                assert 'Q10.0000' in qif
            elif field == 'commission':
                assert 'O4.95' in qif
            elif field == 'amount':
                assert 'T1859.20' in qif
            elif field == 'account':
                assert 'L[Cash]' in qif

def test_csv_to_qif_conversion(tmp_path):
    """Test CSV to QIF conversion"""
    # Create test CSV
    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w") as f:
        f.write("""Transaction Type,Trade Date,Symbol,Price,Quantity,Commission,Notes
Buy,01/15/2024,AAPL,185.92,10,4.95,Test buy
Sell,01/16/2024,AAPL,190.00,5,4.95,Test sell
Div,01/17/2024,AAPL,,,0.96,Quarterly dividend""")
    
    # Create test QIF
    qif_file = tmp_path / "test.qif"
    mapping = {
        'date': 'Trade Date',
        'action': 'Transaction Type',
        'security': 'Symbol',
        'price': 'Price',
        'quantity': 'Quantity',
        'commission': 'Commission',
        'memo': 'Notes'
    }
    csv_to_qif(str(csv_file), str(qif_file), 'investment', mapping)
    
    with open(qif_file) as f:
        content = f.read()
        assert QIFType.INVESTMENT.value in content
        assert content.count("^") == 3  # Three transactions
        assert content.count("NBuy") == 1
        assert content.count("NSell") == 1
        assert content.count("NDiv") == 1

def test_invalid_csv_mapping():
    """Test handling of invalid CSV mapping"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv') as csv_file, \
         tempfile.NamedTemporaryFile(mode='w', suffix='.qif') as qif_file:
        csv_file.write("""Invalid,Headers,Here
Some,Data,Values""")
        csv_file.flush()
        
        with pytest.raises(KeyError):
            csv_to_qif(csv_file.name, qif_file.name, 'investment', {})

def test_transfer_handling():
    """Test transfer transaction handling"""
    transfer_actions = [
        InvestmentAction.BUYX,
        InvestmentAction.SELLX,
        InvestmentAction.SHRSIN,
        InvestmentAction.SHRSOUT
    ]
    
    for action in transfer_actions:
        transaction = QIFInvestmentTransaction(
            date="01/15/2024",
            action=action.value,
            security="AAPL",
            price=185.92,
            quantity=10,
            account="Cash",
            memo=f"Test {action.value}"
        )
        qif = transaction.to_qif()
        assert f"N{action.value}" in qif
        assert "L[Cash]" in qif

def test_invalid_date_format():
    """Test invalid date format handling"""
    with pytest.raises(ValueError):
        convert_date("invalid-date")

def test_missing_required_fields():
    """Test missing required fields"""
    with pytest.raises(TypeError):
        QIFTransaction()
    
    with pytest.raises(TypeError):
        QIFInvestmentTransaction()

def test_qif_type_values():
    """Test QIF type values"""
    assert QIFType.BANK.value == "!Type:Bank"
    assert QIFType.CASH.value == "!Type:Cash"
    assert QIFType.INVESTMENT.value == "!Type:Invst"
    assert QIFType.CREDIT.value == "!Type:CCard"
    assert QIFType.ASSET.value == "!Type:Oth A"
    assert QIFType.LIABILITY.value == "!Type:Oth L"
