import ApatcherClass as ac
import sys
import argparse
import configparser
import os
import string

version = "0.2b"


# Не будем городить класс для парсера, т.к. argparse создает его внутри методов.
# Навернем немного функциональной лапши до непосредственного формирования шаблона.
def create_parser():
    parser = argparse.ArgumentParser(
        prog="apatcher_forward",
        description="Автоматизированная сборка template патча",
        epilog="(c) Alex1OPS.",
        add_help=False
    )
    # группа параметров
    parent_group = parser.add_argument_group(title="Параметры")
    parent_group.add_argument("-p", "--project", required=True, help="Проект")
    parent_group.add_argument("-c", "--commit", action='store_true', default=False, help="Флаг коммита после сборки")
    parent_group.add_argument("-t", "--text", default="Empty comment line", help="Текст комментария к коммиту")
    parent_group.add_argument("--help", "-h", action="help", help="Справка")
    parent_group.add_argument("--version",
                              action="version",
                              help="Номер версии",
                              version="%(prog)s {}".format(version))
    return parser


def main():
    # получим аргументы командной строки
    parser = create_parser()
    namespace = parser.parse_args(sys.argv[1:])
    # получим полный путь до папки проекта и проверим существует ли он
    try:
        t = ac.CfgInfo
        t.init(t)
        path_dir = t.path.get("projects_path", namespace.project)
        if not os.path.isdir(path_dir):
            raise Exception("Can\'t find directory for project", namespace.project)
    except configparser.NoOptionError:
        print("Config file parse error")
        exit(0)
    except Exception as inst:
        print(inst)
        exit(0)

    # получим статусы объектов в репо
    topl = ac.RepoJob(path_dir=path_dir)
    objects_new, objects_mod, objects_del = topl.parse_status(topl.get_status())
    list_files = []
    list_files = list_files + objects_new
    list_files = list_files + objects_mod

    # получим template sql для патча
    ptch_tmp = ac.PatchTemplate
    ptch_tmp.take_from(ptch_tmp)

    # разберем статусы объектов репо по полям патча
    fin_p = ac.Patch(author=t.author)
    fin_p.objects_new = ", ".join([p.rsplit("\\", 1)[-1] for p in objects_new])
    fin_p.objects_mod = ", ".join([p.rsplit("\\", 1)[-1] for p in objects_mod])
    fin_p.objects_del = ", ".join([p.rsplit("\\", 1)[-1] for p in objects_del])
    fin_p.comment = namespace.text
    fin_p.files_list = "\n".join(["@@ ..\\sysobjects" + p.split("\\sysobjects", 1)[-1] for p in list_files])
    fin_p.full = ptch_tmp.full

    # запишем template.sql для патча
    fin_p.prepare(proj_name=namespace.project)
    fin_p.save(path_to_file="template.sql")


if __name__ == "__main__":
    main()
