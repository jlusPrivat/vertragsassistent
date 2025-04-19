from PySide6.QtWidgets import *
from PySide6 import QtCore
import datetime
import decimal
from Data import *


class ContractDialog(QDialog):
    def __init__(self, contract: Contract | None = None):
        super().__init__()
        self.setWindowTitle("Vertragsverwaltung")
        self.setFixedSize(600, 500)
        self._contract = contract

        # initialize layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        # input contract name
        self._input_name = QLineEdit(self, placeholderText='Vertragsname',
                                     text='' if contract is None else contract.name)
        layout.addWidget(self._input_name)

        # input contractor
        self._input_company = QLineEdit(self, placeholderText='Vertragspartner',
                                        text='' if contract is None else contract.company)
        layout.addWidget(self._input_company)

        # pricing table
        group_pricing = QGroupBox("Preise", self)
        layout_pricing = QGridLayout(self)
        group_pricing.setLayout(layout_pricing)
        layout.addWidget(group_pricing)

        self._table_pricing = QTableWidget(self)
        self._table_pricing.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table_pricing.setColumnCount(4)
        self._table_pricing.setHorizontalHeaderLabels(["Start", "Ende", "Interval (Tage)", "Preis"])
        for col in range(4):
            self._table_pricing.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        layout_pricing.addWidget(self._table_pricing, 0, 0, 1, 2)

        btn_add_pricing = QPushButton("Neuer Preis")
        btn_add_pricing.clicked.connect(self.new_pricing)
        layout_pricing.addWidget(btn_add_pricing, 1, 0)
        btn_rem_pricing = QPushButton("Preis Löschen")
        btn_rem_pricing.clicked.connect(self.delete_pricing)
        layout_pricing.addWidget(btn_rem_pricing, 1, 1)

        # end buttons
        widget_btns = QWidget()
        widget_btns_layout = QHBoxLayout()
        widget_btns.setLayout(widget_btns_layout)
        layout.addWidget(widget_btns)
        widget_btns_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        btn_abort = QPushButton("Abbrechen")
        btn_abort.clicked.connect(self.reject)
        widget_btns_layout.addWidget(btn_abort)
        btn_accept = QPushButton("Speichern")
        btn_accept.clicked.connect(self.accept)
        widget_btns_layout.addWidget(btn_accept)

        # reload pricings
        if self._contract is None:
            self.new_pricing()
            return
        query = ContractPricing.select(ContractPricing)\
            .where(ContractPricing.contract == self._contract)
        for pricing in query:
            self.insert_pricing(pricing.start_date, pricing.end_date, pricing.payment_interval_days, pricing.price)

    def insert_pricing(self, start: datetime.date, end: datetime.date, interval: int, price: decimal):
        flags = QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsEditable\
                | QtCore.Qt.ItemFlag.ItemIsSelectable
        self._table_pricing.insertRow(0)

        item_start = QTableWidgetItem(str(start))
        item_start.setFlags(flags)
        self._table_pricing.setItem(0, 0, item_start)

        item_end = QTableWidgetItem(str(end))
        item_end.setFlags(flags)
        self._table_pricing.setItem(0, 1, item_end)

        item_interval = QTableWidgetItem(str(interval))
        item_interval.setFlags(flags)
        self._table_pricing.setItem(0, 2, item_interval)

        item_price = QTableWidgetItem(str(price))
        item_price.setFlags(flags)
        self._table_pricing.setItem(0, 3, item_price)

    @QtCore.Slot()
    def new_pricing(self):
        self.insert_pricing(datetime.date.today(), datetime.date.today().replace(year=datetime.date.today().year+1),
                            365, 10.00)

    @QtCore.Slot()
    def delete_pricing(self):
        self._table_pricing.removeRow(self._table_pricing.currentRow())

    @QtCore.Slot()
    def accept(self):
        # create new contract, if it did not exist yet
        if self._contract is None:
            self._contract = Contract()

        self._contract.name = self._input_name.text()
        self._contract.company = self._input_company.text()
        self._contract.save()

        # delete previous dates and set new ones
        ContractPricing.delete().where(ContractPricing.contract == self._contract).execute()
        for row in range(self._table_pricing.rowCount()):
            pricing = ContractPricing()
            pricing.contract = self._contract
            pricing.start_date = datetime.date.fromisoformat(self._table_pricing.item(row, 0).text())
            pricing.end_date = datetime.date.fromisoformat(self._table_pricing.item(row, 1).text())
            pricing.payment_interval_days = int(self._table_pricing.item(row, 2).text())
            pricing.price = decimal.Decimal(self._table_pricing.item(row, 3).text())
            pricing.save()

        super().accept()
