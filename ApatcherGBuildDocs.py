import datetime
import logging
import os
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET

import fwpt_apatcher.ApatcherRDSettings as ARDS

PATH_LOCAL_DB_CACHE = "cfg/local_cache.db"
PATH_TMP_PREP_CACHE = "cfg/tmp_cache.txt"

logger = logging.getLogger(__name__)


class LocalDBCache:
    path_to = None
    path_build = None
    path_to_tmp = None
    db_inst = None
    connection_thread = None
    project_ext = None

    def __init__(self, path_build, project_ext, path_to=PATH_LOCAL_DB_CACHE, parse_svn=True):
        ldir = os.path.dirname(os.path.realpath(sys.argv[0]))
        self.path_build = path_build
        self.project_ext = project_ext
        self.path_to = os.path.join(ldir, path_to)
        self.path_to_tmp = os.path.join(ldir, PATH_TMP_PREP_CACHE)
        self.init_db()
        if parse_svn: self.init_parse_tmp_cache()

    def get_svn_log(self, begin_rev=None):
        cmd = ["svn", "log", "-v", "--limit", "100", "--xml", "--stop-on-copy"]
        log_t = subprocess.Popen(cmd, shell=False, cwd=self.path_build, stdout=subprocess.PIPE)
        log_text = log_t.communicate()[0]
        return log_text

    def init_db(self):
        try:
            conn = sqlite3.connect(self.path_to)
            db_cur = conn.cursor()
            db_cur.execute('''CREATE TABLE IF NOT EXISTS svn_build_revs
                                  (revision INTEGER PRIMARY KEY, comment TEXT, author TEXT, 
                                   dt_event DATETIME DEFAULT current_timestamp, n_version_build INTEGER,
                                   project_ext TEXT, files_list TEXT)''')
            conn.commit()
            self.connection_thread = conn
        except Exception as ex:
            logging.error("Local cache db error", ex)

    def init_parse_tmp_cache(self):
        conn = self.connection_thread
        db_cur = conn.cursor()
        content = self.get_svn_log()
        root = ET.fromstring(content)
        prepared_list = []
        # TODO добавить проверку путей при сохранении ревизий в ветках
        for child in root:
            rev = child.attrib['revision']
            dt = child.find('date').text
            author = child.find('author').text
            comment = child.find('msg').text
            if comment:
                comment = comment.replace("\n", " ")
            dt = datetime.datetime.strptime(dt[:19], "%Y-%m-%dT%H:%M:%S")
            n_version_num = None
            if "Auto build v." in comment:
                n_version_num = comment.split(" ")[-2].split(".")[-1].split("-")[-1]
            path_fs = child.find("paths")
            files = ",".join([x.text for x in path_fs])
            prepared_list.append((rev, comment, author, dt, n_version_num, self.project_ext, files))

        for item in prepared_list:
            try:
                db_cur.execute('INSERT OR IGNORE INTO svn_build_revs VALUES (?,?,?,?,?,?,?)', item)
            except Exception as ex:
                logging.error(ex)
        conn.commit()

    def get_last_cached_revision(self):
        conn = self.connection_thread
        cursor = conn.execute("SELECT max(revision) FROM svn_build_revs WHERE project_ext = ?", (self.project_ext,))
        rows = cursor.fetchall()
        return rows[0][0] if rows and len(rows) != 0 and len(rows[0]) != 0 else None


class BuildEntity:
    version_num = None
    author = None
    comment = None
    date = None

    def __init__(self, version_num, comment, author=None, date=None):
        self.version_num = version_num
        self.author = author
        self.comment = comment
        self.date = date

    def __str__(self):
        return "BuildEntity:\n\tversion={ver},\n\tauthor={author},\n\tcomment={comment}".format(ver=self.version_num,
                                                                                                author=self.author,
                                                                                                comment=self.comment)


