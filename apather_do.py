import argparse
import configparser
import datetime
import locale
import logging
import os
import sys
import json
import time

import ApatcherClass as ac
import ApatcherGendocs as adoc
import ApatcherMenu as amenu
import ApatcherUtils as autil
from pymorphy2 import MorphAnalyzer

__version__ = "0.9.4"
debug_mode = True


# Не будем городить класс для парсера, т.к. argparse создает его внутри методов.
def create_parser():
    parser = argparse.ArgumentParser(
        prog="apatcher_forward",
        description="Автоматизированная сборка template патча и сопровождающей документации",
        epilog="(c) Alex1OPS.",
        add_help=False
    )
    # группа параметров
    parent_group = parser.add_argument_group(title="Параметры")
    parent_group.add_argument("-p", "--project", help="Проект")
    parent_group.add_argument("-k", "--manual", help="Жесткая передача всех данных для формирования")
    parent_group.add_argument("-c", "--commit", action='store_true', default=False, help="Флаг коммита после сборки")
    parent_group.add_argument("-n", "--nomake", action='store_true', default=False, help="Флаг сборки патча")
    parent_group.add_argument("-d", "--docs", action='store_true', default=False,
                              help="Флаг генерации сопровождающих документов")
    parent_group.add_argument("-o", "--only", action='store_true', default=False,
                              help="Только генерация сопровождающих документов")
    parent_group.add_argument("-a", "--anum", help="Номера патчей для добавления документации")
    parent_group.add_argument("-f", "--fwopt", help="Ключи для стандартной патчилки")
    parent_group.add_argument("-r", "--dir", default="", help="Папка, в которой будет передан патч")
    parent_group.add_argument("-t", "--text", default="Empty comment line", help="Текст комментария к коммиту")
    parent_group.add_argument("-e", "--edit", action='store_true', default=False,
                              help="Флаг редактирования списка файлов")
    parent_group.add_argument("-m", "--make", action='store_true', default=False,
                              help="Только создание патча")
    parent_group.add_argument("-h", "--help", action="help", help="Справка")
    parent_group.add_argument("--version",
                              action="version",
                              help="Номер версии",
                              version="%(prog)s {}".format(__version__))
    return parser


