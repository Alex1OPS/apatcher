import configparser as cfg
import os
import subprocess
import re
import ApatcherUtils as autil


class PatchBase:
    def __init__(self, author=None, date=None, num=None, ticket_num=None, objects_new=None, objects_mod=None,
                 objects_del=None, comment=None, files_list=None):
        self.author = author
        self.date = date
        self.num = num
        self.ticket_num = ticket_num
        self.objects_new = objects_new
        self.objects_mod = objects_mod
        self.objects_del = objects_del
        self.comment = comment
        self.files_list = files_list


class PatchTemplate(PatchBase):
    full = None

    def __init__(self, author=None, date=None, num=None, ticket_num=None, objects_new=None, objects_mod=None,
                 objects_del=None, comment=None, files_list=None, full=None):
        PatchBase.__init__(self, author, date, num, ticket_num, objects_new, objects_mod, objects_del, comment,
                           files_list)
        self.full = full

    def take_from(self, path_to_file="cfg/_temp.sql"):
        try:
            with open(os.path.join(os.path.dirname(__file__), path_to_file), 'r') as fl:
                file_data = fl.read()
            self.full = file_data
        except FileNotFoundError:
            print("Can\'t find a template sql file for make patch")
            exit(0)


class Patch(PatchBase):
    name = None
    full = None

    def prepare(self, proj_name="Default"):
        self.name = proj_name
        self.full = self.full.replace("__author__", self.author)
        self.full = self.full.replace("__ticket_num__", "")
        self.full = self.full.replace("__new_objs__", self.objects_new)
        self.full = self.full.replace("__modify_objs__", self.objects_mod)
        self.full = self.full.replace("__del_objs__", self.objects_del)
        self.full = self.full.replace("__comment_body__", self.comment)
        self.full = self.full.replace("__list_objs__", self.files_list)
        self.full = self.full.replace("__project__", self.name)

    def save(self, path_to_file):
        with open(path_to_file, 'w') as fl:
            fl.write(self.full)

    @staticmethod
    def make_patch(path_to_file):
        cmd = path_to_file
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        result = out.decode("utf-8")
        result = result.split("\n")
        stat_msg = result[-3]

        if "DONE" in stat_msg:
            return True
        else:
            return False


class RepoJob:
    def __init__(self, path_dir=None, objects_new=None, objects_mod=None, objects_del=None):
        self.path_dir = path_dir
        self.objects_new = objects_new
        self.objects_mod = objects_mod
        self.objects_del = objects_del

    # получим статус репо в виде массива строк - 1 на 1 файл репо
    def get_status(self):
        cmd = "svn status " + self.path_dir
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        result = out.decode("utf-8")
        result = result.split("\n")
        result = [p[:-1] for p in result]
        return result

    # парсинг статуса репо вМс1 в 3 массива новых, изменнных, удаленных объектов
    @staticmethod
    def parse_status(status_mass, b_patch=False):
        obj_new = []
        obj_mod = []
        obj_del = []
        # разберем статусы файла, полученные из svn status
        for ptr in status_mass:
            try:
                p_fmt = ptr.split(".", 1)[1]
            except IndexError:
                p_fmt = ""
            if ("patches" in ptr or "template.sql" in ptr) and b_patch is not True:
                continue
            if p_fmt not in ("sql", "pck", "xml"):
                continue
            if ptr[:1] == 'M':
                obj_mod.append(ptr[1:].lstrip())
            elif ptr[:1] == 'N' or ptr[:1] == 'A':
                obj_new.append(ptr[1:].lstrip())
            elif ptr[:1] == 'D':
                obj_del.append(ptr[1:].lstrip())
        return obj_new, obj_mod, obj_del

    # отправка коммита
    def send_commit(self, comment_line):
        cmd = "svn commit " + self.path_dir + " -m \"" + comment_line + " \""
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        result = out.decode("utf-8")
        result = result.split("\n")
        result = "\n".join(result)
        return result


