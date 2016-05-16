import ApatcherClass as ac
import sys
import argparse
import configparser
import os
import test_docx as tdd
import locale
import datetime
import pymorphy2
import ApatcherMenu

version = "0.4b"


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
    parent_group.add_argument("-n", "--nomake", action='store_true', default=False, help="Флаг сборки патча")
    parent_group.add_argument("-d", "--docs", action='store_true', default=False,
                              help="Флаг генерации сопровождающих документов")
    parent_group.add_argument("-r", "--dir", default="", help="Папка, в которой будет передан патч")
    parent_group.add_argument("-t", "--text", default="Empty comment line", help="Текст комментария к коммиту")
    parent_group.add_argument("-e", "--edit", action='store_true', default=False, help="Флаг редактирования списка файлов")
    parent_group.add_argument("-h", "--help", action="help", help="Справка")
    parent_group.add_argument("--version",
                              action="version",
                              help="Номер версии",
                              version="%(prog)s {}".format(version))
    return parser


def main():
    # настроим локаль
    locale.setlocale(locale.LC_ALL, "ru")

    # настроим морфологический анализатор
    morph = pymorphy2.MorphAnalyzer()
    # текущая дата в виде строки
    dt_make = datetime.date.today()
    # получим месяц в родительном падеже
    dt_str_make = dt_make.strftime(u"%d " + morph.parse(dt_make.strftime(u"%B"))[0].inflect({'gent'}).word + " %Y")

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

    # print(namespace)
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
    fin_p.save(path_to_file=os.path.join(path_dir, "patch-template/template.sql"))

    # соберем патч
    if namespace.nomake is True:
        print("Without making patch -> True")
    else:
        b_sucs_making = fin_p.make_patch(path_to_file=os.path.join(path_dir, "patch-template/patch.bat"))
        if b_sucs_making is True:
            print("Making patch -> Success")
        else:
            print("Making patch -> Fail")

    # если нужно, отправим коммит
    if namespace.commit is True:
        print("Commit changes -> True")
        topl.send_commit(comment_line=fin_p.comment)

    # если нужно, соберем сопровождающие документы
    if namespace.docs is True:
        print("Create docs -> True")
        # получим статус репо - ожидаем там увидеть патч
        ts_rp_patch = ac.RepoJob(path_dir=path_dir + "\\patches")
        objects_new_p, objects_mod_p, objects_del_p = ts_rp_patch.parse_status(ts_rp_patch.get_status())
        list_files = [] + objects_new_p + objects_mod_p + objects_del_p
        list_files = [p.rsplit("\\", 1)[-1] for p in list_files]
        if namespace.edit is True:
            choice_ur = 0
            while choice_ur != 3:
                ApatcherMenu.print_list(list_files, name="patches")
                choice_ur = ApatcherMenu.show_menu()
                print(choice_ur)
                # list_files = ApatcherMenu.edit_list(lmass=list_files,action=choice_ur)
        tdd.generate_doc_upd_log(author_name=fin_p.author, dir_name=namespace.dir, date_d=dt_str_make,
                                 list_patch=list_files)


if __name__ == "__main__":
    main()
