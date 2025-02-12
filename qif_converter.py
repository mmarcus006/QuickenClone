import csv
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class QIFType(Enum):
    BANK = "!Type:Bank"
    CASH = "!Type:Cash"
    INVESTMENT = "!Type:Invst"
    CREDIT = "!Type:CCard"
    ASSET = "!Type:Oth A"
    LIABILITY = "!Type:Oth L"

class InvestmentAction(Enum):
    BUY = "Buy"         # Regular buy
    SELL = "Sell"       # Regular sell
    BUYX = "BuyX"       # Buy with transfer
    SELLX = "SellX"     # Sell with transfer
    DIV = "Div"         # Cash dividend
    INTINC = "IntInc"   # Interest income
    REINVDIV = "ReinvDiv"  # Reinvested dividend
    SHRSIN = "ShrsIn"   # Shares transferred in
    SHRSOUT = "ShrsOut" # Shares transferred out
    STKSPLIT = "StkSplit"  # Stock split
    CGLONG = "CGLong"   # Long-term capital gains
    CGSHORT = "CGShort" # Short-term capital gains
    MARGINT = "MargInt" # Margin interest
    MISCINC = "MiscInc" # Miscellaneous income
    MISCEXP = "MiscExp" # Miscellaneous expense

@dataclass
class QIFTransaction:
    date: str
    amount: float
    payee: Optional[str] = None
    memo: Optional[str] = None
    category: Optional[str] = None
    check_num: Optional[str] = None
    
    def to_qif(self) -> str:
        lines = []
        lines.append(f"D{self.date}")
        lines.append(f"T{self.amount:.2f}")
        if self.payee:
            lines.append(f"P{self.payee}")
        if self.memo:
            lines.append(f"M{self.memo}")
        if self.category:
            lines.append(f"L{self.category}")
        if self.check_num:
            lines.append(f"N{self.check_num}")
        lines.append("^")
        return "\n".join(lines)

@dataclass
class QIFInvestmentTransaction:
    date: str
    action: str  # Buy, Sell, BuyX, SellX, Div, IntInc
    security: str
    price: float
    quantity: float
    commission: Optional[float] = None
    memo: Optional[str] = None
    amount: Optional[float] = None
    
    def to_qif(self) -> str:
        lines = []
        lines.append(f"D{self.date}")
        lines.append(f"N{self.action}")
        lines.append(f"Y{self.security}")
        lines.append(f"I{self.price:.4f}")
        lines.append(f"Q{self.quantity:.4f}")
        if self.commission:
            lines.append(f"O{self.commission:.2f}")
        if self.memo:
            lines.append(f"M{self.memo}")
        if self.amount:
            lines.append(f"T{self.amount:.2f}")
        lines.append("^")
        return "\n".join(lines)

class QIFWriter:
    def __init__(self, output_file: str):
        self.output_file = output_file
        
    def write_header(self, qif_type: QIFType):
        with open(self.output_file, 'a') as f:
            f.write(f"{qif_type.value}\n")
            
    def write_transaction(self, transaction):
        with open(self.output_file, 'a') as f:
            f.write(transaction.to_qif() + "\n")

def convert_date(date_str: str) -> str:
    """Convert various date formats to MM/DD/YYYY"""
    try:
        # Try different date formats
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d'):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%m/%d/%Y')
            except ValueError:
                continue
        raise ValueError(f"Unsupported date format: {date_str}")
    except Exception as e:
        raise ValueError(f"Error converting date {date_str}: {str(e)}")

def csv_to_qif(csv_file: str, qif_file: str, transaction_type: str, mapping: Dict[str, str]):
    """
    Convert CSV file to QIF format
    
    Args:
        csv_file: Input CSV file path
        qif_file: Output QIF file path
        transaction_type: Type of transactions ('cash', 'investment')
        mapping: Dictionary mapping CSV columns to QIF fields
    """
    writer = QIFWriter(qif_file)
    
    # Set QIF type based on transaction type
    qif_type = QIFType.INVESTMENT if transaction_type == 'investment' else QIFType.BANK
    writer.write_header(qif_type)
    
    with open(csv_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                if transaction_type == 'investment':
                    transaction = QIFInvestmentTransaction(
                        date=convert_date(row[mapping['date']]),
                        action=row[mapping['action']],
                        security=row[mapping['security']],
                        price=float(row[mapping['price']]),
                        quantity=float(row[mapping['quantity']]),
                        commission=float(row[mapping['commission']]) if 'commission' in mapping else None,
                        memo=row[mapping['memo']] if 'memo' in mapping else None,
                        amount=float(row[mapping['amount']]) if 'amount' in mapping else None
                    )
                else:
                    transaction = QIFTransaction(
                        date=convert_date(row[mapping['date']]),
                        amount=float(row[mapping['amount']]),
                        payee=row[mapping['payee']] if 'payee' in mapping else None,
                        memo=row[mapping['memo']] if 'memo' in mapping else None,
                        category=row[mapping['category']] if 'category' in mapping else None,
                        check_num=row[mapping['check_num']] if 'check_num' in mapping else None
                    )
                writer.write_transaction(transaction)
            except (ValueError, KeyError) as e:
                print(f"Error processing row: {row}")
                print(f"Error details: {str(e)}")
                continue

if __name__ == "__main__":
    # Example usage
    investment_mapping = {
        'date': 'Trade Date',
        'action': 'Transaction Type',
        'security': 'Symbol',
        'price': 'Price',
        'quantity': 'Quantity',
        'commission': 'Commission',
        'memo': 'Notes'
    }
    
    cash_mapping = {
        'date': 'Date',
        'amount': 'Amount',
        'payee': 'Description',
        'category': 'Category',
        'memo': 'Notes'
    }
