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
    
    def update_mapping_fields(self):
        # Clear existing mapping widgets
        for widget in self.mapping_widgets.values():
            widget.setParent(None)
        self.mapping_widgets.clear()
        
        # Define fields based on transaction type
        if self.type_combo.currentText() == "Investment":
            fields = {
                'date': 'Trade Date',
                'action': 'Transaction Type',
                'security': 'Symbol',
                'price': 'Price',
                'quantity': 'Quantity',
                'commission': 'Commission',
                'memo': 'Notes'
            }
        else:
            fields = {
                'date': 'Date',
                'amount': 'Amount',
                'payee': 'Description',
                'category': 'Category',
                'memo': 'Notes',
                'check_num': 'Check Number'
            }
        
        # Create mapping widgets
        for qif_field, default_value in fields.items():
            layout = QHBoxLayout()
            label = QLabel(f"{qif_field}:")
            input_field = QLineEdit(default_value)
            layout.addWidget(label)
            layout.addWidget(input_field)
            self.mapping_widgets[qif_field] = input_field
            self.mapping_layout.addLayout(layout)
    
    def browse_input(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv);;All Files (*.*)")
        if filename:
            self.input_file.setText(filename)
    
    def convert_file(self):
        if not self.input_file.text():
            QMessageBox.warning(self, "Error", "Please select an input file.")
            return
        
        output_file, _ = QFileDialog.getSaveFileName(
            self, "Save QIF File", "", "QIF Files (*.qif);;All Files (*.*)")
        if not output_file:
            return
        
        try:
            # Get mapping from widgets
            mapping = {field: widget.text() 
                      for field, widget in self.mapping_widgets.items()}
            
            # Convert file
            transaction_type = self.type_combo.currentText().lower()
            csv_to_qif(self.input_file.text(), output_file, 
                      transaction_type, mapping)
            
            QMessageBox.information(
                self, "Success", 
                f"File converted successfully and saved to:\n{output_file}")
        except Exception as e:
            QMessageBox.critical(
                self, "Error", 
                f"Error converting file:\n{str(e)}")

def main():
    app = QApplication(sys.argv)
    window = QIFConverterGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
