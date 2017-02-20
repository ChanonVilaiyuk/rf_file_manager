# v.0.0.1 first version
# v.0.0.2 correct file naming adding task
# v.0.0.3 batch shot creation
# v.0.0.4 episode creation fix
# v.0.0.5 batch sequence creation
# v.0.0.6 asset match open scene selection
# v.0.0.7 asset / shot match open scene selection

#Import python modules
import sys, os, re, shutil, random
import subprocess

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

#Import GUI
from PySide import QtCore
from PySide import QtGui

from shiboken import wrapInstance

#Import maya commands
import maya.cmds as mc
import maya.mel as mm
from functools import partial

# import ui
import ui
import fm_dialog
import task_widget
from rftool.utils import file_utils
from rftool.utils import path_info
from rftool.utils import sg_wrapper
from rftool.utils import sg_process
from rftool.utils import icon
from rftool.utils import pipeline_utils
from rftool.utils import maya_utils
from startup import config
from rftool.utils.userCheck import user_app
from rftool.prop_it import propIt_app

moduleDir = sys.modules[__name__].__file__


# If inside Maya open Maya GUI
def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QtGui.QWidget)
    # return sip.wrapinstance(long(ptr), QObject)

import maya.OpenMayaUI as mui

def show():
    uiName = 'SGFileManagerUI'
    deleteUI(uiName)
    myApp = SGFileManager(getMayaWindow())
    myApp.show()
    return myApp

def deleteUI(ui):
    if mc.window(ui, exists=True):
        mc.deleteUI(ui)
        deleteUI(ui)

