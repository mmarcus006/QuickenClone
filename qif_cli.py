#!/usr/bin/env python3
import argparse
import json
from qif_converter import csv_to_qif

def main():
    parser = argparse.ArgumentParser(
        description='Convert CSV files to QIF format')
    
    parser.add_argument('input_file', 
                       help='Input CSV file path')
    parser.add_argument('output_file',
                       help='Output QIF file path')
    parser.add_argument('--type', '-t',
                       choices=['investment', 'cash'],
                       required=True,
                       help='Type of transactions')
    parser.add_argument('--mapping', '-m',
                       type=str,
                       help='JSON string or file path containing field mapping')
    
    args = parser.parse_args()
    
    # Default mappings
    if args.type == 'investment':
        mapping = {
            'date': 'Trade Date',
            'action': 'Transaction Type',
            'security': 'Symbol',
            'price': 'Price',
            'quantity': 'Quantity',
            'commission': 'Commission',
            'memo': 'Notes'
        }
    else:
        mapping = {
            'date': 'Date',
            'amount': 'Amount',
            'payee': 'Description',
            'category': 'Category',
            'memo': 'Notes',
            'check_num': 'Check Number'
        }
    
    # Override with user-provided mapping if specified
    if args.mapping:
        try:
            # Try parsing as JSON string
            custom_mapping = json.loads(args.mapping)
        except json.JSONDecodeError:
            # Try reading as file
            try:
                with open(args.mapping, 'r') as f:
                    custom_mapping = json.load(f)
            except Exception as e:
                parser.error(f"Error reading mapping: {str(e)}")
        
        mapping.update(custom_mapping)
    
    try:
        with open(args.input_file, 'r') as f:
            # Try reading first line to validate CSV format
            header = f.readline().strip().split(',')
            if not all(field in header for field in mapping.values()):
                print(f"Error: CSV headers do not match mapping: {header}")
                exit(1)
        
        csv_to_qif(args.input_file, args.output_file, args.type, mapping)
        print(f"Successfully converted {args.input_file} to {args.output_file}")
    except Exception as e:
        print(f"Error converting file: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
