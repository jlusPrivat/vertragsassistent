from PySide6.QtWidgets import *
from PySide6 import QtCore
import datetime

from Data import *
from ContractDialog import ContractDialog


class MainWindow(QMainWindow):
    def __init__(self, file: str):
        super().__init__()
        self._contracts = []
        self.setWindowTitle(f"Vertragsassistenz ({file})")
        self.setFixedSize(600, 500)

        # initialize main widget
        root = QWidget(self)
        self.setCentralWidget(root)
        window_layout = QGridLayout(root)
        window_layout.setContentsMargins(10, 10, 10, 10)
        root.setLayout(window_layout)

        # add buttons on top
        btn_new_contract = QPushButton("Neuer Vertrag", self)
        window_layout.addWidget(btn_new_contract, 0, 0)
        btn_new_contract.clicked.connect(self.new_contract)
        btn_refresh = QPushButton("Neu laden", self)
        window_layout.addWidget(btn_refresh, 0, 1)
        btn_refresh.clicked.connect(self.refresh)

        # add list view for the contract tags
        group_contract_tags = QGroupBox("Vertrags Tags", self)
        window_layout.addWidget(group_contract_tags, 1, 0, 1, 0)
        group_contract_tags_layout = QVBoxLayout()
        group_contract_tags.setLayout(group_contract_tags_layout)
        self._contract_tags = QListWidget(self)
        group_contract_tags_layout.addWidget(self._contract_tags)

        # add table for contracts
        group_contracts = QGroupBox("Verträge", self)
        window_layout.addWidget(group_contracts, 2, 0, 1, 0)
        group_contracts_layout = QGridLayout()
        group_contracts.setLayout(group_contracts_layout)
        group_contracts_layout.addWidget(QLabel("Nur aktuell gültige Preise werden angezeigt"), 0, 0, 1, 0)

        self._table_contracts = QTableWidget()
        group_contracts_layout.addWidget(self._table_contracts, 1, 0, 1, 0)
        self._table_contracts.setColumnCount(4)
        self._table_contracts.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table_contracts.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table_contracts.cellDoubleClicked.connect(self.open_contract)
        self._table_contracts.setHorizontalHeaderLabels(["Bezeichnung", "Anbieter", "Preis / Monat", "Preis / Jahr"])
        for col in range(4):
            self._table_contracts.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)

        # add labels for the widget
        group_contracts_layout.addWidget(QLabel("Selektierter Preis / Monat:"), 2, 0)
        self._label_price_month = QLabel()
        group_contracts_layout.addWidget(self._label_price_month, 2, 1)
        group_contracts_layout.addWidget(QLabel("Selektierter Preis / Jahr:"), 3, 0)
        self._label_price_year = QLabel()
        group_contracts_layout.addWidget(self._label_price_year, 3, 1)

        self.refresh()

    @QtCore.Slot()
    def new_contract(self):
        if ContractDialog().exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    @QtCore.Slot()
    def open_contract(self, row: int, _: int):
        if ContractDialog(self._contracts[row]).exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    @QtCore.Slot()
    def refresh(self):
        self._table_contracts.clearContents()
        self._contracts.clear()
        query = ContractPricing.select(ContractPricing, Contract) \
            .join(Contract) \
            .where((ContractPricing.start_date <= datetime.date.today())
                   & ((ContractPricing.end_date is None) | (ContractPricing.end_date >= datetime.date.today())))
        for row, pricing in enumerate(query):
            self._table_contracts.setRowCount(row + 1)
            self._contracts.append(pricing.contract)
            price = pricing.price
            interval = pricing.payment_interval_days
            per_day = price / interval
            per_month = round(per_day * 30, 2)
            per_year = round(per_day * 365, 2)
            self._table_contracts.setItem(row, 0, QTableWidgetItem(pricing.contract.name))
            self._table_contracts.setItem(row, 1, QTableWidgetItem(pricing.contract.company))
            self._table_contracts.setItem(row, 2, QTableWidgetItem(str(per_month)))
            self._table_contracts.setItem(row, 3, QTableWidgetItem(str(per_year)))
