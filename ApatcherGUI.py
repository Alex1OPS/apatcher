import configparser as cfg
import datetime as dt
import logging
import sys
import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QMessageBox, QSizePolicy
from PyQt5.uic import loadUi

import ApatcherClass as ac
import apather_do as ado

logger = logging.getLogger(__name__)


class CfgInfo:
    projects = None
    author_name = None
    projects_info = None

    def __init__(self):
        config = cfg.ConfigParser()
        config.read("config.ini")

        p = [x.upper() for x in config["projects_path"]]
        p.sort()
        self.projects = p
        self.projects_info = {pname.upper(): config.get("projects_path", pname) for pname in config["projects_path"]}
        self.author_name = config.get("info", "author")


class SettingNamespace:
    def __init__(self):
        self.manual = None
        self.project = None
        self.text = None
        self.docs = None
        self.only = None
        self.dir = None
        self.customer = None
        self.anum = None
        self.before_script = None
        self.patch_files = None
        self.edit = False
        self.nomake = False
        self.make = False
        self.fwopt = None
        self.commit = False

    # печать состава namespace пользователя
    def print_namespace_composition(self):
        return (("User namespace consists of:\n" +
                 "manual = {manual}\nproject = {project}\ntext = {text}\ndocs = {docs}\nonly = {only}\n" +
                 "dir = {dir}\ncustomer = {customer}\nanum = {anum}\nbefore_scripts = {befscripts}\n" +
                 "patch_files = {patchfiles}\nnomake = {nomake}\nmake = {make}").format(manual=self.manual,
                                                                                        project=self.project,
                                                                                        text=self.text,
                                                                                        docs=self.docs, only=self.only,
                                                                                        dir=self.dir,
                                                                                        customer=self.customer,
                                                                                        anum=self.anum,
                                                                                        befscripts=self.before_script,
                                                                                        patchfiles=self.patch_files,
                                                                                        nomake=self.nomake,
                                                                                        make=self.make)
                )


