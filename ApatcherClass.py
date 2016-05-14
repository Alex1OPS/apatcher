import configparser as cfg
import os


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
    def take_from(self, path_to_file):
        # идём в файл и получаем шаблон патча
        print('take template')

class Patch(PatchBase):
    def save(self, path_to_file):
        # записываем содержимое патча в template.sql
        print('save template')

    def make_patch(self, path_to_file):
        # скармилваем template.sql в Prepare.py
        print('prepare.py started')


class RepoJob:
    def __init__(self, path_dir=None, objects_new=None, objects_mod=None, objects_del=None):
        self.path_dir = path_dir
        self.objects_new = objects_new
        self.objects_mod = objects_mod
        self.objects_del = objects_del

    def get_status(self):
        # получим статус репозитория
        print('take status of repo')


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
        # Получим параметры работы системы
        self.path = config
        print('take params :', self.path.get("info", "author"))