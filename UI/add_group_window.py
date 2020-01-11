# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'add_group_window.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(500, 541)
        self.titleLb = QtWidgets.QLabel(Form)
        self.titleLb.setGeometry(QtCore.QRect(100, 30, 300, 50))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(20)
        self.titleLb.setFont(font)
        self.titleLb.setAlignment(QtCore.Qt.AlignCenter)
        self.titleLb.setObjectName("titleLb")
        self.confirm_groupBtn = QtWidgets.QPushButton(Form)
        self.confirm_groupBtn.setGeometry(QtCore.QRect(200, 470, 100, 50))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(14)
        self.confirm_groupBtn.setFont(font)
        self.confirm_groupBtn.setObjectName("confirm_groupBtn")
        self.all_userLW = QtWidgets.QListWidget(Form)
        self.all_userLW.setGeometry(QtCore.QRect(50, 90, 400, 360))
        self.all_userLW.setObjectName("all_userLW")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.titleLb.setText(_translate("Form", "Select users to add"))
        self.confirm_groupBtn.setText(_translate("Form", "OK"))


