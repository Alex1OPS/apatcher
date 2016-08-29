import os

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
