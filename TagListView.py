from PySide6.QtWidgets import *
from PySide6 import QtCore, QtGui
from Data import *


class TagListView(QListView):
    selected_tags_changed = QtCore.Signal(object)

    def __init__(self, contract: Contract | None = None, /):
        super().__init__()
        self.set_contract(contract)
        self.setFixedHeight(50)
        self.setViewMode(QListView.ViewMode.IconMode)
        self._model.selected_tags_changed.connect(self.selected_tags_changed)

    def reload(self):
        self._model.reload()

    def set_contract(self, contract: Contract | None):
        self._model = TagListModel(contract)
        self.setModel(self._model)


class TagListModel(QtCore.QAbstractListModel):
    selected_tags_changed = QtCore.Signal(object)

    def __init__(self, contract: Contract | None = None, /):
        super().__init__()
        self._contract = contract
        self._tags = None
        self._selected_tags = []
        self.reload()

    def reload(self):
        self._tags = ContractTag.select().order_by(ContractTag.name)
        self.layoutChanged.emit()

    def rowCount(self, /, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex = ...) -> int:
        return len(self._tags) + 1

    def flags(self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, /) -> QtCore.Qt.ItemFlag:
        base = QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsEditable
        if len(self._tags) > index.row():
            return base | QtCore.Qt.ItemFlag.ItemIsUserCheckable
        return base

    def data(self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
             role: int = QtCore.Qt.ItemDataRole.DisplayRole):
        item = self._tags[index.row()] if len(self._tags) > index.row() else None
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return "..." if item is None else f"{item.name} ({len(item.contracts)})"
        if role == QtCore.Qt.ItemDataRole.EditRole:
            return "" if item is None else item.name
        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            if item is None:
                return None
            if self._contract is not None:
                in_db = self._contract in item.contracts
                return QtCore.Qt.CheckState.Checked if in_db else QtCore.Qt.CheckState.Unchecked
            else:
                in_list = item in self._selected_tags
                return QtCore.Qt.CheckState.Checked if in_list else QtCore.Qt.CheckState.Unchecked
        if role == QtCore.Qt.ItemDataRole.ForegroundRole and item is None:
            return QtGui.QColor(180, 0, 0)

    def setData(self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, value, /, role: int = ...) -> bool:
        item = self._tags[index.row()] if len(self._tags) > index.row() else None
        if role == QtCore.Qt.ItemDataRole.EditRole:
            if item is None:
                item = ContractTag()
            item.name = value
            item.save()
            self.reload()
            return True
        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            if item is None:
                # no item was used
                return False

            # check for database change and change it
            checked = (value == QtCore.Qt.CheckState.Checked.value)
            if self._contract is not None:
                # update database, if not already in there
                in_db = self._contract in item.contracts
                if in_db == checked:
                    return False
                if in_db:
                    item.contracts.remove(self._contract)
                else:
                    item.contracts.add(self._contract)
            else:
                in_list = item in self._selected_tags
                if in_list == checked:
                    return False
                if in_list:
                    self._selected_tags.remove(item)
                else:
                    self._selected_tags.append(item)
                self.selected_tags_changed.emit(self._selected_tags)
            self.dataChanged.emit(index, index)
            return True
        return False
