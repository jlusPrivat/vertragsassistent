from PySide6.QtWidgets import *
from PySide6 import QtCore, QtGui
import decimal
from Data import *
from TagListView import TagListView
import DocumentDialog
import subprocess
import platform


class ContractDialog(QDialog):
    def __init__(self, contract: Contract | None = None):
        super().__init__()
        self._contract = contract
        self._table_pricing_model = None
        self._table_docs_model = None
        self.setWindowTitle("Vertragsverwaltung")
        self.setMinimumSize(600, 500)

        # initialize layout
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        # input contract name
        layout.addWidget(QLabel("Vertragsname"), 0, 0)
        self._input_name = QLineEdit(self, placeholderText='Vertragsname',
                                     text='' if contract is None else contract.name)
        layout.addWidget(self._input_name, 0, 1)

        # input contractor
        layout.addWidget(QLabel("Vertragspartner"), 1, 0)
        self._input_company = QLineEdit(self, placeholderText='Vertragspartner',
                                        text='' if contract is None else contract.company)
        layout.addWidget(self._input_company, 1, 1)

        # input description
        layout.addWidget(QLabel("Notizen"), 2, 0)
        self._input_notes = QPlainTextEdit(self, plainText='' if contract is None else contract.notes)
        self._input_notes.setFixedHeight(50)
        layout.addWidget(self._input_notes, 2, 1)

        # input reminder
        layout.addWidget(QLabel("Erinnerung"), 3, 0)
        widget_reminder = QWidget()
        widget_reminder_layout = QHBoxLayout()
        widget_reminder_layout.setContentsMargins(0, 0, 0, 0)
        widget_reminder.setLayout(widget_reminder_layout)
        layout.addWidget(widget_reminder, 3, 1)

        check_input_reminder = QCheckBox()
        check_input_reminder.checkStateChanged.connect(
            lambda checked: self._input_reminder.setEnabled(checked == QtCore.Qt.CheckState.Checked))
        widget_reminder_layout.addWidget(check_input_reminder)
        self._input_reminder = QDateEdit(self)
        self._input_reminder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._input_reminder.setMinimumDate(QtCore.QDate.currentDate())
        if contract is not None and contract.reminder is not None:
            self._input_reminder.setDate(contract.reminder)
            check_input_reminder.setChecked(True)
        else:
            self._input_reminder.setEnabled(False)
            check_input_reminder.setChecked(False)
        widget_reminder_layout.addWidget(self._input_reminder)

        # save buttons
        widget_btns = QWidget()
        widget_btns_layout = QHBoxLayout()
        widget_btns.setLayout(widget_btns_layout)
        layout.addWidget(widget_btns, 4, 0, 1, 2)

        self._btn_delete = QPushButton("Löschen")
        self._btn_delete.clicked.connect(self.delete_contract)
        widget_btns_layout.addWidget(self._btn_delete)
        btn_accept = QPushButton("Speichern")
        btn_accept.setDefault(True)
        btn_accept.clicked.connect(self.save_contract)
        widget_btns_layout.addWidget(btn_accept)

        # tags
        self._group_tags = QGroupBox("Tags", self)
        layout_tags = QVBoxLayout(self)
        self._group_tags.setLayout(layout_tags)
        tag_list = TagListView(self._contract)
        layout_tags.addWidget(tag_list)
        layout.addWidget(self._group_tags, 5, 0, 1, 2)

        # pricing table
        self._group_pricing = QGroupBox("Preise", self)
        layout_pricing = QGridLayout(self)
        self._group_pricing.setLayout(layout_pricing)
        layout.addWidget(self._group_pricing, 6, 0, 1, 2)

        self._table_pricing = QTableView(self)
        self._table_pricing.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout_pricing.addWidget(self._table_pricing, 0, 0, 1, 2)

        btn_add_pricing = QPushButton("Neuer Preis")
        btn_add_pricing.clicked.connect(self.new_pricing)
        layout_pricing.addWidget(btn_add_pricing, 1, 0)
        btn_rem_pricing = QPushButton("Preis Löschen")
        btn_rem_pricing.clicked.connect(self.delete_pricing)
        layout_pricing.addWidget(btn_rem_pricing, 1, 1)

        # documents
        self._group_docs = QGroupBox("Dokumente", self)
        layout_docs = QGridLayout(self)
        self._group_docs.setLayout(layout_docs)
        layout.addWidget(self._group_docs, 7, 0, 1, 2)

        self._table_docs = QTableView(self)
        self._table_docs.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table_docs.doubleClicked.connect(self.open_doc)
        layout_docs.addWidget(self._table_docs, 0, 0, 1, 3)

        btn_add_doc = QPushButton("Neues Dokument")
        btn_add_doc.clicked.connect(self.new_doc)
        layout_docs.addWidget(btn_add_doc, 1, 0)
        btn_edit_doc = QPushButton("Dokument bearbeiten")
        btn_edit_doc.clicked.connect(self.edit_doc)
        layout_docs.addWidget(btn_edit_doc, 1, 1)
        btn_del_doc = QPushButton("Dokument Löschen")
        btn_del_doc.clicked.connect(self.delete_doc)
        layout_docs.addWidget(btn_del_doc, 1, 2)

        self.contract_changed()

    def contract_changed(self):
        enabled = self._contract is not None
        self._group_pricing.setEnabled(enabled)
        self._group_docs.setEnabled(enabled)
        self._btn_delete.setEnabled(enabled)
        if enabled:
            self._table_pricing_model = ContractModel(self._contract)
            self._table_pricing.setModel(self._table_pricing_model)
            for col in range(4):
                self._table_pricing.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
            self._table_docs_model = DocumentModel(self._contract)
            self._table_docs.setModel(self._table_docs_model)
            self._table_docs.horizontalHeader().setStretchLastSection(True)

    @QtCore.Slot()
    def save_contract(self):
        # create new contract, if it did not exist yet
        changed = False
        if self._contract is None:
            self._contract = Contract()
            changed = True

        self._contract.name = self._input_name.text()
        self._contract.company = self._input_company.text()
        self._contract.notes = self._input_notes.toPlainText()
        self._contract.reminder = None if not self._input_reminder.isEnabled()\
            else self._input_reminder.date().toPython()
        self._contract.save()
        if changed:
            self.contract_changed()

    @QtCore.Slot()
    def delete_contract(self):
        if QMessageBox.question(self, "Vertrag löschen", "Wirklich Vertrag löschen?")\
                != QMessageBox.StandardButton.Yes:
            return
        self._contract.delete_instance()
        self.accept()

    @QtCore.Slot()
    def new_pricing(self):
        # create new pricing and save it
        pricing = ContractPricing()
        pricing.contract = self._contract
        today = datetime.date.today()
        pricing.start_date = today
        pricing.end_date = None
        pricing.price = 10
        pricing.payment_interval_days = 365
        pricing.save()

        # inform the view about some change
        self._table_pricing_model.reload()

    @QtCore.Slot()
    def delete_pricing(self):
        idx = self._table_pricing.currentIndex()
        if not idx.isValid():
            return
        if QMessageBox.question(self, "Preis löschen", "Wirklich Preis löschen?")\
                != QMessageBox.StandardButton.Yes:
            return
        self._table_pricing_model.removeRow(idx.row())

    @QtCore.Slot()
    def new_doc(self):
        DocumentDialog.DocumentDialog(self._contract, None).exec()
        self._table_docs_model.reload()

    @QtCore.Slot()
    def edit_doc(self):
        idx = self._table_docs.currentIndex()
        if not idx.isValid():
            return
        doc = self._table_docs_model.get_row_item(idx.row())
        DocumentDialog.DocumentDialog(self._contract, doc).exec()
        self._table_docs_model.reload()

    @QtCore.Slot()
    def delete_doc(self):
        idx = self._table_docs.currentIndex()
        if not idx.isValid():
            return
        if QMessageBox.question(self, "Dokument löschen", "Wirklich die Referenz auf das Dokument löschen?")\
                != QMessageBox.StandardButton.Yes:
            return
        self._table_docs_model.removeRow(self._table_docs.currentIndex().row())

    @QtCore.Slot()
    def open_doc(self, idx: QtCore.QModelIndex):
        if not idx.isValid():
            return
        path = self._table_docs_model.get_row_item(idx.row()).absolute_file
        if platform.system() == 'Windows':
            subprocess.run(['start', path], shell=True)
        elif platform.system() == 'Darwin':
            subprocess.run(['open', path])
        else:
            subprocess.run(['xdg-open', path])


