import configparser as cfg
import os
import subprocess


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

    def make_patch(self, path_to_file):
        cmd = path_to_file
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        result = out.decode("utf-8")
        result = result.split("\n")
        stat_msg = result[-3]
        # result = "\n".join(result)
        if stat_msg == "DONE":
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
    def parse_status(self, status_mass):
        obj_new = []
        obj_mod = []
        obj_del = []
        for ptr in status_mass:
            if ptr[:1] == 'M':
                obj_mod.append(ptr[1:].lstrip())
            elif ptr[:1] == 'N' or ptr[:1] == 'A' or ptr[:1] == '?':
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
        self.path = path
        self.author = author

    def init(self):
        dir = os.path.dirname(__file__)
        config = cfg.ConfigParser()
        config.read(os.path.join(dir, "cfg/config.ini"))
        self.author = config.get("info", "author")
        self.path = config
