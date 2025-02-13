import pytest
from datetime import datetime
from qif_converter import (
    QIFType, InvestmentAction, QIFTransaction, QIFInvestmentTransaction,
    QIFWriter, convert_date, csv_to_qif
)
import tempfile
import os
import csv

@pytest.fixture
def temp_file():
    fd, path = tempfile.mkstemp()
    yield path
    os.close(fd)
    os.unlink(path)

@pytest.fixture
def csv_file():
    fd, path = tempfile.mkstemp(suffix='.csv')
    with os.fdopen(fd, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Trade Date', 'Transaction Type', 'Symbol', 'Price', 
                        'Quantity', 'Commission', 'Notes'])
        writer.writerow(['2024-01-15', 'Buy', 'AAPL', '185.92', '10', '4.95', 
                        'Initial position'])
    yield path
    os.unlink(path)

def test_convert_date():
    """Test date conversion with various formats"""
    assert convert_date('2024-01-15') == '01/15/2024'
    assert convert_date('01/15/2024') == '01/15/2024'
    assert convert_date('15/01/2024') == '01/15/2024'
    with pytest.raises(ValueError):
        convert_date('invalid')

def test_qif_transaction():
    """Test basic QIF transaction formatting"""
    trans = QIFTransaction(
        date='01/15/2024',
        amount=-1234.56,
        payee='Test Payee',
        memo='Test memo',
        category='Expenses:Test',
        check_num='1001'
    )
    qif = trans.to_qif().split('\n')
    assert 'D01/15/2024' in qif
    assert 'T-1234.56' in qif
    assert 'PTest Payee' in qif
    assert 'MTest memo' in qif
    assert 'LExpenses:Test' in qif
    assert 'N1001' in qif
    assert '^' in qif

def test_investment_transaction_buy():
    """Test buy investment transaction"""
    trans = QIFInvestmentTransaction(
        date='01/15/2024',
        action='Buy',
        security='AAPL',
        price=185.92,
        quantity=10,
        commission=4.95,
        memo='Buy Apple'
    )
    qif = trans.to_qif().split('\n')
    assert 'D01/15/2024' in qif
    assert 'NBuy' in qif
    assert 'YAAPL' in qif
    assert 'I185.9200' in qif
    assert 'Q10.0000' in qif
    assert 'O4.95' in qif
    assert 'MBuy Apple' in qif
    assert '^' in qif

def test_investment_transaction_sell():
    """Test sell investment transaction"""
    trans = QIFInvestmentTransaction(
        date='01/15/2024',
        action='Sell',
        security='MSFT',
        price=390.12,
        quantity=5,
        commission=4.95,
        memo='Take profit'
    )
    qif = trans.to_qif().split('\n')
    assert 'D01/15/2024' in qif
    assert 'NSell' in qif
    assert 'YMSFT' in qif
    assert 'I390.1200' in qif
    assert 'Q5.0000' in qif
    assert '^' in qif

def test_investment_transaction_dividend():
    """Test dividend transaction"""
    trans = QIFInvestmentTransaction(
        date='01/15/2024',
        action='Div',
        security='AAPL',
        amount=24.50,
        memo='Quarterly dividend'
    )
    qif = trans.to_qif().split('\n')
    assert 'D01/15/2024' in qif
    assert 'NDiv' in qif
    assert 'YAAPL' in qif
    assert 'T24.50' in qif
    assert '^' in qif

def test_investment_transaction_transfer():
    """Test transfer transaction"""
    trans = QIFInvestmentTransaction(
        date='01/15/2024',
        action='BuyX',
        security='GOOGL',
        price=152.19,
        quantity=15,
        commission=4.95,
        memo='Transfer buy',
        amount=2283.80
    )
    qif = trans.to_qif().split('\n')
    assert 'D01/15/2024' in qif
    assert 'NBuyX' in qif
    assert 'YGOOGL' in qif
    assert 'I152.1900' in qif
    assert 'Q15.0000' in qif
    assert 'T2283.80' in qif
    assert '^' in qif

def test_qif_writer(temp_file):
    """Test QIF file writing"""
    writer = QIFWriter(temp_file)
    writer.write_header(QIFType.INVESTMENT)
    
    trans = QIFInvestmentTransaction(
        date='01/15/2024',
        action='Buy',
        security='AAPL',
        price=185.92,
        quantity=10,
        commission=4.95
    )
    writer.write_transaction(trans)
    
    with open(temp_file, 'r') as f:
        content = f.read()
        assert QIFType.INVESTMENT.value in content
        assert 'D01/15/2024' in content
        assert 'NBuy' in content
        assert '^' in content

def test_csv_to_qif_conversion(csv_file, temp_file):
    """Test CSV to QIF conversion"""
    mapping = {
        'date': 'Trade Date',
        'action': 'Transaction Type',
        'security': 'Symbol',
        'price': 'Price',
        'quantity': 'Quantity',
        'commission': 'Commission',
        'memo': 'Notes'
    }
    
    csv_to_qif(csv_file, temp_file, 'investment', mapping)
    
    with open(temp_file, 'r') as f:
        content = f.read()
        assert QIFType.INVESTMENT.value in content
        assert 'D01/15/2024' in content
        assert 'NBuy' in content
        assert 'YAAPL' in content
        assert 'I185.9200' in content
        assert 'Q10.0000' in content
        assert 'O4.95' in content
        assert '^' in content

def test_invalid_csv_mapping(csv_file, temp_file):
    """Test handling of invalid CSV mapping"""
    mapping = {
        'date': 'NonexistentField',
        'action': 'Transaction Type'
    }
    
    with pytest.raises(KeyError):
        csv_to_qif(csv_file, temp_file, 'investment', mapping)

def test_all_investment_actions():
    """Test all investment action types"""
    actions = [
        ('Buy', {'security': 'AAPL', 'price': 185.92, 'quantity': 10}),
        ('Sell', {'security': 'MSFT', 'price': 390.12, 'quantity': 5}),
        ('BuyX', {'security': 'GOOGL', 'price': 152.19, 'quantity': 15, 'account': 'Cash'}),
        ('SellX', {'security': 'GOOGL', 'price': 155.99, 'quantity': 5, 'account': 'Cash'}),
        ('Div', {'security': 'AAPL', 'amount': 24.50}),
        ('IntInc', {'amount': 12.34}),
        ('ReinvDiv', {'security': 'AAPL', 'amount': 24.50, 'quantity': 0.126, 'price': 190.50}),
        ('ShrsIn', {'security': 'TSLA', 'quantity': 50, 'account': 'Other Account'}),
        ('ShrsOut', {'security': 'NVDA', 'quantity': 10, 'account': 'Other Account'}),
        ('StkSplit', {'security': 'TSLA', 'quantity': 150}),
        ('CGLong', {'security': 'AAPL', 'amount': 1000.00}),
        ('CGShort', {'security': 'MSFT', 'amount': 500.00}),
        ('MargInt', {'amount': -25.50}),
        ('MiscInc', {'amount': 100.00}),
        ('MiscExp', {'amount': -50.00})
    ]
    
    for action, fields in actions:
        trans = QIFInvestmentTransaction(
            date='01/15/2024',
            action=action,
            **fields
        )
        qif = trans.to_qif().split('\n')
        assert f'N{action}' in qif
        if 'security' in fields:
            assert f'Y{fields["security"]}' in qif
        if 'amount' in fields:
            assert f'T{fields["amount"]:.2f}' in qif
        if 'account' in fields:
            assert f'L[{fields["account"]}]' in qif