class CfgInfo:
    author = None
    path = None

    def __init__(self, path=None, author=None):
        dir = os.path.dirname(__file__)
        config = cfg.ConfigParser()
        config.read(os.path.join(dir, "config.ini"))
        self.author = config.get("info", "author")
        self.path = config


class PatchPrint:
    name = None
    list_files = None
    description = None
    db_change = None
    web_change = None
    full_name = None

    def __init__(self, name="", list_files=None, description="", full_name=None):
        if list_files is None:
            list_files = []
        self.name = name
        self.list_files = list_files
        self.description = description
        db_change, web_change = autil.split_list_files(self.list_files)
        self.db_change = ", ".join(map(str, db_change))
        self.web_change = ", ".join(map(str, web_change))
        self.full_name = full_name

    def parse_from_exists(self, full_txt=""):
        try:
            m = re.search('Автор(.+)Дата(.+)Номер патча(.+)'
                          'Номер тикета(.+)Новые объекты(.+)'
                          'Измененные объекты(.+)Удаленные объекты(.+)'
                          'Комментарий(.+)Создан(.+)Список включённых файлов(.+)', full_txt)
            self.name = m.group(3).lstrip(":").strip(" ").lstrip("0")
            self.list_files = [x.strip(" ") for x in (m.group(10).lstrip(":")).split(",")]
            db_change, web_change = autil.split_list_files(self.list_files)
            self.db_change = ", ".join(map(str, db_change))
            self.web_change = ", ".join(map(str, web_change))
            self.description = m.group(8).lstrip(":").strip(" ")
        except AttributeError:
            raise Exception("Не все поля маски найдены в шапке патча")


class PatchPrintExt(PatchPrint):
    author_name = None
    date_cr = None
    dir_take = None
    sdk_patches = None
    base_patches = None
    proj_patches = None
    list_patches = None

    def __init__(self, name, description=None, list_files=None, list_patches=None, sdk_patches=None,
                 base_patches=None, proj_patches=None, author_name=None, date_cr=None, dir_take=None):
        PatchPrint.__init__(self, name, list_files, description)
        self.author_name = author_name
        self.date_cr = date_cr
        self.dir_take = dir_take
        self.list_patches = list_patches
        self.sdk_patches = sdk_patches
        self.base_patches = base_patches
        self.proj_patches = proj_patches


def main():
    # t = PatchPrint()
    # t.parse_from_exists("*Автор:                Куртаков А.Е.  Дата:         "
    #                     "        2016-07-05  Номер патча:          01614  Номер тикета:  "
    #                     "       10801  Новые объекты:   Измененные объекты:   pack_bill  Удаленные объекты: "
    #                     "     Комментарий:    "
    #                     "      Скорректировано определение уровня логирования при массовом выставлении счетов "
    #                     "(ускорено)  "
    #                     "  Создан: 2016-07-05 11:45:08    Список включённых файлов: flexy-525019.sql,"
    #                     " flexy-525051.sql, DIS_BASE_EXCHANGE.pck, DIS_SEARCH_INTERFACE.pck")
    #
    # print(t.name)
    # print(t.list_files)
    # print(t.description)
    sarg_line = "{s:189-191,b:1617-1620,p:814-817}"
    p1, p2, p3 = autil.parse_nums_patches_interval(sarg_line)
    print(p1)
    print(p2)
    print(p3)
    _, tr_sdk, tr_base, tr_proj = autil.get_all_patch_files_by_nums("D:\\FProjects\\database\\sdk\\database\\patches",
                                                                    "D:\\FProjects\\database\\billing\\database\\patches",
                                                                    "D:\\FProjects\\DISCOVERY\\patches",
                                                                    p1,
                                                                    p2,
                                                                    p3)
    print(tr_sdk)
    print(tr_base)
    print(tr_proj)


if __name__ == "__main__":
    main()
