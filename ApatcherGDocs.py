import logging

import fwpt_apatcher.ApatcherUtils as autil

logger = logging.getLogger(__name__)

PATH_TO_IMG = "cfg/box_img.jpg"
PATH_TO_TMPL = "cfg/_temp.sql"
PATH_TO_CFG = "cfg/config.ini"
WARNING_MSG_DELIMITER = ">>>"


class ProjectPatchEntity:
    version_num = None
    changed_files = []
    db_changed = []
    ui_changed = []
    comment = None
    author = None
    path_patch_ = None
    name_file_ = None

    def __init__(self, version_num=None, author=None, changed_files=None, ui_changed=None, db_changed=None,
                 comment=None):
        self.version_num = version_num
        self.author = author
        self.changed_files = changed_files
        self.ui_changed = ui_changed
        self.db_changed = db_changed
        self.comment = comment

    def initFromSource(self, path_patch_, name_file_):
        self.path_patch_ = path_patch_
        self.name_file_ = name_file_
        self.init_from_exists()

    def init_from_exists(self):
        full_txt = autil.get_patch_top_txt(self.path_patch_)

        remap = {ord('\t'): None, ord('\f'): None, ord('\r'): None}
        num_patch = 0

        try:
            author = full_txt[full_txt.find("Автор:") + len("Автор"): full_txt.find("Дата:")].strip(" :\n").translate(
                remap)
            num_patch = full_txt[
                        full_txt.find("Номер патча:") + len("Номер патча"): full_txt.find("Номер тикета:")].strip(
                " :\n").translate(remap)
            descr = full_txt[full_txt.find("Комментарий:") + len("Комментарий"): full_txt.find("Создан:")].strip(
                " :\n").replace("\n", "").translate(remap)
            if full_txt.find("Создан:") != -1 and full_txt.find("Список включённых файлов:") != -1:
                list_files = full_txt[full_txt.find("Список включённых файлов:") + len("Список включённых файлов"): len(
                    full_txt)].strip(" :\n").translate(remap)
                # удалим возможно предупреждение в шапке
                p_delim_place = list_files.find(WARNING_MSG_DELIMITER)
                if p_delim_place != -1:
                    list_files = list_files[:p_delim_place]
                lst_files = [x.strip(" ") for x in (list_files.lstrip(":")).split(",")]
            else:
                new_files = full_txt[full_txt.find("Новые объекты:") + len("Новые объекты"): full_txt.find(
                    "Измененные объекты:")].strip(" :\n").translate(remap)
                change_files = full_txt[full_txt.find("Измененные объекты:") + len("Измененные объекты"): full_txt.find(
                    "Удаленные объекты:")].strip(" :\n").translate(remap)
                del_files = full_txt[full_txt.find("Удаленные объекты:") + len("Удаленные объекты"): full_txt.find(
                    "Комментарий:")].strip(" :\n").translate(remap)
                list_files = new_files + change_files + del_files
                lst_files = [x.strip(" ") for x in (list_files.lstrip(":")).split(",")]

            self.version_num = num_patch.lstrip("0")
            self.changed_files = lst_files
            db_change, web_change = autil.split_list_files(self.changed_files)
            self.db_changed = ", ".join(map(str, db_change))
            self.ui_changed = ", ".join(map(str, web_change))
            self.comment = descr
            self.author = author
        except Exception as e:
            logging.error("Некорректный парсинг шапки патча. Исключение: {}".format(e))
            raise Exception("Некорректный парсинг шапки патча #{}".format(num_patch))

    def __str__(self):
        print("PatchEntity:\nversion={ver}, comment={comment},\n".format(ver=self.version_num, comment=self.comment))


class ProjectCorpus:
    project_name = None
    project_ext = None
    patches = []

    def __init__(self, project_name, project_ext, patches):
        self.project_name = project_name
        self.project_ext = project_ext
        for x in patches:
            if not isinstance(x, ProjectPatchEntity):
                raise TypeError("An invalid type for the project patch collection.")
        self.patches = patches


class DocEntity:
    doc_name = None
    projects = []

    def __init__(self, doc_name, projects):
        self.doc_name = doc_name
        for x in projects:
            if not isinstance(x, ProjectCorpus):
                raise TypeError("An invalid type for the project corpus in document.")
        self.projects = projects
