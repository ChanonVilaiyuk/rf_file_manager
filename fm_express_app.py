# v.0.0.1 first version

#Import python modules
import sys, os, re, shutil
import getpass
import subprocess
import logging


#Import GUI
from Qt import QtCore
from Qt import QtWidgets
from Qt import QtGui

from Qt import wrapInstance
from Qt import _QtUiTools

from functools import partial

#Import maya commands
try: 
    import maya.cmds as mc
    import maya.mel as mm
    isMaya = True

except ImportError: 
    isMaya = False

# import ui
from rftool.utils import log_utils
logFile = log_utils.name('fileManager_express', user=getpass.getuser())
logger = log_utils.init_logger(logFile)
logger.setLevel(logging.INFO)

import fm_dialog
import task_widget
import fm_utils
from rftool.utils import file_utils
from rftool.utils.ui import load
from rftool.utils import path_info
from rftool.utils import icon
from rftool.utils import pipeline_utils
from rftool.utils import maya_utils
from rftool.utils import asm_utils
from startup import config
from rftool.prop_it import propIt_app

moduleDir = os.path.dirname(sys.modules[__name__].__file__)


# If inside Maya open Maya GUI
def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QtWidgets.QWidget)
    # return sip.wrapinstance(long(ptr), QObject)

import maya.OpenMayaUI as mui

def show():
    uiName = 'SGFileManagerExpressUI'
    deleteUI(uiName)
    myApp = SGFileManagerExpress(getMayaWindow())
    # myApp.ui.show()
    return myApp

def deleteUI(ui):
    if mc.window(ui, exists=True):
        mc.deleteUI(ui)
        deleteUI(ui)


