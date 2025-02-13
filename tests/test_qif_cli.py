import pytest
import json
import os
from qif_cli import main
from unittest.mock import patch

@pytest.fixture
def csv_file(tmp_path):
    file_path = tmp_path / "test.csv"
    with open(file_path, "w", newline="") as f:
        f.write("Trade Date,Transaction Type,Symbol,Price,Quantity,Commission,Notes\n")
        f.write("2024-01-15,Buy,AAPL,185.92,10,4.95,Initial position\n")
    return str(file_path)

@pytest.fixture
def qif_file(tmp_path):
    return str(tmp_path / "output.qif")

@pytest.fixture
def mapping_file(tmp_path):
    file_path = tmp_path / "mapping.json"
    mapping = {
        "date": "Trade Date",
        "action": "Transaction Type",
        "security": "Symbol",
        "price": "Price",
        "quantity": "Quantity",
        "commission": "Commission",
        "memo": "Notes"
    }
    with open(file_path, "w") as f:
        json.dump(mapping, f)
    return str(file_path)

def test_cli_basic_conversion(csv_file, qif_file):
    """Test basic CLI conversion with command line arguments"""
    test_args = [
        "qif_cli.py",
        csv_file,
        qif_file,
        "--type", "investment",
        "--mapping", '{"date":"Trade Date","action":"Transaction Type","security":"Symbol","price":"Price","quantity":"Quantity"}'
    ]
    with patch("sys.argv", test_args):
        main()
    assert os.path.exists(qif_file)
    with open(qif_file) as f:
        content = f.read()
        assert "!Type:Invst" in content
        assert "NBuy" in content
        assert "YAAPL" in content

def test_cli_mapping_file(csv_file, qif_file, mapping_file):
    """Test CLI conversion using mapping file"""
    test_args = [
        "qif_cli.py",
        csv_file,
        qif_file,
        "--type", "investment",
        "--mapping", mapping_file
    ]
    with patch("sys.argv", test_args):
        main()
    assert os.path.exists(qif_file)
    with open(qif_file) as f:
        content = f.read()
        assert "!Type:Invst" in content
        assert "NBuy" in content
        assert "YAAPL" in content

def test_cli_invalid_mapping(csv_file, qif_file):
    """Test CLI with invalid mapping JSON"""
    test_args = [
        "qif_cli.py",
        csv_file,
        qif_file,
        "--type", "investment",
        "--mapping", "invalid json"
    ]
    with patch("sys.argv", test_args):
        with pytest.raises(SystemExit):
            main()

def test_cli_missing_required_args():
    """Test CLI with missing required arguments"""
    test_args = ["qif_cli.py"]
    with patch("sys.argv", test_args):
        with pytest.raises(SystemExit):
            main()

def test_cli_file_not_found(qif_file):
    """Test CLI with nonexistent input file"""
    test_args = [
        "qif_cli.py",
        "nonexistent.csv",
        qif_file,
        "--type", "investment"
    ]
    with patch("sys.argv", test_args):
        with pytest.raises(SystemExit):
            main()
