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
import task_widget
from rftool.utils import file_utils
from rftool.utils import path_info
from rftool.utils import sg_wrapper
from rftool.utils import sg_process
from rftool.utils import icon
from rftool.utils import pipeline_utils
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
        self.ui.addEntity_pushButton.clicked.connect(self.create_entity)

        # checkBox
        self.ui.override_checkBox.stateChanged.connect(self.override_filename)
        self.ui.user_checkBox.stateChanged.connect(self.sgUser_signal)

        # comboBox
        self.ui.project_comboBox.currentIndexChanged.connect(self.project_signal)
        self.ui.step_comboBox.currentIndexChanged.connect(self.step_signal)
        self.ui.root_comboBox.currentIndexChanged.connect(self.root_signal)
        self.ui.work_comboBox.currentIndexChanged.connect(self.work_signal)

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

    def set_scene_ui(self):
        # show / hide ui elements
        self.ui.sub1_label.setText('EPISODE')
        self.ui.sub2_label.setText('SEQUENCE')
        self.ui.entity_label.setText('SHOT')

        # hide filter
        self.ui.filter1_comboBox.setVisible(False)
        self.ui.filter_checkBox.setVisible(False)

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
        if sgMode and not self.sgProjects:
            self.sgProjects = sg_process.get_projects()
            projects = sorted([a['name'] for a in self.sgProjects])

        if projects:
            # disconnect signal
            self.ui.project_comboBox.blockSignals(True)

            # get store value
            storeProject = mc.optionVar(q=self.projectVar)

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
        self.ui.fileName_lineEdit.setEnabled(False)
        self.ui.user_checkBox.setChecked(False)
        self.ui.status_checkBox.setVisible(False)
        self.ui.status_comboBox.setVisible(False)
        self.ui.step_comboBox.setVisible(False)
        self.ui.dept_label.setVisible(False)

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
                    self.set_asset_entity_ui()
                    # self.set_work_files()
            if sceneMode:
                self.set_shot_entity_ui()

    def work_signal(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()

        if sgMode:
            if assetMode:
                if not self.firstStartUI:
                    # self.set_asset_entity_ui(self.asset)
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
                        self.set_asset_entity_ui()

                if sceneMode:
                    self.sg_set_sequence_ui()


    def ui2_signal(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()

        if sgMode:
            if assetMode:
                if not self.firstStartUI:
                    self.set_asset_entity_ui()

            if sceneMode:
                self.set_shot_entity_ui()

    def entity_listWidget_signal(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()

        if sgMode:
            self.set_task_ui()
            if sceneMode:
                self.set_path()

    def task_listWidget_signal(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()

        if sgMode:
            if assetMode:
                self.set_workspace_ui()
            if sceneMode:
                self.set_workspace_ui()
                # self.set_work_files()


    def filter1_signal(self):
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()

        if sgMode:
            if assetMode:
                if not self.firstStartUI:
                    self.set_asset_entity_ui()

    def start_browsing(self):
        ''' start the process of list data on this functions'''
        serverMode, sgMode = self.get_server_sg_ui()
        assetMode, sceneMode = self.get_mode_ui()
        myTaskMode = self.ui.user_checkBox.isChecked()

        # sg mode
        if sgMode:
            if myTaskMode:
                self.set_mytask_step()
                # self.set_mytask_status()
                # self.set_asset_entity_ui()
            else:
                # asset mode
                if assetMode:
                    # find type subtype assets
                    self.set_type_ui()
                    self.set_subtype_ui()
                    self.set_episode_ui()
                    self.set_asset_entity_ui()

                if sceneMode:
                    self.sg_set_episode_ui()

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


    def set_asset_entity_ui(self, selectItem=''):
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
            self.ui.entity_listWidget.setSortingEnabled(True)

            for entityId in filterAssets:
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
            self.ui.entity_listWidget.setCurrentRow(index)

            self.set_path()


    def set_workspace_ui(self, sel=''):
        mode = self.get_mode_ui(entity=True)
        asset = self.combine_path()
        selRoot = str(self.ui.root_comboBox.currentText())
        root = self.workspaces[selRoot]
        path = asset.stepPath(root=root, relativePath=False)
        self.ui.work_comboBox.clear()

        self.ui.fileName_lineEdit.clear()
        workspaces = file_utils.listFolder(path)
        if workspaces:
            self.ui.work_comboBox.addItems(workspaces)
            index = workspaces.index(selRoot) if selRoot in workspaces else 0
            self.ui.work_comboBox.setCurrentIndex(index)

    def set_task_ui(self, sel=''):
        selectedItem = self.ui.entity_listWidget.currentItem()
        if selectedItem:
            if not str(selectedItem.text()) == 'No Item':
                entity = selectedItem.data(QtCore.Qt.UserRole)
                tasks = sg_process.get_tasks(entity)

                self.ui.task_listWidget.clear()
                self.ui.file_listWidget.clear()
                # self.ui.task_listWidget.setSortingEnabled(True)

                for task in sorted(tasks):
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

                    # iconWidget = QtGui.QIcon()
                    # iconWidget.addPixmap(QtGui.QPixmap(taskIcon),QtGui.QIcon.Normal,QtGui.QIcon.Off)
                    # item.setIcon(iconWidget)

                # self.ui.task_listWidget.sortItems()

        self.ui.save_pushButton.setEnabled(False)

    def set_asset_step(self):
        selectedItem = self.ui.task_listWidget.currentItem()
        if selectedItem:
            taskEntity = selectedItem.data(QtCore.Qt.UserRole)
            step = config.sgSteps[taskEntity['step']]
            # indexStep = config.steps.index(step)

    def set_work_files(self):
        ''' work files '''
        projectEntity = self.ui.project_comboBox.itemData(self.ui.project_comboBox.currentIndex(), QtCore.Qt.UserRole)
        mode = self.get_mode_ui(entity=True)
        asset = self.combine_path()
        root = self.workspaces[str(self.ui.root_comboBox.currentText())]
        stepPath = asset.stepPath(root=root, relativePath=False)
        work = str(self.ui.work_comboBox.currentText())
        path = '%s/%s' % (stepPath, work)

        saveFilename = ''

        self.ui.file_listWidget.clear()
        self.ui.file_listWidget.setSortingEnabled(True)
        if os.path.exists(path):
            files = file_utils.listFile(path)

            for eachFile in files:
                item = QtGui.QListWidgetItem(self.ui.file_listWidget)
                item.setText(eachFile)
                item.setData(QtCore.Qt.UserRole, ('%s/%s' % (path, eachFile)))

                iconWidget = QtGui.QIcon()
                iconWidget.addPixmap(QtGui.QPixmap(icon.maya),QtGui.QIcon.Normal,QtGui.QIcon.Off)
                item.setIcon(iconWidget)

            saveFilename = self.get_save_filename(mode, projectEntity, path, asset)

        self.ui.file_listWidget.sortItems(QtCore.Qt.DescendingOrder)
        self.set_path(filename=saveFilename)


    # utils
    def combine_path(self):
        mode = self.get_mode_ui(entity=True)
        project = str(self.ui.project_comboBox.currentText())

        entityItem = self.ui.entity_listWidget.currentItem()
        entity = (entityItem.data(QtCore.Qt.UserRole) if entityItem else {})

        if mode == self.asset:
            entitySub1 = entity.get('sg_asset_type', '')
            entitySub2 = entity.get('sg_subtype', '') if entity.get('sg_subtype') else ''
            name = entity.get('code', '')
        if mode == self.scene:
            entitySub1 = ''
            entitySub2 = ''

            if self.ui.ui1_listWidget.currentItem().data(QtCore.Qt.UserRole):
                entitySub1 = self.ui.ui1_listWidget.currentItem().data(QtCore.Qt.UserRole).get('code')

            if self.ui.ui2_listWidget.currentItem().data(QtCore.Qt.UserRole):
                entitySub2 = self.ui.ui2_listWidget.currentItem().data(QtCore.Qt.UserRole).get('sg_shortcode')

            name = entity.get('sg_shortcode', '')

        taskItem = self.ui.task_listWidget.currentItem()
        taskEntity = (taskItem.data(QtCore.Qt.UserRole) if taskItem else {})

        step = config.sgSteps.get(taskEntity.get('step', {}).get('name'), 'None')
        asset = path_info.PathInfo(project=project, entity=mode, entitySub1=entitySub1, entitySub2=entitySub2, name=name, step=step)

        return asset

    def get_save_filename(self, mode, project, path, asset):
        projectCode = project.get('sg_project_code', '')
        version = file_utils.find_next_version(file_utils.listFile(path))
        nameElems = []
        if projectCode:
            nameElems.append(projectCode)
        if mode == self.asset:
            nameElems.append(asset.assetName(step=True))
        if mode == self.scene:
            nameElems.append(asset.shotName(step=True))
        nameElems.append(version)
        nameElems.append(mc.optionVar(q=config.localUser))
        filename = '%s.ma' % ('_').join(nameElems)
        return os.path.basename(file_utils.increment_version('%s/%s' % (path, filename)))


    def set_path(self, filename=''):

        asset = self.combine_path()
        root = self.workspaces[str(self.ui.root_comboBox.currentText())]
        path = asset.stepPath(root=root, relativePath=True)

        if filename:
            self.ui.fileName_lineEdit.setText(filename)

        workspace = str(self.ui.root_comboBox.currentText())
        self.ui.path_lineEdit.setText(path)

        self.ui.save_pushButton.setEnabled(False)
        if os.path.exists(path_info.PathInfo(path).absPath):
            self.ui.save_pushButton.setEnabled(True)

    # file commands

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
        root = self.workspaces[str(self.ui.root_comboBox.currentText())]
        path = str(self.ui.path_lineEdit.text())
        asset = path_info.PathInfo(path)
        absPath = asset.absPath
        workspace = str(self.ui.work_comboBox.currentText())
        filename = str(self.ui.fileName_lineEdit.text())
        saveFile = '%s/%s/%s' % (absPath, workspace, filename)

        mc.file(rename=saveFile)
        result = mc.file(save=True, type='mayaAscii')
        self.set_work_files()

        return result

    def create_entity(self):
        assetMode, sceneMode = self.get_mode_ui()
        root = self.workspaces[str(self.ui.root_comboBox.currentText())]

        entityName = str(self.ui.entity_lineEdit.text())
        entitySub1 = self.ui.ui1_listWidget.currentItem()
        entitySub1 = str(entitySub1.text()) if entitySub1 else ''
        entitySub1 = entitySub1 if not entitySub1 == 'all' else ''
        entitySub2 = self.ui.ui2_listWidget.currentItem()
        entitySub2 = str(entitySub2.text()) if entitySub2 else ''
        entitySub2 = entitySub2 if not entitySub2 == 'all' else ''

        projectEntity = self.ui.project_comboBox.itemData(self.ui.project_comboBox.currentIndex(), QtCore.Qt.UserRole)
        episodeEntity = None
        if self.ui.filter_checkBox.isChecked():
            episodeEntity = self.ui.filter1_comboBox.itemData(self.ui.filter1_comboBox.currentIndex(), QtCore.Qt.UserRole)

        if entitySub1 and entitySub2 and entityName:
            if assetMode:
                # check if not asset in Shotgun
                if not entityName in [a['code'] for a in self.sgAssets]:
                    title = 'Confirm'
                    message = 'Create asset "%s" under type %s, subtype %s?' % (entityName, entitySub1, entitySub2)
                    result = QtGui.QMessageBox.question(self, title, message, QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)

                    if result == QtGui.QMessageBox.Ok:
                        sgResult = sg_process.create_asset(project=projectEntity, assetType=entitySub1, assetSubType=entitySub2, assetName=entityName, episode=episodeEntity, template='default')
                        if sgResult:
                            dirResult = pipeline_utils.create_asset_template(root, projectEntity['name'], entitySub1, entitySub2, entityName)

                        self.sgAssets = None
                        self.set_asset_entity_ui(selectItem=entityName)
                        self.ui.entity_lineEdit.setText('')
                else:
                    QtGui.QMessageBox.warning(self, 'Warning', '%s already exists in Shotgun' % entityName)

        else:
            title = 'Error'
            message = 'Name cannot be empty. Type and Subtype cannot be "all"'
            QtGui.QMessageBox.warning(self, title, message, QtGui.QMessageBox.Ok)

    # show menu
    def show_entity_menu(self, pos):
        ''' context menu for download repo '''
        menu = QtGui.QMenu(self)
        currentItem = self.ui.entity_listWidget.currentItem()
        data = currentItem.data(QtCore.Qt.UserRole)

        if currentItem:
            menu.addAction('Open in Explorer')
            menu.addAction('Create Directory')

            menu.popup(self.ui.entity_listWidget.mapToGlobal(pos))
            selMenuItem = menu.exec_(self.ui.entity_listWidget.mapToGlobal(pos))

            self.menu_command('entity', data, selMenuItem)

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

        title = str(menuItem.text()) if menuItem else ''

        if section == 'entity':
            entity = data
            asset = self.asset_object(entity)
            if title == 'Open in Explorer':
                entityPath = asset.entityPath(root=root)
                if os.path.exists(entityPath) :
                    entityPath = entityPath.replace('/', '\\')
                    subprocess.Popen(r'explorer /select,"%s"' % entityPath)

            if title == 'Create Directory':
                pipeline_utils.create_asset_template(root, asset.project, asset.type, asset.subtype, asset.name)
                self.sgAssets = None
                index = self.ui.entity_listWidget.currentIndex()
                self.set_asset_entity_ui()
                self.ui.entity_listWidget.setCurrentIndex(index)

        if section == 'task':
            category = menuItem.parentWidget().title() if menuItem else ''
            taskEntity = data
            status = title
            if category == 'Set status':
                sgStatus = sg_process.set_task_status(taskEntity['id'], status)

            self.set_task_ui()

        if section == 'file':
            path = item.data(QtCore.Qt.UserRole)
            if title == 'Open in Explorer':
                if os.path.exists(path) :
                    path = path.replace('/', '\\')
                    subprocess.Popen(r'explorer /select,"%s"' % path)

    def asset_object(self, entity):
        project = str(self.ui.project_comboBox.currentText())
        mode = self.asset
        return path_info.PathInfo(project=project, entity=mode, entitySub1=entity['sg_asset_type'], entitySub2=entity['sg_subtype'], name=entity['code'])

    # scene sections
    def sg_set_episode_ui(self):
        project = str(self.ui.project_comboBox.currentText())
        episodes = sg_process.get_episodes(project)
        self.ui.ui1_listWidget.clear()
        self.ui.ui2_listWidget.clear()
        self.ui.entity_listWidget.clear()
        self.ui.task_listWidget.clear()

        for episode in sorted(episodes):
            item = QtGui.QListWidgetItem(self.ui.ui1_listWidget)
            item.setText(episode.get('code'))
            item.setData(QtCore.Qt.UserRole, episode)

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
            print shot.entityPath(root=root)
            iconPath = icon.nodir
            if os.path.exists(shot.entityPath(root=root)):
                iconPath = icon.dir

            item = QtGui.QListWidgetItem(self.ui.entity_listWidget)
            item.setText(shotEntity.get('sg_shortcode'))
            item.setData(QtCore.Qt.UserRole, shotEntity)

            iconWidget = QtGui.QIcon()
            iconWidget.addPixmap(QtGui.QPixmap(iconPath),QtGui.QIcon.Normal,QtGui.QIcon.Off)
            item.setIcon(iconWidget)

        self.set_path()

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
