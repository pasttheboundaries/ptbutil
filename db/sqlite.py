import sqlite3


def create_table(con, schema):
    con.execute(schema)
    con.commit()


def get_connection(db_path):
    con = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    con.row_factory = sqlite3.Row
    return con


def get_tables_list(con):
    return con.execute("SELECT * FROM sqlite_master WHERE type='table'").fetchall()


class InstanceSqlite:
    def __init__(self, path):
        self.path = path

    def connection(self):
        return get_connection(self.path)