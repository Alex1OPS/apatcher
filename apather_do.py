import argparse
import configparser
import datetime
import locale
import os
import sys

from pymorphy2 import MorphAnalyzer

import ApatcherClass as ac
import ApatcherMenu
import ApatcherUtils as autil
import ApatcherGendocs as adoc

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
    parent_group.add_argument("-o", "--only", action='store_true', default=False,
                              help="Только генерация сопровождающих документов")
    parent_group.add_argument("-y", "--directory", help="Алиас пути для поиска патчей")
    parent_group.add_argument("-a", "--anum", help="Номера патчей для добавления документации")
    parent_group.add_argument("-r", "--dir", default="", help="Папка, в которой будет передан патч")
    parent_group.add_argument("-t", "--text", default="Empty comment line", help="Текст комментария к коммиту")
    parent_group.add_argument("-e", "--edit", action='store_true', default=False,
                              help="Флаг редактирования списка файлов")
    parent_group.add_argument("-h", "--help", action="help", help="Справка")
    parent_group.add_argument("--version",
                              action="version",
                              help="Номер версии",
                              version="%(prog)s {}".format(version))
    return parser


def main():
    # настроим локаль
    global path_dir
    locale.setlocale(locale.LC_ALL, "ru")

    # настроим морфологический анализатор
    morph = MorphAnalyzer()
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
        if namespace.directory:
            pathes_b_dir = t.path.get("patches_path", namespace.directory)
        else:
            pathes_b_dir = ""
        if namespace.only is True and not os.path.isdir(pathes_b_dir):
            raise Exception("Can\'t find directory for alias", namespace.directory)
        if not os.path.isdir(path_dir):
            raise Exception("Can\'t find directory for project", namespace.project)
    except configparser.NoOptionError:
        print("Config file parse error")
        exit(0)
    except Exception as inst:
        print(inst)
        exit(0)

    # print(namespace)
    if namespace.only is False:
        # получим статусы объектов в репо
        topl = ac.RepoJob(path_dir=path_dir)
        objects_new, objects_mod, objects_del = topl.parse_status(topl.get_status())
        if namespace.edit is True:
            print("Editing list of files to prepare patch -> True")
            objects_new, objects_mod, objects_del = ApatcherMenu.edit_files_list(new_lm=objects_new, mod_lm=objects_mod,
                                                                                 del_lm=objects_del)
        list_files = [] + objects_new + objects_mod

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
            objects_new_p, objects_mod_p, objects_del_p = ts_rp_patch.parse_status(ts_rp_patch.get_status(),
                                                                                   b_patch=True)
            proj_patch = ac.PatchPrintExt.parse_from_exists(autil.get_patch_top_txt(objects_new_p[0]))
            adoc.generate_doc_changelist(project_patches=[proj_patch for x in range(0,2)])
            adoc.generate_doc_upd_log(author_name=t.author, list_patch=proj_patch.name)
    else:
        # только генерируем документы по патчам, указанным в папке cfg
        print('Только генерация документов')
        print(pathes_b_dir)
        pl = [int(namespace.anum.split("-", 1)[0])] if len(namespace.anum.split("-", 1)) < 2 else list(
            range(int(namespace.anum.split("-", 1)[0]), int(namespace.anum.split("-", 1)[1]) + 1))
        pl_dub = pl
        print(pl)
        # начнем обход папок для поиска патчей
        for path, subdirs, files in os.walk(pathes_b_dir):
            for name in files:
                if str(os.path.join(path, name)).endswith(".sql"):
                    for p_item in pl:
                        if str(p_item) in str(os.path.join(path, name)).split("\\")[-1]:
                            print(os.path.join(path, name))
                            patch_body = autil.get_patch_top_txt(os.path.join(path, name))
                            tmp_ptch = ac.PatchPrint()
                            tmp_ptch.parse_from_exists(patch_body)
                            print(tmp_ptch.name)
                            print(tmp_ptch.description)
                            print(tmp_ptch.list_files)
                            print("-----------------------------------------------")


if __name__ == "__main__":
    main()