def main():
    global path_dir, tcfg_arg
    start_exec_time = time.time()
    log_dir = "back"
    tmp_dir = "tmp"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    logging.basicConfig(filename="back/ct_main.log",
                        level=logging.INFO,
                        format='[%(asctime)s][%(levelname)s] %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S',
                        filemode="a+")
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
    logging.info(sys.argv)

    try:
        # если ручной режим, то парсим полученный json
        data = []
        if namespace.manual is not None:
            with open(namespace.manual) as data_file:
                data = json.load(data_file)
            namespace.project = data['project']
            namespace.text = data['comment']
            namespace.docs = data['with_docs']
    except Exception as inst:
        logging.error("I couldn't find json file {0} in manual mode: {1}".format(namespace.manual, inst))
        print(inst)
        exit(0)

    try:
        tcfg_arg = ac.CfgInfo()
        if namespace.project:
            path_dir = tcfg_arg.path.get("projects_path", namespace.project)
        else:
            logging.warning("path_dir to project is empty")
            path_dir = ""
        if not os.path.isdir(path_dir) and namespace.project:
            logging.error("Can\'t find directory for project = {0}".format(namespace.project))
            raise Exception("Can\'t find directory for project", namespace.project)
    except configparser.NoOptionError:
        logging.error("Config file parse error")
        print("Config file parse error")
        exit(0)
    except Exception as inst:
        logging.error("Unknown error: {0}".format(inst))
        print(inst)
        exit(0)

    # запусти параллельно сжатие логов
    # trd = threading.Thread(target=autil.zip_old_logs(log_dir, critdays=tcfg_arg.path.get("info", "loglife")))
    # trd.start()

    # отобразим конфигурацию
    if debug_mode is True:
        print("Configuration: ")
        print("  Only docs -> {}".format(str(namespace.only)))
        print("  Can edit -> {}".format(str(namespace.edit)))
        print("  Without making patch -> {}".format(str(namespace.nomake)))
        print("  Commit changes -> {}".format(str(namespace.commit)))
        print("  Create docs (patch mode) -> {}".format(str(namespace.docs)))

    if namespace.only is False:
        # получим статусы объектов в репо
        topl = ac.RepoJob(path_dir=path_dir)
        objects_new, objects_mod, objects_del = topl.parse_status(topl.get_status())
        if namespace.edit is True:
            objects_new, objects_mod, objects_del = amenu.edit_files_list(new_lm=objects_new, mod_lm=objects_mod,
                                                                          del_lm=objects_del)
        list_files = [] + objects_new + objects_mod

        # если ручной режим
        if namespace.manual is not None:
            objects_new = objects_del = []
            list_files = objects_mod = data['patch_files']

        # получим template sql для патча
        ptch_tmp = ac.PatchTemplate()
        ptch_tmp.take_from()

        # разберем статусы объектов репо по полям патча
        fin_p = ac.Patch(author=tcfg_arg.author)
        fin_p.comment = namespace.text
        fin_p.objects_new = ", ".join([p.rsplit("\\", 1)[-1] for p in objects_new])
        fin_p.objects_mod = ", ".join([p.rsplit("\\", 1)[-1] for p in objects_mod])
        fin_p.objects_del = ", ".join([p.rsplit("\\", 1)[-1] for p in objects_del])
        fin_p.files_list = "\n".join(["@@ " + p for p in list_files])
        fin_p.full = ptch_tmp.full

        # запишем template.sql для патча
        if namespace.make is False:
            fin_p.prepare(proj_name=namespace.project)
            fin_p.save(path_to_file=os.path.join(path_dir, "patch-template/template.sql"))

        # соберем патч
        if namespace.nomake is False or namespace.make is True:
            b_sucs_making = fin_p.make_patch_fw(path_to_file=os.path.join(path_dir, "patch-template/template.sql"),
                                                root_path=path_dir,
                                                fwoption=namespace.fwopt)
            if b_sucs_making is True:
                print("Making patch -> Success")
            else:
                print("Making patch -> Fail")

        # если нужно, отправим коммит
        if namespace.commit is True:
            topl.send_commit(comment_line=fin_p.comment)

        # если нужно, соберем сопровождающие документы
        if namespace.docs is True and namespace.nomake is False:
            # получим статус репо - ожидаем там увидеть патч
            ts_rp_patch = ac.RepoJob(path_dir=path_dir + "\\patches")
            objects_new_p, objects_mod_p, objects_del_p = ts_rp_patch.parse_status(ts_rp_patch.get_status(),
                                                                                   b_patch=True)
            proj_patch = ac.PatchPrint()
            proj_patch.parse_from_exists(autil.get_patch_top_txt(objects_new_p[0]),
                                         full_name=str(objects_new_p[0]).split("\\")[-1])

            # сгенерируем доки
            adoc.generate_doc_changelist(project_patches=[proj_patch for x in range(0, 1)])
            adoc.generate_doc_upd_log(author_name=tcfg_arg.author,
                                      list_patch=[proj_patch.full_name for x in range(0, 1)],
                                      dir_name=namespace.dir,
                                      date_d=dt_str_make)
    else:
        # только генерируем документы по патчам, указанным в папке cfg
        p_sdk, p_base, p_proj = autil.parse_nums_patches_interval(namespace.anum)
        tf_all, tf_sdk, tf_base, tf_proj = autil.get_all_patch_files_by_nums(tcfg_arg.path.get("patches_path", "sdk"),
                                                                             tcfg_arg.path.get("patches_path", "base"),
                                                                             path_dir,
                                                                             p_sdk,
                                                                             p_base,
                                                                             p_proj)
        # соберём классы по каждому патчу
        sdk_patches = []
        for x in tf_sdk:
            tp = ac.PatchPrint()
            tp.parse_from_exists(autil.get_patch_top_txt(x))
            tp.full_name = x.split("\\")[-1]
            sdk_patches.append(tp)
        base_patches = []
        for x in tf_base:
            tp = ac.PatchPrint()
            tp.parse_from_exists(autil.get_patch_top_txt(x))
            tp.full_name = x.split("\\")[-1]
            base_patches.append(tp)
        proj_patches = []
        for x in tf_proj:
            tp = ac.PatchPrint()
            tp.parse_from_exists(autil.get_patch_top_txt(x))
            tp.full_name = x.split("\\")[-1]
            proj_patches.append(tp)

        tf_all = [x.split("\\")[-1] for x in tf_all]

        # сформируем доки
        adoc.generate_doc_upd_log(tcfg_arg.author, namespace.dir, dt_str_make, list_patch=tf_all)
        adoc.generate_doc_changelist(project_patches=proj_patches,
                                     base_patches=base_patches,
                                     sdk_patches=sdk_patches)

    elapsed_time = time.time() - start_exec_time
    print("Runtime: {0} sec".format(round(elapsed_time, 3)))
    logging.info("Runtime: {0} sec".format(round(elapsed_time, 3)))


if __name__ == "__main__":
    main()
