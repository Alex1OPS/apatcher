class ProjectPatchEntity:
    version_num = None
    changed_files = []
    db_changed = []
    ui_changed = []
    comment = None
    author = None
    path_patch_ = None

    def __init__(self, version_num, author, changed_files, ui_changed, db_changed, comment):
        self.version_num = version_num
        self.author = author
        self.changed_files = changed_files
        self.ui_changed = ui_changed
        self.db_changed = db_changed
        self.comment = comment

    def initFromSource(self, path_patch_):
        self.path_patch_ = path_patch_
        self.init_from_exists()

    def init_from_exists(self):
        pass

    def __str__(self):
        print("PatchEntity:\nversion={ver}, comment={comment},\n".format(ver=self.version_num, comment=self.comment))


class ProjectCorpus:
    project_name = None
    project_ext = None
    patches = []

    def __init__(self, project_name, project_ext, patches):
        self.project_name = project_name
        self.project_ext = project_ext
        for x in patches:
            if not isinstance(x, ProjectPatchEntity):
                raise TypeError("An invalid type for the project patch collection.")
        self.patches = patches


class DocEntity:
    doc_name = None
    projects = []

    def __init__(self, doc_name, projects):
        self.doc_name = doc_name
        for x in projects:
            if not isinstance(x, ProjectCorpus):
                raise TypeError("An invalid type for the project corpus in document.")
        self.projects = projects
