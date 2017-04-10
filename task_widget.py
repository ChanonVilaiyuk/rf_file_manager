from Qt import QtCore
from Qt import QtWidgets
from Qt import QtGui

class TaskWidget(QtWidgets.QWidget) :
	def __init__(self, parent = None) :
		super(TaskWidget, self).__init__(parent)
		# set label
		self.allLayout = QtWidgets.QHBoxLayout()

		self.text1Label = QtWidgets.QLabel()
		self.text2Label = QtWidgets.QLabel()

		# set icon
		self.iconQLabel = QtWidgets.QLabel()


		self.allLayout.addWidget(self.iconQLabel, 0, 0)
		self.allLayout.addWidget(self.text1Label, 0, 1)
		self.allLayout.addWidget(self.text2Label, 0, 2)

		self.text1Label.setMinimumSize(QtCore.QSize(20, 0))
		self.allLayout.setStretch(0, 0)
		self.allLayout.setStretch(1, 2)
		self.allLayout.setStretch(2, 2)

		# self.gridLayout.setColumnStretch(2, 2)
		# self.gridLayout.setSpacing(8)

		self.allLayout.setContentsMargins(2, 2, 2, 2)
		self.setLayout(self.allLayout)

		# set font
		# font = QtWidgets.QFont()
		# font.setPointSize(9)
		# # font.setWeight(70)
		# font.setBold(True)
		# self.text1Label.setFont(font)
		self.text2Label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)


	def set_text1(self, text) :
		self.text1Label.setText(text)

	def set_text2(self, text) :
		self.text2Label.setText(text)

	def set_text_color1(self, color) :
		self.text1Label.setStyleSheet('color: rgb(%s, %s, %s);' % (color[0], color[1], color[2]))

	def set_text_color2(self, color) :
		self.text2Label.setStyleSheet('color: rgb(%s, %s, %s);' % (color[0], color[1], color[2]))

	def set_text_color3(self, color) :
		self.text3Label.setStyleSheet('color: rgb(%s, %s, %s);' % (color[0], color[1], color[2]))

	def set_icon(self, iconPath, size = 16) :
		self.iconQLabel.setPixmap(QtGui.QPixmap(iconPath))


