from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import csv
from os import path

#Save data GUI
class Ui_Save(QtWidgets.QDialog):
    def __init__(self, data, home_path, save_path, parent=None):
        super(Ui_Save, self).__init__(parent)
        uic.loadUi(save_path, self)

        self.data = data
        self.home_path = home_path


    @pyqtSlot( )
    def browseSlot( self ):
        if self.appendRadio.isChecked():
            dir_path = QFileDialog.getOpenFileName(self,"Choose File to Append to",self.home_path, "Comma Separated Values Files (*.csv)")

            self.browseLine.setText(dir_path[0])

        elif self.createRadio.isChecked():
            dir_path = QFileDialog.getSaveFileName(self, "Choose File to Save to", self.home_path,
                                                   "Comma Separated Values Files (*.csv)")

            self.browseLine.setText(dir_path[0])


    @pyqtSlot()
    def accept(self):
        comments = self.commentsLine.text()
        filepath = self.browseLine.text()
        if filepath:
            if self.createRadio.isChecked():
                if path.exists(filepath):
                    error = QMessageBox()
                    error.setIcon(QMessageBox.Warning)
                    error.setWindowTitle("Error")
                    error.setText("Creation error")
                    error.setInformativeText("The file you want to create already exists, please pick a different name!")
                    error.exec()
                else:
                    with open(filepath, "w", newline='') as file:
                        data_writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                        data_writer.writerow(['latitude', 'longitude', 'azimuth', 'altitude', 'declination', 'stars', 'comments'])
                        data_writer.writerow(
                            [self.data[0], self.data[1], self.data[2], self.data[3], self.data[4], self.data[5], comments])
            else:
                if not path.exists(filepath):
                    error = QMessageBox()
                    error.setIcon(QMessageBox.Warning)
                    error.setWindowTitle("Error")
                    error.setText("Append error")
                    error.setInformativeText("The file you want to append to doesn't exist, select a different file!")
                    error.exec()
                else:
                    with open(filepath, "a", newline='') as file:
                        data_writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                        data_writer.writerow(
                            [self.data[0], self.data[1], self.data[2], self.data[3], self.data[4], self.data[5], comments])

            self.close()
        else:
            error = QMessageBox()
            error.setIcon(QMessageBox.Warning)
            error.setWindowTitle("Error")
            error.setText("Save error")
            error.setInformativeText("No file chosen! Please choose a file or click cancel.")
            error.exec()