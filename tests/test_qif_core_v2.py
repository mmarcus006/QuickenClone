"""Test core QIF converter functionality"""
import pytest
from qif_converter import (
    QIFType, InvestmentAction, csv_to_qif,
    convert_date, create_qif_transaction
)
import csv
from io import StringIO

def test_convert_date():
    """Test date conversion"""
    assert convert_date("2024-01-15") == "01/15/2024"
    assert convert_date("01/15/2024") == "01/15/2024"
    assert convert_date("15-01-2024") == "01/15/2024"

def test_qif_transaction():
    """Test QIF transaction creation"""
    data = {
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10,
        'commission': 4.95,
        'memo': 'Test buy'
    }
    qif = create_qif_transaction(data)
    assert "D01/15/2024" in qif
    assert "NBuy" in qif
    assert "YAAPL" in qif
    assert "I185.92" in qif
    assert "Q10" in qif
    assert "O4.95" in qif
    assert "MTest buy" in qif

def test_investment_transaction_buy():
    """Test investment buy transaction"""
    csv_data = """Transaction Type,Trade Date,Symbol,Price,Quantity,Commission,Notes
Buy,01/15/2024,AAPL,185.92,10,4.95,Test buy"""
    qif = csv_to_qif(StringIO(csv_data))
    assert QIFType.INVESTMENT.value in qif
    assert "D01/15/2024" in qif
    assert "NBuy" in qif
    assert "YAAPL" in qif
    assert "I185.92" in qif
    assert "Q10" in qif
    assert "O4.95" in qif
    assert "MTest buy" in qif

def test_investment_transaction_sell():
    """Test investment sell transaction"""
    csv_data = """Transaction Type,Trade Date,Symbol,Price,Quantity,Commission,Notes
Sell,01/15/2024,AAPL,190.00,5,4.95,Test sell"""
    qif = csv_to_qif(StringIO(csv_data))
    assert "D01/15/2024" in qif
    assert "NSell" in qif
    assert "YAAPL" in qif
    assert "I190.00" in qif
    assert "Q-5" in qif
    assert "O4.95" in qif

def test_investment_transaction_dividend():
    """Test dividend transaction"""
    csv_data = """Transaction Type,Trade Date,Symbol,Amount,Notes
Div,01/15/2024,AAPL,0.96,Quarterly dividend"""
    qif = csv_to_qif(StringIO(csv_data))
    assert "D01/15/2024" in qif
    assert "NDiv" in qif
    assert "YAAPL" in qif
    assert "T0.96" in qif
    assert "MQuarterly dividend" in qif

def test_investment_transaction_transfer():
    """Test transfer transaction"""
    csv_data = """Transaction Type,Trade Date,Symbol,Price,Quantity,Account,Notes
BuyX,01/15/2024,AAPL,185.92,10,Cash,Transfer from cash"""
    qif = csv_to_qif(StringIO(csv_data))
    assert "D01/15/2024" in qif
    assert "NBuyX" in qif
    assert "YAAPL" in qif
    assert "I185.92" in qif
    assert "Q10" in qif
    assert "L[Cash]" in qif

def test_qif_writer():
    """Test QIF file writing"""
    csv_data = """Transaction Type,Trade Date,Symbol,Price,Quantity,Commission,Notes
Buy,01/15/2024,AAPL,185.92,10,4.95,Test buy
Sell,01/16/2024,AAPL,190.00,5,4.95,Test sell"""
    qif = csv_to_qif(StringIO(csv_data))
    assert qif.count("^") == 2  # Two transactions
    assert qif.count("NBuy") == 1
    assert qif.count("NSell") == 1

def test_csv_to_qif_conversion():
    """Test full CSV to QIF conversion"""
    csv_data = """Transaction Type,Trade Date,Symbol,Price,Quantity,Commission,Notes
Buy,01/15/2024,AAPL,185.92,10,4.95,Test buy
Sell,01/16/2024,AAPL,190.00,5,4.95,Test sell
Div,01/17/2024,AAPL,0.96,,0,Quarterly dividend"""
    qif = csv_to_qif(StringIO(csv_data))
    assert qif.count("^") == 3  # Three transactions
    assert "!Type:Invst" in qif
    assert qif.count("NBuy") == 1
    assert qif.count("NSell") == 1
    assert qif.count("NDiv") == 1

