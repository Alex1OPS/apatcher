import os
import subprocess
import sqlite3
import sys
import logging
import re
import datetime

PATH_LOCAL_DB_CACHE = "cfg/local_cache.db"
PATH_TMP_PREP_CACHE = "cfg/tmp_cache.txt"

logger = logging.getLogger(__name__)


class LocalDBCache:
    path_to = None
    path_build = None
    path_to_tmp = None
    db_inst = None
    connection_thread = None

    def __init__(self, path_build, path_to=PATH_LOCAL_DB_CACHE):
        ldir = os.path.dirname(os.path.realpath(sys.argv[0]))
        self.path_build = path_build
        self.path_to = os.path.join(ldir, path_to)
        self.path_to_tmp = os.path.join(ldir, PATH_TMP_PREP_CACHE)
        self.init_db()
        if not os.path.isfile(self.path_to):
            self.get_svn_log()
        else:
            os.remove(self.path_to_tmp)
            last_rev = self.get_last_cached_revision()
            try:
                self.get_svn_log(begin_rev=last_rev + 1)
            except Exception as ex:
                logging.error(ex)
        self.init_parse_tmp_cache()

    def get_svn_log(self, begin_rev=None):
        cmd = "svn log"
        add_cmd = " -r {begin}:HEAD"
        if begin_rev:
            cmd = "".join([cmd, add_cmd.format(begin=begin_rev)])

        with open(self.path_to_tmp, "w") as f:
            subprocess.call(cmd, stdout=f, shell=False, cwd=self.path_build)

    def init_db(self):
        try:
            conn = sqlite3.connect(self.path_to)
            db_cur = conn.cursor()
            db_cur.execute('''CREATE TABLE IF NOT EXISTS svn_build_revs
                                  (revision INTEGER PRIMARY KEY, comment TEXT, author TEXT, 
                                   dt_event DATETIME DEFAULT current_timestamp, n_version_build INTEGER)''')
            conn.commit()
            self.connection_thread = conn
        except Exception as ex:
            logging.error("Local cache db error", ex)

    def init_parse_tmp_cache(self):
        conn = self.connection_thread
        db_cur = conn.cursor()
        with open(self.path_to_tmp, "r") as f:
            content = f.read()
        rr = content.split("------------------------------------------------------------------------\n")
        rr = filter(lambda h: len(h) != 0, rr)
        m = re.compile("Auto build v. 3.0 - 8.RC1.(\d*?) V(\d)")
        prepared_list = []
        try:
            for i in rr:
                x = i.split(" | ")
                rev = int(x[0].replace("r", ""))
                author = x[1]
                dt = datetime.datetime.strptime(x[2][:18], "%Y-%m-%d %H:%M:%S")
                comment = x[3].split("\n\n")[1]
                p = m.findall(comment)
                n_version_num = None
                if p and len(p) != 0 and len(p[0]) != 0:
                    n_version_num = p[0][0]
                prepared_list.append((rev, comment, author, dt, n_version_num))
        except Exception as ex:
            logging.error(ex)

        try:
            for item in prepared_list:
                db_cur.execute('INSERT INTO svn_build_revs VALUES (?,?,?,?,?)', item)
        except Exception as ex:
            logging.error(ex)
        conn.commit()

    def get_last_cached_revision(self):
        conn = self.connection_thread
        cursor = conn.execute("SELECT max(revision) FROM svn_build_revs")
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

    def prepare(self):
        ldbc = LocalDBCache(self.path_to)
        conn = ldbc.connection_thread
        query_ = """SELECT tb.n_version_build, 
	  group_concat(tb.comment) AS comment
  FROM (SELECT (CASE 
			     WHEN instr(a.comment, 'Auto build v. 3.0') != 0 THEN ''
				 ELSE a.comment
			   END) AS comment,
               (CASE
                 WHEN a.n_version_build IS NULL THEN
                  (SELECT min(t.n_version_build)
                     FROM svn_build_revs t
                    WHERE t.revision >= a.revision)
                 ELSE
                  a.n_version_build
               END) AS n_version_build
          FROM svn_build_revs a
         WHERE a.revision BETWEEN (SELECT revision FROM svn_build_revs
                                    WHERE n_version_build = ?) 
				   AND (SELECT revision FROM svn_build_revs
                 WHERE n_version_build = ?)
         ORDER BY a.revision ASC) tb
GROUP BY tb.n_version_build"""
        cursor = conn.execute(query_, (min(self.num_patches), max(self.num_patches),))
        rows = cursor.fetchall()
        for i in rows:
            _be = BuildEntity(version_num=i[0], comment=i[1])
            self.patches.append(_be)

    def __str__(self):
        return "BuildProjectCorpus:\n\tname={name},\n\text={ext},\n\tnum_versions={num}".format(name=self.project_name,
                                                                                                ext=self.project_ext,
                                                                                                num=self.num_patches)