class SGFileManager(QtGui.QMainWindow):

    def __init__(self, parent=None):
        self.count = 0
        #Setup Window
        super(SGFileManager, self).__init__(parent)
        self.ui = ui.Ui_SGFileManagerUI()
        self.ui.setupUi(self)
        self.setWindowTitle('SGFileManager v.0.0.7 - asset / shot match open scene selection')

        self.asset = config.asset
        self.scene = config.scene
        self.serverMode = 'server'
        self.shotgunMode = 'shotgun'

        # variable
        self.sgProjects = None
        self.sgAssets = None
        self.sgType = None
        self.sgSubType = None
        self.sgUser = None
        self.allRes = ['pr', 'lo', 'md', 'hi']

        # start ui
        self.firstStartUI = True

        # optionVar
        self.projectVar = config.projectVar
        self.modeVar = config.modeVar
        self.serverVar = config.serverVar
        self.serverSGTask = True

        # set root
        self.set_root()

        # set workspace
        self.workspaces = {'work': config.RFPROJECT, 'publish': config.RFPUBL}

        # set signals
        self.init_signals()

        # read custom setting
        self.init_functions()


    def set_root(self):
        try:
            self.rootWork = config.rootWork
            self.rootPubl = config.rootPubl
            self.rootProd = config.rootProd
        except KeyError as e:
            logger.error('No root define %s' % e)

    def init_functions(self):
        self.check_user('check')
        self.set_default_button()
        self.set_root_ui()
        self.apply_setting()
        self.set_project_ui()
        # self.start_ui()

    def init_signals(self):
        # mode signals
        self.ui.asset_radioButton.toggled.connect(self.set_entity_mode)
        self.ui.server_radioButton.toggled.connect(self.set_server_sg)

        # push button
        self.ui.open_pushButton.clicked.connect(self.open_file)
        self.ui.save_pushButton.clicked.connect(self.save_file)
        self.ui.addSub1_pushButton.clicked.connect(self.add_entity1)
        self.ui.addSub2_pushButton.clicked.connect(self.add_entity2)
        self.ui.addEntity_pushButton.clicked.connect(self.create_entity)

        # checkBox
        self.ui.override_checkBox.stateChanged.connect(self.override_filename)
        self.ui.user_checkBox.stateChanged.connect(self.sgUser_signal)
        self.ui.taskFilter_checkBox.stateChanged.connect(self.set_work_files)

        # comboBox
        self.ui.project_comboBox.currentIndexChanged.connect(self.project_signal)
        self.ui.step_comboBox.currentIndexChanged.connect(self.step_signal)
        self.ui.root_comboBox.currentIndexChanged.connect(self.root_signal)
        self.ui.work_comboBox.currentIndexChanged.connect(self.work_signal)

        # radioButton
        self.ui.pr_radioButton.clicked.connect(partial(self.res_signal, 'pr'))
        self.ui.lo_radioButton.clicked.connect(partial(self.res_signal, 'lo'))
        self.ui.md_radioButton.clicked.connect(partial(self.res_signal, 'md'))
        self.ui.hi_radioButton.clicked.connect(partial(self.res_signal, 'hi'))

        # listWidget
        self.ui.ui1_listWidget.itemSelectionChanged.connect(self.ui1_signal)
        self.ui.ui2_listWidget.itemSelectionChanged.connect(self.ui2_signal)
        self.ui.entity_listWidget.itemSelectionChanged.connect(self.entity_listWidget_signal)
        self.ui.task_listWidget.itemSelectionChanged.connect(self.task_listWidget_signal)

        # show menu
        self.ui.entity_listWidget.customContextMenuRequested.connect(self.show_entity_menu)
        self.ui.task_listWidget.customContextMenuRequested.connect(self.show_task_menu)
        self.ui.file_listWidget.customContextMenuRequested.connect(self.show_file_menu)

        # filters
        self.ui.filter_checkBox.stateChanged.connect(self.filter1_signal)
        self.ui.filter1_comboBox.currentIndexChanged.connect(self.filter1_signal)

        # user setting
        self.ui.user_pushButton.clicked.connect(self.check_user)


    def start_ui(self):
        ''' refresh ui here '''
        ''' start browsing depend on mode '''
        assetMode, sceneMode = self.get_mode_ui()
        serverMode, sgMode = self.get_server_sg_ui()
        # set mode label
        if assetMode:
            self.set_asset_ui()
        if sceneMode:
            self.set_scene_ui()
        if sgMode and self.ui.user_checkBox.isChecked():
            self.set_mytask_ui()

        # start browsing
        self.set_ui()

    def set_ui(self):
        self.set_step_ui()
        self.set_user_ui()
        self.set_status_ui()
        if not self.firstStartUI:
            self.start_browsing()

    def set_entity_mode(self):
        ''' set browse mode asset / scene '''
        assetMode, sceneMode = self.get_mode_ui()
        if assetMode:
            var = self.asset
        if sceneMode:
            var = self.scene

        mc.optionVar(sv=(self.modeVar, var))
        self.start_ui()

    def set_server_sg(self):
        ''' set server or browse sg mode '''
        serverMode, sgMode = self.get_server_sg_ui()

        if serverMode:
            var = self.serverMode
        if sgMode:
            var = self.shotgunMode

        mc.optionVar(sv=(self.serverVar, var))
        self.start_ui()

    def set_asset_ui(self):
        # show / hide ui elements
        self.ui.sub1_label.setText('TYPE')
        self.ui.sub2_label.setText('SUBTYPE')
        self.ui.entity_label.setText('ASSET')

        # show filter
        self.ui.filter_checkBox.setText('Episode')
        self.ui.filter1_comboBox.setVisible(True)
        self.ui.filter_checkBox.setVisible(True)
        self.ui.resolution_frame.setVisible(True)

    def set_scene_ui(self):
        # show / hide ui elements
        self.ui.sub1_label.setText('EPISODE')
        self.ui.sub2_label.setText('SEQUENCE')
        self.ui.entity_label.setText('SHOT')

        # hide filter
        self.ui.filter1_comboBox.setVisible(False)
        self.ui.filter_checkBox.setVisible(False)
        self.ui.resolution_frame.setVisible(False)

    def set_mytask_ui(self):
        mode = self.get_mode_ui(entity=True)
        if mode == self.asset:
            entityLabel = 'ASSET'
        if mode == self.scene:
            entityLabel = 'SHOT'
        # show / hide ui elements
        self.ui.sub1_label.setText('EPISODE')
        self.ui.sub2_label.setText('STATUSES')
        self.ui.entity_label.setText(entityLabel)

        # hide filter
        self.ui.filter1_comboBox.setVisible(False)
        self.ui.filter_checkBox.setVisible(False)


    def get_mode_ui(self, entity=False):
        ''' return mode state on ui '''
        if entity:
            if self.ui.asset_radioButton.isChecked():
                return self.asset
            if self.ui.scene_radioButton.isChecked():
                return self.scene
        return self.ui.asset_radioButton.isChecked(), self.ui.scene_radioButton.isChecked()

    def get_server_sg_ui(self):
        ''' return mode state on ui '''
        return self.ui.server_radioButton.isChecked(), self.ui.shotgun_radioButton.isChecked()

    def check_user(self, mode='setting'):
        linkSuccess = False
        run = True

        # get sg user
        if not self.sgUser:
            self.sgUser = sg_process.get_users()

        user = mc.optionVar(q=config.localUser)

        # always run
        if mode == 'setting':
            run = True

        # check if user linked
        if mode == 'check':
            if not user == 0:
                if user in [a['sg_localuser'] for a in self.sgUser]:
                    linkSuccess = True
                    run = False
                else:
                    run = True
            else:
                run = True

        if run:
            dialog = user_app.userDialog(self.sgUser, self)
            result = dialog.exec_()
            self.sgUser = sg_process.get_users()

            if mode == 'setting':
                self.set_user_ui()

            if mode == 'check':
                if not dialog.ui.checkBox.isChecked():
                    self.check_user('check')

    def group_user(self):
        groupDict = dict()
        if self.sgUser:
            for user in self.sgUser:
                name = user['name']
                groups = user['groups']

                if groups:
                    for group in groups:
                        groupName = group['name']
                        if not groupName in groupDict.keys():
                            groupDict[groupName] = [{'name': name, 'id': user['id']}]
                        else:
                            groupDict[groupName].append({'name': name, 'id': user['id']})

        return groupDict

    def apply_setting(self):
        ''' read setting from var and apply to ui options. set ui will trigger signal to run start_ui()'''
        # asset / scene mode
        mode = mc.optionVar(q=self.modeVar)
        serverSg = mc.optionVar(q=self.serverVar)

        if mode == 0 or mode == self.asset:
            self.ui.asset_radioButton.setChecked(True)
        if mode == self.scene:
            self.ui.scene_radioButton.setChecked(True)

        if serverSg == 0 or serverSg == self.serverMode:
            self.ui.server_radioButton.setChecked(True)
        if serverSg == self.shotgunMode:
            self.ui.shotgun_radioButton.setChecked(True)


    # server
    def set_project_ui(self):
        ''' set project comboBox '''
        serverMode, sgMode = self.get_server_sg_ui()
        projects = []
        # get store value
        storeProject = mc.optionVar(q=self.projectVar)

        if sgMode and not self.sgProjects:
            self.sgProjects = sg_process.get_projects()

        if serverMode:
            self.sgProjects = sg_process.get_projects()

        if self.sgProjects:
            projects = sorted([a['name'] for a in self.sgProjects])

        if projects:
            # disconnect signal
            self.ui.project_comboBox.blockSignals(True)


            # add items
            self.ui.project_comboBox.clear()

            for row, project in enumerate(sorted(self.sgProjects)):
                self.ui.project_comboBox.addItem(project['name'])
                self.ui.project_comboBox.setItemData(row, project, QtCore.Qt.UserRole)
            # self.ui.project_comboBox.addItems(projects)
            self.ui.project_comboBox.model().sort(0)

            # reconnect signal
            self.ui.project_comboBox.blockSignals(False)

            # set last selected project, then signal from project will browse assets
            index = projects.index(storeProject) if storeProject in projects else 0
            self.ui.project_comboBox.setCurrentIndex(index)

            # signal won't work if index == 0, force browse manually
            if index == 0:
                self.start_browsing()

        # if serverMode:
        #     root = str(self.ui.root_lineEdit.text())
        #     projects = file_utils.listFolder(root)
        #     self.ui.project_comboBox.clear()
        #     self.ui.project_comboBox.addItems(sorted(projects))

        #     index = projects.index(storeProject) if storeProject in projects else 0
        #     self.ui.project_comboBox.setCurrentIndex(index)

    def set_step_ui(self):
        ''' set department comboBox only work on server mode'''
        self.ui.step_comboBox.blockSignals(True)
        self.ui.step_comboBox.clear()
        self.ui.step_comboBox.addItems(config.steps)

        # get previous setting and apply when reopen
        step = mc.optionVar(q=config.stepVar)
        index = config.steps.index(step) if step in config.steps else 0
        self.ui.step_comboBox.setCurrentIndex(index)
        self.ui.step_comboBox.blockSignals(False)

    def set_user_ui(self):
        ''' set sg user comboBox and local user comboBox '''
        if self.sgUser:
            sgUsers = sorted([a['name'] for a in self.sgUser])
            self.ui.user_comboBox.clear()
            self.ui.user_comboBox.addItems(sgUsers)
            localUser = mc.optionVar(q=config.localUser)
            matchUser = [a for a in self.sgUser if a['sg_localuser'] == localUser]

            if matchUser:
                index = sgUsers.index(matchUser[0]['name'])
                self.ui.user_comboBox.setCurrentIndex(index)

            self.ui.localUser_comboBox.clear()
            self.ui.localUser_comboBox.addItem(localUser)

    def set_status_ui(self):
        ''' set sg status comboBox '''
        self.ui.status_comboBox.clear()
        self.ui.status_comboBox.addItem('all')

        for row, status in enumerate(config.sgStatus):
            self.ui.status_comboBox.addItem(status)
            iconPath = config.sgIconMap[status]
            iconWidget = QtGui.QIcon()
            iconWidget.addPixmap(QtGui.QPixmap(iconPath), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.ui.status_comboBox.setItemIcon(row+1, iconWidget)


    def set_root_ui(self):
        self.ui.root_comboBox.clear()
        self.ui.root_comboBox.addItems(self.workspaces.keys())

    def set_default_button(self):
        self.ui.save_pushButton.setEnabled(False)
        self.ui.root_lineEdit.setEnabled(False)
        self.ui.path_lineEdit.setEnabled(False)
        self.ui.fileName_lineEdit.setEnabled(False)
        self.ui.user_checkBox.setChecked(False)
        self.ui.status_checkBox.setVisible(False)
        self.ui.status_comboBox.setVisible(False)
        self.ui.step_comboBox.setVisible(False)
        self.ui.dept_label.setVisible(False)
        self.ui.entity_listWidget.setSortingEnabled(True)
        self.ui.file_listWidget.setSortingEnabled(True)
        self.ui.ui2_listWidget.setSortingEnabled(True)

    def override_filename(self):
        self.ui.fileName_lineEdit.setEnabled(self.ui.override_checkBox.isChecked())


    # signals

    # ui state signals
    def sgUser_signal(self):
        state = self.ui.user_checkBox.isChecked()
        self.ui.user_comboBox.setEnabled(state)
        self.ui.status_checkBox.setVisible(state)
        self.ui.status_comboBox.setVisible(state)
        self.ui.step_comboBox.setVisible(state)
        self.ui.dept_label.setVisible(state)

        self.start_ui()

    def project_signal(self):
        project = str(self.ui.project_comboBox.currentText())
        mc.optionVar(sv=(self.projectVar, project))

        # clear cache
        self.sgAssets = None
        self.start_browsing()

    def step_signal(self):
        step = str(self.ui.step_comboBox.currentText())
        mc.optionVar(sv=(config.stepVar, step))

    def root_signal(self, index):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()
        # set root
        rootPath = os.environ.get(self.workspaces[self.workspaces.keys()[index]], 'Not found')
        self.ui.root_lineEdit.setText(rootPath)

        if sgMode:
            if assetMode:
                if not self.firstStartUI:
                    self.set_asset_entity_sgui()
                    # self.set_work_files()
            if sceneMode:
                self.set_shot_entity_ui()
        if serverMode:
            self.set_type_svui()

    def work_signal(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()

        if sgMode:
            if assetMode:
                if not self.firstStartUI:
                    # self.set_asset_entity_sgui(self.asset)
                    self.set_work_files()
            if sceneMode:
                self.set_work_files()

        if serverMode:
            if assetMode:
                self.set_work_files()

            if sceneMode:
                self.set_work_files()

    def ui1_signal(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()
        myTaskMode = self.ui.user_checkBox.isChecked()

        if sgMode:
            if myTaskMode:
                self.set_mytask_status()
            else:
                if assetMode:
                    if not self.firstStartUI:
                        self.set_subtype_sgui(filters=True)
                        # self.set_asset_entity_sgui()

                if sceneMode:
                    self.sg_set_sequence_ui()

        if serverMode:
            if assetMode:
                self.set_subtype_svui()

            if sceneMode:
                self.set_sequence_svui()


    def ui2_signal(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()

        if sgMode:
            if assetMode:
                if not self.firstStartUI:
                    self.set_asset_entity_sgui()

            if sceneMode:
                self.set_shot_entity_ui()

        if serverMode:
            if assetMode:
                self.set_entity_svui()

            if sceneMode:
                self.set_shot_svui()


    def entity_listWidget_signal(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()

        if sgMode:
            self.set_task_ui()
            if sceneMode:
                self.set_path()

        if serverMode:
            if assetMode:
                if self.serverSGTask:
                    self.set_entity_sgItem()
                    self.set_task_ui()

                else:
                    self.set_step_svui()

            if sceneMode:
                self.set_entity_sgItem()
                self.set_task_ui()

    def res_signal(self, res):
        self.set_task_ui()
        # self.set_work_files()


    def task_listWidget_signal(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()

        if sgMode:
            if assetMode:
                self.set_workspace_ui()
            if sceneMode:
                self.set_workspace_ui()
                # self.set_work_files()

        if serverMode:
            if assetMode:
                self.set_workspace_ui()

            if sceneMode:
                self.set_workspace_ui()


    def filter1_signal(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()

        if sgMode:
            if assetMode:
                if not self.firstStartUI:
                    self.set_asset_entity_sgui()

    def start_browsing(self):
        ''' start the process of list data on this functions'''
        print 'start_browsing'
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()
        myTaskMode = self.ui.user_checkBox.isChecked()

        # sg mode
        if sgMode:
            if myTaskMode:
                self.set_mytask_step()
                # self.set_mytask_status()
                # self.set_asset_entity_sgui()
            else:
                # asset mode
                if assetMode:
                    # find type subtype assets
                    self.set_type_sgui()
                    self.set_subtype_sgui()
                    self.set_episode_sgui()
                    self.set_asset_entity_sgui()

                if sceneMode:
                    self.set_sceneEpisode_sgui()

            self.firstStartUI = False

        # server mode
        if serverMode:
            if assetMode:
                self.set_type_svui()

            if sceneMode:
                self.set_sceneEpisode_svui()

            self.firstStartUI = False



    # server ===========================================
    def set_type_svui(self):
        self.ui.ui1_listWidget.clear()
        self.ui.ui2_listWidget.clear()
        self.ui.entity_listWidget.clear()
        self.ui.task_listWidget.clear()
        self.ui.work_comboBox.clear()
        self.ui.file_listWidget.clear()
        projectRoot = self.get_project_root()

        types = file_utils.listFolder(projectRoot)

        for assetType in types:
            path = '%s/%s' % (projectRoot, assetType)

            item = QtGui.QListWidgetItem(self.ui.ui1_listWidget)
            item.setText(assetType)

            iconWidget = QtGui.QIcon()
            iconWidget.addPixmap(QtGui.QPixmap(icon.dir),QtGui.QIcon.Normal,QtGui.QIcon.Off)

            item.setIcon(iconWidget)
            item.setData(QtCore.Qt.UserRole, {'path': path})

        # set current selection
        asset = path_info.PathInfo()
        if asset.type in types:
            index = types.index(asset.type)
            self.ui.ui1_listWidget.setCurrentRow(index)




    def set_subtype_svui(self):
        self.ui.ui2_listWidget.clear()
        self.ui.entity_listWidget.clear()
        self.ui.task_listWidget.clear()
        self.ui.work_comboBox.clear()
        self.ui.file_listWidget.clear()

        ui1Root = self.get_project_root(level=1)

        if ui1Root:
            subDirs2 = file_utils.listFolder(ui1Root)

            for subDir in subDirs2:
                path = '%s/%s' % (ui1Root, subDir)

                item = QtGui.QListWidgetItem(self.ui.ui2_listWidget)
                item.setText(subDir)

                iconWidget = QtGui.QIcon()
                iconWidget.addPixmap(QtGui.QPixmap(icon.dir),QtGui.QIcon.Normal,QtGui.QIcon.Off)

                item.setIcon(iconWidget)
                item.setData(QtCore.Qt.UserRole, {'path': path})

            # set current selection
            asset = path_info.PathInfo()
            if asset.subtype in subDirs2:
                index = subDirs2.index(asset.subtype)
                self.ui.ui2_listWidget.setCurrentRow(index)


    def set_entity_svui(self):
        self.ui.entity_listWidget.clear()
        self.ui.task_listWidget.clear()
        self.ui.work_comboBox.clear()
        self.ui.file_listWidget.clear()

        ui2Root = self.get_project_root(level=2)

        if ui2Root:
            entityDirs = file_utils.listFolder(ui2Root)

            for entityDir in entityDirs:
                item = QtGui.QListWidgetItem(self.ui.entity_listWidget)
                item.setText(entityDir)

                iconWidget = QtGui.QIcon()
                iconWidget.addPixmap(QtGui.QPixmap(icon.dir),QtGui.QIcon.Normal,QtGui.QIcon.Off)

                item.setIcon(iconWidget)

            # set current selection
            asset = path_info.PathInfo()
            if asset.name in entityDirs:
                self.set_res_ui(asset.taskName)
                index = entityDirs.index(asset.name)
                self.ui.entity_listWidget.setCurrentRow(index)
                # set task res

    def set_res_ui(self, taskName):
        if 'pr' in taskName:
            self.ui.pr_radioButton.setChecked(True)
        if 'lo' in taskName:
            self.ui.lo_radioButton.setChecked(True)
        if 'md' in taskName:
            self.ui.md_radioButton.setChecked(True)
        if 'hi' in taskName:
            self.ui.hi_radioButton.setChecked(True)


    def set_step_svui(self, selectItem=''):
        self.ui.task_listWidget.clear()
        self.ui.work_comboBox.clear()
        self.ui.file_listWidget.clear()

        ui3Root = self.get_project_root(level=3)

        if ui3Root:
            stepDirs = file_utils.listFolder(ui3Root)

            for stepDir in stepDirs:
                item = QtGui.QListWidgetItem(self.ui.task_listWidget)
                item.setText(stepDir)

                iconWidget = QtGui.QIcon()
                iconWidget.addPixmap(QtGui.QPixmap(icon.dir),QtGui.QIcon.Normal,QtGui.QIcon.Off)
                item.setIcon(iconWidget)

            if selectItem in stepDirs:
                index = entityDirs.index(selectItem)
                self.ui.task_listWidget.setCurrentRow(index)


    def set_entity_sgItem(self):
        assetMode, sceneMode = self.get_mode_ui()
        project = str(self.ui.project_comboBox.currentText())
        entityItem = self.ui.entity_listWidget.currentItem()
        assetName = str(entityItem.text())

        if assetMode:
            if not entityItem.data(QtCore.Qt.UserRole):
                entity = sg_process.get_one_asset(project, assetName)
                if entity:
                    entityItem.setData(QtCore.Qt.UserRole, entity)
                else:
                    iconWidget = QtGui.QIcon()
                    iconWidget.addPixmap(QtGui.QPixmap(icon.sgNa),QtGui.QIcon.Normal,QtGui.QIcon.Off)
                    entityItem.setIcon(iconWidget)

        if sceneMode:
            if not entityItem.data(QtCore.Qt.UserRole):
                path = self.get_project_root(level=3)
                print 'path', path
                shot = path_info.PathInfo(path)
                shotName = shot.shotName(project=True)
                entity = sg_process.get_shot_entity(project, shotName)

                if entity:
                    entityItem.setData(QtCore.Qt.UserRole, entity)

                else:
                    iconWidget = QtGui.QIcon()
                    iconWidget.addPixmap(QtGui.QPixmap(icon.sgNa),QtGui.QIcon.Normal,QtGui.QIcon.Off)
                    entityItem.setIcon(iconWidget)

    def set_type_sgui(self, selectItem=''):
        if not self.sgType:
            self.sgType = sorted(sg_process.get_type())
            self.sgType = [a for a in self.sgType if a in config.assetTypes]

        index = self.sgType.index(selectItem) if selectItem in self.sgType else 0
        self.ui.ui1_listWidget.clear()
        self.ui.ui1_listWidget.addItem('all')
        self.ui.ui1_listWidget.addItems(self.sgType)
        self.ui.ui1_listWidget.setCurrentRow(index)


    def set_subtype_sgui(self, selectItem='', filters=False):
        if not self.sgSubType:
            self.sgSubType = sorted(sg_process.get_subtype())
        index = self.sgSubType.index(selectItem) if selectItem in self.sgSubType else 0

        if not filters:
            self.ui.ui2_listWidget.clear()
            self.ui.ui2_listWidget.addItem('all')
            self.ui.ui2_listWidget.addItems(self.sgSubType)
            self.ui.ui2_listWidget.setCurrentRow(index)

        if filters:
            selType = str(self.ui.ui1_listWidget.currentItem().text())
            items = [self.ui.ui2_listWidget.item(i) for i in range(self.ui.ui2_listWidget.count())]
            nestedDict = self.type_subtype_data()
            if selType in nestedDict.keys():
                subTypes = sorted(nestedDict[selType])
                validSubtypes = [a for a in items if str(a.text()) in subTypes]

            else:
                validSubtypes = []

                if selType == 'all':
                    validSubtypes = items

            for item in items:
                if str(item.text()) in [str(a.text()) for a in validSubtypes]:
                    # item.setFont(QtGui.QFont('Verdana', italic=True))
                    item.setForeground(QtGui.QColor(255, 255, 255))
                else:
                    # item.setFont(QtGui.QFont('Verdana', italic=False))
                    item.setForeground(QtGui.QColor(100, 100, 100))

            self.set_asset_entity_sgui()



    def set_episode_sgui(self):
        project = str(self.ui.project_comboBox.currentText())
        sgEpisodes = sg_process.get_episodes(project)
        episodes = sorted([a['code'] for a in sgEpisodes])
        self.ui.filter1_comboBox.clear()

        for row, ep in enumerate(sgEpisodes):
            self.ui.filter1_comboBox.addItem(ep['code'])
            self.ui.filter1_comboBox.setItemData(row, ep, QtCore.Qt.UserRole)


    def set_asset_entity_sgui(self, selectItem=''):
        # get ui selection
        project = str(self.ui.project_comboBox.currentText())
        assetTypes = [str(a.text()) for a in self.ui.ui1_listWidget.selectedItems()]
        subTypes = [str(a.text()) for a in self.ui.ui2_listWidget.selectedItems()]
        episodes = [self.ui.filter1_comboBox.itemData(self.ui.filter1_comboBox.currentIndex(), QtCore.Qt.UserRole)]
        root = self.workspaces[str(self.ui.root_comboBox.currentText())]

        assetTypeFilter = []
        assetSubTypeFilter = []
        episodeFilter = []

        # query sg assets
        if not self.sgAssets:
            self.sgAssets = sg_process.get_assets(project)

        # convert data to {'asset-id': entity}
        sgAssetDict = dict()

        for sgAsset in self.sgAssets:
            name = sgAsset['code']
            entityId = sgAsset['id']
            sgAssetDict.update({entityId: sgAsset})

        # all assets
        allAssets = sorted(sgAssetDict.keys())

        if assetTypes and not 'all' in assetTypes:
            assetTypeFilter = sorted([a['id'] for a in self.sgAssets if a['sg_asset_type'] in assetTypes])
        if 'all' in assetTypes:
            assetTypeFilter = allAssets

        if subTypes and not 'all' in subTypes:
            assetSubTypeFilter = sorted([a['id'] for a in self.sgAssets if a['sg_subtype'] in subTypes])
        if 'all' in subTypes:
            assetSubTypeFilter = allAssets

        if self.ui.filter_checkBox.isChecked() and episodes:
            episodeFilter = []
            for eachAsset in self.sgAssets:
                if eachAsset.get('sg_episodes'):
                    if eachAsset.get('sg_episodes').get('id') in [a['id'] for a in episodes]:
                        episodeFilter.append(eachAsset['id'])
            # episodeFilter = [a for a in self.sgAssets if a.get('sg_episodes').get('id') if a.get('sg_episodes') else {} in [b for b in]]
        else:
            episodeFilter = allAssets

        filterAssets = [a for a in allAssets if a in assetTypeFilter and a in assetSubTypeFilter and a in episodeFilter]
        self.ui.entity_listWidget.clear()
        self.ui.task_listWidget.clear()
        self.ui.file_listWidget.clear()
        self.ui.work_comboBox.clear()
        self.ui.entity_listWidget.addItem('No Item')


        if filterAssets:
            # convert data to asset
            assetLists = sorted([sgAssetDict[a]['code'] for a in filterAssets])
            self.ui.entity_listWidget.clear()
            sceneAsset = path_info.PathInfo()

            currentRow = 0
            for row, entityId in enumerate(filterAssets):
                item = QtGui.QListWidgetItem(self.ui.entity_listWidget)
                item.setText(sgAssetDict[entityId]['code'])
                item.setData(QtCore.Qt.UserRole, sgAssetDict[entityId])
                iconPath = icon.nodir

                asset = path_info.PathInfo(project=project, entity=self.asset, entitySub1=sgAssetDict[entityId].get('sg_asset_type', ''), entitySub2=str(sgAssetDict[entityId].get('sg_subtype')), name=sgAssetDict[entityId].get('code'))

                if os.path.exists(asset.entityPath(root=root)):
                    iconPath = icon.dir

                iconWidget = QtGui.QIcon()
                iconWidget.addPixmap(QtGui.QPixmap(iconPath),QtGui.QIcon.Normal,QtGui.QIcon.Off)
                item.setIcon(iconWidget)

            index = assetLists.index(selectItem) if selectItem in assetLists else 0
            self.ui.entity_listWidget.sortItems()
            self.set_res_ui(sceneAsset.taskName)
            self.ui.entity_listWidget.setCurrentRow(currentRow)
            # self.ui.entity_listWidget.setCurrentRow(index)

            # set current active
            asset = path_info.PathInfo()
            index = [a for a in range(self.ui.entity_listWidget.count()) if str(self.ui.entity_listWidget.item(a).text()) == asset.name]
            if index:
                self.ui.entity_listWidget.setCurrentRow(index[0])


            self.set_path()


    def set_workspace_ui(self, sel=''):
        asset = self.combine_path()

        if asset:
            selRoot = str(self.ui.root_comboBox.currentText())
            root = self.workspaces[selRoot]
            path = asset.stepPath(root=root, relativePath=False)
            self.ui.work_comboBox.clear()
            taskEntity = self.ui.task_listWidget.currentItem().data(QtCore.Qt.UserRole)
            app = (taskEntity.get('sg_app') or asset.activeApp)


            self.ui.fileName_lineEdit.clear()
            # workspaces = file_utils.listFolder(path)
            workspaces = self.get_workspace_dir(path)
            if workspaces:
                rootApp = '%s/%s' % (app, selRoot)
                self.ui.work_comboBox.addItems(workspaces)
                index = workspaces.index(rootApp) if rootApp in workspaces else 0
                self.ui.work_comboBox.setCurrentIndex(index)

    def set_task_ui(self, sel='', cache=False):
        assetMode, sceneMode = self.get_mode_ui()
        selectedItem = self.ui.entity_listWidget.currentItem()
        self.ui.task_listWidget.clear()
        self.ui.file_listWidget.clear()
        res = self.get_asset_res()

        if selectedItem:
            if not str(selectedItem.text()) == 'No Item':
                entity = selectedItem.data(QtCore.Qt.UserRole)
                if entity:
                    tasks = sg_process.get_tasks(entity)
                    if assetMode:
                        tasks = self.filterTask(tasks, res)

                    # self.ui.task_listWidget.setSortingEnabled(True)

                    if tasks:
                        currentRow = 0
                        # set current selection
                        pathInfo = path_info.PathInfo()

                        for row, task in enumerate(sorted(tasks)):
                            taskIcon = config.sgIconMap.get(task['sg_status_list'])
                            assignees = [a.get('name') for a in task['task_assignees']]
                            assigneesStr = (',').join(assignees)

                            taskWidget = task_widget.TaskWidget()
                            taskWidget.set_text1(task['content'])
                            taskWidget.set_icon(taskIcon)
                            taskWidget.set_text2(assigneesStr)

                            item = QtGui.QListWidgetItem(self.ui.task_listWidget)
                            item.setSizeHint(taskWidget.sizeHint())

                            self.ui.task_listWidget.setItemWidget(item, taskWidget)
                            # item = QtGui.QListWidgetItem(self.ui.task_listWidget)
                            # item.setText('%s - %s' % (task['content'], task['task_assignees']))
                            item.setData(QtCore.Qt.UserRole, task)

                            if task['content'] == pathInfo.taskName:
                                currentRow = row

                            # iconWidget = QtGui.QIcon()
                            # iconWidget.addPixmap(QtGui.QPixmap(taskIcon),QtGui.QIcon.Normal,QtGui.QIcon.Off)
                            # item.setIcon(iconWidget)

                        # self.ui.task_listWidget.sortItems()
                        self.ui.task_listWidget.setCurrentRow(currentRow)

                    else:
                        self.ui.task_listWidget.addItem('No tasks in Shotgun')

                else:
                    self.ui.task_listWidget.addItem('No asset in Shotgun')

        else:
            self.ui.save_pushButton.setEnabled(False)

    def set_asset_step(self):
        selectedItem = self.ui.task_listWidget.currentItem()
        if selectedItem:
            taskEntity = selectedItem.data(QtCore.Qt.UserRole)
            step = config.sgSteps[taskEntity['step']]
            # indexStep = config.steps.index(step)

    def set_work_files(self):
        ''' work files '''
        serverMode, sgMode = self.get_server_sg_ui()
        projectEntity = self.ui.project_comboBox.itemData(self.ui.project_comboBox.currentIndex(), QtCore.Qt.UserRole)
        mode = self.get_mode_ui(entity=True)
        asset = self.combine_path()

        if asset:
            root = self.workspaces[str(self.ui.root_comboBox.currentText())]
            stepPath = asset.stepPath(root=root, relativePath=False)
            work = str(self.ui.work_comboBox.currentText())
            path = '%s/%s' % (stepPath, work)
            filterRes = '%s_%s' % (asset.step, self.get_asset_res())

            saveFilename = ''

            self.ui.file_listWidget.clear()

            if os.path.exists(path):
                files = file_utils.listFile(path)
                if self.ui.taskFilter_checkBox.isChecked():
                    files = [a for a in files if filterRes in a]

                for eachFile in files:
                    item = QtGui.QListWidgetItem(self.ui.file_listWidget)
                    item.setText(eachFile)
                    item.setData(QtCore.Qt.UserRole, ('%s/%s' % (path, eachFile)))

                    iconWidget = QtGui.QIcon()
                    iconWidget.addPixmap(QtGui.QPixmap(icon.maya),QtGui.QIcon.Normal,QtGui.QIcon.Off)
                    item.setIcon(iconWidget)

                saveFilename = self.get_save_filename(projectEntity, mode, path, asset)

            self.ui.file_listWidget.sortItems(QtCore.Qt.DescendingOrder)
            self.set_path(filename=saveFilename)


    # utils
    def get_workspace_dir(self, path):
        dirs = file_utils.listFolder(path)
        workspaceDir = []

        for dirname in dirs:
            subDirs = file_utils.listFolder('%s/%s' % (path, dirname))
            if subDirs:
                for subDir in subDirs:
                    workspaceDir.append('%s/%s' % (dirname, subDir))

            else:
                workspaceDir.append('%s' % dirname)

        return workspaceDir


    def type_subtype_data(self):
        nestedDict = dict()
        if self.sgAssets:
            for each in self.sgAssets:
                assetType = each['sg_asset_type']
                assetSubType = each['sg_subtype']
                assetName = each['code']

                if not assetType in nestedDict.keys():
                    nestedDict.update({assetType: {assetSubType: [assetName]}})
                else:
                    if not assetSubType in nestedDict[assetType].keys():
                        nestedDict[assetType].update({assetSubType: [assetName]})
                    else:
                        nestedDict[assetType][assetSubType].append(assetName)
        return nestedDict

    def combine_path(self):
        serverMode, sgMode = self.get_server_sg_ui()
        if sgMode:
            mode = self.get_mode_ui(entity=True)
            project = str(self.ui.project_comboBox.currentText())

            entityItem = self.ui.entity_listWidget.currentItem()
            entity = (entityItem.data(QtCore.Qt.UserRole) if entityItem else {})

            if mode == self.asset:
                entitySub1 = entity.get('sg_asset_type', '')
                entitySub2 = entity.get('sg_subtype', '') if entity.get('sg_subtype') else ''
                name = entity.get('code', '')

            if mode == self.scene:
                entitySub1 = entity.get('sg_episode', {}).get('name', '')
                entitySub2 = entity.get('sg_sequence.Sequence.sg_shortcode', '')
                name = entity.get('sg_shortcode', '')

            taskItem = self.ui.task_listWidget.currentItem()
            if taskItem:
                taskEntity = (taskItem.data(QtCore.Qt.UserRole) if taskItem else {})
                # print 'taskEntity', taskEntity

                if taskEntity:
                    step = config.sgSteps.get(taskEntity.get('step', {}).get('name'), 'None')
                    taskName = taskEntity.get('content', '')
                    asset = path_info.PathInfo(project=project, entity=mode, entitySub1=entitySub1, entitySub2=entitySub2, name=name, step=step, task=taskName)

                    return asset

        if serverMode:
            asset = self.get_project_root(auto=True, obj=True)
            return asset


    def get_save_filename(self, project, mode, path, asset):
        ''' define naming convention for file name '''
        projectCode = project.get('sg_project_code', '')
        allFiles = file_utils.listFile(path)

        nameElems = []
        # if projectCode:
            # nameElems.append(projectCode)
        if mode == self.asset:
            taskEntity = self.ui.task_listWidget.currentItem()
            taskName = taskEntity.data(QtCore.Qt.UserRole).get('content')
            filterRes = '%s_%s' % (asset.step, self.get_asset_res())
            allFiles = [a for a in allFiles if filterRes in a]

            # add step name
            # nameElems.append(asset.assetName(step=True))
            # add task name
            nameElems.append(asset.assetName(step=True))
            if any(a for a in self.allRes if a in taskName):
                nameElems.append(self.get_asset_res())
        if mode == self.scene:
            if projectCode:
                nameElems.append(projectCode)
                nameElems.append(asset.shotName(step=True))

        version = file_utils.find_next_version(allFiles)
        nameElems.append(version)
        nameElems.append(mc.optionVar(q=config.localUser))
        filename = '%s.ma' % ('_').join(nameElems)
        return os.path.basename(file_utils.increment_version('%s/%s' % (path, filename)))


    def set_path(self, filename=''):

        asset = self.combine_path()
        root = self.workspaces[str(self.ui.root_comboBox.currentText())]
        if asset:
            path = asset.stepPath(root=root, relativePath=True)

            if filename:
                self.ui.fileName_lineEdit.setText(filename)

            workspace = str(self.ui.root_comboBox.currentText())
            self.ui.path_lineEdit.setText(path)

            self.ui.save_pushButton.setEnabled(False)
            if os.path.exists(path_info.PathInfo(path).absPath):
                self.ui.save_pushButton.setEnabled(True)

    # file commands

    def set_scene_path(self):
        project = str(self.ui.project_comboBox.currentText())
        selEpisode = self.ui.ui1_listWidget.currentItem()
        selSequence = self.ui.ui2_listWidget.currentItem()
        selShot = self.ui.entity_listWidget.currentItem()
        selTask = self.ui.task_listWidget.currentItem()

    def open_file(self):
        ''' open maya file '''
        selItem = self.ui.file_listWidget.currentItem()
        path = selItem.data(QtCore.Qt.UserRole)
        isMaya = False
        if os.path.splitext(path)[-1] in config.mayaExt:
            isMaya = True

        if isMaya:
            if mc.file(q=True, modified=True):
                result = QtGui.QMessageBox.question(self, 'Warning', 'Scene has changed since last save. Do you want to open?', QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)
                if result == QtGui.QMessageBox.Ok:
                    return mc.file(path, o=True, f=True)

            return mc.file(path, o=True, f=True)

        else:
            print path
            os.system("start "+path)

    def save_file(self):
        root = self.workspaces[str(self.ui.root_comboBox.currentText())]
        path = str(self.ui.path_lineEdit.text())
        asset = path_info.PathInfo(path)
        absPath = asset.absPath
        workspace = str(self.ui.work_comboBox.currentText())
        filename = str(self.ui.fileName_lineEdit.text())
        saveFile = '%s/%s/%s' % (absPath, workspace, filename)
        save = True
        if os.path.exists(saveFile):
            save = False
            saveDecision = QtGui.QMessageBox.question(self, 'Confirm', '%s exists. Do you want to overwrite?' % saveFile, QtGui.QMessageBox.Yes, QtGui.QMessageBox.Cancel)
            if saveDecision == QtGui.QMessageBox.Yes:
                save = True

        if save:
            mc.file(rename=saveFile)
            result = mc.file(save=True, type='mayaAscii')
            self.set_work_files()

            return result

    def add_entity1(self):
        ''' create type for asset, create episode for scene '''
        assetMode, sceneMode = self.get_mode_ui()
        serverMode, sgMode = self.get_server_sg_ui()
        inputStr = str(self.ui.sub1_lineEdit.text())
        root = str(self.ui.root_lineEdit.text())
        projectEntity = self.ui.project_comboBox.itemData(self.ui.project_comboBox.currentIndex(), QtCore.Qt.UserRole)
        # episodeEntity = self.ui.ui1_listWidget.currentItem().data(QtCore.Qt.UserRole)

        if sgMode:
            if assetMode:
                if inputStr:
                    # QtGui.QMessageBox.question(self, 'Warning', 'No working')
                    # return
                    values = sg_process.add_list_field(inputStr, 'sg_asset_type')
                    self.ui.ui1_listWidget.blockSignals(True)
                    self.sgType = None
                    self.set_type_sgui()
                    self.ui.ui1_listWidget.blockSignals(False)

                    if values:
                        QtGui.QMessageBox.information(self, 'Complete', 'Add type %s complete' % inputStr)

            if sceneMode:
                result = QtGui.QMessageBox.question(self, 'Create episode?', 'Create episode %s?' % inputStr, QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)

                if result == QtGui.QMessageBox.Ok:
                    sgResult = sg_process.create_episode(projectEntity, inputStr)

                    if sgResult:
                        shot = path_info.PathInfo(project=projectEntity.get('name'), entity=self.scene, entitySub1=inputStr)
                        episodePath = shot.entity1Path()

                        if not os.path.exists(episodePath):
                            os.makedirs(episodePath)

                        self.set_sceneEpisode_sgui()
                        self.ui.sub1_lineEdit.setText('')

        if serverMode:
            if assetMode:
                # create folder
                root = self.get_project_root(level=0)
                targetDir = '%s/%s' % (root, inputStr)

                if not os.path.exists(targetDir):
                    os.makedirs(targetDir)

                # create shotgun
                values = sg_process.add_list_field(inputStr, 'sg_asset_type')

                if values:
                    QtGui.QMessageBox.information(self, 'Complete', 'Add type %s complete' % inputStr)

                # refresh
                self.set_type_svui()

            if sceneMode:
                dialog = fm_dialog.entityDialog(mode='episode', episode=str(self.ui.sub1_lineEdit.text()), parent=self)
                result = dialog.exec_()

                if result:
                    episodeCode = str(dialog.ui.lineEdit1_lineEdit.text())
                    shortCode = str(dialog.ui.lineEdit2_lineEdit.text())

                    sgResult = sg_process.create_episode(projectEntity, episodeCode)

                    if sgResult:
                        shot = path_info.PathInfo(project=projectEntity.get('name'), entity=self.scene, entitySub1=episodeCode)
                        episodePath = shot.entity1Path()
                        print 'episodePath', episodePath

                        if not os.path.exists(episodePath):
                            os.makedirs(episodePath)

                        self.set_sceneEpisode_svui()
                        self.ui.sub1_lineEdit.setText('')


    def add_entity2(self):
        ''' create type for asset, create episode for scene '''
        assetMode, sceneMode = self.get_mode_ui()
        serverMode, sgMode = self.get_server_sg_ui()
        inputStr = str(self.ui.sub2_lineEdit.text())
        projectEntity = self.ui.project_comboBox.itemData(self.ui.project_comboBox.currentIndex(), QtCore.Qt.UserRole)

        if sgMode:
            if assetMode:
                if inputStr:
                    # QtGui.QMessageBox.question(self, 'Warning', 'No working')
                    # return
                    values = sg_process.add_list_field(inputStr, 'sg_subtype')
                    self.ui.ui2_listWidget.blockSignals(True)
                    self.sgSubType = None
                    self.set_subtype_sgui()
                    self.ui.ui2_listWidget.blockSignals(False)

                    if values:
                        QtGui.QMessageBox.information(self, 'Complete', 'Add subtype %s complete' % inputStr)


            if sceneMode:
                selEpisode = self.ui.ui1_listWidget.currentItem()
                if selEpisode:
                    episodeEntity = selEpisode.data(QtCore.Qt.UserRole)
                    shot = path_info.PathInfo(project=projectEntity.get('name'), entity=self.scene, entitySub1=episodeEntity.get('code'), entitySub2=inputStr)

                    result = QtGui.QMessageBox.question(self, 'Create sequence?', 'Create sequence %s?' % inputStr, QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)

                    if result == QtGui.QMessageBox.Ok:
                        sgResult = sg_process.create_sequence(projectEntity, episodeEntity, shot.sequenceName(project=True), inputStr)

                        if sgResult:
                            sequencePath = shot.entity2Path()

                            if not os.path.exists(sequencePath):
                                os.makedirs(sequencePath)

                        self.sg_set_sequence_ui()
                        self.ui.sub2_lineEdit.setText('')

        if serverMode:
            if assetMode:
                # create folder
                root = self.get_project_root(level=1)
                targetDir = '%s/%s' % (root, inputStr)

                if not os.path.exists(targetDir):
                    os.makedirs(targetDir)

                # create shotgun
                values = sg_process.add_list_field(inputStr, 'sg_subtype')

                if values:
                    QtGui.QMessageBox.information(self, 'Complete', 'Add subtype %s complete' % inputStr)

                # refresh
                self.set_subtype_svui()

            if sceneMode:
                selEpisode = self.ui.ui1_listWidget.currentItem()
                if selEpisode:
                    dialog = fm_dialog.entityDialog(mode='sequence', project=projectEntity, episode=str(selEpisode.text()), sequence=str(self.ui.sub2_lineEdit.text()), parent=self)
                    result = dialog.exec_()

                    if result:
                        data = dialog.data
                        for shortCode, sequenceCode in sorted(data.iteritems()):
                            # shortCode = str(dialog.ui.lineEdit1_lineEdit.text())
                            # sequenceCode = str(dialog.ui.lineEdit2_lineEdit.text())

                            episodeEntity = selEpisode.data(QtCore.Qt.UserRole)
                            if not episodeEntity:
                                episodeEntity = sg_process.get_one_episode(projectEntity.get('name'), str(selEpisode.text()))
                                selEpisode.setData(QtCore.Qt.UserRole, episodeEntity)

                            if episodeEntity:
                                sgResult = sg_process.create_sequence(projectEntity, episodeEntity, sequenceCode, shortCode)
                                # sgResult = True

                                if sgResult:
                                    shot = path_info.PathInfo(project=projectEntity.get('name'), entity=self.scene, entitySub1=str(selEpisode.text()), entitySub2=shortCode)
                                    sequencePath = shot.entity2Path()

                                    if not os.path.exists(sequencePath):
                                        os.makedirs(sequencePath)

                                    self.set_sequence_svui()
                                    self.ui.sub2_lineEdit.setText('')


    def create_entity(self):
        assetMode, sceneMode = self.get_mode_ui()
        serverMode, sgMode = self.get_server_sg_ui()
        project = str(self.ui.project_comboBox.currentText())
        root = self.workspaces[str(self.ui.root_comboBox.currentText())]
        entityName = str(self.ui.entity_lineEdit.text())
        entitySub1 = self.ui.ui1_listWidget.currentItem()
        entitySub2 = self.ui.ui2_listWidget.currentItem()
        projectEntity = self.ui.project_comboBox.itemData(self.ui.project_comboBox.currentIndex(), QtCore.Qt.UserRole)
        episodeEntity = None
        entityList = [str(self.ui.entity_listWidget.item(a).text()) for a in range(self.ui.entity_listWidget.count())]


        if sgMode:
            entitySub1 = str(entitySub1.text()) if entitySub1 else ''
            entitySub1 = entitySub1 if not entitySub1 == 'all' else ''
            entitySub2 = str(entitySub2.text()) if entitySub2 else ''
            entitySub2 = entitySub2 if not entitySub2 == 'all' else ''

            if self.ui.filter_checkBox.isChecked():
                episodeEntity = self.ui.filter1_comboBox.itemData(self.ui.filter1_comboBox.currentIndex(), QtCore.Qt.UserRole)

            if entitySub1 and entitySub2 and entityName:
                if assetMode:
                    # check if not asset in Shotgun
                    if not entityName in [a['code'] for a in self.sgAssets]:
                        title = 'Confirm'
                        # message = 'Create asset "%s" under type %s, subtype %s?' % (entityName, entitySub1, entitySub2)
                        # result = QtGui.QMessageBox.question(self, title, message, QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)
                        dialog = fm_dialog.entityDialog(mode='asset', asset=entityName, parent=self)
                        result = dialog.exec_()

                        if result:
                            entityName = str(dialog.ui.lineEdit1_lineEdit.text())
                            taskTemplate = dialog.ui.comboBox.itemData(dialog.ui.comboBox.currentIndex(), QtCore.Qt.UserRole)
                            sgResult = sg_process.create_asset(project=projectEntity, assetType=entitySub1, assetSubType=entitySub2, assetName=entityName, episode=episodeEntity, taskTemplate=taskTemplate)
                            if sgResult:
                                dirResult = pipeline_utils.create_asset_template(root, projectEntity['name'], entitySub1, entitySub2, entityName)

                                self.sgAssets = None
                                self.set_asset_entity_sgui(selectItem=entityName)
                                self.ui.entity_lineEdit.setText('')

                            else:
                                QtGui.QMessageBox.warning(self, 'Error', 'Failed to create asset %s in Shotgun' % entityName)
                    else:
                        QtGui.QMessageBox.warning(self, 'Warning', '%s already exists in Shotgun' % entityName)

                if sceneMode:
                    episodeEntity = self.ui.ui1_listWidget.currentItem().data(QtCore.Qt.UserRole)
                    sequenceEntity = self.ui.ui2_listWidget.currentItem().data(QtCore.Qt.UserRole)
                    shot = path_info.PathInfo(project=projectEntity.get('name'), entity=self.scene, entitySub1=entitySub1, entitySub2=entitySub2, name=entityName)
                    shortCode = entityName
                    if not shortCode in [str(a.text()) for a in self.get_all_listWidget_items(self.ui.entity_listWidget)]:
                        title = 'question'
                        shotName = shot.shotName(project=True)
                        message = 'Do you want to create shot %s? Sg name is %s' % (entityName, shotName)
                        result = QtGui.QMessageBox.warning(self, title, message, QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)

                        if result == QtGui.QMessageBox.Ok:
                            sgResult = sg_process.create_shot(projectEntity, episodeEntity, sequenceEntity, shotName, shortCode, template='default')
                            if sgResult:
                                dirResult = pipeline_utils.create_scene_template(root, project=projectEntity.get('name'), episodeName=entitySub1, sequenceName=entitySub2, shotName=entityName)

                            self.set_shot_entity_ui()
                            self.ui.entity_lineEdit.setText('')

                    else:
                        QtGui.QMessageBox.warning(self, 'warning', '%s exists' % entityName, QtGui.QMessageBox.Ok)

        if serverMode:
            if entityName and entitySub1 and entitySub2:
                targetDir = '%s/%s' % (root, entityName)
                entityItem1 = str(entitySub1.text())
                entityItem2 = str(entitySub2.text())

                if assetMode:
                    if not entityName in entityList:
                        print targetDir
                        title = 'Confirm'
                        # message = 'Create asset "%s" under type %s, subtype %s?' % (entityName, entityItem1, entityItem2)
                        # result = QtGui.QMessageBox.question(self, title, message, QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)
                        dialog = fm_dialog.entityDialog(mode='asset', asset=entityName, parent=self)
                        result = dialog.exec_()

                        if result:
                            entityName = str(dialog.ui.lineEdit1_lineEdit.text())
                            taskTemplate = dialog.ui.comboBox.itemData(dialog.ui.comboBox.currentIndex(), QtCore.Qt.UserRole)
                            dirResult = pipeline_utils.create_asset_template(root, project, entityItem1, entityItem2, entityName)
                            sgResult = sg_process.create_asset(project=projectEntity, assetType=entityItem1, assetSubType=entityItem2, assetName=entityName, episode=episodeEntity, taskTemplate=taskTemplate)

                            self.set_entity_svui()
                            self.ui.entity_lineEdit.setText('')

                    else:
                        QtGui.QMessageBox.warning(self, 'Warning', '%s already created' % entityName)

                if sceneMode:
                    dialog = fm_dialog.entityDialog(mode='shot', project=projectEntity, episode=entityItem1, sequence=entityItem2, shot=entityName, parent=self)
                    result = dialog.exec_()

                    if result:
                        print 'dialog OK'
                        data = dialog.data

                        for shortCode, shotName in sorted(data.iteritems()):
                            # dir code
                            # shortCode = str(dialog.ui.lineEdit1_lineEdit.text())
                            # shotName = str(dialog.ui.lineEdit2_lineEdit.text())

                            # range
                            # startFrame = int(str(dialog.ui.start_lineEdit.text()))
                            # endFrame = int(str(dialog.ui.end_lineEdit.text()))
                            # duration = int(endFrame) - int(startFrame) + 1

                            # shot entity
                            shot = self.get_project_root(level=2, obj=True)
                            sequenceName = shot.sequenceName(project=True)

                            episodeEntity = entitySub1.data(QtCore.Qt.UserRole)
                            if not episodeEntity:
                                episodeEntity = sg_process.get_one_episode(projectEntity.get('name'), str(entitySub1.text()))
                                entitySub1.setData(QtCore.Qt.UserRole, episodeEntity)

                            sequenceEntity = entitySub2.data(QtCore.Qt.UserRole)
                            print episodeEntity
                            print sequenceName
                            if not sequenceEntity:
                                sequenceEntity = sg_process.get_one_sequence(projectEntity.get('name'), episodeEntity.get('code'), sequenceName)
                                entitySub2.setData(QtCore.Qt.UserRole, sequenceEntity)

                            print sequenceEntity

                            if episodeEntity and sequenceEntity:
                                sgResult = sg_process.create_shot(projectEntity, episodeEntity, sequenceEntity, shotName, shortCode, template='default')
                                if sgResult:
                                    shot = path_info.PathInfo(project=projectEntity.get('name'), entity=self.scene, entitySub1=entityItem1, entitySub2=entityItem2, name=shortCode)
                                    shotPath = shot.entityPath()

                                    if not os.path.exists(shotPath):
                                        dirResult = pipeline_utils.create_scene_template(root, project=projectEntity.get('name'), episodeName=entityItem1, sequenceName=entityItem2, shotName=shortCode)

                                    self.set_entity_svui()
                                    self.ui.entity_lineEdit.setText('')

                            else:
                                QtGui.QMessageBox.warning(self, 'Warning', 'Episode or Sequence are not in Shotgun')


    # else:
        #     title = 'Error'
        #     message = 'Name cannot be empty. Type and Subtype cannot be "all"'
        #     QtGui.QMessageBox.warning(self, title, message, QtGui.QMessageBox.Ok)

    # show menu
    def show_entity_menu(self, pos):
        ''' context menu for download repo '''
        menu = QtGui.QMenu(self)
        currentItem = self.ui.entity_listWidget.currentItem()
        data = currentItem.data(QtCore.Qt.UserRole)

        if currentItem:
            menu.addAction('Open in Explorer')
            menu.addAction('Create Directory')

            self.reference_menu(menu)
            self.propit_menu(menu)

            menu.popup(self.ui.entity_listWidget.mapToGlobal(pos))
            selMenuItem = menu.exec_(self.ui.entity_listWidget.mapToGlobal(pos))

            self.menu_command('entity', data, selMenuItem)

    def reference_menu(self, menu):
        currentItem = self.ui.entity_listWidget.currentItem()
        mode = self.get_mode_ui(entity=True)
        entity = currentItem.data(QtCore.Qt.UserRole)
        asset = self.entity_object(mode, entity)
        refs = asset.getRefs()

        if mode == self.asset:
            menu.addSeparator()
            referenceMenu = QtGui.QMenu('Reference', self)
            referenceMenu.triggered.connect(partial(self.create_reference, asset))

            if refs:
                for ref in refs:
                    referenceMenu.addAction(ref)
            else:
                referenceMenu.addAction('No File')

            menu.addMenu(referenceMenu)

    def propit_menu(self, menu):
        mode = self.get_mode_ui(entity=True)

        if mode == self.asset:
            menu.addSeparator()
            menu.addAction('Prop it')


    def show_task_menu(self, pos):
        ''' context menu for download repo '''
        menu = QtGui.QMenu(self)
        currentItem = self.ui.task_listWidget.currentItem()
        data = currentItem.data(QtCore.Qt.UserRole)
        taskEntity = currentItem.data(QtCore.Qt.UserRole)

        if currentItem:
            self.set_status_menu(menu, taskEntity)
            self.set_assign_menu(menu, taskEntity)

            menu.popup(self.ui.task_listWidget.mapToGlobal(pos))
            selMenuItem = menu.exec_(self.ui.task_listWidget.mapToGlobal(pos))

            # self.menu_command('task', data, selMenuItem)

    def show_file_menu(self, pos):
        menu = QtGui.QMenu(self)
        currentItem = self.ui.file_listWidget.currentItem()
        data = currentItem.data(QtCore.Qt.UserRole)

        if currentItem:
            menu.addAction('Open in Explorer')

        menu.popup(self.ui.file_listWidget.mapToGlobal(pos))
        selMenuItem = menu.exec_(self.ui.file_listWidget.mapToGlobal(pos))

        self.menu_command('file', data, selMenuItem)


    def set_status_menu(self, menu, taskEntity):
        setStatusMenu = QtGui.QMenu('Set status', self)
        setStatusMenu.triggered.connect(partial(self.set_task_status, taskEntity))

        for sgIcon in config.sgIconMap.keys():
            iconWidget = QtGui.QIcon()
            iconWidget.addPixmap(QtGui.QPixmap(config.sgIconMap[sgIcon]),QtGui.QIcon.Normal,QtGui.QIcon.Off)
            setStatusMenu.addAction(iconWidget, sgIcon)

        menu.addMenu(setStatusMenu)

    def set_assign_menu(self, menu, taskEntity):
        userMenu = QtGui.QMenu('Assign to', self)
        groupUsers = self.group_user()

        for group in sorted(groupUsers.keys()):
            groupMenu = QtGui.QMenu(group, userMenu)
            users = groupUsers[group]
            groupMenu.triggered.connect(partial(self.assign_user, taskEntity))

            for user in users:
                groupMenu.addAction('%s [%s]' % (user['name'], user['id']))

            userMenu.addMenu(groupMenu)
        menu.addMenu(userMenu)

    def create_reference(self, asset, menuItem):
        referenceFile = str(menuItem.text())
        res = path_info.guess_res(referenceFile)
        refDir = asset.libPath()
        refPath = '%s/%s' % (refDir, referenceFile)

        if res:
            namespace = '%s_%s' % (asset.name, res)
        else:
            # invalid filename
            namespace = asset.name

        if os.path.exists(refPath):
            maya_utils.create_reference(namespace, refPath)

    def set_task_status(self, taskEntity, menuItem):
        status = str(menuItem.text())
        sgStatus = sg_process.set_task_status(taskEntity['id'], status)
        self.set_task_ui()

    def assign_user(self, taskEntity, menuItem):
        name = str(menuItem.text())
        userId = int(name.split('[')[-1].replace(']', ''))
        result = sg_process.assign_task(taskEntity['id'], userId)
        self.set_task_ui()

    def menu_command(self, section, data, menuItem):
        root = self.workspaces[str(self.ui.root_comboBox.currentText())]
        project = str(self.ui.project_comboBox.currentText())
        mode = self.get_mode_ui(entity=True)

        title = str(menuItem.text()) if menuItem else ''

        if section == 'entity':
            entity = data
            asset = self.entity_object(mode, entity)
            shot = self.entity_object(mode, entity)

            if title == 'Open in Explorer':
                entityPath = asset.entityPath(root=root)
                if os.path.exists(entityPath) :
                    entityPath = entityPath.replace('/', '\\')
                    subprocess.Popen(r'explorer /select,"%s"' % entityPath)

            if title == 'Create Directory':
                if mode == self.asset:
                    pipeline_utils.create_asset_template(root, asset.project, asset.type, asset.subtype, asset.name)
                    self.sgAssets = None
                    index = self.ui.entity_listWidget.currentRow()
                    self.set_asset_entity_sgui()
                    self.ui.entity_listWidget.setCurrentRow(index)

                if mode == self.scene:
                    index = self.ui.entity_listWidget.currentRow()
                    pipeline_utils.create_scene_template(root, shot.project, shot.episode, shot.sequence, shot.shotName(fullName=False))
                    self.set_shot_entity_ui()
                    self.ui.entity_listWidget.setCurrentRow(index)

            if title == 'Prop it':
                print 'asset', asset
                propIt_app.show(asset, entity)


        if section == 'task':
            category = menuItem.parentWidget().title() if menuItem else ''
            taskEntity = data
            status = title
            if category == 'Set status':
                sgStatus = sg_process.set_task_status(taskEntity['id'], status)

            self.set_task_ui()

        if section == 'file':
            path = data
            if title == 'Open in Explorer':
                if os.path.exists(path) :
                    path = path.replace('/', '\\')
                    subprocess.Popen(r'explorer /select,"%s"' % path)

    def entity_object(self, mode, entity):
        project = str(self.ui.project_comboBox.currentText())
        if mode == self.asset:
            return path_info.PathInfo(project=project, entity=mode, entitySub1=entity['sg_asset_type'], entitySub2=entity['sg_subtype'], name=entity['code'])
        if mode == self.scene:
            return path_info.PathInfo(project=project, entity=mode, entitySub1=entity['sg_episode']['name'], entitySub2=entity['sg_sequence.Sequence.sg_shortcode'], name=entity['sg_shortcode'])

    # server mode
    def set_sceneEpisode_svui(self):
        projectRoot = self.get_project_root(level=0)
        episodes = file_utils.listFolder(projectRoot)

        # clear ui
        self.ui.ui1_listWidget.clear()
        self.ui.ui2_listWidget.clear()
        self.ui.entity_listWidget.clear()
        self.ui.task_listWidget.clear()
        self.ui.work_comboBox.clear()
        self.ui.file_listWidget.clear()

        if episodes:
            for episode in episodes:
                item = QtGui.QListWidgetItem(self.ui.ui1_listWidget)
                item.setText(episode)
                iconWidget = QtGui.QIcon()
                iconWidget.addPixmap(QtGui.QPixmap(icon.dir),QtGui.QIcon.Normal,QtGui.QIcon.Off)
                item.setIcon(iconWidget)

        shot = path_info.PathInfo()
        if shot.episode in episodes:
            self.ui.ui1_listWidget.setCurrentRow(episodes.index(shot.episode))


    def set_sequence_svui(self):
        projectRoot = self.get_project_root(level=1)
        sequences = file_utils.listFolder(projectRoot)

        # clear ui
        self.ui.ui2_listWidget.clear()
        self.ui.entity_listWidget.clear()
        self.ui.task_listWidget.clear()
        self.ui.work_comboBox.clear()
        self.ui.file_listWidget.clear()

        if sequences:
            for sequence in sequences:
                item = QtGui.QListWidgetItem(self.ui.ui2_listWidget)
                item.setText(sequence)
                iconWidget = QtGui.QIcon()
                iconWidget.addPixmap(QtGui.QPixmap(icon.dir),QtGui.QIcon.Normal,QtGui.QIcon.Off)
                item.setIcon(iconWidget)

        shot = path_info.PathInfo()
        if shot.sequence in sequences:
            self.ui.ui2_listWidget.setCurrentRow(sequences.index(shot.sequence))

    def set_shot_svui(self):
        projectRoot = self.get_project_root(level=2)
        shots = file_utils.listFolder(projectRoot)

        # clear ui
        self.ui.entity_listWidget.clear()
        self.ui.task_listWidget.clear()
        self.ui.work_comboBox.clear()
        self.ui.file_listWidget.clear()

        if shots:
            for shot in shots:
                item = QtGui.QListWidgetItem(self.ui.entity_listWidget)
                item.setText(shot)
                iconWidget = QtGui.QIcon()
                iconWidget.addPixmap(QtGui.QPixmap(icon.dir),QtGui.QIcon.Normal,QtGui.QIcon.Off)
                item.setIcon(iconWidget)

        shot = path_info.PathInfo()
        if shot.name in shots:
            self.ui.entity_listWidget.setCurrentRow(shots.index(shot.name))


    # scene sections
    def set_sceneEpisode_sgui(self):
        project = str(self.ui.project_comboBox.currentText())
        episodes = sg_process.get_episodes(project)
        self.ui.ui1_listWidget.clear()
        self.ui.ui2_listWidget.clear()
        self.ui.entity_listWidget.clear()
        self.ui.task_listWidget.clear()
        shot = path_info.PathInfo()
        index = 0

        for row, episode in enumerate(sorted(episodes)):
            item = QtGui.QListWidgetItem(self.ui.ui1_listWidget)
            item.setText(episode.get('code'))
            item.setData(QtCore.Qt.UserRole, episode)
            if shot.episode == episode.get('code'):
                index = row
        self.ui.ui1_listWidget.setCurrentRow(index)


    def sg_set_sequence_ui(self):
        projectEntity = self.ui.project_comboBox.itemData(self.ui.project_comboBox.currentIndex(), QtCore.Qt.UserRole)
        episodeEntity = self.ui.ui1_listWidget.currentItem().data(QtCore.Qt.UserRole)
        sequences = sg_process.get_sequences(projectEntity, episodeEntity)
        self.ui.ui2_listWidget.clear()
        self.ui.entity_listWidget.clear()
        self.ui.task_listWidget.clear()

        for sequence in sorted(sequences):
            item = QtGui.QListWidgetItem(self.ui.ui2_listWidget)
            item.setText(sequence.get('sg_shortcode'))
            item.setData(QtCore.Qt.UserRole, sequence)

        self.ui.ui2_listWidget.sortItems()

        shot = path_info.PathInfo()
        index = [a for a in range(self.ui.ui2_listWidget.count()) if str(self.ui.ui2_listWidget.item(a).text()) == shot.sequence]
        if index:
            self.ui.ui2_listWidget.setCurrentRow(index[0])

        if projectEntity and episodeEntity:
            shot = path_info.PathInfo(project=projectEntity.get('name'), entity=self.scene, entitySub1=episodeEntity.get('code', ''))
            self.ui.path_lineEdit.setText(path_info.convertRel(shot.entity1Path()))

    def set_shot_entity_ui(self):
        root = self.workspaces[str(self.ui.root_comboBox.currentText())]
        projectEntity = self.ui.project_comboBox.itemData(self.ui.project_comboBox.currentIndex(), QtCore.Qt.UserRole)
        episodeEntity = self.ui.ui1_listWidget.currentItem().data(QtCore.Qt.UserRole)
        sequenceEntity = self.ui.ui2_listWidget.currentItem().data(QtCore.Qt.UserRole)
        shotEntities = sg_process.get_shots(projectEntity, episodeEntity, sequenceEntity)
        self.ui.entity_listWidget.clear()
        self.ui.task_listWidget.clear()


        for shotEntity in sorted(shotEntities):
            shot = path_info.PathInfo(project=projectEntity.get('name'), entity=self.scene, entitySub1=episodeEntity.get('code', ''), entitySub2=sequenceEntity.get('sg_shortcode'), name=shotEntity.get('sg_shortcode'))
            iconPath = icon.nodir
            if os.path.exists(shot.entityPath(root=root)):
                iconPath = icon.dir

            item = QtGui.QListWidgetItem(self.ui.entity_listWidget)
            item.setText(shotEntity.get('sg_shortcode'))
            item.setData(QtCore.Qt.UserRole, shotEntity)

            iconWidget = QtGui.QIcon()
            iconWidget.addPixmap(QtGui.QPixmap(iconPath),QtGui.QIcon.Normal,QtGui.QIcon.Off)
            item.setIcon(iconWidget)

        self.ui.entity_listWidget.sortItems()

        shot = path_info.PathInfo()
        index = [a for a in range(self.ui.entity_listWidget.count()) if str(self.ui.entity_listWidget.item(a).text()) == shot.name]
        if index:
            self.ui.entity_listWidget.setCurrentRow(index[0])

        self.set_path()

    def get_project_root(self, level=0, obj=False, auto=False):
        assetMode, sceneMode = self.get_mode_ui()
        root = str(self.ui.root_lineEdit.text())
        project = str(self.ui.project_comboBox.currentText())
        ui1Item = self.ui.ui1_listWidget.currentItem()
        ui2Item = self.ui.ui2_listWidget.currentItem()
        entityItem = self.ui.entity_listWidget.currentItem()
        taskItem = self.ui.task_listWidget.currentItem()
        workSpace = self.ui.work_comboBox.currentText()
        taskName = ''
        if taskItem:
            taskName = taskItem.data(QtCore.Qt.UserRole).get('content', '')

        if assetMode:
            subDir = self.asset
        if sceneMode:
            subDir = self.scene

        rootProject = '%s/%s/%s' % (root, project, subDir)

        if auto:
            if ui1Item and ui2Item and entityItem and taskItem and workSpace:
                return self.get_project_root(level=5, obj=obj)
            if ui1Item and ui2Item and entityItem and taskItem:
                return self.get_project_root(level=4, obj=obj)
            if ui1Item and ui2Item and entityItem:
                return self.get_project_root(level=3, obj=obj)
            if ui1Item and ui2Item:
                return self.get_project_root(level=2, obj=obj)
            if ui1Item:
                return self.get_project_root(level=1, obj=obj)


        if not auto:

            if level == 0:
                return rootProject
            if level == 1:
                if ui1Item:
                    if not obj:
                        return '%s/%s' % (rootProject, str(ui1Item.text()))

            if level == 2:
                if ui1Item and ui2Item:
                    if not obj:
                        return '%s/%s' % (self.get_project_root(level=1), str(ui2Item.text()))
                    else:
                        asset = path_info.PathInfo(self.get_project_root(level=2))
                        asset.task = taskName
                        return asset

            if level == 3:
                if ui1Item and ui2Item and entityItem:
                    if not obj:
                        return '%s/%s' % (self.get_project_root(level=2), str(entityItem.text()))
                    else:
                        asset = path_info.PathInfo(self.get_project_root(level=3))
                        asset.task = taskName
                        return asset
            if level == 4:
                if ui1Item and ui2Item and entityItem and taskItem:
                    if not taskItem.data(QtCore.Qt.UserRole):
                        task = str(taskItem.text())
                    else:
                        task = config.sgSteps.get(taskItem.data(QtCore.Qt.UserRole)['step']['name'])
                    if not obj:
                        return '%s/%s' % (self.get_project_root(level=3), task)
                    if obj:
                        asset = path_info.PathInfo(self.get_project_root(level=4))
                        asset.task = taskName
                        return asset
            if level == 5:
                if ui1Item and ui2Item and entityItem and taskItem and workSpace:
                    if not obj:
                        return '%s/%s' % (self.get_project_root(level=4), str(workSpace))
                    if obj:
                        asset = path_info.PathInfo(self.get_project_root(level=5))
                        asset.task = taskName
                        return asset


    def get_asset_res(self):
        if self.ui.pr_radioButton.isChecked():
            return 'pr'
        if self.ui.lo_radioButton.isChecked():
            return 'lo'
        if self.ui.md_radioButton.isChecked():
            return 'md'
        if self.ui.hi_radioButton.isChecked():
            return 'hi'

    def filterTask(self, tasks, res):
        newTasks = []
        for task in tasks:
            if res in task.get('content'):
                newTasks.append(task)
            else:
                if not any(a for a in self.allRes if a in task.get('content')):
                    newTasks.append(task)

        return newTasks

    # my task sections
    def set_mytask_step(self):
        steps = sg_process.get_step()
        self.ui.ui1_listWidget.clear()

        for step in steps:
            entityType = step.get('entity_type')
            if entityType == 'Asset':
                if step.get('code') in config.sgSteps.keys():
                    item = QtGui.QListWidgetItem(self.ui.ui1_listWidget)
                    item.setText(config.sgSteps.get(step.get('code')))
                    item.setData(QtCore.Qt.UserRole, step)


    def set_mytask_status(self):
        ''' get task data and list here '''
        step = self.ui.ui1_listWidget.currentItem().data(QtCore.Qt.UserRole)
        self.ui.ui2_listWidget.clear()
        self.ui.ui2_listWidget.addItem('all')
        # sgTaskData = self.get_sg_asset_task(step)

        # for row, status in enumerate(config.sgStatus):
        #     item = QtGui.QListWidgetItem(self.ui.ui2_listWidget)
        #     self.ui.status_comboBox.addItem(status)
        #     iconPath = config.sgIconMap[status]
        #     iconWidget = QtGui.QIcon()
        #     iconWidget.addPixmap(QtGui.QPixmap(iconPath), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        #     self.ui.status_comboBox.setItemIcon(row+1, iconWidget)

    def get_sg_asset_task(self, step):
        sg_process.get_task(entityType, userEntity, projectEntity, episodeEntity, stepEntity)

    def get_all_listWidget_items(self, widget):
        return [widget.item(a) for a in range(widget.count())]