class BuildProjectCorpus:
    project_name = None
    project_ext = None
    patches = []
    weight = None
    num_patches = []
    path_to = None

    def __init__(self, project_name=None, project_ext=None, patches=None, path_to=None):
        self.project_name = project_name
        self.project_ext = project_ext
        if patches is not None and len(patches) > 0:
            for x in patches:
                if not isinstance(x, BuildEntity):
                    raise TypeError("An invalid type for the build collection.")
            self.patches = patches
        else:
            self.patches = []
        self.path_to = path_to

    def set_primary(self, project_name, project_ext, weight, num_patches):
        self.weight = weight
        self.num_patches = num_patches
        self.project_ext = project_ext
        self.project_name = project_name

    def set_path_to_proj_svn(self, path_to):
        self.path_to = path_to

    def prepare(self, build_cfg):
        ldbc = LocalDBCache(path_build=self.path_to, project_ext=self.project_ext)

        if not self.project_ext.startswith("build_oss"):
            conn = ldbc.connection_thread
            query_ = """SELECT tb.n_version_build, 
                               group_concat(tb.comment, ';') AS comment
      FROM (SELECT (CASE 
                     WHEN a.author = 'builder' THEN ''
                     ELSE a.comment
                   END) AS comment,
                   (CASE
                     WHEN a.n_version_build IS NULL THEN
                      (SELECT min(t.n_version_build)
                         FROM svn_build_revs t
                        WHERE t.revision >= a.revision
                          AND t.project_ext = :EXT_PROJECT)
                     ELSE
                      a.n_version_build
                   END) AS n_version_build
              FROM svn_build_revs a
             WHERE a.project_ext = :EXT_PROJECT 
               AND a.revision > (SELECT revision FROM svn_build_revs WHERE project_ext = :EXT_PROJECT  AND n_version_build = :MIN_VERSION - 1) 
               AND a.revision <= (SELECT revision FROM svn_build_revs WHERE project_ext = :EXT_PROJECT  AND n_version_build = :MAX_VERSION)
             ORDER BY a.revision ASC) tb
    GROUP BY tb.n_version_build"""
            cursor = conn.execute(query_, {"EXT_PROJECT": self.project_ext, "MIN_VERSION": min(self.num_patches),
                                           "MAX_VERSION": max(self.num_patches)})
            rows = cursor.fetchall()
            for i in rows:
                _be = BuildEntity(version_num=i[0], comment=i[1])
                self.patches.append(_be)

    def __str__(self):
        return "BuildProjectCorpus:\n\tname={name},\n\text={ext},\n\tnum_versions={num}".format(name=self.project_name,
                                                                                                ext=self.project_ext,
                                                                                                num=self.num_patches)


def process_oss_build(l_build):
    l_add_oss_builds = []
    l_oss_del = []
    query_ = """SELECT tb.n_version_build, 
                       group_concat(tb.comment, ';') AS comment,
                       group_concat(files_list, ',')         
          FROM (SELECT (CASE 
                         WHEN a.author = 'builder' THEN ''
                         ELSE a.comment
                       END) AS comment,
                       (CASE
                         WHEN a.n_version_build IS NULL THEN
                          (SELECT min(t.n_version_build)
                             FROM svn_build_revs t
                            WHERE t.revision >= a.revision
                              AND t.project_ext = :EXT_PROJECT)
                         ELSE
                          a.n_version_build
                       END) AS n_version_build,
                       a.files_list
                  FROM svn_build_revs a
                 WHERE a.project_ext = :EXT_PROJECT 
                   AND a.revision > (SELECT revision FROM svn_build_revs WHERE project_ext = :EXT_PROJECT  AND n_version_build = :MIN_VERSION - 1) 
                   AND a.revision <= (SELECT revision FROM svn_build_revs WHERE project_ext = :EXT_PROJECT  AND n_version_build = :MAX_VERSION)
                 ORDER BY a.revision ASC) tb
        GROUP BY tb.n_version_build"""

    for i in l_build:
        if i.project_ext.startswith("build_oss"):
            l_oss_del.append(i)
            ldbc = LocalDBCache(path_build=i.path_to, project_ext=i.project_ext, parse_svn=False)
            conn = ldbc.connection_thread
            for jproj_key in ARDS.OSS_PLUGINS:
                _pc = BuildProjectCorpus()
                _pc.set_primary(project_name=jproj_key.upper(), project_ext=jproj_key,
                                weight=i.weight,
                                num_patches=i.num_patches)
                cursor = conn.execute(query_, {"EXT_PROJECT": i.project_ext, "MIN_VERSION": min(i.num_patches),
                                               "MAX_VERSION": max(i.num_patches)})
                rows = cursor.fetchall()
                for r_cur in rows:
                    files_committed = r_cur[2]
                    if not isinstance(files_committed, str): continue
                    files_committed = files_committed.split(",")
                    this_build = False
                    for prefix_build in ARDS.OSS_PLUGINS[jproj_key]:
                        if any(prefix_build in x for x in files_committed):
                            this_build = True
                            break
                    if this_build:
                        _be = BuildEntity(version_num=r_cur[0], comment=r_cur[1])
                        _pc.patches.append(_be)

                l_add_oss_builds.append(_pc)
    l_build.extend(l_add_oss_builds)
    for idel in l_oss_del: l_build.remove(idel)
