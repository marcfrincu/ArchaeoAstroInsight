from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import os.path

#Set parameters GUI
FORM_CLASS1, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),'dialog.ui'))
class Ui_Dialog(QtWidgets.QDialog, FORM_CLASS1):
    def __init__(self, path, parent=None):
        self.path = path
        self.ui_path = os.path.join(path, "dialog.ui")
        self.config_path = os.path.join(path, "config.txt")

        super(Ui_Dialog, self).__init__(parent)
        uic.loadUi(self.ui_path, self)

        self.comboBox.addItem("Roadmap")
        self.comboBox.addItem("Terrain")
        self.comboBox.addItem("Satellite")
        self.comboBox.addItem("Hybrid")

        with open(self.config_path, 'r') as f:
            f.readline()
            self.resultsLine.setText(f.readline().rstrip("\n"))
            self.rscriptLine.setText(f.readline().rstrip("\n"))

            if f.readline().rstrip("\n") == "Yes":
                self.checkBox.setChecked(True)
                self.comboBox.setCurrentText(f.readline().rstrip("\n"))
            else:
                self.checkBox.setChecked(False)
                f.readline()

            self.widthLine.setText(f.readline().rstrip("\n"))

            self.sleepLine.setText(f.readline().rstrip("\n"))


    @pyqtSlot( )
    def resultsSlot( self ):
        home = self.path
        dir_path = QFileDialog.getExistingDirectory(self, "Choose Directory", home)

        self.resultsLine.setText(dir_path)

    @pyqtSlot( )
    def rscriptSlot( self ):
        home = self.path
        dir_path = QFileDialog.getExistingDirectory(self, "Choose Directory", home)

        self.rscriptLine.setText(dir_path)

    @pyqtSlot()
    def stateChangedSlot(self):
        if self.checkBox.isChecked():
            self.comboBox.setEnabled(True)
        else:
            self.comboBox.setEnabled(False)

    @pyqtSlot()
    def accept(self):
        with open(self.config_path, 'w') as f:
            f.write(self.path)

            f.write('\n')

            if self.resultsLine.text():
                f.write(self.resultsLine.text())
            else:
                f.write("Empty")

            f.write('\n')

            if self.rscriptLine.text():
                test = self.rscriptLine.text()
                if "Rscript" in test:
                    f.write(test)
                else:
                    f.write(os.path.join(self.rscriptLine.text(), "Rscript"))
            else:
                f.write("Empty")

            f.write('\n')

            if self.checkBox.isChecked():
                f.write("Yes")
                f.write('\n')
                f.write(self.comboBox.currentText())
            else:
                f.write("No")
                f.write('\n')
                f.write("No Map")

            f.write('\n')

            if self.widthLine.text():
                f.write(self.widthLine.text())
            else:
                f.write(str(0.5))

            f.write('\n')

            if self.sleepLine.text():
                f.write(self.sleepLine.text())
            else:
                f.write(str(2))

        self.close()