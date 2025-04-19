from PySide6.QtWidgets import *
from PySide6 import QtCore, QtGui
from Data import *


class TagListView(QListView):
    def __init__(self, contract: Contract | None = None, /):
        super().__init__()
        self._model = TagListModel(contract)
        self.setModel(self._model)
        self.setFixedHeight(50)
        self.setViewMode(QListView.ViewMode.IconMode)


class TagListModel(QtCore.QAbstractListModel):
    def __init__(self, contract: Contract | None = None, /):
        super().__init__()
        self._contract = contract
        self._tags = None
        self.reload()

    def reload(self):
        self._tags = ContractTag.select(ContractTag, fn.COUNT(ContractTagConnection.contract).alias('count'),
                                        ContractTagConnection.alias())\
            .join(ContractTagConnection, JOIN.LEFT_OUTER).group_by(ContractTag)\
            .order_by(ContractTag.name)
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
            return "..." if item is None else f"{item.name} ({item.count})"
        if role == QtCore.Qt.ItemDataRole.EditRole:
            return "" if item is None else item.name
        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            return None if item is None else QtCore.Qt.CheckState.Checked
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
                return False
            checked = value == QtCore.Qt.CheckState.Checked
            if self._contract is not None:
                pass
            self.dataChanged(index, index).emit()
            return True
        return False