def test_invalid_csv_mapping():
    """Test handling of invalid CSV mapping"""
    csv_data = """Invalid,Headers,Here
Some,Data,Values"""
    with pytest.raises(KeyError):
        csv_to_qif(StringIO(csv_data))

def test_all_investment_actions():
    """Test all investment action types"""
    for action in InvestmentAction:
        csv_data = f"""Transaction Type,Trade Date,Symbol,Price,Quantity,Commission,Amount,Account,Notes
{action.value},01/15/2024,AAPL,185.92,10,4.95,1859.20,Cash,Test {action.value}"""
        qif = csv_to_qif(StringIO(csv_data))
        assert f"N{action.value}" in qif
        assert "D01/15/2024" in qif
        assert "YAAPL" in qif

def test_transaction_data_handling():
    """Test transaction data handling"""
    data = {
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10,
        'commission': 4.95,
        'amount': 1859.20,
        'account': 'Cash',
        'memo': 'Test transaction'
    }
    qif = create_qif_transaction(data)
    assert all(field in qif for field in [
        'D01/15/2024',
        'NBuy',
        'YAAPL',
        'I185.92',
        'Q10',
        'O4.95',
        'T1859.20',
        'L[Cash]',
        'MTest transaction'
    ])

def test_transaction_validation():
    """Test transaction data validation"""
    # Missing required fields
    with pytest.raises(KeyError):
        create_qif_transaction({})
    
    # Invalid action
    with pytest.raises(ValueError):
        create_qif_transaction({'action': 'InvalidAction'})
    
    # Invalid date format
    with pytest.raises(ValueError):
        create_qif_transaction({
            'action': InvestmentAction.BUY.value,
            'date': 'invalid-date'
        })

def test_file_operations(tmp_path):
    """Test file I/O operations"""
    # Create test CSV
    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w") as f:
        f.write("""Transaction Type,Trade Date,Symbol,Price,Quantity,Commission,Notes
Buy,01/15/2024,AAPL,185.92,10,4.95,Test buy""")
    
    # Create test QIF
    qif_file = tmp_path / "test.qif"
    with open(csv_file) as f, open(qif_file, "w") as out:
        out.write(csv_to_qif(f))
    
    # Verify QIF content
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
        data = {
            'action': action.value,
            'date': '01/15/2024',
            'security': 'AAPL',
            'price': 185.92,
            'quantity': 10,
            'commission': 4.95,
            'amount': 1859.20,
            'account': 'Cash',
            'memo': f'Test {action.value}'
        }
        qif = create_qif_transaction(data)
        assert f"N{action.value}" in qif
        for field in required_fields:
            if field == 'price':
                assert 'I185.92' in qif
            elif field == 'quantity':
                assert 'Q10' in qif
            elif field == 'commission':
                assert 'O4.95' in qif
            elif field == 'amount':
                assert 'T1859.20' in qif
            elif field == 'account':
                assert 'L[Cash]' in qif

def test_transfer_handling():
    """Test transfer transaction handling"""
    transfer_actions = [
        InvestmentAction.BUYX,
        InvestmentAction.SELLX,
        InvestmentAction.SHRSIN,
        InvestmentAction.SHRSOUT
    ]
    
    for action in transfer_actions:
        data = {
            'action': action.value,
            'date': '01/15/2024',
            'security': 'AAPL',
            'price': 185.92,
            'quantity': 10,
            'account': 'Cash',
            'memo': f'Test {action.value}'
        }
        qif = create_qif_transaction(data)
        assert f"N{action.value}" in qif
        assert "L[Cash]" in qif

def test_duplicate_transaction():
    """Test transaction duplication"""
    original = {
        'action': InvestmentAction.BUY.value,
        'date': '01/15/2024',
        'security': 'AAPL',
        'price': 185.92,
        'quantity': 10,
        'commission': 4.95,
        'memo': 'Original transaction'
    }
    
    duplicate = original.copy()
    duplicate['date'] = '01/16/2024'
    duplicate['memo'] = 'Duplicated transaction'
    
    qif1 = create_qif_transaction(original)
    qif2 = create_qif_transaction(duplicate)
    
    assert "D01/15/2024" in qif1
    assert "D01/16/2024" in qif2
    assert "MOriginal transaction" in qif1
    assert "MDuplicated transaction" in qif2
