import sys
from PySide6 import QtCore, QtWidgets
from Data import *
import MainWindow


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    filename = ' '.join(sys.argv[1:])
    if not QtCore.QFileInfo.exists(filename):
        # no parameter given, therefore ask for path
        filename = QtWidgets.QFileDialog.getSaveFileName(caption="Wähle eine neue Datei oder die zu öffnende Datei",
                                                         options=QtWidgets.QFileDialog.Option.DontConfirmOverwrite)[0]
    if len(filename) == 0:
        # no file given, therefore close
        sys.exit(0)

    if not QtCore.QFileInfo.exists(filename):
        if QtWidgets.QMessageBox.question(QtWidgets.QWidget(),
                                          "Neue Datei", "Soll die Datenbank neu erstellt werden?")\
                != QtWidgets.QMessageBox.StandardButton.Yes:
            sys.exit(0)
        db.init(filename)
        create_tables()
    else:
        db.init(filename)

    main_window = MainWindow.MainWindow(filename)
    main_window.show()
    ret = app.exec()
    db.close()
    sys.exit(ret)