class ContractModel(QtCore.QAbstractTableModel):
    col_start = 0
    col_end = 1
    col_interval = 2
    col_price = 3

    def __init__(self, contract: Contract, **kwargs):
        super().__init__(**kwargs)
        self._pricings = None
        self._contract = contract
        self.reload()

    def reload(self):
        self._pricings = ContractPricing.select(ContractPricing)\
            .where(ContractPricing.contract == self._contract)\
            .order_by(ContractPricing.start_date)
        self.layoutChanged.emit()

    def columnCount(self, /, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex = ...):
        return 4

    def rowCount(self, /, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex = ...):
        return len(self._pricings)

    def flags(self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, /):
        return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsEditable\
               | QtCore.Qt.ItemFlag.ItemIsSelectable

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, /, role: int = ...):
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == QtCore.Qt.Orientation.Horizontal:
            if section == self.col_start:
                return "Start"
            if section == self.col_end:
                return "Ende"
            if section == self.col_interval:
                return "Abrechnungsintervall"
            if section == self.col_price:
                return "Preis / Intervall"
        else:
            return section + 1

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        item: ContractPricing = self._pricings[index.row()]
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if index.column() == self.col_start:
                return str(item.start_date)
            if index.column() == self.col_end:
                return "Keins" if item.end_date is None else str(item.end_date)
            if index.column() == self.col_interval:
                return f"{item.payment_interval_days} Tage"
            if index.column() == self.col_price:
                return f"{round(item.price, 2)} €"
        if role == QtCore.Qt.ItemDataRole.EditRole:
            if index.column() == self.col_start:
                return QtCore.QDate.fromString(str(item.start_date), 'yyyy-MM-dd')
            if index.column() == self.col_end:
                return str(item.end_date)
            if index.column() == self.col_interval:
                return item.payment_interval_days
            if index.column() == self.col_price:
                return round(item.price, 2)
        if role == QtCore.Qt.ItemDataRole.ForegroundRole and index.column() == self.col_start and index.row() > 0:
            prev: ContractPricing = self._pricings[index.row() - 1]
            if prev.end_date is None or (prev.end_date + datetime.timedelta(days=1)) != item.start_date:
                return QtGui.QColor(180, 0, 0)
        if role == QtCore.Qt.ItemDataRole.ForegroundRole and item.is_active:
            return QtGui.QColor(0, 180, 0)

    def setData(self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, value, /, role: int = ...) -> bool:
        item: ContractPricing = self._pricings[index.row()]
        if index.column() == self.col_start:
            item.start_date = value.toPython()
        if index.column() == self.col_end:
            date = QtCore.QDate.fromString(value, 'yyyy-MM-dd')
            item.end_date = date.toPython() if date.isValid() else None
        if index.column() == self.col_interval:
            item.payment_interval_days = value
        if index.column() == self.col_price:
            item.price = decimal.Decimal(value)
        item.save()

        # inform about changes
        self.layoutChanged.emit()
        return True

    def removeRow(self, row: int, /, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex = ...) -> bool:
        self._pricings[row].delete_instance()
        self.reload()
        return True


