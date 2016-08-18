import configparser as cfg
import datetime as dt
import sys

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.uic import loadUi


class CfgInfo:
    projects = None

    def __init__(self):
        config = cfg.ConfigParser()
        config.read("config.ini")
        p = [x.capitalize() for x in config["projects_path"]]
        p.sort()
        self.projects = p


# noinspection PyCallByClass
class DemoImpl(QMainWindow):
    def __init__(self, *args):
        super(DemoImpl, self).__init__(*args)
        loadUi('gui_apatcher.ui', self)

        t = CfgInfo()
        self.comboProjects.addItems(t.projects)

        self.listFiles.addItem("new1")
        self.listFiles.addItem("new2")

    @pyqtSlot(name='on_button1_clicked')
    def on_button1_clicked(self):
        for s in "This is a demo".split(" "):
            self.list.addItem(s)

    @pyqtSlot(int, name='on_comboProjects_currentIndexChanged')
    def comboProjects_currentIndexChanged(self):
        print(self.comboProjects.itemText(self.comboProjects.currentIndex()))

    @pyqtSlot(str, name='on_lineAuthor_textChanged')
    def changed_author_line(self):
        print(self.lineAuthor.text())

    @pyqtSlot(name='on_textComment_textChanged')
    def changed_comment_text(self):
        print(self.textComment.toPlainText())

    @pyqtSlot(name='on_listFiles_itemSelectionChanged')
    def changed_position_list_files(self):
        print(self.listFiles.currentItem().text())

    @pyqtSlot(name='on_pushDel_clicked')
    def del_file_from_list(self):
        self.textLog.append(
            "[{0}] Delete file \"{1}\" from list.".format(dt.datetime.now().strftime("%y-%m-%d %H:%M:%S"),
                                                          self.listFiles.currentItem().text()))
        listItems = self.listFiles.selectedItems()
        if not listItems:
            return
        for item in listItems:
            self.listFiles.takeItem(self.listFiles.row(item))

    @pyqtSlot(name='on_pushAdd_clicked')
    def add_file_to_list(self):
        filter_filetype = "All (*);;sql (*.sql)"
        fname_add = QFileDialog.getOpenFileNames(self, "Добавить файл", "", filter=filter_filetype)[0]
        for x in fname_add:
            self.listFiles.addItem(x)
            self.textLog.append(
                "[{0}] Add file \"{1}\" to list.".format(dt.datetime.now().strftime("%y-%m-%d %H:%M:%S"),
                                                         x))

    @pyqtSlot(name='on_pushQuit_clicked')
    def quit_but(self):
        self.close()

    @pyqtSlot(name='on_pushStart_clicked')
    def start_process(self):
        self.textLog.append("[{0}] Process started using:".format(dt.datetime.now().strftime("%y-%m-%d %H:%M:%S")))
        self.textLog.append(
            "[{0}] ... "
            "only-docs = {1}"
            ", commit = {2} "
            ", author=\"{3}\""
            ", comment=\"{4}\"".format(dt.datetime.now().strftime("%y-%m-%d %H:%M:%S"),
                                       self.checkBoxOnlyDocs.isChecked(),
                                       self.checkBoxCommit.isChecked(),
                                       self.lineAuthor.text(),
                                       self.textComment.toPlainText()))


def main():
    app = QApplication(sys.argv)
    widget = DemoImpl()
    widget.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
