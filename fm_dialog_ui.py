# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:/Users/TA/Dropbox/script_server/core/maya/rftool/file_manager/fm_dialog_ui.ui'
#
# Created: Wed Feb 15 09:59:47 2017
#      by: pyside-uic 0.2.14 running on PySide 1.2.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(284, 268)
        self.verticalLayout_4 = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.verticalLayout_6 = QtGui.QVBoxLayout()
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.label1_label = QtGui.QLabel(Dialog)
        self.label1_label.setObjectName("label1_label")
        self.verticalLayout_6.addWidget(self.label1_label)
        self.lineEdit1_lineEdit = QtGui.QLineEdit(Dialog)
        self.lineEdit1_lineEdit.setObjectName("lineEdit1_lineEdit")
        self.verticalLayout_6.addWidget(self.lineEdit1_lineEdit)
        self.label2_label = QtGui.QLabel(Dialog)
        self.label2_label.setObjectName("label2_label")
        self.verticalLayout_6.addWidget(self.label2_label)
        self.lineEdit2_lineEdit = QtGui.QLineEdit(Dialog)
        self.lineEdit2_lineEdit.setObjectName("lineEdit2_lineEdit")
        self.verticalLayout_6.addWidget(self.lineEdit2_lineEdit)
        self.verticalLayout_4.addLayout(self.verticalLayout_6)
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
        self.label3_label = QtGui.QLabel(Dialog)
        self.label3_label.setObjectName("label3_label")
        self.verticalLayout_4.addWidget(self.label3_label)
        self.preset_checkBox = QtGui.QCheckBox(Dialog)
        self.preset_checkBox.setObjectName("preset_checkBox")
        self.verticalLayout_4.addWidget(self.preset_checkBox)
        self.preset_frame = QtGui.QFrame(Dialog)
        self.preset_frame.setObjectName("preset_frame")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.preset_frame)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_8 = QtGui.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label = QtGui.QLabel(self.preset_frame)
        self.label.setObjectName("label")
        self.horizontalLayout_8.addWidget(self.label)
        self.start_lineEdit = QtGui.QLineEdit(self.preset_frame)
        self.start_lineEdit.setObjectName("start_lineEdit")
        self.horizontalLayout_8.addWidget(self.start_lineEdit)
        self.label_2 = QtGui.QLabel(self.preset_frame)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_8.addWidget(self.label_2)
        self.end_lineEdit = QtGui.QLineEdit(self.preset_frame)
        self.end_lineEdit.setObjectName("end_lineEdit")
        self.horizontalLayout_8.addWidget(self.end_lineEdit)
        self.label_3 = QtGui.QLabel(self.preset_frame)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_8.addWidget(self.label_3)
        self.step_lineEdit = QtGui.QLineEdit(self.preset_frame)
        self.step_lineEdit.setObjectName("step_lineEdit")
        self.horizontalLayout_8.addWidget(self.step_lineEdit)
        self.verticalLayout_2.addLayout(self.horizontalLayout_8)
        self.instruction_label = QtGui.QLabel(self.preset_frame)
        self.instruction_label.setObjectName("instruction_label")
        self.verticalLayout_2.addWidget(self.instruction_label)
        self.verticalLayout_4.addWidget(self.preset_frame)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.button1_pushButton = QtGui.QPushButton(Dialog)
        self.button1_pushButton.setObjectName("button1_pushButton")
        self.horizontalLayout_2.addWidget(self.button1_pushButton)
        self.button3_pushButton = QtGui.QPushButton(Dialog)
        self.button3_pushButton.setObjectName("button3_pushButton")
        self.horizontalLayout_2.addWidget(self.button3_pushButton)
        self.button2_pushButton = QtGui.QPushButton(Dialog)
        self.button2_pushButton.setObjectName("button2_pushButton")
        self.horizontalLayout_2.addWidget(self.button2_pushButton)
        self.verticalLayout_4.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label1_label.setText(QtGui.QApplication.translate("Dialog", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.label2_label.setText(QtGui.QApplication.translate("Dialog", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.label4_label.setText(QtGui.QApplication.translate("Dialog", "template : ", None, QtGui.QApplication.UnicodeUTF8))
        self.label3_label.setText(QtGui.QApplication.translate("Dialog", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.preset_checkBox.setText(QtGui.QApplication.translate("Dialog", "Batch Preset ", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "S: ", None, QtGui.QApplication.UnicodeUTF8))
        self.start_lineEdit.setText(QtGui.QApplication.translate("Dialog", "10", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Dialog", "-", None, QtGui.QApplication.UnicodeUTF8))
        self.end_lineEdit.setText(QtGui.QApplication.translate("Dialog", "20", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Dialog", "Step", None, QtGui.QApplication.UnicodeUTF8))
        self.step_lineEdit.setText(QtGui.QApplication.translate("Dialog", "10", None, QtGui.QApplication.UnicodeUTF8))
        self.instruction_label.setText(QtGui.QApplication.translate("Dialog", "Create shot s0010 - s0020", None, QtGui.QApplication.UnicodeUTF8))
        self.button1_pushButton.setText(QtGui.QApplication.translate("Dialog", "Create", None, QtGui.QApplication.UnicodeUTF8))
        self.button3_pushButton.setText(QtGui.QApplication.translate("Dialog", "Create", None, QtGui.QApplication.UnicodeUTF8))
        self.button2_pushButton.setText(QtGui.QApplication.translate("Dialog", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
