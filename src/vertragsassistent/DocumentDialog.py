from PySide6.QtWidgets import *
from PySide6 import QtCore
from Data import *


class DocumentDialog(QDialog):
    def __init__(self, contract: Contract, document: ContractDocument | None, /):
        super().__init__()
        self._contract = contract
        self._document = document
        self.setWindowTitle("Dokument verwalten")
        self.setMinimumSize(300, 200)
        layout = QGridLayout(self)
        self.setLayout(layout)

        # add description
        layout.addWidget(QLabel("Title: "), 0, 0)
        self._input_description = QLineEdit(text="" if document is None else document.description)
        layout.addWidget(self._input_description, 0, 1, 1, 2)

        # add date
        layout.addWidget(QLabel("Datum: "), 1, 0)
        self._input_date = QDateEdit(date=datetime.date.today() if document is None else document.date)
        layout.addWidget(self._input_date, 1, 1, 1, 2)

        # add path
        layout.addWidget(QLabel("Pfad: "), 2, 0)
        self._input_path = QLineEdit(text="" if document is None else document.file)
        layout.addWidget(self._input_path, 2, 1)
        btn_select_path = QPushButton("...")
        btn_select_path.clicked.connect(self.path_selector)
        layout.addWidget(btn_select_path, 2, 2)

        # add final button
        btn_save = QPushButton("Speichern")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self.accept)
        layout.addWidget(btn_save, 3, 0, 1, 3)

    @QtCore.Slot()
    def path_selector(self):
        basedir = os.path.dirname(db.database)
        f = QFileDialog.getOpenFileName(self, "Dokument auswählen", basedir)[0]
        if len(f) == 0 or not os.path.isfile(f):
            return
        f = os.path.relpath(f, basedir).replace('\\', '/')
        self._input_path.setText(f)

    @QtCore.Slot()
    def accept(self):
        if self._document is None:
            self._document = ContractDocument()
        self._document.contract = self._contract
        self._document.description = self._input_description.text()
        self._document.date = self._input_date.date().toPython()
        self._document.file = self._input_path.text()
        self._document.save()
        super().accept()