class PguiApatcherWindow(QMainWindow):
    user_config = None
    current_project = None
    current_proj_path = ""

    def __init__(self, *args):
        super().__init__(*args)
        self.user_config = CfgInfo()

        self.initUI()
        self.connectAllSignals()
        self.setDefaultEnv()

    def initUI(self):
        loadUi(os.path.join(os.path.dirname(__file__), 'mainwindow.ui'), self)
        self.setWindowTitle("Автопатчилка GUI ver. 0.1")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icon.jpg')))
        self.comboProjects.addItems(self.user_config.projects)

    def connectAllSignals(self):
        self.pushQuit.clicked.connect(self.btnQuitClick)
        self.pushStart.clicked.connect(self.start_generate_proc)
        self.comboProjects.currentIndexChanged[str].connect(self.changeActiveProject)
        self.tableFiles.cellClicked[int, int].connect(self.editCell)
        self.pushAdd.clicked.connect(self.addRow)
        self.pushRefresh.clicked.connect(self.getRepoFiles)
        self.checkBoxWithFiles.clicked.connect(self.changeWriteModePath)
        self.pushErase.clicked.connect(self.cancel_current_set)

    def setDefaultEnv(self):
        self.lineAuthor.setText(self.user_config.author_name)
        self.lineAuthor.setReadOnly(True)

        self.lineDirToPass.setDisabled(True)
        self.lineDirToPass.setReadOnly(True)

        self.lineDirToPass.setToolTip("Папка для передачи документации")
        self.comboProjects.setCurrentIndex(-1)

        # подготовка таблицы файлов
        self.tableFiles.setColumnCount(2)
        self.tableFiles.setColumnWidth(0, 420)
        self.tableFiles.setColumnWidth(1, 80)
        self.tableFiles.verticalHeader().setVisible(True)
        tab_labels = ["Файл", "Действие"]
        self.tableFiles.setHorizontalHeaderLabels(tab_labels)

        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)

    def appendLog(self, text):
        self.textLog.append(text)

    def btnQuitClick(self):
        sys.exit(self.close())

    def changeActiveProject(self, proj_name):
        current_project_path = self.user_config.projects_info.get(proj_name)
        if proj_name is not None and current_project_path is not None:
            self.current_project = proj_name
            self.current_proj_path = current_project_path
            self.appendLog("Текущий проект изменён на {0} = {1}".format(proj_name, current_project_path))

    def editCell(self, row, col):
        if col == 1:
            self.tableFiles.removeRow(row)

    def refreshFilesRows(self, added_files):
        for xf in added_files:
            self.tableFiles.insertRow(0)
            self.tableFiles.setItem(0, 0, QTableWidgetItem(xf))
            self.tableFiles.setItem(0, 1, QTableWidgetItem("Удалить"))
            self.tableFiles.item(0, 1).setFlags(Qt.ItemIsSelectable)

    def addRow(self):
        options = QFileDialog.Options()
        dlg = QFileDialog()
        filenames = dlg.getOpenFileNames(self, "Добавить файлы к патчу", self.current_proj_path, "All files (*)",
                                         options=options)
        self.refreshFilesRows([x.replace("/", "\\") for x in filenames[0]])

    def getRepoFiles(self):
        current_proj_path = self.current_proj_path
        if current_proj_path is None:
            self.appendLog("Выберите проект перед обновлением статуса репозитория!")
            return
        trepo = ac.RepoJob(path_dir=current_proj_path)
        objects_new, objects_mod, objects_del, objects_unchecked = trepo.parse_status(trepo.get_status())
        self.refreshFilesRows(objects_mod)

        if len(objects_unchecked) != 0:
            msgBox = QMessageBox()
            msgBox.setText("Не все файлы добавлены в патч.")
            msgBox.setInformativeText(
                "Найдены файлы, находящиеся не под контролем версий и недобавленные в шаблон патча.")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.setDefaultButton(QMessageBox.Ok)
            msgBox.setDetailedText(";\n".join(objects_unchecked))
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle("Внимание!")
            msgBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            msgBox.setStyleSheet("QLabel{font-size: 14px;} QPushButton{ width:100px; font-size: 14px; }")
            msgBox.exec_()

    def changeWriteModePath(self):
        if self.checkBoxWithFiles.isChecked():
            self.lineDirToPass.setDisabled(False)
            self.lineDirToPass.setReadOnly(False)
        else:
            self.lineDirToPass.setDisabled(True)
            self.lineDirToPass.setReadOnly(True)

    def cancel_current_set(self):
        self.tableFiles.clearContents()
        self.tableFiles.setRowCount(0)
        self.lineDirToPass.setText("")
        self.lineDirToPass.setDisabled(True)
        self.lineDirToPass.setReadOnly(True)
        self.checkBoxWithFiles.setChecked(False)
        self.checkBoxPrepareCustomer.setChecked(False)
        self.textComment.clear()
        self.textBeforeFiles.clear()
        self.setDefaultEnv()

    def get_tab_files_content(self, process_col=0):
        table = self.tableFiles
        data = []
        for row in range(table.rowCount()):
            item = str(table.item(row, process_col).text())
            data.append(item)
        return data

    def start_generate_proc(self):
        self.appendLog("[{0}] Process started using:".format(dt.datetime.now().strftime("%y-%m-%d %H:%M:%S")))
        self.progressBar.setValue(0)
        user_space_set = SettingNamespace()

        user_space_set.manual = False
        user_space_set.project = self.current_project
        user_space_set.text = self.textComment.toPlainText()
        user_space_set.docs = self.checkBoxWithFiles.isChecked()
        user_space_set.only = True if self.tabWidget.currentIndex() == 1 else False
        user_space_set.nomake = user_space_set.only
        user_space_set.make = not user_space_set.nomake
        if user_space_set.docs or user_space_set.only:
            user_space_set.dir = self.lineDirToPass.text().strip("/")
            user_space_set.customer = self.checkBoxPrepareCustomer.isChecked()
            user_space_set.anum = "[s:{sdk},b:{base},p:{proj}]".format(sdk=self.lineBasePatch.text(),
                                                                       base=self.lineSDKPatch.text(),
                                                                       proj=self.lineProjectPatch.text())
        user_space_set.before_script = self.textBeforeFiles.toPlainText()
        user_space_set.patch_files = self.get_tab_files_content()
        user_space_set.fwopt = None

        logging.info("User namespace:{}".format(user_space_set.print_namespace_composition()))
        ado.generate_process_doc_patch(user_space_set)

        self.progressBar.setValue(100)


def main():
    app = QApplication(sys.argv)
    widget = PguiApatcherWindow()
    widget.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
