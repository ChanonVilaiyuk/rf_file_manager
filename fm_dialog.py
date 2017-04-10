import sys
import os
from Qt import QtWidgets, QtCore
import fm_dialog_ui as ui
from rftool.utils.ui import load
reload(ui)
import maya.cmds as mc
moduleDir = os.path.dirname(sys.modules[__name__].__file__)

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler)

from startup import config

class entityDialog(QtWidgets.QDialog):

    def __init__(self, mode='', project=None, asset='', episode='', sequence='', shot='', parent = None):
        QtWidgets.QDialog.__init__(self, parent)
        # self.ui = ui.Ui_Dialog()
        # self.ui.setupUi(self)
        uiFile = '%s/fm_dialog_ui.ui' % moduleDir
        self.ui = load.loadUI(uiFile, self)
        # self.ui.show()

        self.data = dict()
        self.mode = mode
        self.entities = []
        self.project = project
        self.episode = episode
        self.sequence = sequence
        self.asset = asset
        self.shot = shot
        self.init_signals()
        self.init_funcs()

    def init_signals(self):
        self.ui.button2_pushButton.clicked.connect(self.closeUI)
        self.ui.button1_pushButton.clicked.connect(self.run)
        self.ui.button3_pushButton.clicked.connect(self.run_preset)

        if self.mode == 'episode' or self.mode == 'sequence' or self.mode == 'shot':
            self.ui.lineEdit1_lineEdit.textChanged.connect(self.set_sgname)
            self.ui.start_lineEdit.textChanged.connect(self.check_preset)
            self.ui.end_lineEdit.textChanged.connect(self.check_preset)
            self.ui.step_lineEdit.textChanged.connect(self.check_preset)
            self.ui.preset_checkBox.stateChanged.connect(self.set_preset)

    def init_funcs(self):
        self.ui.label3_label.setVisible(False)
        self.ui.preset_frame.setVisible(False)
        self.ui.comboBox_frame.setVisible(False)
        self.ui.button3_pushButton.setVisible(False)
        self.ui.preset_checkBox.setVisible(False)

        if self.mode == 'episode':
            self.ui.label1_label.setText('Episode')
            self.ui.label2_label.setText('Short Name')
            self.ui.lineEdit1_lineEdit.setText(self.episode)
            self.ui.lineEdit2_lineEdit.setText(self.episode)

        if self.mode == 'sequence':
            self.ui.label1_label.setText('Dir/Short code')
            self.ui.label2_label.setText('SG name')
            self.ui.lineEdit1_lineEdit.setText(self.sequence)
            self.ui.preset_checkBox.setVisible(True)
            self.ui.button3_pushButton.setEnabled(False)

        if self.mode == 'shot':
            self.ui.label1_label.setText('Dir/Short code')
            self.ui.label2_label.setText('SG name')
            self.ui.lineEdit1_lineEdit.setText(self.shot)
            self.ui.button3_pushButton.setText('Batch Create')
            self.ui.preset_checkBox.setVisible(True)
            self.ui.button3_pushButton.setEnabled(False)
            # self.ui.start_lineEdit.setText(str(int(mc.playbackOptions(q=True, min=True))))
            # self.ui.end_lineEdit.setText(str(int(mc.playbackOptions(q=True, max=True))))

        if self.mode == 'asset':
            self.ui.label1_label.setText('Dir/Short code')
            self.ui.label2_label.setVisible(False)
            self.ui.lineEdit2_lineEdit.setVisible(False)
            self.ui.comboBox_frame.setVisible(True)
            self.ui.lineEdit1_lineEdit.setText(self.asset)
            self.add_taskTemplate()

        self.ui.resize(300, 100)

    def closeUI(self, *args):
        self.ui.done(QtWidgets.QDialog.Rejected)

    def run(self, *args):
        if self.mode in ['sequence', 'shot', 'episode']:
            if str(self.ui.lineEdit1_lineEdit.text()) and str(self.ui.lineEdit2_lineEdit.text()):
                self.data = {str(self.ui.lineEdit1_lineEdit.text()): str(self.ui.lineEdit2_lineEdit.text())}
                self.ui.done(QtWidgets.QDialog.Accepted)

            else:
                self.ui.label3_label.setVisible(True)
                self.ui.label3_label.setText('*Please fill dir name')

        if self.mode in ['asset']:
            if str(self.ui.lineEdit1_lineEdit.text()):
                self.ui.done(QtWidgets.QDialog.Accepted)

    def set_preset(self, *args):
        self.ui.preset_frame.setVisible(self.ui.preset_checkBox.isChecked())
        self.ui.button3_pushButton.setVisible(self.ui.preset_checkBox.isChecked())
        self.ui.button1_pushButton.setVisible(not self.ui.preset_checkBox.isChecked())

        if self.mode == 'sequence':
            self.ui.instruction_label.setText('Create %s %s(s) q0010 - q0020' % (len(self.entities), self.mode))
        if self.mode == 'shot':
            self.ui.instruction_label.setText('Create %s %s(s) s0010 - s0020' % (len(self.entities), self.mode))

        if not self.ui.preset_checkBox.isChecked():
            self.ui.resize(300, 100)

    def run_preset(self, *args):
        if self.mode == 'shot':
            if self.entities:
                for shot in self.entities:
                    shortCode = 's%04d' % shot
                    sgname = '%s_%s_%s_%s' % (self.project.get('sg_project_code'), self.episode, self.sequence, shortCode)
                    self.data.update({shortCode: sgname})

        if self.mode == 'sequence':
            if self.entities:
                for sequence in self.entities:
                    shortCode = 'q%04d' % sequence
                    sgname = '%s_%s_%s' % (self.project.get('sg_project_code'), self.episode, shortCode)
                    self.data.update({shortCode: sgname})

        self.ui.done(QtWidgets.QDialog.Accepted)


    def check_preset(self, *args):
        start = self.ui.start_lineEdit.text()
        end = self.ui.end_lineEdit.text()
        step = self.ui.step_lineEdit.text()
        self.entities = []
        self.ui.button3_pushButton.setEnabled(True)

        if start.isdigit() and end.isdigit() and step.isdigit():
            startStr = '%04d' % int(start)
            endStr = '%04d' % int(end)
            stepStr = int(step)
            self.entities = [a for a in xrange(int(start), int(end)+1, int(step))]
            if self.mode == 'shot':
                self.ui.instruction_label.setText('Create %s %s(s) s%s - s%s' % (len(self.entities), self.mode, startStr, endStr))
            if self.mode == 'sequence':
                self.ui.instruction_label.setText('Create %s %s(s) q%s - q%s' % (len(self.entities), self.mode, startStr, endStr))

        else:
            self.ui.instruction_label.setText('*Field must be digit')

    def set_sgname(self, *args):
        if self.mode == 'episode':
            episode = str(self.ui.lineEdit1_lineEdit.text())
            sgname = episode
            self.ui.lineEdit2_lineEdit.setText(sgname)

        if self.mode == 'sequence':
            if self.project and self.episode:
                seq = str(self.ui.lineEdit1_lineEdit.text())
                sgname = '%s_%s_%s' % (self.project.get('sg_project_code'), self.episode, seq)

                self.ui.lineEdit2_lineEdit.setText(sgname)

            else:
                logger.error('No project and no episode')

        if self.mode == 'shot':
            if self.project and self.episode and self.sequence:
                shot = str(self.ui.lineEdit1_lineEdit.text())
                sgname = '%s_%s_%s_%s' % (self.project.get('sg_project_code'), self.episode, self.sequence, shot)

                self.ui.lineEdit2_lineEdit.setText(sgname)

            else:
                logger.error('No project and no episode and no sequence')


    def add_taskTemplate(self, *args):
        self.ui.comboBox.clear()
        for row, key in enumerate(config.sgTemplate['asset']):
            taskTemplate = config.sgTemplate['asset'][key]
            self.ui.comboBox.addItem(key)
            self.ui.comboBox.setItemData(row, taskTemplate, QtCore.Qt.UserRole)