class SGFileManagerExpress(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        self.count = 0
        #Setup Window
        super(SGFileManagerExpress, self).__init__(parent)
        # self.ui = ui.Ui_SGFileManagerUI()
        uiFile = '%s/ui2.ui' % moduleDir
        self.ui = load.loadUI(uiFile, self)
        self.ui.show()
        self.ui.setWindowTitle('Auto Naming Express v.0.0.1 ui')

        # string var
        self.pathSep = '/'
        self.fileSep = '_'

        # cache 
        self.projectCode = dict()
        self.defaultWorkspace = 'maya/work'
        self.entityCache = dict()

        # root var
        self.rootWork = os.environ[config.RFPROJECT]
        self.rootPubl = os.environ[config.RFPUBL]
        self.rootProd = os.environ[config.RFPROD]
        self.workspaces = {'work': self.rootWork, 'publish': self.rootPubl}
        self.asset = config.asset
        self.scene = config.scene

        # workfile extension
        self.ext = '.ma'

        # entity var
        self.entity = path_info.PathInfo()
        self.res = 'md'

        self.init_pre_signals()
        self.init_functions()
        self.init_post_signals()


    def init_functions(self): 
        self.set_user()
        self.set_root_ui()
        self.set_project()
        self.apply_setting()
        self.set_label()
        self.set_default_ui()
        self.start_browsing()


    def init_pre_signals(self): 
        self.ui.ui1_listWidget.currentItemChanged.connect(self.ui1_trigger)
        self.ui.ui2_listWidget.currentItemChanged.connect(self.ui2_trigger)
        self.ui.entity_listWidget.currentItemChanged.connect(self.entity_trigger)
        self.ui.task_listWidget.currentItemChanged.connect(self.step_trigger)


    def init_post_signals(self): 
        # button 
        self.ui.user_pushButton.clicked.connect(self.user_setting)
        self.ui.open_pushButton.clicked.connect(self.open_action)
        self.ui.save_pushButton.clicked.connect(self.save_action)

        # comboBox
        self.ui.root_comboBox.currentIndexChanged.connect(self.root_trigger)
        self.ui.project_comboBox.currentIndexChanged.connect(self.project_trigger)
        self.ui.work_comboBox.currentIndexChanged.connect(self.work_trigger)

        # radioButton
        self.ui.asset_radioButton.clicked.connect(partial(self.mode_trigger, self.asset))
        self.ui.scene_radioButton.clicked.connect(partial(self.mode_trigger, self.scene))

        self.ui.pr_radioButton.clicked.connect(partial(self.res_trigger, 'pr'))
        self.ui.lo_radioButton.clicked.connect(partial(self.res_trigger, 'lo'))
        self.ui.md_radioButton.clicked.connect(partial(self.res_trigger, 'md'))
        self.ui.hi_radioButton.clicked.connect(partial(self.res_trigger, 'hi'))

        # checkBox
        self.ui.resFilter_checkBox.stateChanged.connect(self.work_trigger)
        self.ui.override_checkBox.stateChanged.connect(self.override_filename)

        # context menu
        self.ui.ui1_listWidget.customContextMenuRequested.connect(partial(self.show_context_menu, self.ui.ui1_listWidget, 'ui1'))
        self.ui.ui2_listWidget.customContextMenuRequested.connect(partial(self.show_context_menu, self.ui.ui2_listWidget, 'ui2'))
        self.ui.entity_listWidget.customContextMenuRequested.connect(partial(self.show_context_menu, self.ui.entity_listWidget, 'entity'))
        self.ui.task_listWidget.customContextMenuRequested.connect(partial(self.show_context_menu, self.ui.task_listWidget, 'step'))
        self.ui.file_listWidget.customContextMenuRequested.connect(partial(self.show_context_menu, self.ui.file_listWidget, 'file'))


    def user_setting(self): 
        """ user setting dialog """ 
        user, ok = QtWidgets.QInputDialog.getText(self, 'Input User', 'Enter your name :')

        if user: 
            mc.optionVar(sv=(config.localUser, user))
            self.set_user()
        else: 
            self.user_setting()


    def set_user(self): 
        """ add user to ui """ 
        user = get_user()

        if user in [0, '', '0']: 
            self.user_setting()
        else: 
            self.ui.localUser_comboBox.clear()
            self.ui.localUser_comboBox.addItem(user)

    # browse ui 
    def set_root_ui(self): 
        self.ui.root_comboBox.clear()
        self.ui.root_comboBox.addItems(self.workspaces.keys())
        self.ui.root_lineEdit.setText(self.rootWork)

    def root_trigger(self): 
        logger.info('root_trigger')
        root = str(self.ui.root_comboBox.currentText())
        path = self.workspaces.get(root)
        self.ui.root_lineEdit.setText(path)

        self.start_browsing()


    def project_trigger(self): 
        """ project comboBox trigger """ 
        logger.info('project_trigger')
        project = str(self.ui.project_comboBox.currentText())
        mc.optionVar(sv=(config.projectVar, project))
        self.start_browsing()

    def set_project(self): 
        """ list projects and set to ui """ 
        projects = fm_utils.get_projects(self.rootWork) 
        self.ui.project_comboBox.clear()
        self.ui.project_comboBox.addItems(projects)
        lastSelected = mc.optionVar(q=config.projectVar)

        if lastSelected in projects: 
            self.ui.project_comboBox.setCurrentIndex(projects.index(lastSelected))


    def apply_setting(self): 
        # read mode 
        mode = mc.optionVar(q=config.modeVar)
        if mode == self.asset: 
            self.ui.asset_radioButton.setChecked(True)
            self.mode = self.asset 
        if mode == self.scene: 
            self.ui.scene_radioButton.setChecked(True)
            self.mode = self.scene 


    def mode_trigger(self, mode): 
        """ save setting and start browsing """ 
        mc.optionVar(sv=(config.modeVar, mode))
        self.mode = mode 
        self.start_browsing()
        self.set_label()


    def res_trigger(self, res): 
        """ res radioButton presed """ 
        self.res = res 
        self.work_trigger()
        self.set_filename()

    def set_res(self, res): 
        """ set res from file """ 
        logger.info('set_res')

        if res == 'pr': 
            self.ui.pr_radioButton.blockSignals(True)
            self.ui.pr_radioButton.setChecked(True)
            self.ui.pr_radioButton.blockSignals(False)
        if res == 'lo': 
            self.ui.lo_radioButton.blockSignals(True)
            self.ui.lo_radioButton.setChecked(True)
            self.ui.lo_radioButton.blockSignals(False)
        if res == 'md': 
            self.ui.md_radioButton.blockSignals(True)
            self.ui.md_radioButton.setChecked(True)
            self.ui.md_radioButton.blockSignals(False)
        if res == 'hi': 
            self.ui.hi_radioButton.blockSignals(True)
            self.ui.hi_radioButton.setChecked(True)
            self.ui.hi_radioButton.blockSignals(False)


    def set_label(self): 
        # set labels 
        if self.mode == self.asset: 
            self.ui.sub1_label.setText('TYPE')
            self.ui.sub2_label.setText('SUBTYPE')
            self.ui.entity_label.setText('ASSET NAME')
            self.ui.task_label.setText('DEPARTMENT')
            self.ui.resolution_frame.setVisible(True)

        if self.mode == self.scene: 
            self.ui.sub1_label.setText('EPISODE')
            self.ui.sub2_label.setText('SEQUENCE')
            self.ui.entity_label.setText('SHOT')
            self.ui.task_label.setText('DEPARTMENT')
            self.ui.resolution_frame.setVisible(False)

    def set_default_ui(self): 
        """ set default state of ui """ 
        self.ui.fileName_lineEdit.setEnabled(False)
        self.ui.root_lineEdit.setEnabled(False)


    def start_browsing(self): 
        """ refresh here """ 
        logger.info('start browsing')
        root = str(self.ui.root_lineEdit.text())
        project = str(self.ui.project_comboBox.currentText())
        mode = self.mode
        print 'mode', mode

        if self.mode == self.asset: 
            select = self.entity.type
        if self.mode == self.scene: 
            select = self.entity.episode

        ui1Path = self.pathSep.join([root, project, mode])
        self.clear_ui(ui2=True, entity=True, step=True, space=True, workfile=True, path=True, fileName=True)
        self.browse_ui(self.ui.ui1_listWidget, icon.dir, ui1Path, select)


    def ui1_trigger(self): 
        """ type or episode trigger  """ 
        logger.info('ui1_trigger')
        selItem = self.ui.ui1_listWidget.currentItem()

        if self.mode == self.asset: 
            select = self.entity.subtype
        if self.mode == self.scene: 
            select = self.entity.sequence
        if selItem: 
            currentPath = selItem.data(QtCore.Qt.UserRole).get('path')

            # browse subtype or episode
            self.clear_ui(entity=True, step=True, space=True, workfile=True)
            self.browse_ui(self.ui.ui2_listWidget, icon.dir, currentPath, select)
            self.set_path()


    def ui2_trigger(self): 
        """ subtype or sequence trigger  """ 
        logger.info('ui2_trigger')
        selItem = self.ui.ui2_listWidget.currentItem()
        select = self.entity.name

        if selItem: 
            currentPath = selItem.data(QtCore.Qt.UserRole).get('path')
            
            # browse entity 
            self.clear_ui(step=True, space=True, workfile=True)
            self.browse_ui(self.ui.entity_listWidget, icon.dir, currentPath, select)
            self.set_path()


    def entity_trigger(self): 
        """ entity trigger  """ 
        logger.info('entity_trigger')
        selItem = self.ui.entity_listWidget.currentItem()
        select = self.entity.step

        if selItem: 
            currentPath = selItem.data(QtCore.Qt.UserRole).get('path')
            
            # browse entity 
            self.clear_ui(space=True, workfile=True, fileName=True)
            self.browse_ui(self.ui.task_listWidget, icon.dir, currentPath, select)
            self.set_path()


    def step_trigger(self): 
        """ step trigger  """ 
        logger.info('step_trigger')
        selItem = self.ui.task_listWidget.currentItem()
        select = self.entity.step

        fileRes = path_info.guess_res(self.entity.filename)
        self.set_res(fileRes)

        if selItem: 
            itemData = selItem.data(QtCore.Qt.UserRole)
            
            if itemData: 
                currentPath = itemData.get('path')
                # browse workspace 
                self.browse_workspace(currentPath)
                self.set_path()
                self.set_filename()


    def work_trigger(self): 
        """ work trigger """ 
        logger.info('work_trigger')
        currentText = self.ui.work_comboBox.count()
        itemData = self.ui.work_comboBox.itemData(self.ui.work_comboBox.currentIndex(), QtCore.Qt.UserRole)

        if itemData: 
            path = itemData.get('path')
            self.browse_workfiles(path)


    def browse_ui(self, widget, iconPath, path, defaultSelection=None): 
        """ browse any thing """ 
        # logger.info('browse %s' % path)
        uiDirs = file_utils.listFolder(path)
        widget.clear()

        # icons 
        iconWidget = QtGui.QIcon()
        iconWidget.addPixmap(QtGui.QPixmap(iconPath),QtGui.QIcon.Normal,QtGui.QIcon.Off)

        for each in uiDirs: 
            item = QtWidgets.QListWidgetItem(widget)
            item.setText(each)

            # add this path to data 
            currentPath = self.pathSep.join([path, each])
            item.setIcon(iconWidget)
            item.setData(QtCore.Qt.UserRole, {'path': currentPath})

        if defaultSelection in uiDirs: 
            widget.setCurrentRow(uiDirs.index(defaultSelection))


    def browse_workspace(self, path): 
        """ browse workspace """ 
        logger.info('browse workspaces')
        self.ui.work_comboBox.blockSignals(True)
        self.ui.work_comboBox.clear()

        apps = file_utils.listFolder(path)
        spaces = []

        for app in apps: 
            workspaces = file_utils.listFolder(self.pathSep.join([path, app]))

            for workspace in workspaces: 
                spaces.append(self.pathSep.join([app, workspace]))

        spaces.append('/')

        for row, space in enumerate(spaces): 
            currentPath = self.pathSep.join([path, space])
            self.ui.work_comboBox.addItem(space)
            self.ui.work_comboBox.setItemData(row, {'path': currentPath}, QtCore.Qt.UserRole)

        select = self.defaultWorkspace

        if self.entity.application and self.entity.workspace: 
            select = self.pathSep.join([self.entity.application, self.entity.workspace])

        if select in spaces: 
            self.ui.work_comboBox.setCurrentIndex(spaces.index(select))

        self.work_trigger()
        self.ui.work_comboBox.blockSignals(False)


    def browse_workfiles(self, path): 
        """ browse work files """ 
        logger.info('browse_workfiles')
        files = file_utils.listFile(path)
        self.ui.file_listWidget.clear()

        # set file filters 
        if self.mode == self.asset: 
            if not self.ui.resFilter_checkBox.isChecked(): 
                files = [a for a in files if path_info.guess_res(a) == self.res]

        # icons 
        iconWidget = QtGui.QIcon()
        iconWidget.addPixmap(QtGui.QPixmap(icon.maya),QtGui.QIcon.Normal,QtGui.QIcon.Off)

        for each in files: 
            item = QtWidgets.QListWidgetItem(self.ui.file_listWidget)
            item.setText(each)

            # add this path to data 
            currentPath = self.pathSep.join([path, each])
            item.setIcon(iconWidget)
            item.setData(QtCore.Qt.UserRole, {'path': currentPath})

        self.ui.file_listWidget.sortItems(QtCore.Qt.DescendingOrder)

    def set_path(self): 
        """ set path display """ 
        root = str(self.ui.root_lineEdit.text())
        project = str(self.ui.project_comboBox.currentText())
        subItem1 = self.ui.ui1_listWidget.currentItem()
        subItem2 = self.ui.ui2_listWidget.currentItem()
        entityItem = self.ui.entity_listWidget.currentItem()
        stepItem = self.ui.task_listWidget.currentItem()

        pathList = []
        pathList.append(root)
        pathList.append(project)
        pathList.append(self.mode)

        if subItem1: 
            pathList.append(str(subItem1.text()))
        if subItem2: 
            pathList.append(str(subItem2.text()))
        if entityItem: 
            pathList.append(str(entityItem.text()))
        if stepItem: 
            pathList.append(str(stepItem.text()))

        combinePath = path_info.convertRel(self.pathSep.join(pathList))
        self.ui.path_lineEdit.setText(combinePath)

        return combinePath

    def set_filename(self): 
        fileElem = []
        project = str(self.ui.project_comboBox.currentText())
        subItem1 = self.ui.ui1_listWidget.currentItem()
        subItem2 = self.ui.ui2_listWidget.currentItem()
        entityItem = self.ui.entity_listWidget.currentItem()
        stepItem = self.ui.task_listWidget.currentItem()
        user = str(self.ui.localUser_comboBox.currentText())

        if subItem1 and subItem2 and entityItem and stepItem: 
            entity = self.get_entity_object()
        
            if self.mode == self.asset: 
                entityItem = self.ui.entity_listWidget.currentItem()
                res = self.res

                fileBaseName = self.fileSep.join([entity.assetName(step=True), res])


            if self.mode == self.scene: 
                projectCode = self.projectCode.get(project)

                if not projectCode: 
                    projectCode = entity.projectCode
                    self.projectCode.update({project: projectCode})

                fileBaseName = self.fileSep.join([projectCode, str(subItem1.text()), str(subItem2.text()), str(entityItem.text()), str(stepItem.text())])

            if fileBaseName: 
                version = self.get_version(fileBaseName)
                fileName = self.fileSep.join([fileBaseName, version, user])
                fileNameExt = '%s%s' % (fileName, self.ext)

                self.ui.fileName_lineEdit.setText(fileNameExt)




    def get_version(self, basename): 
        """ find local increment version """ 
        logger.info('get_version')
        path = self.get_combine_path()

        if path: 
            # continue if path exists 
            if os.path.exists(path): 
                files = file_utils.listFile(path)

                # filter only local file 
                files = [a for a in files if basename in a]
                version = file_utils.find_next_version(files)
        
        else: 
            version = 'v001'

        return version

    def get_combine_path(self): 
        """ get path combination from ui """ 
        absPath = path_info.convertAbs(str(self.ui.path_lineEdit.text()))
        workspace = str(self.ui.work_comboBox.currentText())

        if workspace: 
            path = self.pathSep.join([absPath, workspace])

            return path

    def override_filename(self): 
        self.ui.fileName_lineEdit.setEnabled(self.ui.override_checkBox.isChecked())
        

    def clear_ui(self, ui1=False, ui2=False, entity=False, step=False, space=False, workfile=False, path=False, fileName=False): 
        """ clear ui """ 
        if ui1: 
            # logger.info('clear ui1')
            self.ui.ui1_listWidget.blockSignals(True)
            self.ui.ui1_listWidget.clear()
            self.ui.ui1_listWidget.blockSignals(False)
        if ui2: 
            # logger.info('clear ui2')
            self.ui.ui2_listWidget.blockSignals(True)
            self.ui.ui2_listWidget.clear()
            self.ui.ui2_listWidget.blockSignals(False)
        if entity: 
            # logger.info('clear entity')
            self.ui.entity_listWidget.blockSignals(True)
            self.ui.entity_listWidget.clear()
            self.ui.entity_listWidget.blockSignals(False)
        if step: 
            # logger.info('clear step')
            self.ui.task_listWidget.blockSignals(True)
            self.ui.task_listWidget.clear()
            self.ui.task_listWidget.blockSignals(False)
        if space: 
            # logger.info('clear space')
            self.ui.work_comboBox.blockSignals(True)
            self.ui.work_comboBox.clear() 
            self.ui.work_comboBox.blockSignals(False)
        if workfile: 
            # logger.info('clear workfile')
            self.ui.file_listWidget.blockSignals(True)
            self.ui.file_listWidget.clear()
            self.ui.file_listWidget.blockSignals(False)
        if path: 
            self.ui.path_lineEdit.clear()
        if fileName: 
            self.ui.fileName_lineEdit.clear()


    # context ui menu 
    # show menu
    def show_context_menu(self, widget, ui, pos):
        """ show context menu """
        menu = QtWidgets.QMenu(self)
        currentItem = widget.currentItem()
        data = currentItem.data(QtCore.Qt.UserRole)
        asset = self.get_entity_object()

        if currentItem:
            # basic menu 
            openItem = menu.addAction('Open in Explorer')
            openItem.triggered.connect(partial(self.open_in_explorer, widget))
            menu.addSeparator()
            copyPathItem = menu.addAction('Copy Path')
            copyPathItem.triggered.connect(partial(self.copy_path, widget))

            # only entity widget
            if widget == self.ui.entity_listWidget and self.mode == self.asset: 
                menu.addSeparator()
                self.show_reference_menu(menu, asset)
                menu.addSeparator()
                propitItem = menu.addAction('PropIt')
                propitItem.triggered.connect(partial(self.launch_propit, asset))

            menu.popup(widget.mapToGlobal(pos))

    def show_reference_menu(self, menu, asset): 
        currentItem = self.ui.entity_listWidget.currentItem()
        entity = currentItem.data(QtCore.Qt.UserRole)
        refs = asset.getRefs()

        referenceMenu = QtWidgets.QMenu('Reference', self)
        referenceMenu.triggered.connect(partial(self.create_reference, asset))

        if refs:
            for ref in refs:
                referenceMenu.addAction(ref)
        else:
            referenceMenu.addAction('No File')

        menu.addMenu(referenceMenu)


    def create_reference(self, asset, item): 
        """ create reference from selected item """ 
        logger.info('create_ref')
        referenceFile = str(item.text())
        refPath = self.pathSep.join([asset.libPath(), referenceFile])
        asm = False

        if '_%s' % config.asmSuffix in referenceFile:
            asm = True

        namespace = asset.name

        if os.path.exists(refPath): 
            # create normal reference 
            if not asm: 
                maya_utils.create_reference(namespace, refPath)

            if asm:
                node = maya_utils.create_asm_reference(namespace, refPath)
                asm_utils.setActiveRep(node, 'Gpu_pr')
                logger.info('Create Assembly Reference namespace: %s, %s' % (namespace, refPath))


    def launch_propit(self, asset): 
        logger.info('launch propit')
        key = self.fileSep.join([asset.type, asset.subtype, asset.name])
        if key not in self.entityCache.keys(): 
            entity = asset.sgEntity
            self.entityCache.update({key: entity})
            logger.debug('read from server')

        else: 
            entity = self.entityCache.get(key)
            logger.debug('read from cache')

        propIt_app.show(asset, entity)


    # context menu commands 
    def open_in_explorer(self, widget): 
        data = widget.currentItem().data(QtCore.Qt.UserRole)
        if data: 
            path = data.get('path').replace('/', '\\')
            subprocess.Popen(r'explorer /select,"%s"' % path)

    def copy_path(self, widget): 
        data = widget.currentItem().data(QtCore.Qt.UserRole)
        if data: 
            path = data.get('path')
            result = mm.eval('system("echo %s|clip")' % path)


    def get_entity_object(self): 
        """ get entity object from existing information """ 
        project = str(self.ui.project_comboBox.currentText())
        subItem1 = self.ui.ui1_listWidget.currentItem()
        subItem2 = self.ui.ui2_listWidget.currentItem()
        entityItem = self.ui.entity_listWidget.currentItem()
        stepItem = self.ui.task_listWidget.currentItem()
        user = str(self.ui.localUser_comboBox.currentText())

        if subItem1 and subItem2 and entityItem: 
            if not stepItem: 
                stepItem = ''
            entity = path_info.PathInfo(project=project, entity=self.mode, entitySub1=str(subItem1.text()), entitySub2=str(subItem2.text()), name=str(entityItem.text()), step=str(stepItem.text()))
            return entity

    # maya commands signal 
    def open_action(self): 
        """ open action button """ 
        logger.info('open')
        confirmOpen = True
        path = self.get_combine_path()

        fileItem = self.ui.file_listWidget.currentItem()

        if fileItem: 
            filePath = self.pathSep.join([path, str(fileItem.text())])
            
            if check_scene_modify(): 
                confirmOpen = False
                result = QtWidgets.QMessageBox.question(self, 'Warning', 'Scene has changed since last save. Do you want to open?', QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

                if result == QtWidgets.QMessageBox.Yes: 
                    confirmOpen = True

            if confirmOpen: 
                open_file(filePath)


    def save_action(self): 
        """ save action button """ 
        logger.info('save')
        path = self.get_combine_path()

        if path: 
            fileName = str(self.ui.fileName_lineEdit.text())
            saveFile = self.pathSep.join([path, fileName])
            confirmSave = True 

            if os.path.exists(saveFile): 
                confirmSave = False
                result = QtWidgets.QMessageBox.question(self, 'Confirm', '%s exists. Do you want to overwrite?' % saveFile, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

                if result == QtWidgets.QMessageBox.Yes: 
                    confirmSave = True

            if confirmSave: 
                save_file(saveFile)

                # refresh file ui 
                self.work_trigger()

        else: 
            QtWidgets.QMessageBox.warning(self, 'Error', 'No workspace found. Cannot Save', QtWidgets.QMessageBox.Ok)



# maya commands 
def save_file(saveFile): 
    mc.file(rename=saveFile)
    result = mc.file(save=True, type='mayaAscii')
    return result

def open_file(path): 
    return mc.file(path, o=True, f=True)

def check_scene_modify(): 
    return mc.file(q=True, modified=True)

def get_user(): 
    localUser = mc.optionVar(q=config.localUser)
    return localUser
