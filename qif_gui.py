import sys
import os
import csv
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QComboBox, QPushButton, 
                           QFileDialog, QMessageBox, QLineEdit, QDialog,
                           QDialogButtonBox, QListWidget, QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt
from qif_converter import QIFType, InvestmentAction, csv_to_qif

class TransactionDialog(QDialog):
    def __init__(self, parent=None, transaction_data=None):
        super().__init__(parent)
        self.setWindowTitle("Transaction Details")
        self.setMinimumWidth(500)
        self.exec_result = True
        layout = QVBoxLayout(self)
        
        # Transaction type selection
        type_group = QGroupBox("Transaction Type")
        type_layout = QVBoxLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems([action.value for action in InvestmentAction])
        self.type_combo.currentTextChanged.connect(self.update_fields)
        type_layout.addWidget(self.type_combo)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Fields group
        fields_group = QGroupBox("Transaction Details")
        self.fields_layout = QGridLayout()
        fields_group.setLayout(self.fields_layout)
        layout.addWidget(fields_group)
        
        # Create all possible fields
        self.create_fields()
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Fill data if editing
        if transaction_data:
            self.type_combo.setCurrentText(transaction_data['action'])
            for field, value in transaction_data.items():
                if field in self.fields and value is not None:
                    self.fields[field].setText(str(value))
        
        self.update_fields(self.type_combo.currentText())
    
    def create_fields(self):
        """Create all possible fields"""
        self.fields = {}
        field_defs = [
            ('date', 'Date (MM/DD/YYYY):', 0),
            ('security', 'Security/Symbol:', 1),
            ('price', 'Price:', 2),
            ('quantity', 'Quantity:', 3),
            ('commission', 'Commission:', 4),
            ('amount', 'Amount:', 5),
            ('account', 'Transfer Account:', 6),
            ('memo', 'Memo:', 7)
        ]
        
        for field, label, row in field_defs:
            label_widget = QLabel(label)
            self.fields[field] = QLineEdit()
            self.fields_layout.addWidget(label_widget, row, 0)
            self.fields_layout.addWidget(self.fields[field], row, 1)
    
    def update_fields(self, action_type):
        """Show/hide fields based on transaction type"""
        # Default visible fields
        visible_fields = {'date', 'security', 'memo'}  # Always visible
        
        # Add fields based on action type
        if action_type in [InvestmentAction.BUY.value, InvestmentAction.SELL.value]:
            visible_fields.update({'price', 'quantity', 'commission', 'amount'})
        
        elif action_type in [InvestmentAction.BUYX.value, InvestmentAction.SELLX.value]:
            visible_fields.update({'price', 'quantity', 'account', 'amount'})
        
        elif action_type in [InvestmentAction.DIV.value, InvestmentAction.INTINC.value,
                           InvestmentAction.CGLONG.value, InvestmentAction.CGSHORT.value]:
            visible_fields.add('amount')
        
        elif action_type == InvestmentAction.REINVDIV.value:
            visible_fields.update({'price', 'quantity', 'amount'})
        
        elif action_type in [InvestmentAction.SHRSIN.value, InvestmentAction.SHRSOUT.value]:
            visible_fields.update({'quantity', 'price', 'account'})
        
        elif action_type == InvestmentAction.STKSPLIT.value:
            visible_fields.add('quantity')
        
        elif action_type in [InvestmentAction.MARGINT.value, InvestmentAction.MISCINC.value,
                           InvestmentAction.MISCEXP.value]:
            visible_fields.add('amount')
        
        # Show/hide fields
        for field, widget in self.fields.items():
            widget.setVisible(field in visible_fields)
            label = self.fields_layout.itemAtPosition(
                list(self.fields.keys()).index(field), 0
            ).widget()
            label.setVisible(field in visible_fields)
            
        # Update type_combo visible fields for mock testing
        if hasattr(self.type_combo, '_visible_fields'):
            self.type_combo._visible_fields = visible_fields
    
    def get_data(self):
        """Get the transaction data"""
        data = {}
        
        # Get required fields
        data['action'] = self.type_combo.currentText()
        data['date'] = self.fields['date'].text().strip()
        data['security'] = self.fields['security'].text().strip()
        
        # Add other fields if they're not empty
        for field, widget in self.fields.items():
            if field not in ('date', 'security', 'action'):  # Already added
                text = widget.text().strip()
                if text:  # Only add non-empty fields
                    if field in ('price', 'quantity', 'commission', 'amount'):
                        try:
                            data[field] = float(text)
                        except ValueError:
                            continue  # Skip invalid numeric fields
                    else:
                        data[field] = text
        
        # Validate required fields
        if not all(k in data and data[k] and str(data[k]).strip() for k in ['date', 'action', 'security']):
            return None
            
        return data

class QIFConverterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV to QIF Converter")
        self.setMinimumWidth(800)
        self.transactions = []
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Transaction list
        list_group = QGroupBox("Transactions")
        list_layout = QVBoxLayout()
        
        self.transaction_list = QListWidget()
        self.transaction_list.itemDoubleClicked.connect(self.edit_transaction)
        list_layout.addWidget(self.transaction_list)
        
        # Transaction buttons
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("Add Transaction")
        add_button.clicked.connect(self.add_transaction)
        
        duplicate_button = QPushButton("Duplicate Selected")
        duplicate_button.clicked.connect(self.duplicate_transaction)
        duplicate_button.setToolTip("Create a copy of the selected transaction")
        
        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self.delete_transaction)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(duplicate_button)
        button_layout.addWidget(delete_button)
        list_layout.addLayout(button_layout)
        
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        # Import/Export buttons
        convert_layout = QHBoxLayout()
        
        import_button = QPushButton("Import from CSV")
        import_button.clicked.connect(self.import_csv)
        
        export_button = QPushButton("Export to QIF")
        export_button.clicked.connect(self.export_qif)
        
        convert_layout.addWidget(import_button)
        convert_layout.addWidget(export_button)
        layout.addLayout(convert_layout)
        
        # Initialize mapping fields
        self.mapping = {}
    
    def add_transaction(self):
        """Add a new transaction"""
        dialog = TransactionDialog(self)
        if dialog.exec():  # Dialog accepted
            data = dialog.get_data()
            if data and all(data.get(field) for field in ['action', 'date', 'security']):  # Valid data
                self.transactions.append(data.copy())  # Make a copy to be safe
                self.update_transaction_list()
                return True
        return False
    
    def edit_transaction(self, item):
        """Edit an existing transaction"""
        try:
            if isinstance(item, int):
                idx = item
            else:
                idx = self.transaction_list.row(item)
            if idx < 0 or idx >= len(self.transactions):
                QMessageBox.warning(self, "Error", "Invalid transaction index")
                return False
            dialog = TransactionDialog(self, self.transactions[idx])
            # Run dialog and validate
            if not dialog.exec():  # Dialog cancelled
                return False
            # Get data after successful dialog
            data = dialog.get_data()
            if not data:  # Double check data validity
                QMessageBox.warning(self, "Error", "Invalid transaction data")
                return False
            # Update transaction
            self.transactions[idx] = data
            self.update_transaction_list()
            return True  # Return True for successful update
        except (AttributeError, TypeError, ValueError) as e:
            QMessageBox.critical(self, "Error", f"Failed to edit transaction: {str(e)}")
            return False
    
    def duplicate_transaction(self):
        """Duplicate selected transaction"""
        if not self.transaction_list.currentItem():
            QMessageBox.warning(self, "Error", "Please select a transaction to duplicate")
            return False
            
        idx = self.transaction_list.currentRow()
        if idx < 0 or idx >= len(self.transactions):
            return False
            
        data = self.transactions[idx].copy()
        dialog = TransactionDialog(self, data)
        if dialog.exec():  # Dialog accepted
            new_data = dialog.get_data()
            if new_data and all(new_data.get(field) for field in ['action', 'date', 'security']):  # Valid data
                self.transactions.append(new_data.copy())  # Make a copy to be safe
                self.update_transaction_list()
                return True
        return False
    
    def delete_transaction(self):
        """Delete the selected transaction"""
        idx = self.transaction_list.currentRow()
        if idx >= 0 and idx < len(self.transactions):
            self.transactions.pop(idx)
            self.transaction_list.clear()
            self.update_transaction_list()
            self.transaction_list.setCurrentRow(-1)
    
    def update_transaction_list(self):
        self.transaction_list.clear()
        for trans in self.transactions:
            item_text = f"{trans['date']} - {trans['action']}"
            if trans.get('security'):
                item_text += f" - {trans['security']}"
            if trans.get('quantity'):
                item_text += f" - {trans['quantity']} shares"
            if trans.get('amount'):
                item_text += f" - ${trans['amount']:.2f}"
            self.transaction_list.addItem(item_text)
    
    def import_csv(self):
        """Import transactions from CSV file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import CSV File", "", "CSV Files (*.csv);;All Files (*.*)")
        if not filename or not filename.strip():
            return False
            
        try:
            # Read CSV file
            with open(filename, 'r') as f:
                # Parse CSV
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    QMessageBox.warning(self, "Error", "Empty CSV file")
                    return False
                    
                # Validate header
                required_fields = ['Transaction Type', 'Trade Date', 'Symbol']
                if not all(field in reader.fieldnames for field in required_fields):
                    QMessageBox.warning(self, "Error", "Invalid CSV format")
                    return False
                
                # Process rows
                valid_rows = []
                for row in reader:
                    try:
                        # Required fields must be present and non-empty
                        if not all(row.get(field, '').strip() for field in required_fields):
                            QMessageBox.warning(self, "Warning", "Skipping row with missing required fields")
                            continue
                            
                        # Create transaction with required fields
                        trans = {
                            'action': row['Transaction Type'].strip(),
                            'date': row['Trade Date'].strip(),
                            'security': row['Symbol'].strip()
                        }
                        
                        # Add optional numeric fields
                        if 'Price' in row and row['Price'].strip():
                            trans['price'] = float(row['Price'])
                        if 'Quantity' in row and row['Quantity'].strip():
                            trans['quantity'] = float(row['Quantity'])
                        if 'Commission' in row and row['Commission'].strip():
                            trans['commission'] = float(row['Commission'])
                        if 'Notes' in row and row['Notes'].strip():
                            trans['memo'] = row['Notes'].strip()
                            
                        valid_rows.append(trans)
                    except (ValueError, KeyError) as e:
                        QMessageBox.warning(self, "Warning", 
                            f"Skipping invalid row: {str(e)}")
                        continue
                
                # Update transactions and UI if we have valid rows
                if valid_rows:
                    self.transactions.extend(valid_rows)
                    self.update_transaction_list()
                    return True
                
                QMessageBox.warning(self, "Error", "No valid transactions found in CSV")
                return False
                    
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", "File not found")
            return False
        except csv.Error as e:
            QMessageBox.critical(self, "Error", f"Invalid CSV format: {str(e)}")
            return False
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error importing CSV: {str(e)}")
            return False
    
    def export_qif(self):
        """Export transactions to QIF file"""
        if not self.transactions:
            QMessageBox.warning(self, "Warning", "No transactions to export")
            return False
            
        # Get filename
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export QIF File", "", "QIF Files (*.qif);;All Files (*.*)")
        if not filename or not filename.strip():
            return False
            
        # Ensure .qif extension
        if not filename.lower().endswith('.qif'):
            filename += '.qif'
            
        # Validate transactions before writing
        valid_transactions = []
        for trans in self.transactions:
            if all(trans.get(field) and str(trans[field]).strip() 
                  for field in ['date', 'action', 'security']):
                valid_transactions.append(trans)
            else:
                QMessageBox.warning(self, "Warning", "Skipping transaction with missing required fields")
        
        if not valid_transactions:
            QMessageBox.warning(self, "Error", "No valid transactions to export")
            return False
            
        try:
            # Write transactions
            with open(filename, 'w') as f:
                # Write header
                f.write('!Type:Invst\n')
                
                # Write transactions
                for trans in valid_transactions:
                    # Write required fields
                    f.write(f'D{trans["date"]}\n')
                    f.write(f'N{trans["action"]}\n')
                    f.write(f'Y{trans["security"]}\n')
                    
                    # Optional numeric fields
                    if 'price' in trans and trans['price'] is not None:
                        f.write(f'I{float(trans["price"]):.4f}\n')
                    if 'quantity' in trans and trans['quantity'] is not None:
                        f.write(f'Q{float(trans["quantity"]):.4f}\n')
                    if 'commission' in trans and trans['commission'] is not None:
                        f.write(f'O{float(trans["commission"]):.2f}\n')
                    if 'memo' in trans and trans['memo']:
                        f.write(f'M{trans["memo"]}\n')
                    f.write('^\n')
            return True
        except (IOError, OSError) as e:
            QMessageBox.critical(self, "Error", f"Failed to write file: {str(e)}")
            return False


def main():
    """Main entry point"""
    try:
        app = QApplication(sys.argv)
        window = QIFConverterGUI()
        window.show()
        return app.exec()
    except Exception:
        return 1

if __name__ == "__main__":
    sys.exit(main())
