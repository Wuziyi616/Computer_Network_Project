# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'log_in_window.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(600, 445)
        self.label = QtWidgets.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(15, 20, 550, 100))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(24)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.idLE = QtWidgets.QLineEdit(Form)
        self.idLE.setGeometry(QtCore.QRect(220, 180, 250, 30))
        font = QtGui.QFont()
        font.setFamily("宋体")
        font.setPointSize(16)
        self.idLE.setFont(font)
        self.idLE.setObjectName("idLE")
        self.log_inBtn = QtWidgets.QPushButton(Form)
        self.log_inBtn.setGeometry(QtCore.QRect(230, 340, 150, 70))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(16)
        self.log_inBtn.setFont(font)
        self.log_inBtn.setObjectName("log_inBtn")
        self.label_3 = QtWidgets.QLabel(Form)
        self.label_3.setGeometry(QtCore.QRect(110, 170, 101, 51))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(16)
        self.label_3.setFont(font)
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.label_2 = QtWidgets.QLabel(Form)
        self.label_2.setGeometry(QtCore.QRect(350, 100, 201, 51))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(16)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.pswLE = QtWidgets.QLineEdit(Form)
        self.pswLE.setGeometry(QtCore.QRect(220, 230, 250, 30))
        font = QtGui.QFont()
        font.setFamily("宋体")
        font.setPointSize(16)
        self.pswLE.setFont(font)
        self.pswLE.setEchoMode(QtWidgets.QLineEdit.Password)
        self.pswLE.setObjectName("pswLE")
        self.label_4 = QtWidgets.QLabel(Form)
        self.label_4.setGeometry(QtCore.QRect(90, 220, 121, 51))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(16)
        self.label_4.setFont(font)
        self.label_4.setAlignment(QtCore.Qt.AlignCenter)
        self.label_4.setObjectName("label_4")
        self.use_my_central_serverCB = QtWidgets.QCheckBox(Form)
        self.use_my_central_serverCB.setGeometry(QtCore.QRect(220, 280, 231, 41))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(14)
        self.use_my_central_serverCB.setFont(font)
        self.use_my_central_serverCB.setObjectName("use_my_central_serverCB")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label.setText(_translate("Form", "Stay Connecting, Stay Chatting"))
        self.log_inBtn.setText(_translate("Form", "Log In"))
        self.label_3.setText(_translate("Form", "User ID:"))
        self.label_2.setText(_translate("Form", "Presented by wzy"))
        self.label_4.setText(_translate("Form", "Password:"))
        self.use_my_central_serverCB.setText(_translate("Form", "Use my central server"))


