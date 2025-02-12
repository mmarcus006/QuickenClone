import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QComboBox, QPushButton, 
                           QFileDialog, QMessageBox, QLineEdit, QDialog,
                           QDialogButtonBox, QListWidget, QGroupBox, QGridLayout)
from qif_converter import QIFType, InvestmentAction
from PyQt6.QtCore import Qt
from qif_converter import csv_to_qif

class TransactionDialog(QDialog):
    def __init__(self, parent=None, transaction_data=None):
        super().__init__(parent)
        self.setWindowTitle("Transaction Details")
        self.setMinimumWidth(500)
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
            ('memo', 'Memo:', 6)
        ]
        
        for field, label, row in field_defs:
            label_widget = QLabel(label)
            self.fields[field] = QLineEdit()
            self.fields_layout.addWidget(label_widget, row, 0)
            self.fields_layout.addWidget(self.fields[field], row, 1)
    
    def update_fields(self, action_type):
        """Show/hide fields based on transaction type"""
        # Default visible fields
        visible_fields = {'date', 'memo'}
        
        # Add fields based on action type
        if action_type in [InvestmentAction.BUY.value, InvestmentAction.SELL.value]:
            visible_fields.update({'security', 'price', 'quantity', 'commission', 'amount'})
        
        elif action_type in [InvestmentAction.DIV.value, InvestmentAction.INTINC.value,
                           InvestmentAction.CGLONG.value, InvestmentAction.CGSHORT.value]:
            visible_fields.update({'security', 'amount'})
        
        elif action_type == InvestmentAction.REINVDIV.value:
            visible_fields.update({'security', 'price', 'quantity', 'amount'})
        
        elif action_type in [InvestmentAction.SHRSIN.value, InvestmentAction.SHRSOUT.value]:
            visible_fields.update({'security', 'quantity', 'price'})
        
        elif action_type == InvestmentAction.STKSPLIT.value:
            visible_fields.update({'security', 'quantity'})
        
        # Show/hide fields
        for field, widget in self.fields.items():
            widget.setVisible(field in visible_fields)
            self.fields_layout.itemAtPosition(
                list(self.fields.keys()).index(field), 0
            ).widget().setVisible(field in visible_fields)
    
    def get_data(self):
        """Get the transaction data"""
        data = {
            'action': self.type_combo.currentText(),
            'date': self.fields['date'].text()
        }
        
        # Add other fields if they're visible and not empty
        for field, widget in self.fields.items():
            if widget.isVisible() and widget.text():
                if field in ['price', 'quantity', 'commission', 'amount']:
                    try:
                        data[field] = float(widget.text())
                    except ValueError:
                        pass
                else:
                    data[field] = widget.text()
        
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
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Transaction type selection
        type_layout = QHBoxLayout()
        type_label = QLabel("Transaction Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Investment", "Cash"])
        self.type_combo.currentTextChanged.connect(self.update_mapping_fields)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # File selection
        file_layout = QHBoxLayout()
        self.input_file = QLineEdit()
        self.input_file.setPlaceholderText("Select input CSV file...")
        self.input_file.setReadOnly(True)
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_input)
        file_layout.addWidget(self.input_file)
        file_layout.addWidget(browse_button)
        layout.addLayout(file_layout)
        
        # Field mapping section
        mapping_label = QLabel("Field Mapping:")
        layout.addWidget(mapping_label)
        
        self.mapping_widgets = {}
        self.mapping_layout = QVBoxLayout()
        layout.addLayout(self.mapping_layout)
        
        # Convert button
        convert_button = QPushButton("Convert to QIF")
        convert_button.clicked.connect(self.convert_file)
        layout.addWidget(convert_button)
        
        # Initialize mapping fields
        self.update_mapping_fields()
    
    def add_transaction(self):
        dialog = TransactionDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.transactions.append(data)
            self.update_transaction_list()
    
    def edit_transaction(self, item):
        idx = self.transaction_list.row(item)
        dialog = TransactionDialog(self, self.transactions[idx])
        if dialog.exec():
            self.transactions[idx] = dialog.get_data()
            self.update_transaction_list()
    
    def duplicate_transaction(self):
        if not self.transaction_list.currentItem():
            return
        idx = self.transaction_list.currentRow()
        data = self.transactions[idx].copy()
        dialog = TransactionDialog(self, data)
        if dialog.exec():
            self.transactions.append(dialog.get_data())
            self.update_transaction_list()
    
    def delete_transaction(self):
        if not self.transaction_list.currentItem():
            return
        idx = self.transaction_list.currentRow()
        self.transactions.pop(idx)
        self.update_transaction_list()
    
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
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import CSV File", "", "CSV Files (*.csv);;All Files (*.*)")
        if not filename:
            return
            
        try:
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.transactions.append({
                        'action': row['Transaction Type'],
                        'date': row['Trade Date'],
                        'security': row.get('Symbol', ''),
                        'price': float(row['Price']) if row.get('Price') else None,
                        'quantity': float(row['Quantity']) if row.get('Quantity') else None,
                        'commission': float(row['Commission']) if row.get('Commission') else None,
                        'memo': row.get('Notes', '')
                    })
            self.update_transaction_list()
            QMessageBox.information(self, "Success", "CSV file imported successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error importing CSV: {str(e)}")
    
    def export_qif(self):
        if not self.transactions:
            QMessageBox.warning(self, "Error", "No transactions to export")
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export QIF File", "", "QIF Files (*.qif);;All Files (*.*)")
        if not filename:
            return
            
        try:
            with open(filename, 'w') as f:
                f.write(f"{QIFType.INVESTMENT.value}\n")
                for trans in self.transactions:
                    f.write(f"D{trans['date']}\n")
                    f.write(f"N{trans['action']}\n")
                    if trans.get('security'):
                        f.write(f"Y{trans['security']}\n")
                    if trans.get('price'):
                        f.write(f"I{trans['price']:.4f}\n")
                    if trans.get('quantity'):
                        f.write(f"Q{trans['quantity']:.4f}\n")
                    if trans.get('commission'):
                        f.write(f"O{trans['commission']:.2f}\n")
                    if trans.get('amount'):
                        f.write(f"T{trans['amount']:.2f}\n")
                    if trans.get('memo'):
                        f.write(f"M{trans['memo']}\n")
                    f.write("^\n")
            QMessageBox.information(self, "Success", "Transactions exported to QIF successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error exporting to QIF: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = QIFConverterGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
