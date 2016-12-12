#Import python modules
import sys, os, re, shutil, random

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
from rftool.utils import file_utils
from rftool.utils import path_info
from rftool.utils import sg_wrapper
from rftool.utils import sg_process
from startup import config
from rftool.utils.userCheck import user_app

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

        # start ui
        self.firstStartUI = True

        # optionVar
        self.projectVar = config.projectVar
        self.modeVar = config.modeVar
        self.serverVar = config.serverVar

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
        self.apply_setting()
        # self.start_ui()

    def init_signals(self):
        # mode signals
        self.ui.asset_radioButton.toggled.connect(self.set_entity_mode)
        self.ui.server_radioButton.toggled.connect(self.set_server_sg)

        # push button
        self.ui.open_pushButton.clicked.connect(self.open_file)
        self.ui.save_pushButton.clicked.connect(self.save_file)

        # comboBox
        self.ui.project_comboBox.currentIndexChanged.connect(self.project_signal)
        self.ui.step_comboBox.currentIndexChanged.connect(self.step_signal)
        self.ui.work_comboBox.currentIndexChanged.connect(self.work_signal)

        # listWidget
        self.ui.ui1_listWidget.itemSelectionChanged.connect(self.ui1_signal)
        self.ui.ui2_listWidget.itemSelectionChanged.connect(self.ui2_signal)
        self.ui.entity_listWidget.itemSelectionChanged.connect(self.entity_listWidget_signal)
        self.ui.task_listWidget.itemSelectionChanged.connect(self.task_listWidget_signal)

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

        # start browsing
        self.set_ui()

    def set_ui(self):
        self.set_project_ui()
        self.set_step_ui()
        self.set_user_ui()
        self.set_status_ui()
        self.set_default_button()

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

    def set_scene_ui(self):
        # show / hide ui elements
        self.ui.sub1_label.setText('EPISODE')
        self.ui.sub2_label.setText('SEQUENCE')
        self.ui.entity_label.setText('SHOT')

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
                self.check_user('check')


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
        if sgMode and not self.sgProjects:
            self.sgProjects = sg_wrapper.get_projects()
            projects = sorted([a['name'] for a in self.sgProjects])

        # disconnect signal
        self.ui.project_comboBox.blockSignals(True)

        # add items
        self.ui.project_comboBox.clear()
        self.ui.project_comboBox.addItems(projects)

        # reconnect signal
        self.ui.project_comboBox.blockSignals(False)

        # set last selected project, then signal from project will browse assets
        index = projects.index(mc.optionVar(q=self.projectVar)) if mc.optionVar(q=self.projectVar) in projects else 0
        self.ui.project_comboBox.setCurrentIndex(index)

        # signal won't work if index == 0, force browse manually
        if index == 0:
            self.browse_asset()

    def set_step_ui(self):
        ''' set department comboBox '''
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
        self.ui.status_comboBox.addItems(config.sgStatus)

    def set_workspaces_ui(self):
        self.ui.work_comboBox.clear()
        self.ui.work_comboBox.addItems(self.workspaces.keys())

    def set_default_button(self):
        self.ui.save_pushButton.setEnabled(False)


    # signals
    def project_signal(self):
        project = str(self.ui.project_comboBox.currentText())
        mc.optionVar(sv=(self.projectVar, project))

        # clear cache
        self.sgAssets = None
        self.browse_asset()

    def step_signal(self):
        step = str(self.ui.step_comboBox.currentText())
        mc.optionVar(sv=(config.stepVar, step))

    def work_signal(self, index):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()
        # set root
        # rootPath = os.environ.get(self.workspaces[self.workspaces.keys()[index]], 'Not found')
        # self.ui.root_lineEdit.setText(rootPath)

        if sgMode:
            if assetMode:
                if not self.firstStartUI:
                    self.set_work_files()

    def ui1_signal(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()

        if sgMode:
            if assetMode:
                if not self.firstStartUI:
                    self.set_entity_ui(self.asset)


    def ui2_signal(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()

        if sgMode:
            if assetMode:
                if not self.firstStartUI:
                    self.set_entity_ui(self.asset)

    def entity_listWidget_signal(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()

        if sgMode:
            if assetMode:
                self.set_asset_task()

    def task_listWidget_signal(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()

        if sgMode:
            if assetMode:
                self.set_work_files()


    def filter1_signal(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()

        if sgMode:
            if assetMode:
                if not self.firstStartUI:
                    self.set_entity_ui(self.asset)

    def browse_asset(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()

        # sg mode
        if sgMode:
            # asset mode
            if assetMode:
                # find type subtype assets
                self.set_type_ui()
                self.set_subtype_ui()
                self.set_episode_ui()
                self.set_workspaces_ui()
                self.set_entity_ui(self.asset)
                self.firstStartUI = False


    def set_type_ui(self, selectItem=''):
        if not self.sgType:
            self.sgType = sorted(sg_process.get_type())
        index = self.sgType.index(selectItem) if selectItem in self.sgType else 0
        self.ui.ui1_listWidget.clear()
        self.ui.ui1_listWidget.addItem('all')
        self.ui.ui1_listWidget.addItems(self.sgType)
        self.ui.ui1_listWidget.setCurrentRow(index)


    def set_subtype_ui(self, selectItem=''):
        if not self.sgSubType:
            self.sgSubType = sorted(sg_process.get_subtype())
        index = self.sgSubType.index(selectItem) if selectItem in self.sgSubType else 0
        self.ui.ui2_listWidget.clear()
        self.ui.ui2_listWidget.addItem('all')
        self.ui.ui2_listWidget.addItems(self.sgSubType)
        self.ui.ui2_listWidget.setCurrentRow(index)

    def set_episode_ui(self, selectItem=''):
        project = str(self.ui.project_comboBox.currentText())
        sgEpisodes = sg_process.get_episodes(project)
        episodes = sorted([a['code'] for a in sgEpisodes])
        self.ui.filter1_comboBox.clear()

        for row, ep in enumerate(sgEpisodes):
            self.ui.filter1_comboBox.addItem(ep['code'])
            self.ui.filter1_comboBox.setItemData(row, ep, QtCore.Qt.UserRole)


    def set_entity_ui(self, mode, selectItem=''):
        # get ui selection
        project = str(self.ui.project_comboBox.currentText())
        assetTypes = [str(a.text()) for a in self.ui.ui1_listWidget.selectedItems()]
        subTypes = [str(a.text()) for a in self.ui.ui2_listWidget.selectedItems()]
        episodes = [self.ui.filter1_comboBox.itemData(self.ui.filter1_comboBox.currentIndex(), QtCore.Qt.UserRole)]

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
        self.ui.entity_listWidget.addItem('No Item')


        if filterAssets:
            # convert data to asset
            assetLists = sorted([sgAssetDict[a]['code'] for a in filterAssets])
            self.ui.entity_listWidget.clear()

            for entityId in filterAssets:
                item = QtGui.QListWidgetItem(self.ui.entity_listWidget)
                item.setText(sgAssetDict[entityId]['code'])
                item.setData(QtCore.Qt.UserRole, sgAssetDict[entityId])

            index = assetLists.index(selectItem) if selectItem in assetLists else 0
            self.ui.entity_listWidget.setCurrentRow(index)

            self.set_path()

    def set_asset_task(self):
        selectedItem = self.ui.entity_listWidget.currentItem()
        if selectedItem:
            if not str(selectedItem.text()) == 'No Item':
                entity = selectedItem.data(QtCore.Qt.UserRole)
                tasks = sg_process.get_tasks(entity)

                self.ui.task_listWidget.clear()
                self.ui.task_listWidget.setSortingEnabled(True)

                for task in tasks:
                    item = QtGui.QListWidgetItem(self.ui.task_listWidget)
                    item.setText('%s - %s - %s' % (task['content'], task['sg_status_list'], task['task_assignees']))
                    item.setData(QtCore.Qt.UserRole, task)

                self.ui.task_listWidget.sortItems()

    def set_asset_step(self):
        selectedItem = self.ui.task_listWidget.currentItem()
        if selectedItem:
            taskEntity = selectedItem.data(QtCore.Qt.UserRole)
            step = config.sgSteps[taskEntity['step']]
            # indexStep = config.steps.index(step)

    def set_work_files(self):
        ''' work files '''
        mode = self.get_mode_ui(entity=True)
        asset = self.combine_path()
        root = self.workspaces[str(self.ui.work_comboBox.currentText())]
        path = asset.workspacePath(root=root, relativePath=False)

        saveFilename = ''

        self.ui.file_listWidget.clear()
        self.ui.file_listWidget.setSortingEnabled(True)
        if os.path.exists(path):
            files = file_utils.listFile(path)

            for eachFile in files:
                item = QtGui.QListWidgetItem(self.ui.file_listWidget)
                item.setText(eachFile)
                item.setData(QtCore.Qt.UserRole, ('%s/%s' % (path, eachFile)))

            saveFilename = self.get_save_filename(path, asset)

        self.ui.file_listWidget.sortItems(QtCore.Qt.DescendingOrder)
        self.set_path(filename=saveFilename)


    def combine_path(self):
        mode = self.get_mode_ui(entity=True)
        project = str(self.ui.project_comboBox.currentText())

        entityItem = self.ui.entity_listWidget.currentItem()
        entity = (entityItem.data(QtCore.Qt.UserRole) if entityItem else {})
        assetType = entity.get('sg_asset_type', '')
        assetSubType = entity.get('sg_subtype', '')
        name = entity.get('code', '')

        taskItem = self.ui.task_listWidget.currentItem()
        taskEntity = (taskItem.data(QtCore.Qt.UserRole) if taskItem else {})

        step = config.sgSteps.get(taskEntity.get('step', {}).get('name'), '')
        print project
        print mode
        print assetType
        print assetSubType
        print name
        print step

        asset = path_info.PathInfo(project=project, entity=mode, entitySub1=assetType, entitySub2=assetSubType, name=name, step=step)

        return asset

    def get_save_filename(self, path, asset):
        filename = '{0}_v001_{1}.ma'.format(asset.assetName(step=True), mc.optionVar(q=config.localUser))
        return os.path.basename(file_utils.increment_version('%s/%s' % (path, filename)))


    def set_path(self, filename=''):

        asset = self.combine_path()
        root = self.workspaces[str(self.ui.work_comboBox.currentText())]
        path = asset.workspacePath(root=root, relativePath=True)

        if filename:
            self.ui.fileName_lineEdit.setText(filename)

        workspace = str(self.ui.work_comboBox.currentText())
        self.ui.root_lineEdit.setText(path)

        self.ui.save_pushButton.setEnabled(False)
        if os.path.exists(path_info.PathInfo(path).absPath):
            self.ui.save_pushButton.setEnabled(True)


    def open_file(self):
        ''' open maya file '''
        selItem = self.ui.file_listWidget.currentItem()
        path = selItem.data(QtCore.Qt.UserRole)
        if mc.file(q=True, modified=True):
            result = QtGui.QMessageBox.question(self, 'Warning', 'Scene has changed since last save. Do you want to open?', QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)
            if result == QtGui.QMessageBox.Ok:
                return mc.file(path, o=True, f=True)

        return mc.file(path, o=True, f=True)

    def save_file(self):
        root = self.workspaces[str(self.ui.work_comboBox.currentText())]
        path = str(self.ui.root_lineEdit.text())
        asset = path_info.PathInfo(path)
        absPath = asset.absPath
        filename = str(self.ui.fileName_lineEdit.text())
        saveFile = '%s/%s' % (absPath, filename)

        mc.file(rename=saveFile)
        result = mc.file(save=True, type='mayaAscii')
        self.set_work_files()

        return result
