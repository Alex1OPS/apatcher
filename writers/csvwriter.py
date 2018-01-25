import csv


def generate_update_log_context(doc_entity):
    list_patch = [jpatch.name_file_ for iproject in doc_entity.projects for jpatch in iproject.patches]
    return ["num", "patch"], [{"num": idx, "patch": item} for idx, item in enumerate(list_patch, start=1)]


def generate_changelist_context(doc_entity):
    return [], []


def generate_builds_changelist_context(doc_entity):
    return [], []


def render_save(columns, context, path_to):
    with open(path_to, "w+", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(context)
