# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/main_window.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(717, 404)
        MainWindow.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.filename_label = QtWidgets.QLabel(self.centralwidget)
        self.filename_label.setGeometry(QtCore.QRect(30, 20, 651, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.filename_label.setFont(font)
        self.filename_label.setObjectName("filename_label")
        self.serial_label = QtWidgets.QLabel(self.centralwidget)
        self.serial_label.setGeometry(QtCore.QRect(30, 140, 71, 17))
        self.serial_label.setObjectName("serial_label")
        self.serial_ports = QtWidgets.QComboBox(self.centralwidget)
        self.serial_ports.setGeometry(QtCore.QRect(30, 160, 231, 25))
        self.serial_ports.setObjectName("serial_ports")
        self.loaders = QtWidgets.QComboBox(self.centralwidget)
        self.loaders.setGeometry(QtCore.QRect(30, 90, 231, 25))
        self.loaders.setObjectName("loaders")
        self.loader_label = QtWidgets.QLabel(self.centralwidget)
        self.loader_label.setGeometry(QtCore.QRect(30, 70, 71, 17))
        self.loader_label.setObjectName("loader_label")
        self.logger_text = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.logger_text.setGeometry(QtCore.QRect(30, 220, 661, 151))
        self.logger_text.setReadOnly(True)
        self.logger_text.setObjectName("logger_text")
        self.test_button = QtWidgets.QPushButton(self.centralwidget)
        self.test_button.setEnabled(True)
        self.test_button.setGeometry(QtCore.QRect(310, 160, 80, 25))
        self.test_button.setObjectName("test_button")
        self.flash_button = QtWidgets.QPushButton(self.centralwidget)
        self.flash_button.setEnabled(True)
        self.flash_button.setGeometry(QtCore.QRect(520, 160, 80, 25))
        self.flash_button.setStyleSheet("QPushButton{color: red; font-weight: bold;} \n"
"QPushButton:disabled{color:grey; font-weight:normal;}")
        self.flash_button.setObjectName("flash_button")
        self.force_serial_checkbox = QtWidgets.QCheckBox(self.centralwidget)
        self.force_serial_checkbox.setGeometry(QtCore.QRect(440, 90, 121, 23))
        self.force_serial_checkbox.setObjectName("force_serial_checkbox")
        self.serial_number = QtWidgets.QLineEdit(self.centralwidget)
        self.serial_number.setGeometry(QtCore.QRect(570, 90, 113, 25))
        self.serial_number.setInputMethodHints(QtCore.Qt.ImhNone)
        self.serial_number.setObjectName("serial_number")
        self.serial_number_label = QtWidgets.QLabel(self.centralwidget)
        self.serial_number_label.setGeometry(QtCore.QRect(570, 70, 111, 17))
        self.serial_number_label.setObjectName("serial_number_label")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 717, 22))
        self.menubar.setObjectName("menubar")
        self.menu_File = QtWidgets.QMenu(self.menubar)
        self.menu_File.setObjectName("menu_File")
        self.menu_Help = QtWidgets.QMenu(self.menubar)
        self.menu_Help.setObjectName("menu_Help")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.action_Exit = QtWidgets.QAction(MainWindow)
        self.action_Exit.setObjectName("action_Exit")
        self.action_About_AMSAT_Hostloader = QtWidgets.QAction(MainWindow)
        self.action_About_AMSAT_Hostloader.setMenuRole(QtWidgets.QAction.TextHeuristicRole)
        self.action_About_AMSAT_Hostloader.setObjectName("action_About_AMSAT_Hostloader")
        self.action_Open = QtWidgets.QAction(MainWindow)
        self.action_Open.setObjectName("action_Open")
        self.menu_File.addAction(self.action_Open)
        self.menu_File.addAction(self.action_Exit)
        self.menu_Help.addAction(self.action_About_AMSAT_Hostloader)
        self.menubar.addAction(self.menu_File.menuAction())
        self.menubar.addAction(self.menu_Help.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "AMSAT Hostloader"))
        self.filename_label.setText(_translate("MainWindow", "Flash file:"))
        self.serial_label.setText(_translate("MainWindow", "Serial port:"))
        self.loader_label.setText(_translate("MainWindow", "Loader"))
        self.test_button.setText(_translate("MainWindow", "Test port"))
        self.flash_button.setText(_translate("MainWindow", "FLASH"))
        self.force_serial_checkbox.setText(_translate("MainWindow", "Force Serial"))
        self.serial_number_label.setText(_translate("MainWindow", "Serial number"))
        self.menu_File.setTitle(_translate("MainWindow", "&File"))
        self.menu_Help.setTitle(_translate("MainWindow", "&Help"))
        self.action_Exit.setText(_translate("MainWindow", "&Exit"))
        self.action_About_AMSAT_Hostloader.setText(_translate("MainWindow", "&About AMSAT Hostloader"))
        self.action_Open.setText(_translate("MainWindow", "&Open"))
