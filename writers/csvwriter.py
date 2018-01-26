import csv


def generate_update_log_context(doc_entity):
    list_patch = [jpatch.name_file_ for iproject in doc_entity.projects for jpatch in iproject.patches]
    return ["num", "patch"], [{"num": idx, "patch": item} for idx, item in enumerate(list_patch, start=1)]


def generate_changelist_context(doc_entity):
    list_patch = [[iproject, jpatch] for iproject in doc_entity.projects for jpatch in iproject.patches]
    return ["project", "version", "comment", "db_changed", "ui_changed"], \
           [{"project": item[0].project_name,
             "version": item[1].version_num,
             "comment": " ".join(item[1].comment.split()),
             "db_changed": ",".join(map(str, item[1].db_changed)),
             "ui_changed": ",".join(map(str, item[1].ui_changed))} for item in list_patch]


def generate_builds_changelist_context(doc_entity):
    dsub_builds = [x for x in doc_entity.projects if x.patches and len(x.patches) != 0]
    return ["project", "num", "comment"], \
           [{"project": xproj.project_name,
             "num": str(ypatch.version_num),
             "comment": " ".join(ypatch.comment.split())} for xproj in dsub_builds for ypatch in xproj.patches]


def render_save(columns, context, path_to):
    with open(path_to, "w+", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(context)
