# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:/Users/TA/Dropbox/script_server/core/maya/rftool/file_manager/preset_dialog.ui'
#
# Created: Tue Feb 14 23:10:29 2017
#      by: pyside-uic 0.2.14 running on PySide 1.2.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(244, 132)
        self.verticalLayout_4 = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.label_3 = QtGui.QLabel(Dialog)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_4.addWidget(self.label_3)
        self.duration_frame = QtGui.QFrame(Dialog)
        self.duration_frame.setObjectName("duration_frame")
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.duration_frame)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label = QtGui.QLabel(self.duration_frame)
        self.label.setObjectName("label")
        self.horizontalLayout_3.addWidget(self.label)
        self.start_lineEdit = QtGui.QLineEdit(self.duration_frame)
        self.start_lineEdit.setObjectName("start_lineEdit")
        self.horizontalLayout_3.addWidget(self.start_lineEdit)
        self.label_2 = QtGui.QLabel(self.duration_frame)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_3.addWidget(self.label_2)
        self.end_lineEdit = QtGui.QLineEdit(self.duration_frame)
        self.end_lineEdit.setObjectName("end_lineEdit")
        self.horizontalLayout_3.addWidget(self.end_lineEdit)
        self.verticalLayout_4.addWidget(self.duration_frame)
        self.comboBox_frame = QtGui.QFrame(Dialog)
        self.comboBox_frame.setFrameShape(QtGui.QFrame.NoFrame)
        self.comboBox_frame.setFrameShadow(QtGui.QFrame.Plain)
        self.comboBox_frame.setObjectName("comboBox_frame")
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.comboBox_frame)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label4_label = QtGui.QLabel(self.comboBox_frame)
        self.label4_label.setObjectName("label4_label")
        self.horizontalLayout_4.addWidget(self.label4_label)
        self.comboBox = QtGui.QComboBox(self.comboBox_frame)
        self.comboBox.setObjectName("comboBox")
        self.horizontalLayout_4.addWidget(self.comboBox)
        self.horizontalLayout_4.setStretch(0, 1)
        self.horizontalLayout_4.setStretch(1, 4)
        self.verticalLayout_4.addWidget(self.comboBox_frame)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.button1_pushButton = QtGui.QPushButton(Dialog)
        self.button1_pushButton.setObjectName("button1_pushButton")
        self.horizontalLayout_2.addWidget(self.button1_pushButton)
        self.button2_pushButton = QtGui.QPushButton(Dialog)
        self.button2_pushButton.setObjectName("button2_pushButton")
        self.horizontalLayout_2.addWidget(self.button2_pushButton)
        self.verticalLayout_4.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Dialog", "Batch creation", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "S: ", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Dialog", "-", None, QtGui.QApplication.UnicodeUTF8))
        self.label4_label.setText(QtGui.QApplication.translate("Dialog", "template : ", None, QtGui.QApplication.UnicodeUTF8))
        self.button1_pushButton.setText(QtGui.QApplication.translate("Dialog", "Create", None, QtGui.QApplication.UnicodeUTF8))
        self.button2_pushButton.setText(QtGui.QApplication.translate("Dialog", "Cancel", None, QtGui.QApplication.UnicodeUTF8))

