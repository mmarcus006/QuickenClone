"""Test CLI functionality"""
import pytest
from qif_cli import main
import json
import os
from unittest.mock import patch
import tempfile

def test_main_investment(tmp_path):
    """Test main function with investment transactions"""
    # Create test CSV
    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w") as f:
        f.write("""Transaction Type,Trade Date,Symbol,Price,Quantity,Commission,Notes
Buy,01/15/2024,AAPL,185.92,10,4.95,Test buy""")
    
    # Create test mapping
    mapping = {
        'date': 'Trade Date',
        'action': 'Transaction Type',
        'security': 'Symbol',
        'price': 'Price',
        'quantity': 'Quantity',
        'commission': 'Commission',
        'memo': 'Notes'
    }
    mapping_file = tmp_path / "mapping.json"
    with open(mapping_file, "w") as f:
        json.dump(mapping, f)
    
    # Run main function
    qif_file = tmp_path / "test.qif"
    with patch('sys.argv', ['qif_cli.py', str(csv_file), str(qif_file), '--type', 'investment',
                          '--mapping', json.dumps(mapping)]):
        main()
    
    # Verify output
    assert os.path.exists(qif_file)
    with open(qif_file) as f:
        content = f.read()
        assert "!Type:Invst" in content
        assert "NBuy" in content
        assert "YAAPL" in content

def test_main_cash(tmp_path):
    """Test main function with cash transactions"""
    # Create test CSV
    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w") as f:
        f.write("""Date,Amount,Description,Category,Notes,Check Number
01/15/2024,100.00,Deposit,Income,Test deposit,1001""")
    
    # Create test mapping
    mapping = {
        'date': 'Date',
        'amount': 'Amount',
        'payee': 'Description',
        'category': 'Category',
        'memo': 'Notes',
        'check_num': 'Check Number'
    }
    
    # Run main function
    qif_file = tmp_path / "test.qif"
    with patch('sys.argv', ['qif_cli.py', str(csv_file), str(qif_file), '--type', 'cash',
                          '--mapping', json.dumps(mapping)]):
        main()
    
    # Verify output
    assert os.path.exists(qif_file)
    with open(qif_file) as f:
        content = f.read()
        assert "!Type:Bank" in content
        assert "D01/15/2024" in content
        assert "T100.00" in content
        assert "N1001" in content

def test_main_default_mapping(tmp_path):
    """Test main function with default mapping"""
    # Create test CSV
    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w") as f:
        f.write("""Transaction Type,Trade Date,Symbol,Price,Quantity,Commission,Notes
Buy,01/15/2024,AAPL,185.92,10,4.95,Test buy""")
    
    # Run main function
    qif_file = tmp_path / "test.qif"
    with patch('sys.argv', ['qif_cli.py', str(csv_file), str(qif_file), '--type', 'investment']):
        main()
    
    # Verify output
    assert os.path.exists(qif_file)
    with open(qif_file) as f:
        content = f.read()
        assert "!Type:Invst" in content
        assert "NBuy" in content
        assert "YAAPL" in content

def test_main_invalid_mapping_json():
    """Test main function with invalid mapping JSON"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv') as csv_file:
        csv_file.write("""Date,Amount,Description\n01/15/2024,100.00,Test""")
        csv_file.flush()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.qif') as qif_file:
            with patch('sys.argv', ['qif_cli.py', csv_file.name, qif_file.name, '--type', 'cash',
                                  '--mapping', 'invalid json']):
                with pytest.raises(SystemExit):
                    main()

def test_main_invalid_mapping_file(tmp_path):
    """Test main function with invalid mapping file"""
    # Create test CSV
    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w") as f:
        f.write("""Date,Amount,Description\n01/15/2024,100.00,Test""")
    
    # Create invalid mapping file
    mapping_file = tmp_path / "mapping.json"
    with open(mapping_file, "w") as f:
        f.write("invalid json")
    
    # Run main function
    qif_file = tmp_path / "test.qif"
    with patch('sys.argv', ['qif_cli.py', str(csv_file), str(qif_file), '--type', 'cash',
                          '--mapping', str(mapping_file)]):
        with pytest.raises(SystemExit):
            main()

def test_main_missing_file():
    """Test main function with missing input file"""
    with patch('sys.argv', ['qif_cli.py', 'nonexistent.csv', 'output.qif', '--type', 'investment']):
        with pytest.raises(SystemExit):
            main()

def test_main_invalid_csv(tmp_path):
    """Test main function with invalid CSV file"""
    # Create invalid CSV
    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w") as f:
        f.write("invalid,csv\nfile,content")
    
    # Run main function
    qif_file = tmp_path / "test.qif"
    with patch('sys.argv', ['qif_cli.py', str(csv_file), str(qif_file), '--type', 'investment']):
        with pytest.raises(SystemExit):
            main()

def test_main_invalid_type():
    """Test main function with invalid type"""
    with patch('sys.argv', ['qif_cli.py', 'input.csv', 'output.qif', '--type', 'invalid']):
        with pytest.raises(SystemExit):
            main()
