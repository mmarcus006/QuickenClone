import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QComboBox, QPushButton, 
                           QFileDialog, QMessageBox, QLineEdit)
from PyQt6.QtCore import Qt
from qif_converter import csv_to_qif

class QIFConverterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV to QIF Converter")
        self.setMinimumWidth(600)
        
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
