import decimal

from PySide6.QtWidgets import *
from PySide6 import QtCore, QtGui
from Data import *
from ContractDialog import ContractDialog
from TagListView import TagListView


class MainWindow(QMainWindow):
    def __init__(self, file: str):
        super().__init__()
        self._contracts = []
        self._tag_list = []
        self.setWindowTitle(f"Vertragsassistenz ({file})")
        self.setMinimumSize(500, 300)

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
        window_layout.addWidget(group_contract_tags, 1, 0, 1, 2)
        group_contract_tags_layout = QGridLayout()
        group_contract_tags.setLayout(group_contract_tags_layout)
        self._contract_tags = TagListView()
        self._contract_tags.setFixedHeight(70)
        self._contract_tags.selected_tags_changed.connect(self.apply_tag_filter)
        group_contract_tags_layout.addWidget(self._contract_tags, 0, 0, 1, 4)
        group_contract_tags_layout.setColumnStretch(3, 1)

        group_contract_tags_layout.addWidget(QLabel("Verknüpfen:"), 1, 0)
        self._radio_tag_sort_and = QRadioButton("UND", group_contract_tags)
        self._radio_tag_sort_and.setChecked(True)
        self._radio_tag_sort_and.clicked.connect(self.refresh)
        group_contract_tags_layout.addWidget(self._radio_tag_sort_and, 1, 1)
        self._radio_tag_sort_or = QRadioButton("ODER", group_contract_tags)
        self._radio_tag_sort_or.clicked.connect(self.refresh)
        group_contract_tags_layout.addWidget(self._radio_tag_sort_or, 1, 2)

        # add table for contracts
        group_contracts = QGroupBox("Verträge", self)
        window_layout.addWidget(group_contracts, 2, 0, 1, 2)
        window_layout.setRowStretch(2, 1)
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
        for col, val in enumerate([QHeaderView.ResizeMode.Interactive, QHeaderView.ResizeMode.Stretch,
                                   QHeaderView.ResizeMode.ResizeToContents, QHeaderView.ResizeMode.ResizeToContents]):
            self._table_contracts.horizontalHeader().setSectionResizeMode(col, val)
        self._table_contracts.setSortingEnabled(True)

        # add labels for the widget
        font_bold = self.font()
        font_bold.setBold(True)
        group_contracts_layout.addWidget(QLabel("Selektierter Preis / Monat:"), 2, 0)
        self._label_price_month = QLabel()
        self._label_price_month.setFont(font_bold)
        group_contracts_layout.addWidget(self._label_price_month, 2, 1)
        group_contracts_layout.addWidget(QLabel("Selektierter Preis / Jahr:"), 3, 0)
        self._label_price_year = QLabel()
        self._label_price_year.setFont(font_bold)
        group_contracts_layout.addWidget(self._label_price_year, 3, 1)

        self.refresh()

    @QtCore.Slot()
    def new_contract(self):
        ContractDialog().exec()
        self.refresh()

    @QtCore.Slot()
    def open_contract(self, row: int, _: int):
        ContractDialog(self._contracts[row]).exec()
        self.refresh()

    @QtCore.Slot(object)
    def apply_tag_filter(self, tag_list: list[ContractTag]):
        self._tag_list = tag_list
        self.refresh()

    @QtCore.Slot()
    def refresh(self):
        self._contract_tags.reload()
        self._table_contracts.clearContents()
        self._table_contracts.setRowCount(0)
        self._contracts.clear()

        query = Contract.select().order_by(Contract.name, Contract.company)
        total_price_month = decimal.Decimal(0)
        total_price_year = decimal.Decimal(0)
        if self._tag_list:
            if self._radio_tag_sort_or.isChecked():
                # select all items, where any tag is in the list of tags
                sel = any
            else:
                # select all items, where all selected tags match
                sel = all
            query = filter(lambda con: sel((sel_tag in con.tags) for sel_tag in self._tag_list), query)
        for row, contract in enumerate(query):
            today = datetime.date.today()
            active_pricing_query = ContractPricing.select()\
                .where((ContractPricing.contract == contract) & (ContractPricing.start_date <= today)
                       & ((ContractPricing.end_date >> None) | (ContractPricing.end_date >= today)))\
                .order_by(ContractPricing.start_date.desc()).limit(1)
            pricing = None if len(active_pricing_query) == 0 else active_pricing_query[0]

            self._table_contracts.setRowCount(row + 1)
            self._contracts.append(contract)
            price = 0 if pricing is None else pricing.price
            interval = 365 if pricing is None else pricing.payment_interval_days
            per_day = price / interval
            per_month = round(per_day * 30, 2)
            per_year = round(per_day * 365, 2)
            total_price_month += decimal.Decimal(per_month)
            total_price_year += decimal.Decimal(per_year)
            first_item = QTableWidgetItem(contract.name)
            if contract.reminder is not None and contract.reminder <= today:
                first_item.setData(QtCore.Qt.ItemDataRole.BackgroundRole, QtGui.QColor(180, 180, 255))
            self._table_contracts.setItem(row, 0, first_item)
            self._table_contracts.setItem(row, 1, QTableWidgetItem(contract.company))
            self._table_contracts.setItem(row, 2, QTableWidgetItem(str(per_month)))
            self._table_contracts.setItem(row, 3, QTableWidgetItem(str(per_year)))
        self._label_price_month.setText(f"{round(total_price_month, 2)} €")
        self._label_price_year.setText(f"{round(total_price_year, 2)} €")
