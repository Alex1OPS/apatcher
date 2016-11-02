import glob
import os
import time
import logging
import zipfile
from fw_patches.Prepare import PatchPrepare

logger = logging.getLogger(__name__)
zip_log_name = "archlogs.zip"

# разбиение списка файлов на две категории - бд и веб
def split_list_files(lmass):
    lm_db = []
    lm_web = []
    for item in lmass:
        if "flexy-" in item:
            lm_web.append(item)
        else:
            lm_db.append(item)

    lm_db.sort()
    lm_web.sort()

    return lm_db, lm_web


# получение содержимого файла целиком
def get_full_txt(path_to):
    with open(path_to) as f:
        data = f.read().replace('\n', '')
    return data


# получение шапки патча
def get_patch_top_txt(path_to):
    data = get_full_txt(path_to)
    patch_body = data[data.find("/*") + 1: data.find("*/")]
    return patch_body


# парсинг переданных номеров патчей для получения интервалов
def parse_nums_patches_interval(sarg_line):
    sdk_num = sarg_line[sarg_line.find("s:") + 2: sarg_line.find(",", sarg_line.find("s:"))]
    base_num = sarg_line[sarg_line.find("b:") + 2: sarg_line.find(",", sarg_line.find("b:"))]
    proj_num = sarg_line[sarg_line.find("p:") + 2: sarg_line.find(",", sarg_line.find("p:"))]
    try:
        p1 = [int(sdk_num.split("-", 1)[0])] if len(sdk_num.split("-", 1)) < 2 else list(
            range(int(sdk_num.split("-", 1)[0]), int(sdk_num.split("-", 1)[1]) + 1))
    except ValueError:
        p1 = []
    try:
        p2 = [int(base_num.split("-", 1)[0])] if len(base_num.split("-", 1)) < 2 else list(
            range(int(base_num.split("-", 1)[0]), int(base_num.split("-", 1)[1]) + 1))
    except ValueError:
        p2 = []

    try:
        p3 = [int(proj_num.split("-", 1)[0])] if len(proj_num.split("-", 1)) < 2 else list(
            range(int(proj_num.split("-", 1)[0]), int(proj_num.split("-", 1)[1]) + 1))
    except ValueError:
        p3 = []

    return p1, p2, p3


# получение полного списка файлов - патчей для включения в документацию
def get_all_patch_files_by_nums(p_dir_sdk, p_dir_base, p_dir_proj, p_sdk=None, p_base=None, p_proj=None):
    fl_lst = []
    fl_sdk = []
    fl_base = []
    fl_proj = []
    # начнем обход папок для поиска патчей
    if p_dir_sdk != "":
        for p in p_sdk:
            xname = p_dir_sdk + "\\**\\*{0}.sql".format(str(p))
            lst_tm = glob.glob(xname, recursive=True)
            fl_lst += lst_tm
            fl_sdk += lst_tm
    if p_dir_base != "":
        for p in p_base:
            xname = p_dir_base + "\\**\\*{0}.sql".format(str(p))
            lst_tm = glob.glob(xname, recursive=True)
            fl_lst += lst_tm
            fl_base += lst_tm
    if p_dir_proj != "":
        for p in p_proj:
            xname = p_dir_proj + "\\**\\*{0}.sql".format(str(p))
            lst_tm = glob.glob(xname, recursive=True)
            fl_lst += lst_tm
            fl_proj += lst_tm

    fl_sdk = sorted(list(set(fl_sdk)))
    fl_base = sorted(list(set(fl_base)))
    fl_proj = sorted(list(set(fl_proj)))
    return fl_lst, fl_sdk, fl_base, fl_proj

# вызов создания патча из fw_patches
def make_patch_f(args):
    if args[0][:2].upper() == '-S':
        p = PatchPrepare(args[0][2:])
        args = args[1:]
        if not args:
            print ("Usage 'python Prepare.py [-Ssettings.conf] <template.sql> [re|<patch-number>|out <filename>]'")
    else:
        p = PatchPrepare()

    template = args[0]
    replace = None
    forceOutput = None
    if len(args) > 2:
        assert args[1] == '-out', 'Invalid option. Required re or patch-number or out <filename>'
        forceOutput = args[2]
    elif len(args) > 1:
        replace = args[1]

    p.prepare_impl(template, replace, forceOutput)

# периодическое сжатие логов
def zip_old_logs(logdir, critdays=7):
    current_time = time.time()

    if not os.path.exists(os.path.join(logdir, zip_log_name)):
        zarch = zipfile.ZipFile(os.path.join(logdir, zip_log_name), "w")
    else:
        zarch = zipfile.ZipFile(os.path.join(logdir, zip_log_name), "a")


    for f in os.listdir(logdir):
        creation_time = os.path.getctime(os.path.join(logdir, f))
        if (current_time - creation_time) // (24 * 3600) >= int(critdays) and "main" not in f:
            zarch.write(os.path.join(logdir, f), os.path.basename(os.path.join(logdir, f)))
            os.remove(os.path.join(logdir, f))
            logger.info('File {} replaced to zip log file.'.format(f))
            logger.info('File {} removed from log directory.'.format(f))
    return 0

# тестирование
def main():
    # _, tr_sdk, tr_base, tr_proj = get_all_patch_files_by_nums("D:\\FProjects\\database\\sdk\\database\\patches",
    #                                                           "D:\\FProjects\\database\\billing\\database\\patches",
    #                                                           "D:\\FProjects\\DISCOVERY\\patches",
    #                                                           [189, 190, 191],
    #                                                           [1617, 1618, 1619, 1620],
    #                                                           [31, 32, 33])
    # print(tr_sdk)
    # print(tr_base)
    # print(tr_proj)

    ls, lp, lk = parse_nums_patches_interval("[s:215-217,b:1691-1693,p:]")
    print(ls)
    print(lp)
    print(lk)


if __name__ == "__main__":
    main()