class DocumentModel(QtCore.QAbstractTableModel):
    col_date = 0
    col_description = 1

    def __init__(self, contract: Contract, **kwargs):
        super().__init__(**kwargs)
        self._docs = None
        self._contract = contract
        self.reload()

    def reload(self):
        self._docs = ContractDocument.select(ContractDocument)\
            .where(ContractDocument.contract == self._contract)\
            .order_by(ContractDocument.date)
        self.layoutChanged.emit()

    def get_row_item(self, row: int) -> ContractDocument:
        return self._docs[row]

    def columnCount(self, /, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex = ...):
        return 2

    def rowCount(self, /, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex = ...):
        return len(self._docs)

    def flags(self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, /):
        return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, /, role: int = ...):
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == QtCore.Qt.Orientation.Horizontal:
            if section == self.col_date:
                return "Datum"
            if section == self.col_description:
                return "Bezeichnung"
        else:
            return section + 1

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        item: ContractDocument = self._docs[index.row()]
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if index.column() == self.col_date:
                return str(item.date)
            if index.column() == self.col_description:
                return item.description
        if role == QtCore.Qt.ItemDataRole.ForegroundRole:
            if not item.file_exists:
                return QtGui.QColor(180, 0, 0)

    def removeRow(self, row: int, /, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex = ...) -> bool:
        self._docs[row].delete_instance()
        self.reload()
        return True
